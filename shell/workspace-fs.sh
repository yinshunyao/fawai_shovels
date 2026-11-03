#!/usr/bin/env bash
# Thin launcher for python/workspace-fs.py (Cursor-like read/grep/glob outside Cursor).
#
# Usage:
#   bash fawai_shovels/shell/workspace-fs.sh read <file> [--offset N] [--limit N]
#   bash fawai_shovels/shell/workspace-fs.sh grep <pattern> [--path DIR] [--glob '*.py']
#   bash fawai_shovels/shell/workspace-fs.sh glob '**/*.md' [--path DIR]
#   bash fawai_shovels/shell/workspace-fs.sh catalog rsync

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${WORKSPACE_FS_PYTHON:-${PYTHON:-python3}}"
exec "$PYTHON" "$ROOT/python/workspace-fs.py" "$@"
