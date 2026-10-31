#!/usr/bin/env bash
# Thin launcher for python/workspace-fs.py (Cursor-like read/grep/glob outside Cursor).
#
# Usage:
#   bash hipp-tools/shell/workspace-fs.sh read <file> [--offset N] [--limit N]
#   bash hipp-tools/shell/workspace-fs.sh grep <pattern> [--path DIR] [--glob '*.py']
#   bash hipp-tools/shell/workspace-fs.sh glob '**/*.md' [--path DIR]
#   bash hipp-tools/shell/workspace-fs.sh catalog rsync

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${WORKSPACE_FS_PYTHON:-${PYTHON:-python3}}"
exec "$PYTHON" "$ROOT/python/workspace-fs.py" "$@"
