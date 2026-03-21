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


def extract_stage_titles(method_text: str) -> List[str]:
    titles = re.findall(r"Stage\s+\d+\s*:\s*(.+)", method_text)
    if titles:
        return [t.strip() for t in titles[:3]]
    numbered = re.findall(r"^\d+\.\s+([A-Za-z][^\n]+)$", method_text, flags=re.MULTILINE)
    if numbered:
        return [t.strip() for t in numbered[:3]]
    return ["Diagnose", "Localize", "Align"]


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
) -> str:
    stage_bullets = extract_stage_bullets(method_text)

    input_fill = "#E6F3FA"
    diagnose_fill = "#D9EAF7"
    diagnose_stroke = "#2E75B6"
    localize_fill = "#FBE8B2"
    localize_stroke = "#D9951A"
    align_fill = "#DCEEDB"
    align_stroke = "#4A9E61"
    output_fill = "#E5F1DC"
    output_stroke = "#7FA354"

    anchors = [
        Anchor("input", 45, 78, 72, 54),
        Anchor("rubric", 286, 202, 28, 28),
        Anchor("ga", 365, 174, 26, 26),
        Anchor("rc", 365, 254, 26, 26),
        Anchor("kba", 365, 334, 26, 26),
        Anchor("cc", 365, 414, 26, 26),
        Anchor("score", 760, 246, 46, 34),
        Anchor("local-compare", 182, 624, 34, 34),
        Anchor("analysis", 275, 610, 40, 40),
        Anchor("metric-a", 130, 808, 30, 30),
        Anchor("metric-b", 240, 808, 30, 30),
        Anchor("metric-c", 350, 808, 30, 30),
        Anchor("focal-stack", 515, 688, 42, 42),
        Anchor("chosen", 700, 628, 30, 30),
        Anchor("rejected", 792, 628, 30, 30),
        Anchor("token-opt", 706, 816, 30, 30),
        Anchor("aligned-model", 902, 694, 54, 42),
    ]
    assign_icons_to_anchors(icon_infos, anchors)
    anchor_map = {anchor.name: anchor for anchor in anchors}

    defs = f"""
  <defs>
    <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
      <polygon points="0 0, 10 5, 0 10" fill="#3A78B8" />
    </marker>
    <marker id="arrow-orange" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
      <polygon points="0 0, 10 5, 0 10" fill="#D97B1E" />
    </marker>
    <marker id="arrow-green" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
      <polygon points="0 0, 10 5, 0 10" fill="#4A9E61" />
    </marker>
    <linearGradient id="diagGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#EAF4FC" />
      <stop offset="100%" stop-color="{diagnose_fill}" />
    </linearGradient>
    <linearGradient id="locGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFF6D7" />
      <stop offset="100%" stop-color="{localize_fill}" />
    </linearGradient>
    <linearGradient id="alignGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#EDF7ED" />
      <stop offset="100%" stop-color="{align_fill}" />
    </linearGradient>
  </defs>
"""

    parts = [
        f'<svg xmlns="{SVG_NS}" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        defs,
        f'<rect width="{width}" height="{height}" fill="white"/>',
        text_block(512, 26, [title], font_size=14, font_weight="bold"),
        text_block(252, 26, [stage_titles[0]], font_size=14, font_weight="bold", fill=diagnose_stroke),
        text_block(413, 26, ["->"], font_size=14, font_weight="bold", fill="#2B2B2B"),
        text_block(544, 26, [stage_titles[1]], font_size=14, font_weight="bold", fill="#BF8F00"),
        text_block(663, 26, ["->"], font_size=14, font_weight="bold", fill="#2B2B2B"),
        text_block(770, 26, [stage_titles[2]], font_size=14, font_weight="bold", fill="#548235"),
    ]

    parts.append(rect_with_title(x=10, y=66, width=180, height=396, fill=input_fill, stroke=diagnose_stroke, title="Multi-Agent Context"))
    parts.append('<rect x="26" y="150" width="112" height="52" rx="10" fill="white" stroke="#89B4D8" stroke-width="2"/>')
    parts.append(text_block(82, 171, ["System", "Instruction"], font_size=14, font_weight="bold"))
    parts.append('<rect x="26" y="212" width="112" height="52" rx="10" fill="white" stroke="#89B4D8" stroke-width="2"/>')
    parts.append(text_block(82, 233, ["User / Peer", "Instruction"], font_size=14, font_weight="bold"))
    parts.append('<rect x="26" y="274" width="112" height="52" rx="10" fill="white" stroke="#89B4D8" stroke-width="2"/>')
    parts.append(text_block(82, 301, ["Task"], font_size=14, font_weight="bold"))
    parts.append('<rect x="26" y="336" width="112" height="64" rx="10" fill="white" stroke="#89B4D8" stroke-width="2"/>')
    parts.append(text_block(82, 361, ["Agent", "Trajectory"], font_size=14, font_weight="bold"))
    parts.append(text_block(143, 214, ["Instruction", "Conflict"], font_size=12, font_weight="bold", fill="#E6791C"))
    parts.append('<path d="M 54 196 L 54 234" stroke="#E6791C" stroke-width="4" marker-end="url(#arrow-orange)"/>')
    parts.append('<path d="M 70 234 L 70 196" stroke="#E6791C" stroke-width="4" marker-end="url(#arrow-orange)"/>')
    parts.append(placeholder(anchor_map["input"]))

    parts.append(rect_with_title(x=244, y=66, width=766, height=392, fill="url(#diagGrad)", stroke=diagnose_stroke, title=f"1. {stage_titles[0]}", subtitle="Contextualized Role Adherence Score (CRAS)", title_size=22, subtitle_size=16))
    parts.append(arrow(190, 278, 242, 278, color="#3A78B8", stroke_width=8))
    parts.append(text_block(214, 248, ["Input"], font_size=13, font_weight="bold"))
    parts.append('<polygon points="268,214 350,278 268,342" fill="#3A78B8"/>')
    parts.append(text_block(323, 295, ["Context-Aware", "Rubric", "Instantiation"], font_size=15, font_weight="bold"))
    parts.append(placeholder(anchor_map["rubric"]))

    cras_cards = [
        ("Goal Alignment (GA)", 312, 154, "ga"),
        ("Role Consistency (RC)", 312, 234, "rc"),
        ("Knowledge Boundary Adherence (KBA)", 312, 314, "kba"),
        ("Constraint Compliance (CC)", 312, 394, "cc"),
    ]
    for label, x, y, anchor_name in cras_cards:
        parts.append(f'<rect x="{x}" y="{y}" width="214" height="48" rx="12" fill="white" stroke="{diagnose_stroke}" stroke-width="2"/>')
        parts.append(text_block(x + 118, y + 30, split_text(label, 22), font_size=13, font_weight="bold"))
        parts.append(placeholder(anchor_map[anchor_name]))
    parts.extend(
        [
            elbow_arrow(350, 278, 312, 178, mid_x=284, color="#4F91CE", stroke_width=3),
            elbow_arrow(350, 278, 312, 258, mid_x=286, color="#4F91CE", stroke_width=3),
            elbow_arrow(350, 278, 312, 338, mid_x=286, color="#4F91CE", stroke_width=3),
            elbow_arrow(350, 278, 312, 418, mid_x=284, color="#4F91CE", stroke_width=3),
            elbow_arrow(526, 178, 676, 278, mid_x=566, color="#4F91CE", stroke_width=3),
            elbow_arrow(526, 258, 676, 278, mid_x=578, color="#4F91CE", stroke_width=3),
            elbow_arrow(526, 338, 676, 278, mid_x=590, color="#4F91CE", stroke_width=3),
            elbow_arrow(526, 418, 676, 278, mid_x=602, color="#4F91CE", stroke_width=3),
            '<path d="M 720 278 A 42 42 0 0 1 806 278" stroke="#3A78B8" stroke-width="8" fill="none"/>',
            '<path d="M 720 278 A 30 30 0 0 1 780 278" stroke="#F5A623" stroke-width="12" fill="none"/>',
            '<path d="M 780 278 A 22 22 0 0 1 824 278" stroke="#F0D75D" stroke-width="12" fill="none"/>',
            '<path d="M 748 278 L 776 244" stroke="#4D4D4D" stroke-width="5"/>',
        ]
    )
    parts.append(text_block(826, 314, ["Scoring &", "Aggregation"], font_size=16, font_weight="bold"))
    parts.append(text_block(944, 286, ["Scalar", "CRAS Score"], font_size=13, font_weight="bold"))
    parts.append(arrow(858, 278, 918, 278, color="#3A78B8", stroke_width=5))
    parts.append(text_block(858, 374, ["Diagnostic Signal + Preference", "Supervision"], font_size=14))
    parts.append(placeholder(anchor_map["score"]))
    parts.append(arrow(584, 456, 584, 510, color="#3A78B8", stroke_width=8))
    parts.append(text_block(676, 486, ["CRAS & Trajectory Data"], font_size=16, font_weight="bold"))

    parts.append(rect_with_title(x=0, y=500, width=566, height=522, fill="url(#locGrad)", stroke=localize_stroke, title=f"2. {stage_titles[1]}", subtitle="Conflict-sensitive layer discovery", title_size=20, subtitle_size=15))
    parts.append('<circle cx="54" cy="648" r="16" fill="#58B878"/>')
    parts.append(text_block(54, 653, ["✓"], font_size=18, font_weight="bold", fill="white"))
    parts.append(text_block(46, 706, ["Non-conflict", "Input"], font_size=14, font_weight="bold"))
    parts.append('<circle cx="54" cy="838" r="16" fill="#D84B4B"/>')
    parts.append(text_block(54, 843, ["×"], font_size=18, font_weight="bold", fill="white"))
    parts.append(text_block(46, 896, ["Conflict", "Input"], font_size=14, font_weight="bold"))
    parts.append(arrow(88, 648, 154, 648, color="#58B878", stroke_width=4, marker_end="url(#arrow-green)"))
    parts.append(arrow(88, 838, 154, 838, color="#D97B1E", stroke_width=4, marker_end="url(#arrow-orange)"))
    parts.append('<rect x="154" y="588" width="234" height="174" rx="16" fill="#FFF8E5" stroke="#D9951A" stroke-width="2"/>')
    parts.append(text_block(271, 740, ["Attention Analysis", "& Drift Detection"], font_size=15, font_weight="bold"))
    parts.append(placeholder(anchor_map["local-compare"]))
    parts.append(placeholder(anchor_map["analysis"]))
    parts.append(text_block(170, 790, ["Head-Level Attention Drift Analysis"], font_size=16, font_weight="bold", anchor="start"))
    for idx, (x, label) in enumerate([(138, "Magnitude Shift"), (258, "Direction Reorientation"), (378, "Distribution Reshaping")]):
        parts.append(f'<rect x="{x}" y="826" width="88" height="110" rx="14" fill="#FFF5D8" stroke="#E3BB66" stroke-width="1.5"/>')
        parts.append(text_block(x + 44, 912, split_text(label, 12), font_size=12, font_weight="bold"))
    parts.append(placeholder(anchor_map["metric-a"]))
    parts.append(placeholder(anchor_map["metric-b"]))
    parts.append(placeholder(anchor_map["metric-c"]))
    parts.append('<rect x="412" y="652" width="132" height="260" rx="16" fill="#FFF5D8" stroke="#D9951A" stroke-width="2"/>')
    parts.append(text_block(478, 694, ["Focal Layer", "Identification"], font_size=15, font_weight="bold"))
    parts.append(text_block(478, 742, ["Attention Drift", "Score S^(l,h)"], font_size=13))
    parts.append('<rect x="450" y="782" width="56" height="18" rx="4" fill="#B4B4B4"/>')
    parts.append('<rect x="450" y="818" width="56" height="18" rx="4" fill="#FF8A00"/>')
    parts.append('<rect x="450" y="854" width="56" height="18" rx="4" fill="#B4B4B4"/>')
    parts.append('<rect x="450" y="890" width="56" height="18" rx="4" fill="#B4B4B4"/>')
    parts.append(text_block(478, 965, ["Top-k% Heads", "& Focal Layers", "(θ_focal)"], font_size=13, font_weight="bold"))
    parts.append(placeholder(anchor_map["focal-stack"]))
    parts.append(arrow(388, 674, 412, 674, color="#D9951A", stroke_width=5, marker_end="url(#arrow-orange)"))
    parts.append(arrow(544, 774, 612, 774, color="#D9951A", stroke_width=5, marker_end="url(#arrow-orange)"))

    parts.append(rect_with_title(x=606, y=500, width=228, height=512, fill="url(#alignGrad)", stroke=align_stroke, title=f"3. {stage_titles[2]}", subtitle="SAIL: Surgical Alignment of Instruction Layers", title_size=20, subtitle_size=14))
    parts.append(arrow(566, 774, 606, 774, color="#4A9E61", stroke_width=5, marker_end="url(#arrow-green)"))
    parts.append('<rect x="618" y="574" width="202" height="116" rx="14" fill="#F7FCF6" stroke="#7DB48B" stroke-width="2"/>')
    parts.append(text_block(719, 598, ["CRAS Preference Pairs"], font_size=16, font_weight="bold"))
    parts.append('<rect x="650" y="620" width="62" height="44" rx="10" fill="white" stroke="#7DB48B" stroke-width="1.5"/>')
    parts.append('<rect x="730" y="620" width="62" height="44" rx="10" fill="white" stroke="#7DB48B" stroke-width="1.5"/>')
    parts.append(text_block(681, 680, ["Chosen"], font_size=12, font_weight="bold"))
    parts.append(text_block(761, 680, ["Rejected"], font_size=12, font_weight="bold"))
    parts.append(placeholder(anchor_map["chosen"]))
    parts.append(placeholder(anchor_map["rejected"]))
    parts.append('<rect x="620" y="708" width="198" height="270" rx="14" fill="white" stroke="#7DB48B" stroke-width="2"/>')
    parts.append(text_block(719, 744, ["Token-Weighted", "DPO-style Optimization"], font_size=16, font_weight="bold"))
    parts.append(text_block(652, 814, ["Non-Focal", "Layers", "(Frozen)"], font_size=12))
    parts.append(text_block(652, 888, ["Focal", "Layers"], font_size=12))
    parts.append(text_block(652, 956, ["Non-Focal", "Layers", "(Frozen)"], font_size=12))
    parts.append('<rect x="708" y="806" width="38" height="16" rx="4" fill="#B4B4B4"/>')
    parts.append('<rect x="708" y="838" width="38" height="16" rx="4" fill="#4A9E61"/>')
    parts.append('<rect x="708" y="870" width="38" height="16" rx="4" fill="#B4B4B4"/>')
    parts.append('<rect x="708" y="902" width="38" height="16" rx="4" fill="#B4B4B4"/>')
    parts.append(text_block(782, 888, ["LoRA", "Adapters", "(Updated)"], font_size=12))
    parts.append(arrow(712, 642, 722, 642, color="#4A9E61", stroke_width=4, marker_end="url(#arrow-green)"))
    parts.append(arrow(746, 642, 758, 642, color="#D84B4B", stroke_width=4, marker_end="url(#arrow-orange)"))
    parts.append(placeholder(anchor_map["token-opt"]))
    parts.append(text_block(719, 1000, ["LoRA on Focal Layers Only,", "Focal-Weighted DPO"], font_size=13, font_weight="bold"))

    parts.append(rect_with_title(x=885, y=562, width=138, height=356, fill=output_fill, stroke=output_stroke, title="Reliable MAS under Instruction Conflicts", title_size=18))
    parts.append(arrow(834, 774, 885, 774, color="#4A9E61", stroke_width=6, marker_end="url(#arrow-green)"))
    parts.append(text_block(856, 760, ["Aligned", "Model"], font_size=13, font_weight="bold"))
    parts.append(placeholder(anchor_map["aligned-model"]))
    parts.append(text_block(954, 854, ["Improved", "Hierarchy", "Compliance,", "Preserved", "General", "Capability"], font_size=13, font_weight="bold"))
    parts.append(text_block(954, 980, ["Better Instruction", "Hierarchy Compliance,", "No Full-Model Finetuning"], font_size=12, font_weight="bold"))

    first_stage = stage_bullets.get(stage_titles[0], [])
    if first_stage:
        parts.append(text_block(885, 340, split_text(first_stage[0], 28)[:2], font_size=11, anchor="start"))

    for anchor in anchors:
        if anchor.label:
            parts.append(placeholder(anchor))

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a local Codex SVG template for AutoFigure-Edit.")
    parser.add_argument("--method_file", required=True)
    parser.add_argument("--boxlib_path", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--icon_infos_path")
    args = parser.parse_args()

    method_text = Path(args.method_file).read_text(encoding="utf-8")
    width, height = load_boxlib(Path(args.boxlib_path))
    title = extract_title(method_text)
    stage_titles = extract_stage_titles(method_text)
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
    )

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
