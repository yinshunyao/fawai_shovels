#!/usr/bin/env python3
# --- shovel ---
# id: knowledge_svg
# title: Shared SVG helpers for knowledge notes
# when_to_use: Import SvgDoc/write_svg when generating UTF-8 knowledge SVGs
# runtime: python
# kind: library
# requires: stdlib
# side_effects: fs_write
# platforms: macOS,Linux,Windows
# tags: svg,library
# privacy: public
# completeness: 4
# generality: 3
# efficiency: 5
# invoke: from knowledge_svg import SvgDoc, write_svg
# depends_shovels: 
# --- end-shovel ---
"""Shared helpers for UTF-8 knowledge-base SVGs under 识别问题/基础知识.

Import from sibling scripts, or:
  from knowledge_svg import SvgDoc, FONT, write_svg
"""

from __future__ import annotations

from pathlib import Path

FONT = "PingFang SC, Hiragino Sans GB, Noto Sans SC, Microsoft YaHei, sans-serif"
BG = "#FFFEFB"
INK = "#1F2933"
MUTED = "#52606D"
BLUE = "#2B6CB0"
BLUE_BG = "#EBF8FF"
ORANGE = "#C05621"
ORANGE_BG = "#FFFAF0"
ORANGE_STROKE = "#DD6B20"
GREEN = "#2F855A"
GREEN_BG = "#F0FFF4"
GREEN_STROKE = "#38A169"
RED = "#C53030"
RED_BG = "#FED7D7"
RED_STROKE = "#E53E3E"
GRAY = "#718096"
GRAY_STROKE = "#CBD5E0"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class SvgDoc:
    def __init__(self, width: int, height: int, title: str):
        self.w = width
        self.h = height
        self.title = title
        self.parts: list[str] = []
        self._markers: set[str] = set()

    def marker(self, mid: str, color: str) -> None:
        if mid in self._markers:
            return
        self._markers.add(mid)
        self.parts.append(
            f'<marker id="{mid}" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">'
            f'<path d="M0,0 L8,4 L0,8 z" fill="{color}"/></marker>'
        )

    def bg(self) -> None:
        self.parts.append(f'<rect width="{self.w}" height="{self.h}" fill="{BG}"/>')

    def title_block(self, headline: str, sub: str, x: int = 40, y1: int = 36, y2: int = 58) -> None:
        self.parts.append(
            f'<text x="{x}" y="{y1}" font-family="{FONT}" font-size="16" font-weight="600" fill="{INK}">{esc(headline)}</text>'
        )
        if sub:
            self.parts.append(
                f'<text x="{x}" y="{y2}" font-family="{FONT}" font-size="12" fill="{MUTED}">{esc(sub)}</text>'
            )

    def panel(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        fill: str,
        stroke: str,
        rx: int = 10,
        sw: float = 1.5,
    ) -> None:
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def box(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        fill: str = "#FFFFFF",
        stroke: str = GRAY_STROKE,
        rx: int = 8,
        sw: float = 1.4,
    ) -> None:
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def text(
        self,
        x: int,
        y: int,
        s: str,
        *,
        size: int = 13,
        fill: str = INK,
        anchor: str = "start",
        weight: str = "400",
    ) -> None:
        wattr = f' font-weight="{weight}"' if weight != "400" else ""
        self.parts.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}"{wattr} fill="{fill}">{esc(s)}</text>'
        )

    def multiline(
        self,
        x: int,
        y: int,
        lines: list[str],
        *,
        size: int = 12,
        fill: str = MUTED,
        anchor: str = "start",
        dy: int = 16,
    ) -> None:
        for i, line in enumerate(lines):
            self.text(x, y + i * dy, line, size=size, fill=fill, anchor=anchor)

    def arrow(self, x1: int, y1: int, x2: int, y2: int, color: str = INK, mid: str = "arrK") -> None:
        self.marker(mid, color)
        self.parts.append(
            f'<path d="M{x1} {y1} L {x2} {y2}" fill="none" stroke="{color}" stroke-width="1.6" marker-end="url(#{mid})"/>'
        )

    def hline(self, x1: int, x2: int, y: int, color: str = INK, mid: str = "arrK", sw: float = 1.6) -> None:
        self.marker(mid, color)
        self.parts.append(
            f'<path d="M{x1} {y} H {x2}" fill="none" stroke="{color}" stroke-width="{sw}" marker-end="url(#{mid})"/>'
        )

    def raw(self, xml: str) -> None:
        self.parts.append(xml)

    def render(self) -> str:
        body = "\n  ".join(self.parts)
        defs = ""
        # markers already embedded in parts; wrap if any marker tags present
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" role="img">\n'
            f"  <title>{esc(self.title)}</title>\n"
            f"  {body}\n"
            f"</svg>\n"
        )


def write_svg(path: Path | str, content: str) -> Path:
    """Always UTF-8 text; never use Cursor Write for Chinese SVG."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = content if content.startswith("<?xml") else content
    p.write_text(text, encoding="utf-8", newline="\n")
    raw = p.read_bytes()
    if b"\x00" in raw:
        raise RuntimeError(f"NUL bytes after write: {p}")
    return p
