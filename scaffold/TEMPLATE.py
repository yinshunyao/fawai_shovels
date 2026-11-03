#!/usr/bin/env python3
# --- shovel ---
# id: example_shovel
# title: Example shovel
# when_to_use: Copy this file when adding a new Python shovel
# runtime: python
# kind: shovel
# requires: stdlib
# side_effects: none
# platforms: macOS,Linux,Windows
# tags: example
# privacy: public
# completeness: 3
# generality: 5
# efficiency: 5
# invoke: python3 fawai_shovels/python/example_shovel.py
# depends_shovels:
# --- end-shovel ---
"""One-line human summary. Details stay here, not in the shovel meta block."""

from __future__ import annotations


def main() -> None:
    raise SystemExit("replace with real work")


if __name__ == "__main__":
    # Local demo knobs only — not CLI argparse unless this is a real CLI entry.
    main()
