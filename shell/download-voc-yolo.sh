#!/usr/bin/env bash
# --- shovel ---
# id: download_voc_yolo
# title: Download YOLO VOC.yaml zip packs
# when_to_use: Need Ultralytics VOC.yaml release zips (2007/2012)
# runtime: bash
# kind: shovel
# requires: bash, curl|wget; unzip if VOC_UNZIP=1
# side_effects: network,fs_write
# platforms: macOS,Linux
# tags: dataset,voc,yolo
# privacy: public
# completeness: 4
# generality: 4
# efficiency: 4
# invoke: DEST=<data-dir> bash fawai_shovels/shell/download-voc-yolo.sh
# depends_shovels: 
# --- end-shovel ---
# Download PASCAL VOC packs used by Ultralytics YOLO VOC.yaml (2007 trainval/test + 2012 trainval).
# Default: download archives only (no unzip). Uses Ultralytics GitHub release assets (.zip), same as VOC.yaml.
# Usage:
#   DEST=<数据目录> bash fawai_shovels/shell/download-voc-yolo.sh
#   bash fawai_shovels/shell/download-voc-yolo.sh <数据目录>
# Optional:
#   VOC_UNZIP=1   also unzip after download (needs unzip + enough free space)
set -euo pipefail

DEST="${DEST:-${1:-}}"
if [[ -z "${DEST}" ]]; then
  echo "用法: DEST=<数据目录> $0" >&2
  echo "  或: $0 <数据目录>" >&2
  exit 1
fi

UNZIP="${VOC_UNZIP:-0}"
ASSETS_BASE="${VOC_ASSETS_BASE:-https://github.com/ultralytics/assets/releases/download/v0.0.0}"

mkdir -p "${DEST}"
cd "${DEST}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "缺少命令: $1" >&2
    exit 1
  }
}
need_cmd wget
if [[ "${UNZIP}" == "1" ]]; then
  need_cmd unzip
fi

# Same three packs as ultralytics/cfg/datasets/VOC.yaml
NAMES=(
  "VOCtrainval_06-Nov-2007.zip"
  "VOCtest_06-Nov-2007.zip"
  "VOCtrainval_11-May-2012.zip"
)

download_one() {
  local name="$1"
  local url="${ASSETS_BASE}/${name}"
  # Drop empty / failed partials so wget -c does not stick on a 0-byte file
  if [[ -f "${name}" && ! -s "${name}" ]]; then
    rm -f "${name}"
  fi
  echo "==> 下载 ${name}"
  wget -c --show-progress -O "${name}" "${url}"
}

for name in "${NAMES[@]}"; do
  download_one "${name}"
done

if [[ "${UNZIP}" == "1" ]]; then
  for name in "${NAMES[@]}"; do
    echo "==> 解压 ${name}"
    unzip -n "${name}"
  done
fi

echo "==> 完成: ${DEST}"
ls -lh "${NAMES[@]}"
