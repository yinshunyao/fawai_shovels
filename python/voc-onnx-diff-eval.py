#!/usr/bin/env python3
# --- shovel ---
# id: voc_onnx_diff_eval
# title: VOC vs ONNX detection IoU diff
# when_to_use: Compare ONNX detector outputs to VOC boxes and dump FP/FN visuals
# runtime: python
# kind: shovel
# requires: onnxruntime, numpy, opencv-python; optional Pillow
# side_effects: fs_read,fs_write
# platforms: macOS,Linux,Windows
# tags: eval,onnx,voc
# privacy: public
# completeness: 3
# generality: 3
# efficiency: 2
# invoke: python3 fawai_shovels/python/voc-onnx-diff-eval.py
# depends_shovels: 
# --- end-shovel ---
"""Pascal VOC 上跑 RT-DETRv2 ONNX，按 IoU 匹配后输出与标注的差异。

用途：本地用已导出的 .onnx 对 VOC 包做推理，与 Annotations 在给定 IoU
阈值下匹配，写出汇总、jsonl，以及差异可视化（默认只落有 FP/FN 的图）。

依赖：onnxruntime、numpy、opencv-python（或 cv2）、Pillow（可选，无则只用 cv2）。
"""

from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort


@dataclass
class Box:
    label: str
    xyxy: list[float]
    score: float = 1.0
    match: str = ""  # tp / fp / fn
    iou: float = 0.0


@dataclass
class ImageResult:
    file_name: str
    stem: str
    package: str
    width: int
    height: int
    predictions: list[dict[str, Any]] = field(default_factory=list)
    ground_truth: list[dict[str, Any]] = field(default_factory=list)
    tp: int = 0
    fp: int = 0
    fn: int = 0
    has_diff: bool = False


def iou_xyxy(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return float(inter / (area_a + area_b - inter + 1e-9))


def parse_voc_xml(path: Path, keep_labels: set[str] | None) -> tuple[int, int, list[Box]]:
    root = ET.parse(path).getroot()
    size = root.find("size")
    w = int(size.findtext("width") or 0) if size is not None else 0
    h = int(size.findtext("height") or 0) if size is not None else 0
    boxes: list[Box] = []
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        if keep_labels is not None and name not in keep_labels:
            continue
        bb = obj.find("bndbox")
        if bb is None:
            continue
        boxes.append(
            Box(
                label=name,
                xyxy=[
                    float(bb.findtext("xmin") or 0),
                    float(bb.findtext("ymin") or 0),
                    float(bb.findtext("xmax") or 0),
                    float(bb.findtext("ymax") or 0),
                ],
            )
        )
    return w, h, boxes


def match_iou(
    preds: list[Box], gts: list[Box], iou_thr: float
) -> tuple[list[Box], list[Box], int, int, int]:
    """同类 greedy 匹配；返回打过 match 标记的 preds/gts 与计数。"""
    preds_out = [
        Box(label=p.label, xyxy=list(p.xyxy), score=p.score, match="fp", iou=0.0)
        for p in preds
    ]
    gts_out = [
        Box(label=g.label, xyxy=list(g.xyxy), score=1.0, match="fn", iou=0.0)
        for g in gts
    ]
    used_gt: set[int] = set()
    order = sorted(range(len(preds_out)), key=lambda i: -preds_out[i].score)
    for pi in order:
        p = preds_out[pi]
        best_i, best_iou = None, 0.0
        for gi, g in enumerate(gts_out):
            if gi in used_gt or g.label != p.label:
                continue
            iou = iou_xyxy(p.xyxy, g.xyxy)
            if iou >= iou_thr and iou > best_iou:
                best_iou, best_i = iou, gi
        if best_i is not None:
            used_gt.add(best_i)
            p.match = "tp"
            p.iou = best_iou
            gts_out[best_i].match = "tp"
            gts_out[best_i].iou = best_iou
    tp = sum(1 for p in preds_out if p.match == "tp")
    fp = sum(1 for p in preds_out if p.match == "fp")
    fn = sum(1 for g in gts_out if g.match == "fn")
    return preds_out, gts_out, tp, fp, fn


def preprocess_bgr(bgr: np.ndarray, imgsz: int) -> tuple[np.ndarray, int, int]:
    h, w = bgr.shape[:2]
    work = bgr
    if work.ndim == 2:
        work = cv2.cvtColor(work, cv2.COLOR_GRAY2BGR)
    elif work.ndim == 3 and work.shape[2] == 1:
        work = cv2.cvtColor(work[:, :, 0], cv2.COLOR_GRAY2BGR)
    rgb = cv2.cvtColor(work, cv2.COLOR_BGR2RGB)
    side = max(1, int(imgsz))
    if rgb.shape[0] != side or rgb.shape[1] != side:
        rgb = cv2.resize(rgb, (side, side), interpolation=cv2.INTER_LINEAR)
    ten = np.ascontiguousarray(rgb).transpose(2, 0, 1).astype(np.float32) / 255.0
    return ten[None, ...], w, h


class OnnxDetector:
    def __init__(self, model_path: Path, class_names: list[str], imgsz: int = 1024):
        self.names = list(class_names)
        self.imgsz = int(imgsz)
        self.session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        inputs = self.session.get_inputs()
        self.image_name = inputs[0].name
        self.size_name = inputs[1].name if len(inputs) > 1 else "orig_target_sizes"
        outs = [o.name for o in self.session.get_outputs()]
        if all(n in outs for n in ("labels", "boxes", "scores")):
            self.out_names = ["labels", "boxes", "scores"]
        else:
            self.out_names = outs[:3]

    def predict(self, bgr: np.ndarray, conf: float) -> list[Box]:
        images, w, h = preprocess_bgr(bgr, self.imgsz)
        sizes = np.asarray([[int(w), int(h)]], dtype=np.int64)
        labels, boxes, scores = self.session.run(
            self.out_names, {self.image_name: images, self.size_name: sizes}
        )
        labels_a = np.asarray(labels)
        boxes_a = np.asarray(boxes)
        scores_a = np.asarray(scores)
        if labels_a.ndim == 1:
            labels_a = labels_a[None, ...]
            boxes_a = boxes_a[None, ...]
            scores_a = scores_a[None, ...]
        out: list[Box] = []
        lab, box, sco = labels_a[0], boxes_a[0], scores_a[0]
        n = min(len(lab), len(box), len(sco))
        for i in range(n):
            score = float(sco[i])
            if score < conf:
                continue
            xyxy = np.asarray(box[i], dtype=float).reshape(-1)
            if xyxy.size < 4:
                continue
            cls_id = int(lab[i])
            name = self.names[cls_id] if 0 <= cls_id < len(self.names) else str(cls_id)
            out.append(
                Box(
                    label=name,
                    xyxy=[float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])],
                    score=score,
                )
            )
        return out


# BGR
_COLOR = {
    "tp": (80, 180, 80),
    "fp": (40, 40, 220),
    "fn": (0, 200, 255),
    "gt_other": (160, 160, 160),
}


def draw_diff(
    bgr: np.ndarray,
    preds: list[Box],
    gts: list[Box],
    *,
    title: str,
) -> np.ndarray:
    canvas = bgr.copy()
    for g in gts:
        color = _COLOR.get(g.match, _COLOR["fn"])
        x1, y1, x2, y2 = [int(round(v)) for v in g.xyxy]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        tag = f"GT/{g.match} {g.label}"
        cv2.putText(
            canvas, tag, (x1, max(16, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1
        )
    for p in preds:
        color = _COLOR.get(p.match, _COLOR["fp"])
        x1, y1, x2, y2 = [int(round(v)) for v in p.xyxy]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        tag = f"P/{p.match} {p.label} {p.score:.2f}"
        cv2.putText(
            canvas, tag, (x1, min(canvas.shape[0] - 4, y2 + 14)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1,
        )
    legend = "green=TP  red=FP  yellow=FN(GT miss)  |  " + title
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 28), (30, 30, 30), -1)
    cv2.putText(
        canvas, legend, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1
    )
    return canvas


def eval_voc_dir(
    voc_dir: Path,
    detector: OnnxDetector,
    *,
    conf: float,
    iou_thr: float,
    eval_labels: set[str],
    out_dir: Path,
    save_all_vis: bool = False,
) -> dict[str, Any]:
    voc_dir = voc_dir.resolve()
    jpeg = voc_dir / "JPEGImages"
    ann = voc_dir / "Annotations"
    if not jpeg.is_dir() or not ann.is_dir():
        raise FileNotFoundError(f"VOC 缺少 JPEGImages/Annotations: {voc_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    vis_diff = out_dir / "vis_diff"
    vis_all = out_dir / "vis_all"
    vis_diff.mkdir(exist_ok=True)
    if save_all_vis:
        vis_all.mkdir(exist_ok=True)

    pred_path = out_dir / "predictions.jsonl"
    images = sorted(jpeg.glob("*.jpg")) + sorted(jpeg.glob("*.png"))
    package = voc_dir.name
    totals = Counter()
    per_class = defaultdict(lambda: Counter())
    gt_label_all = Counter()
    gt_label_eval = Counter()
    latency_ms: list[float] = []
    rows: list[ImageResult] = []

    with pred_path.open("w", encoding="utf-8") as fout:
        for idx, img_path in enumerate(images, start=1):
            xml_path = ann / f"{img_path.stem}.xml"
            if not xml_path.is_file():
                continue
            # 全量标注统计（含模型未训类）
            _, _, all_gt = parse_voc_xml(xml_path, keep_labels=None)
            for g in all_gt:
                gt_label_all[g.label] += 1
            w_xml, h_xml, gts = parse_voc_xml(xml_path, keep_labels=eval_labels)
            for g in gts:
                gt_label_eval[g.label] += 1

            bgr = cv2.imread(str(img_path))
            if bgr is None:
                continue
            h, w = bgr.shape[:2]
            if w_xml <= 0:
                w_xml, h_xml = w, h

            t0 = time.perf_counter()
            raw_preds = detector.predict(bgr, conf=conf)
            latency_ms.append((time.perf_counter() - t0) * 1000.0)
            # 只保留评测类
            preds = [p for p in raw_preds if p.label in eval_labels]
            preds_m, gts_m, tp, fp, fn = match_iou(preds, gts, iou_thr)
            totals["tp"] += tp
            totals["fp"] += fp
            totals["fn"] += fn
            totals["images"] += 1
            if gts:
                totals["images_with_gt"] += 1
                if tp > 0:
                    totals["images_hit"] += 1
            for p in preds_m:
                per_class[p.label][p.match] += 1
            for g in gts_m:
                if g.match == "fn":
                    per_class[g.label]["fn"] += 1

            has_diff = fp > 0 or fn > 0
            if has_diff:
                totals["images_diff"] += 1

            rec = ImageResult(
                file_name=img_path.name,
                stem=img_path.stem,
                package=package,
                width=w_xml,
                height=h_xml,
                predictions=[asdict(p) for p in preds_m],
                ground_truth=[asdict(g) for g in gts_m],
                tp=tp,
                fp=fp,
                fn=fn,
                has_diff=has_diff,
            )
            # 附带未参与匹配的其它 GT 类，便于对照标注
            other_gt = [
                asdict(Box(label=g.label, xyxy=g.xyxy, match="ignored"))
                for g in all_gt
                if g.label not in eval_labels
            ]
            payload = asdict(rec)
            payload["ground_truth_ignored"] = other_gt
            fout.write(json.dumps(payload, ensure_ascii=False) + "\n")
            rows.append(rec)

            title = f"{package} {img_path.name} tp={tp} fp={fp} fn={fn}"
            canvas = draw_diff(bgr, preds_m, gts_m, title=title)
            if has_diff:
                cv2.imwrite(str(vis_diff / img_path.name), canvas)
            if save_all_vis:
                cv2.imwrite(str(vis_all / img_path.name), canvas)

            if idx == 1 or idx % 20 == 0 or idx == len(images):
                print(f"[{package}] {idx}/{len(images)} {img_path.name} tp={tp} fp={fp} fn={fn}")

    def prf(tp: int, fp: int, fn: int) -> dict[str, float]:
        r = tp / (tp + fn) if (tp + fn) else 0.0
        p = tp / (tp + fp) if (tp + fp) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        return {"recall": r, "precision": p, "f1": f1}

    per_class_out: dict[str, Any] = {}
    for label, c in sorted(per_class.items()):
        tp, fp, fn = int(c["tp"]), int(c["fp"]), int(c["fn"])
        per_class_out[label] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            **prf(tp, fp, fn),
        }

    summary = {
        "package": package,
        "voc_dir": str(voc_dir),
        "out_dir": str(out_dir),
        "images": int(totals["images"]),
        "images_with_eval_gt": int(totals["images_with_gt"]),
        "images_hit": int(totals["images_hit"]),
        "images_diff": int(totals["images_diff"]),
        "conf": conf,
        "iou_thr": iou_thr,
        "eval_labels": sorted(eval_labels),
        "tp": int(totals["tp"]),
        "fp": int(totals["fp"]),
        "fn": int(totals["fn"]),
        **prf(int(totals["tp"]), int(totals["fp"]), int(totals["fn"])),
        "per_class": per_class_out,
        "gt_boxes_all_labels": dict(gt_label_all),
        "gt_boxes_eval_labels": dict(gt_label_eval),
        "latency_ms": {
            "mean": float(np.mean(latency_ms)) if latency_ms else 0.0,
            "p50": float(np.median(latency_ms)) if latency_ms else 0.0,
            "n": len(latency_ms),
        },
        "predictions_path": str(pred_path),
        "vis_diff_dir": str(vis_diff),
        "vis_note": "vis_diff 仅含 IoU 匹配后仍有 FP 或 FN 的图；绿=TP 红=FP 黄=漏检GT",
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def run(
    model_path: Path,
    class_names: list[str],
    voc_dirs: list[Path],
    out_root: Path,
    *,
    conf: float = 0.5,
    iou_thr: float = 0.5,
    imgsz: int = 1024,
    save_all_vis: bool = False,
) -> dict[str, Any]:
    detector = OnnxDetector(model_path, class_names=class_names, imgsz=imgsz)
    eval_labels = set(class_names)
    out_root.mkdir(parents=True, exist_ok=True)
    package_summaries = []
    for voc in voc_dirs:
        sub = out_root / voc.name
        print(f"=== eval {voc} -> {sub} ===")
        summary = eval_voc_dir(
            voc,
            detector,
            conf=conf,
            iou_thr=iou_thr,
            eval_labels=eval_labels,
            out_dir=sub,
            save_all_vis=save_all_vis,
        )
        package_summaries.append(summary)
        print(
            f"  tp={summary['tp']} fp={summary['fp']} fn={summary['fn']} "
            f"R={summary['recall']:.3f} P={summary['precision']:.3f} "
            f"diff_images={summary['images_diff']}"
        )

    # 合并
    merge_tp = sum(s["tp"] for s in package_summaries)
    merge_fp = sum(s["fp"] for s in package_summaries)
    merge_fn = sum(s["fn"] for s in package_summaries)
    def prf(tp, fp, fn):
        r = tp / (tp + fn) if (tp + fn) else 0.0
        p = tp / (tp + fp) if (tp + fp) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        return {"recall": r, "precision": p, "f1": f1}

    merged = {
        "model_path": str(model_path),
        "class_names": class_names,
        "conf": conf,
        "iou_thr": iou_thr,
        "packages": [s["package"] for s in package_summaries],
        "tp": merge_tp,
        "fp": merge_fp,
        "fn": merge_fn,
        **prf(merge_tp, merge_fp, merge_fn),
        "per_package": package_summaries,
    }
    (out_root / "summary.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    readme = out_root / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# ONNX VOC 差异评测",
                "",
                f"- 模型：`{model_path}`",
                f"- 置信度 / IoU：`{conf}` / `{iou_thr}`",
                f"- 评测类：{', '.join(class_names)}",
                f"- 合计 TP/FP/FN = {merge_tp}/{merge_fp}/{merge_fn}；"
                f"R={merged['recall']:.3f} P={merged['precision']:.3f} F1={merged['f1']:.3f}",
                "",
                "各包目录含 `summary.json`、`predictions.jsonl`、`vis_diff/`（仅有差异的图）。",
                "框色：绿=TP，红=FP，黄=漏检 GT。VOC 里未训类只记在 jsonl 的 `ground_truth_ignored`。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return merged


if __name__ == "__main__":
    # 本地：3.3.1 权重测 B05 / B06 VOC，差异图另存
    MODEL_PATH = Path("/Volumes/shunyao-h1/scanly/训练结果/v3.3/v3.3.1/3.3.1.onnx")
    CLASS_NAMES = ["GlueSeam", "Tackless", "GlueGap"]
    DATA_ROOT = Path("/Users/shunyaoyin/Documents/ai-company/scanly/样本数据/GlueGap")
    VOC_DIRS = [
        DATA_ROOT / "B05-1022-voc",
        DATA_ROOT / "B06-1022-voc",
    ]
    OUT_ROOT = Path(
        "/Volumes/shunyao-h1/scanly/训练结果/v3.3/v3.3.1/eval_B05B06_本地"
    )
    CONF = 0.5
    IOU_THR = 0.5
    IMGSZ = 1024
    SAVE_ALL_VIS = False  # True 时额外写 vis_all/

    run(
        model_path=MODEL_PATH,
        class_names=CLASS_NAMES,
        voc_dirs=VOC_DIRS,
        out_root=OUT_ROOT,
        conf=CONF,
        iou_thr=IOU_THR,
        imgsz=IMGSZ,
        save_all_vis=SAVE_ALL_VIS,
    )
