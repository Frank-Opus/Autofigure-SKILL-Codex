#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from xml.sax.saxutils import escape


@dataclass
class IconInfo:
    label: str
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2.0

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class Anchor:
    name: str
    x: float
    y: float
    width: float
    height: float
    label: Optional[str] = None

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0


SVG_NS = 'http://www.w3.org/2000/svg'
ANCHOR_LIMIT = 17


def split_text(text: str, max_len: int = 18) -> List[str]:
    text = " ".join(text.split())
    if not text:
        return []
    words = text.split(" ")
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_len:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(
    x: float,
    y: float,
    lines: Iterable[str],
    *,
    font_size: int = 18,
    font_weight: str = "normal",
    fill: str = "#1F1F1F",
    anchor: str = "middle",
    line_gap: int = 20,
) -> str:
    lines = list(lines)
    if not lines:
        return ""
    pieces = [
        (
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'font-family="Arial, Helvetica, sans-serif" '
            f'font-size="{font_size}" font-weight="{font_weight}" fill="{fill}">'
        )
    ]
    for idx, line in enumerate(lines):
        dy = 0 if idx == 0 else line_gap
        if idx == 0:
            pieces.append(f'<tspan x="{x}" dy="0">{escape(line)}</tspan>')
        else:
            pieces.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
    pieces.append("</text>")
    return "".join(pieces)


def rect_with_title(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    stroke: str,
    title: str,
    subtitle: Optional[str] = None,
    title_size: int = 20,
    subtitle_size: int = 14,
    radius: int = 18,
) -> str:
    parts = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
        text_block(
            x + width / 2.0,
            y + 34,
            [title],
            font_size=title_size,
            font_weight="bold",
        ),
    ]
    if subtitle:
        parts.append(
            text_block(
                x + width / 2.0,
                y + 62,
                split_text(subtitle, 34),
                font_size=subtitle_size,
                fill="#3D3D3D",
            )
        )
    return "".join(parts)


def arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: str = "#3A78B8",
    stroke_width: int = 6,
    marker_end: str = "url(#arrow-blue)",
) -> str:
    return (
        f'<path d="M {x1} {y1} L {x2} {y2}" '
        f'stroke="{color}" stroke-width="{stroke_width}" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round" marker-end="{marker_end}"/>'
    )


def elbow_arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    mid_x: Optional[float] = None,
    color: str = "#3A78B8",
    stroke_width: int = 4,
    marker_end: str = "url(#arrow-blue)",
) -> str:
    if mid_x is None:
        mid_x = (x1 + x2) / 2.0
    return (
        f'<path d="M {x1} {y1} L {mid_x} {y1} L {mid_x} {y2} L {x2} {y2}" '
        f'stroke="{color}" stroke-width="{stroke_width}" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round" marker-end="{marker_end}"/>'
    )


def placeholder(anchor: Anchor) -> str:
    if not anchor.label:
        return ""
    label_text = anchor.label.replace("AF", "<AF>")
    return (
        f'<g id="{escape(anchor.label)}">'
        f'<rect x="{anchor.x}" y="{anchor.y}" width="{anchor.width}" height="{anchor.height}" '
        'fill="#808080" stroke="black" stroke-width="2"/>'
        f'<text x="{anchor.center_x}" y="{anchor.center_y}" text-anchor="middle" dominant-baseline="middle" '
        'font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="bold" fill="white">'
        f'{escape(label_text)}'
        "</text>"
        "</g>"
    )


def extract_title(method_text: str) -> str:
    quoted = re.search(r'for the paper:\s*"([^"]+)"', method_text, flags=re.IGNORECASE)
    if quoted:
        return quoted.group(1).strip()
    line = next((ln.strip() for ln in method_text.splitlines() if ln.strip()), "")
    return line[:110] if line else "AutoFigure Codex Pipeline"


def load_figure_spec(path: Optional[Path]) -> Dict:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_stage_titles(method_text: str, figure_spec: Optional[Dict] = None) -> List[str]:
    if figure_spec:
        stages = figure_spec.get("stages") or []
        labels = [str(stage.get("title", "")).strip() for stage in stages if str(stage.get("title", "")).strip()]
        if labels:
            return labels[:3]
    titles = re.findall(r"Stage\s+\d+\s*:\s*(.+)", method_text)
    if titles:
        return [t.strip() for t in titles[:3]]
    numbered = re.findall(r"^\d+\.\s+([A-Za-z][^\n]+)$", method_text, flags=re.MULTILINE)
    if numbered:
        return [t.strip() for t in numbered[:3]]
    return ["Stage 1", "Stage 2", "Stage 3"]


def extract_stage_bullets(method_text: str) -> Dict[str, List[str]]:
    bullets: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for raw_line in method_text.splitlines():
        line = raw_line.strip()
        stage_match = re.match(r"Stage\s+\d+\s*:\s*(.+)", line)
        if stage_match:
            current = stage_match.group(1).strip()
            bullets.setdefault(current, [])
            continue
        if line.endswith(":") and line.lower().startswith("far-"):
            current = line[:-1]
            bullets.setdefault(current, [])
            continue
        if current and line.startswith("- "):
            bullets[current].append(line[2:].strip())
    return bullets


def load_boxlib(boxlib_path: Path) -> tuple[int, int]:
    with boxlib_path.open("r", encoding="utf-8") as f:
        boxlib = json.load(f)
    image_size = boxlib.get("image_size", {})
    return int(image_size.get("width", 1024)), int(image_size.get("height", 1024))


def load_icon_infos(path: Optional[Path]) -> List[IconInfo]:
    if path is None or not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    icons = []
    for item in payload:
        icons.append(
            IconInfo(
                label=str(item["label_clean"]),
                x1=float(item["x1"]),
                y1=float(item["y1"]),
                x2=float(item["x2"]),
                y2=float(item["y2"]),
                width=float(item["width"]),
                height=float(item["height"]),
            )
        )
    return icons


def filter_icons(icon_infos: List[IconInfo], width: int, height: int) -> List[IconInfo]:
    canvas_area = width * height
    min_area = max(420.0, canvas_area * 0.00035)
    max_area = canvas_area * 0.012
    selected: List[IconInfo] = []
    for icon in icon_infos:
        aspect = icon.width / max(icon.height, 1.0)
        if icon.area < min_area or icon.area > max_area:
            continue
        if icon.width < 18 or icon.height < 18:
            continue
        if aspect < 0.4 or aspect > 2.8:
            continue
        selected.append(icon)
    if not selected:
        selected = sorted(icon_infos, key=lambda item: item.area, reverse=True)[:8]
    return sorted(selected, key=lambda item: (item.center_y, item.center_x))[:ANCHOR_LIMIT]


def assign_icons_to_anchors(icon_infos: List[IconInfo], anchors: List[Anchor]) -> None:
    remaining = anchors[:]
    for icon in icon_infos:
        if not remaining:
            break
        nearest = min(
            remaining,
            key=lambda anchor: math.hypot(anchor.center_x - icon.center_x, anchor.center_y - icon.center_y),
        )
        nearest.label = icon.label
        remaining.remove(nearest)


def render_svg(
    *,
    title: str,
    stage_titles: List[str],
    method_text: str,
    width: int,
    height: int,
    icon_infos: List[IconInfo],
    figure_spec: Optional[Dict] = None,
) -> str:
    figure_spec = figure_spec or {}
    stages = figure_spec.get("stages") or []
    while len(stages) < 3:
        idx = len(stages) + 1
        stages.append({"title": f"Stage {idx}", "subtitle": "", "bullets": []})
    stages = stages[:3]

    input_fill = "#F4F8FB"
    stage_fills = ["#D9EAF7", "#FBE8B2", "#DCEEDB"]
    stage_strokes = ["#2E75B6", "#D9951A", "#4A9E61"]

    defs = f"""
  <defs>
    <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
      <polygon points="0 0, 10 5, 0 10" fill="#3A78B8" />
    </marker>
    <linearGradient id="panelBlue" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#EEF6FC" />
      <stop offset="100%" stop-color="#D9EAF7" />
    </linearGradient>
    <linearGradient id="panelYellow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFF7DA" />
      <stop offset="100%" stop-color="#FBE8B2" />
    </linearGradient>
    <linearGradient id="panelGreen" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#EFF8EF" />
      <stop offset="100%" stop-color="#DCEEDB" />
    </linearGradient>
  </defs>
"""

    parts = [
        f'<svg xmlns="{SVG_NS}" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        defs,
        f'<rect width="{width}" height="{height}" fill="white"/>',
        text_block(width / 2.0, 34, [title], font_size=18, font_weight="bold"),
    ]

    margin = 28
    top_y = 72
    header_h = 64
    panel_gap = 20
    stage_gap = 18
    input_w = 176
    usable_w = width - margin * 2 - input_w - panel_gap
    stage_w = (usable_w - stage_gap * 2) / 3.0
    stage_h = min(360, height - top_y - 120)

    # left input panel: neutral project-driven input source, no old-paper semantics
    input_x = margin
    input_y = top_y + 24
    input_h = stage_h - 24
    parts.append(rect_with_title(x=input_x, y=input_y, width=input_w, height=input_h, fill=input_fill, stroke="#8AA8C0", title="Current Project Inputs", subtitle=figure_spec.get("purpose", "Section-derived figure constraints"), title_size=20, subtitle_size=13))
    input_cards = [
        "Section Text",
        "Figure Spec",
        "Required Labels",
        "Forbidden Terms",
    ]
    card_y = input_y + 88
    for idx, label in enumerate(input_cards):
        y = card_y + idx * 64
        parts.append(f'<rect x="{input_x + 22}" y="{y}" width="132" height="42" rx="10" fill="white" stroke="#AFC4D6" stroke-width="2"/>')
        parts.append(text_block(input_x + 88, y + 26, split_text(label, 18), font_size=13, font_weight="bold"))

    stage_x0 = input_x + input_w + panel_gap
    panel_y = top_y

    stage_gradients = ["url(#panelBlue)", "url(#panelYellow)", "url(#panelGreen)"]

    for idx, stage in enumerate(stages):
        sx = stage_x0 + idx * (stage_w + stage_gap)
        parts.append(rect_with_title(
            x=sx,
            y=panel_y,
            width=stage_w,
            height=stage_h,
            fill=stage_gradients[idx],
            stroke=stage_strokes[idx],
            title=f"{idx + 1}. {stage.get('title', stage_titles[idx])}",
            subtitle=str(stage.get('subtitle', '')).strip() or None,
            title_size=21,
            subtitle_size=13,
        ))
        bullet_box_y = panel_y + 96
        bullets = stage.get("bullets") or []
        for j, bullet in enumerate(bullets[:4]):
            by = bullet_box_y + j * 62
            parts.append(f'<rect x="{sx + 20}" y="{by}" width="{stage_w - 40}" height="44" rx="12" fill="white" stroke="{stage_strokes[idx]}" stroke-width="1.8"/>')
            parts.append(text_block(sx + stage_w / 2.0, by + 27, split_text(str(bullet), 26), font_size=12, font_weight="bold"))

    # arrows between input and stages
    parts.append(arrow(input_x + input_w, input_y + input_h / 2.0, stage_x0 - 10, panel_y + stage_h / 2.0, color="#3A78B8", stroke_width=7))
    parts.append(arrow(stage_x0 + stage_w, panel_y + stage_h / 2.0, stage_x0 + stage_w + stage_gap - 8, panel_y + stage_h / 2.0, color="#D97B1E", stroke_width=6))
    parts.append(arrow(stage_x0 + 2 * stage_w + stage_gap, panel_y + stage_h / 2.0, stage_x0 + 2 * stage_w + 2 * stage_gap - 8, panel_y + stage_h / 2.0, color="#4A9E61", stroke_width=6))

    # icon anchors: place a small number of icons only inside relevant stage panels
    stage_anchor_names = [
        ["s1_a", "s1_b", "s1_c", "s1_d"],
        ["s2_a", "s2_b", "s2_c", "s2_d"],
        ["s3_a", "s3_b", "s3_c", "s3_d"],
    ]
    anchors: List[Anchor] = []
    for idx in range(3):
        sx = stage_x0 + idx * (stage_w + stage_gap)
        for j in range(4):
            by = panel_y + 108 + j * 62
            anchors.append(Anchor(stage_anchor_names[idx][j], sx + 26, by + 8, 28, 28))
    assign_icons_to_anchors(icon_infos, anchors)
    for anchor in anchors:
        parts.append(placeholder(anchor))

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a local Codex SVG template for AutoFigure-Edit.")
    parser.add_argument("--method_file", required=True)
    parser.add_argument("--boxlib_path", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--icon_infos_path")
    parser.add_argument("--figure_spec_json")
    args = parser.parse_args()

    method_text = Path(args.method_file).read_text(encoding="utf-8")
    figure_spec = load_figure_spec(Path(args.figure_spec_json)) if args.figure_spec_json else {}
    width, height = load_boxlib(Path(args.boxlib_path))
    title = str(figure_spec.get("title", "")).strip() or extract_title(method_text)
    stage_titles = extract_stage_titles(method_text, figure_spec)
    while len(stage_titles) < 3:
        stage_titles.append(f"Stage {len(stage_titles) + 1}")

    icon_infos = load_icon_infos(Path(args.icon_infos_path) if args.icon_infos_path else None)
    filtered = filter_icons(icon_infos, width, height)
    svg = render_svg(
        title=title,
        stage_titles=stage_titles[:3],
        method_text=method_text,
        width=width,
        height=height,
        icon_infos=filtered,
        figure_spec=figure_spec,
    )

    forbidden_terms = [str(x) for x in figure_spec.get("forbidden_terms", []) if str(x).strip()]
    for term in forbidden_terms:
        if term and term in svg:
            svg = svg.replace(term, "")

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
