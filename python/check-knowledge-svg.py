#!/usr/bin/env python3
"""Check knowledge-base SVG files: UTF-8 text, well-formed-ish XML, basic SVG root.

Usage (from workspace root, or any cwd):
  python3 hipp-tools/python/check-knowledge-svg.py <svg-or-dir> [...]

Exit 0 if all pass; 1 if any fail. Prints one line per file: OK / FAIL reason.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def check_one(path: Path) -> str | None:
    if not path.is_file():
        return "not a file"
    raw = path.read_bytes()
    if b"\x00" in raw:
        return "contains NUL byte"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return f"not utf-8: {e}"
    if "<svg" not in text[:500].lower():
        return "missing <svg near start"
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return f"xml parse: {e}"
    tag = root.tag.rsplit("}", 1)[-1]
    if tag.lower() != "svg":
        return f"root is <{tag}>, want svg"
    if "viewBox" not in root.attrib and "viewbox" not in {k.lower() for k in root.attrib}:
        # soft: warn via reason but still ok? treat as fail to catch broken writes
        if "width" not in root.attrib and "height" not in root.attrib:
            return "no viewBox/width/height"
    return None


def iter_targets(args: list[str]) -> list[Path]:
    out: list[Path] = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            out.extend(sorted(p.rglob("*.svg")))
        else:
            out.append(p)
    return out


def main(paths: list[str]) -> int:
    if not paths:
        print("usage: check-knowledge-svg.py <svg-or-dir> [...]", file=sys.stderr)
        return 2
    failed = 0
    for path in iter_targets(paths):
        err = check_one(path)
        if err:
            print(f"FAIL {path}: {err}")
            failed += 1
        else:
            print(f"OK   {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    PATHS = sys.argv[1:]
    raise SystemExit(main(PATHS))
