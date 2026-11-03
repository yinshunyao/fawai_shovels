#!/usr/bin/env python3
# --- shovel ---
# id: workspace_fs
# title: Cursor-like read/grep/glob/catalog
# when_to_use: Outside Cursor: read file slices, ripgrep, glob, or search shovel ledgers
# runtime: python
# kind: shovel
# requires: stdlib; grep needs rg
# side_effects: fs_read
# platforms: macOS,Linux,Windows
# tags: fs,search,catalog
# privacy: public
# completeness: 5
# generality: 5
# efficiency: 5
# invoke: python3 fawai_shovels/python/workspace-fs.py --help
# depends_shovels: 
# --- end-shovel ---
"""Cursor-like workspace helpers for use outside Cursor: read / grep / glob / catalog.

Requires: Python 3.8+ (stdlib). Subcommand `grep` needs `rg` (ripgrep) on PATH.

Examples:
  python3 fawai_shovels/python/workspace-fs.py read path/to/file.md --offset 1 --limit 40
  python3 fawai_shovels/python/workspace-fs.py grep 'TODO' --path . --glob '*.py' -i --head-limit 20
  python3 fawai_shovels/python/workspace-fs.py glob '**/*.md' --path study --head-limit 30
  python3 fawai_shovels/python/workspace-fs.py catalog rsync
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def _die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def cmd_read(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser()
    if not path.is_file():
        _die(f"not a file: {path}")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        _die(f"not a UTF-8 text file: {path} (binary/image not supported in this CLI)")

    lines = text.splitlines()
    n = len(lines)
    if n == 0:
        return 0

    offset = args.offset
    limit = args.limit

    if offset is None:
        start = 0
    elif offset > 0:
        start = offset - 1
    else:
        # negative: count from end (-1 = last line)
        start = max(0, n + offset)

    if start >= n:
        _die(f"offset beyond end of file ({n} lines)")

    if limit is None:
        end = n
    else:
        if limit < 1:
            _die("--limit must be >= 1")
        end = min(n, start + limit)

    width = len(str(end))
    for i in range(start, end):
        print(f"{i + 1:>{width}}|{lines[i]}")
    return 0


def _rg_bin() -> str:
    from shutil import which

    rg = which("rg")
    if not rg:
        _die("rg (ripgrep) not found on PATH; install ripgrep to use grep")
    return rg


def cmd_grep(args: argparse.Namespace) -> int:
    rg = _rg_bin()
    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        _die(f"path not found: {root}")

    cmd = [rg, "--line-number", "--color", "never", "--no-heading"]
    if args.ignore_case:
        cmd.append("-i")
    if args.fixed:
        cmd.append("-F")
    if args.after is not None:
        cmd.extend(["-A", str(args.after)])
    if args.before is not None:
        cmd.extend(["-B", str(args.before)])
    if args.context is not None:
        cmd.extend(["-C", str(args.context)])
    if args.glob:
        for g in args.glob:
            cmd.extend(["--glob", g])
    if args.type:
        cmd.extend(["--type", args.type])
    if args.no_ignore:
        cmd.append("--no-ignore")
    # Prefer respecting .gitignore; also skip common junk
    cmd.extend(["--glob", "!.git/**", "--glob", "!**/__pycache__/**", "--glob", "!**/.venv/**"])

    cmd.append("--")
    cmd.append(args.pattern)
    cmd.append(str(root))

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as e:
        _die(f"failed to run rg: {e}")

    # rg exit 1 = no matches; 2 = error
    if proc.returncode not in (0, 1):
        err = (proc.stderr or "").strip() or f"rg exit {proc.returncode}"
        _die(err, code=proc.returncode)

    out = proc.stdout.splitlines()
    if args.head_limit is not None and args.head_limit > 0:
        out = out[: args.head_limit]
    for line in out:
        print(line)
    return 0 if out or proc.returncode == 1 else 0


def _iter_glob(root: Path, pattern: str):
    # pathlib Path.glob does not treat leading **/ specially on all versions the same way;
    # normalize: if pattern has no slash and no **, search recursively as **/pattern
    pat = pattern
    if pat.startswith("/"):
        pat = pat.lstrip("/")
    if "**" not in pat and "/" not in pat and not pat.startswith("."):
        pat = f"**/{pat}"

    skip_parts = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
    for p in root.glob(pat):
        if not p.is_file():
            continue
        if any(part in skip_parts for part in p.parts):
            continue
        yield p


def cmd_glob(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        _die(f"not a directory: {root}")

    files = list(_iter_glob(root, args.pattern))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if args.head_limit is not None and args.head_limit > 0:
        files = files[: args.head_limit]
    for p in files:
        try:
            print(p.relative_to(root).as_posix())
        except ValueError:
            print(p.as_posix())
    return 0


def _tools_root() -> Path:
    env = (
        os.environ.get("FAWAI_SHOVELS_ROOT", "").strip()
        or os.environ.get("HIPP_TOOLS_ROOT", "").strip()  # legacy alias
    )
    if env:
        return Path(env).expanduser().resolve()
    # this file: fawai_shovels/python/workspace-fs.py
    return Path(__file__).resolve().parents[1]


def cmd_catalog(args: argparse.Namespace) -> int:
    """Search tool ledgers (zh/en fawai_shovels readmes and optional .cursor/tools/readme.md)."""
    root = _tools_root()
    ledgers = [root / "readme.md", root / "readme.en.md"]
    # sibling .cursor/tools when fawai_shovels sits under ai-company
    cursor_tools = root.parent / ".cursor" / "tools" / "readme.md"
    if cursor_tools.is_file():
        ledgers.append(cursor_tools)

    query = " ".join(args.query).strip()
    if not query:
        _die("catalog needs at least one keyword")

    terms = [t.lower() for t in re.split(r"\s+", query) if t]
    hits = []
    for ledger in ledgers:
        if not ledger.is_file():
            continue
        for i, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("|") or line.startswith("|---") or "路径" in line[:12]:
                continue
            low = line.lower()
            if all(t in low for t in terms):
                hits.append((ledger, i, line.strip()))

    if args.head_limit is not None and args.head_limit > 0:
        hits = hits[: args.head_limit]

    for ledger, i, line in hits:
        rel = ledger
        try:
            rel = ledger.relative_to(_tools_root().parent)
        except ValueError:
            pass
        print(f"{rel}:{i}: {line}")

    return 0 if hits else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="workspace-fs",
        description="Cursor-like read/grep/glob (and tool catalog search) for terminals outside Cursor.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("read", help="Read a text file with line numbers")
    pr.add_argument("path", help="file path")
    pr.add_argument(
        "--offset",
        type=int,
        default=None,
        help="1-based start line; negative counts from end (-1 = last line)",
    )
    pr.add_argument("--limit", type=int, default=None, help="max number of lines to print")
    pr.set_defaults(func=cmd_read)

    pg = sub.add_parser("grep", help="Search file contents via ripgrep")
    pg.add_argument("pattern", help="regex (or fixed string with --fixed)")
    pg.add_argument("--path", default=".", help="file or directory (default: .)")
    pg.add_argument("--glob", action="append", default=[], help="rg --glob (repeatable)")
    pg.add_argument("--type", default=None, help="rg --type (e.g. py)")
    pg.add_argument("-i", "--ignore-case", action="store_true")
    pg.add_argument("-F", "--fixed", action="store_true", help="fixed string, not regex")
    pg.add_argument("-A", "--after", type=int, default=None)
    pg.add_argument("-B", "--before", type=int, default=None)
    pg.add_argument("-C", "--context", type=int, default=None)
    pg.add_argument("--head-limit", type=int, default=None, help="max output lines")
    pg.add_argument("--no-ignore", action="store_true", help="do not respect .gitignore")
    pg.set_defaults(func=cmd_grep)

    pl = sub.add_parser("glob", help="List files matching a glob, newest first")
    pl.add_argument("pattern", help="glob, e.g. '**/*.py' or '*.md'")
    pl.add_argument("--path", default=".", help="root directory (default: .)")
    pl.add_argument("--head-limit", type=int, default=None)
    pl.set_defaults(func=cmd_glob)

    pc = sub.add_parser("catalog", help="Search fawai_shovels / .cursor/tools readme ledgers")
    pc.add_argument("query", nargs="+", help="keywords (AND)")
    pc.add_argument("--head-limit", type=int, default=None)
    pc.set_defaults(func=cmd_catalog)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
