#!/usr/bin/env bash
# Download COCO 2017 detect packs (train/val images + trainval annotations) into DEST.
# Usage:
#   DEST=<数据目录> bash hipp-tools/shell/download-coco2017.sh
#   bash hipp-tools/shell/download-coco2017.sh <数据目录>
# Optional:
#   COCO_SKIP_TRAIN=1   only val + annotations
#   COCO_WITH_TEST=1    also test2017 images + image_info (no public boxes)
#   COCO_UNZIP=0        download only (default 1 = unzip after each zip)
#   COCO_KEEP_ZIP=1     keep zip files after unzip (ignored when COCO_UNZIP=0)
set -euo pipefail

DEST="${DEST:-${1:-}}"
if [[ -z "${DEST}" ]]; then
  echo "用法: DEST=<数据目录> $0" >&2
  echo "  或: $0 <数据目录>" >&2
  exit 1
fi

SKIP_TRAIN="${COCO_SKIP_TRAIN:-0}"
WITH_TEST="${COCO_WITH_TEST:-0}"
UNZIP_AFTER="${COCO_UNZIP:-1}"
KEEP_ZIP="${COCO_KEEP_ZIP:-0}"

mkdir -p "${DEST}"
cd "${DEST}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "缺少命令: $1" >&2
    exit 1
  }
}
need_cmd wget
need_cmd unzip

download_one() {
  local url="$1"
  local name
  name="$(basename "${url}")"
  echo "==> 下载 ${name}"
  wget -c --show-progress -O "${name}" "${url}"
}

unzip_one() {
  local zip="$1"
  if [[ ! -f "${zip}" ]]; then
    echo "找不到 ${zip}，跳过解压" >&2
    return 1
  fi
  echo "==> 解压 ${zip}"
  unzip -n "${zip}"
  if [[ "${KEEP_ZIP}" != "1" ]]; then
    rm -f "${zip}"
    echo "==> 已删除 ${zip}"
  fi
}

maybe_unzip() {
  if [[ "${UNZIP_AFTER}" == "1" ]]; then
    unzip_one "$1"
  else
    echo "==> 跳过解压 ${1}（COCO_UNZIP=0）"
  fi
}

# Smallest first so the tree becomes usable sooner.
download_one "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
maybe_unzip "annotations_trainval2017.zip"

download_one "http://images.cocodataset.org/zips/val2017.zip"
maybe_unzip "val2017.zip"

if [[ "${SKIP_TRAIN}" != "1" ]]; then
  download_one "http://images.cocodataset.org/zips/train2017.zip"
  maybe_unzip "train2017.zip"
else
  echo "==> 跳过 train2017（COCO_SKIP_TRAIN=1）"
fi

if [[ "${WITH_TEST}" == "1" ]]; then
  download_one "http://images.cocodataset.org/annotations/image_info_test2017.zip"
  maybe_unzip "image_info_test2017.zip"
  download_one "http://images.cocodataset.org/zips/test2017.zip"
  maybe_unzip "test2017.zip"
fi

echo "==> 完成。目录: ${DEST}"
ls -la "${DEST}"
