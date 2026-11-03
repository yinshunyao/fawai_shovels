#!/usr/bin/env bash
# --- shovel ---
# id: workspace_fs_sh
# title: Launcher for workspace-fs.py
# when_to_use: Prefer bash entry to Cursor-like read/grep/glob/catalog
# runtime: bash
# kind: launcher
# requires: bash, python3
# side_effects: fs_read
# platforms: macOS,Linux
# tags: fs,launcher
# privacy: public
# completeness: 5
# generality: 5
# efficiency: 5
# invoke: bash fawai_shovels/shell/workspace-fs.sh catalog rsync
# depends_shovels: workspace_fs
# --- end-shovel ---
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
