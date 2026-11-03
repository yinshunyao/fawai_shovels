#!/usr/bin/env python3
"""几行中文合成一张小红书竖版字图（3:4）。

用法：改 __main__ 里的 LINES / OUT 后运行
  python3 fawai_shovels/python/xhs-text-card.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = (1080, 1440)
BG = (247, 244, 238)
INK = (28, 28, 28)
MUTED = (90, 86, 80)
RULE = (196, 122, 74)

FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    last: Exception | None = None
    for path in FONT_CANDIDATES:
        p = Path(path)
        if not p.exists():
            continue
        try:
            return ImageFont.truetype(str(p), size=size, index=0)
        except Exception as exc:  # noqa: BLE001
            last = exc
            try:
                return ImageFont.truetype(str(p), size=size)
            except Exception as exc2:  # noqa: BLE001
                last = exc2
    raise RuntimeError(f"no Chinese font; last={last}")


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def render_text_card(lines: list[str], out: Path, kicker: str = "") -> None:
    cleaned = [line.strip() for line in lines if line.strip()]
    if not cleaned:
        raise ValueError("lines is empty")
    width, height = SIZE
    image = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 18), fill=RULE)

    kicker_font = _font(36)
    body_font = _font(64)
    gap = 56
    kicker_gap = 72 if kicker.strip() else 0
    body_heights = []
    for line in cleaned:
        box = draw.textbbox((0, 0), line, font=body_font)
        body_heights.append(box[3] - box[1])
    kicker_h = 0
    if kicker.strip():
        box = draw.textbbox((0, 0), kicker.strip(), font=kicker_font)
        kicker_h = box[3] - box[1]
    block_h = kicker_h + kicker_gap + sum(body_heights) + gap * (len(cleaned) - 1)
    y = (height - block_h) // 2

    if kicker.strip():
        label = kicker.strip()
        x = (width - _text_width(draw, label, kicker_font)) // 2
        draw.text((x, y), label, font=kicker_font, fill=MUTED)
        y += kicker_h + kicker_gap

    for line, line_h in zip(cleaned, body_heights):
        x = (width - _text_width(draw, line, body_font)) // 2
        draw.text((x, y), line, font=body_font, fill=INK)
        y += line_h + gap

    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, format="PNG")


if __name__ == "__main__":
    KICKER = "需求对接群"
    LINES = [
        "有软件需求的，进这个群",
        "做开发的，也进这个群",
        "同一个群里对接",
    ]
    OUT = (
        "study/介绍案例/小红书宣传/需求对接群宣传/"
        "文案2_20261028_两边都进群对接/小红书/01_封面.png"
    )
    render_text_card(LINES, Path(OUT), kicker=KICKER)
    print(OUT)
