#!/usr/bin/env python3
# --- shovel ---
# id: shovel_catalog
# title: Scan and validate shovel headers
# when_to_use: After adding/editing shovels; CI or local --check before commit
# runtime: python
# kind: shovel
# requires: stdlib
# side_effects: fs_read
# platforms: macOS,Linux,Windows
# tags: scaffold, catalog, validate
# privacy: public
# completeness: 5
# generality: 5
# efficiency: 5
# invoke: python3 fawai_shovels/scaffold/catalog.py --check
# depends_shovels:
# --- end-shovel ---
"""Parse `# --- shovel ---` headers under shell/ python/ media/ scaffold/."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("shell", "python", "media", "scaffold")
SKIP_NAMES = {"TEMPLATE.py", "TEMPLATE.sh"}

BEGIN = "# --- shovel ---"
END = "# --- end-shovel ---"
ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
PLATFORM_TOKENS = frozenset({"macOS", "Linux", "Windows"})
REQUIRED = (
    "id",
    "title",
    "when_to_use",
    "runtime",
    "kind",
    "requires",
    "side_effects",
    "platforms",
    "privacy",
    "completeness",
    "generality",
    "efficiency",
    "invoke",
)
SCORE_KEYS = ("completeness", "generality", "efficiency")


def parse_platforms(raw: str) -> tuple[set[str] | None, str | None]:
    """Return (tokens, error). ``all`` expands to the full closed set."""
    text = (raw or "").strip()
    if not text:
        return None, "platforms empty"
    if text == "all":
        return set(PLATFORM_TOKENS), None
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None, "platforms empty"
    bad = [p for p in parts if p not in PLATFORM_TOKENS]
    if bad:
        return None, (
            "platforms unknown "
            f"{bad!r}; allowed: macOS,Linux,Windows or all"
        )
    return set(parts), None


def _iter_files() -> list[Path]:
    out: list[Path] = []
    for name in SCAN_DIRS:
        d = ROOT / name
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if not p.is_file():
                continue
            if p.name in SKIP_NAMES or p.name.startswith("."):
                continue
            if p.suffix in {".py", ".sh"}:
                out.append(p)
    return out


def parse_header(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines[:80]):
        if line.strip() == BEGIN:
            start = i
            break
    if start is None:
        return None
    meta: dict[str, str] = {}
    for line in lines[start + 1 : start + 80]:
        s = line.strip()
        if s == END:
            return meta
        if not s.startswith("#"):
            return meta if meta else None
        body = s[1:].strip()
        if not body or body.startswith("---"):
            continue
        if ":" not in body:
            continue
        key, _, val = body.partition(":")
        key = key.strip().lower()
        val = val.strip()
        if key:
            meta[key] = val
    return meta if meta else None


def validate(meta: dict[str, str], path: Path) -> list[str]:
    errs: list[str] = []
    for k in REQUIRED:
        if not str(meta.get(k, "")).strip():
            errs.append(f"missing {k}")
    sid = meta.get("id", "")
    if sid and not ID_RE.match(sid):
        errs.append(f"bad id {sid!r}")
    runtime = meta.get("runtime") or ""
    if runtime not in {None, "", "python", "bash"}:
        errs.append(f"bad runtime {runtime!r}")
    if meta.get("kind") not in {None, "", "shovel", "launcher", "library"}:
        errs.append(f"bad kind {meta.get('kind')!r}")
    if meta.get("privacy") not in {None, "", "public", "private"}:
        errs.append(f"bad privacy {meta.get('privacy')!r}")

    plats, plat_err = parse_platforms(meta.get("platforms", ""))
    if plat_err:
        errs.append(plat_err)
    elif plats is not None:
        if runtime == "bash":
            if meta.get("platforms", "").strip() == "all":
                errs.append(
                    "bash shovel cannot use platforms=all; "
                    "list macOS and/or Linux only"
                )
            if "Windows" in plats:
                errs.append(
                    "bash shovel cannot list Windows "
                    "(use Linux for WSL)"
                )

    for sk in SCORE_KEYS:
        raw = meta.get(sk, "")
        if not raw:
            continue
        try:
            n = int(raw)
        except ValueError:
            errs.append(f"bad {sk} {raw!r}")
            continue
        if n < 1 or n > 5:
            errs.append(f"{sk} out of range")
    return errs


def cmd_check(_: argparse.Namespace) -> int:
    files = _iter_files()
    missing = 0
    bad = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT).as_posix()
        meta = parse_header(text)
        if meta is None:
            print(f"MISSING {rel}", file=sys.stderr)
            missing += 1
            continue
        errs = validate(meta, p)
        if errs:
            print(f"BAD {rel}: {'; '.join(errs)}", file=sys.stderr)
            bad += 1
            continue
        print(f"OK {rel} id={meta['id']}")
    if missing or bad:
        print(f"fail: missing={missing} bad={bad}", file=sys.stderr)
        return 1
    print(f"pass: {len(files)} shovels")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    rows = []
    for p in _iter_files():
        meta = parse_header(p.read_text(encoding="utf-8"))
        if not meta:
            continue
        rel = p.relative_to(ROOT).as_posix()
        rows.append(
            (
                rel,
                meta.get("platforms", ""),
                meta.get("completeness", ""),
                meta.get("generality", ""),
                meta.get("efficiency", ""),
                meta.get("title", ""),
                meta.get("invoke", ""),
                meta.get("kind", ""),
            )
        )
    print("| path | platforms | C | G | E | title | invoke | kind |")
    print("|:---|:---|:---:|:---:|:---:|:---|:---|:---|")
    for r in rows:
        print(
            f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} | "
            f"{r[5]} | `{r[6]}` | {r[7]} |"
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="fawai_shovels header catalog")
    ap.add_argument("--check", action="store_true", help="validate all shovel headers")
    ap.add_argument("--list", action="store_true", help="print markdown table from headers")
    args = ap.parse_args()
    if args.check:
        return cmd_check(args)
    if args.list:
        return cmd_list(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
