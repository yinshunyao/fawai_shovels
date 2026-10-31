#!/usr/bin/env bash
# Build and upload a Python project (pyproject.toml) to PyPI via twine.
#
# Required:
#   PUBLISH_ROOT   directory containing pyproject.toml
# Optional:
#   PUBLISH_REPO   twine repository name (default: pypi)
#   PUBLISH_DRY=1  build only, do not upload
#   PUBLISH_PYTHON interpreter (default: python3; prefers local miniconda if present)
#   PUBLISH_CLEAN_GLOBS  space-separated paths under PUBLISH_ROOT to rm -rf before build
#                        (default: dist build *.egg-info)

set -euo pipefail

: "${PUBLISH_ROOT:?set PUBLISH_ROOT}"
REPO="${PUBLISH_REPO:-pypi}"
PYTHON="${PUBLISH_PYTHON:-${PYTHON:-python3}}"
if [[ -x /Users/shunyaoyin/miniconda310/miniconda3/bin/python ]]; then
  PYTHON="${PUBLISH_PYTHON:-/Users/shunyaoyin/miniconda310/miniconda3/bin/python}"
fi
CLEAN_GLOBS="${PUBLISH_CLEAN_GLOBS:-dist build *.egg-info}"

if [[ ! -f "$PUBLISH_ROOT/pyproject.toml" ]]; then
  echo "pyproject missing: $PUBLISH_ROOT/pyproject.toml" >&2
  exit 1
fi

cd "$PUBLISH_ROOT"
# shellcheck disable=SC2086
rm -rf $CLEAN_GLOBS 2>/dev/null || true
"$PYTHON" -m pip install -q --upgrade build twine
"$PYTHON" -m build
"$PYTHON" -m twine check dist/*

if [[ "${PUBLISH_DRY:-}" == "1" ]]; then
  echo "dry-run: built $(ls dist)"
  exit 0
fi

"$PYTHON" -m twine upload -r "$REPO" dist/*
echo "uploaded: $(ls dist)"
