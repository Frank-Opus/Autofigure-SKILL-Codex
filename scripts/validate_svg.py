#!/usr/bin/env python3
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_svg.py <svg-path>", file=sys.stderr)
        return 1

    svg_path = Path(sys.argv[1]).resolve()
    if not svg_path.is_file():
        print(f"missing file: {svg_path}", file=sys.stderr)
        return 1

    try:
        text = svg_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"read-failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        root = ET.fromstring(text)
    except Exception as exc:
        print(f"xml-invalid: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    tag = root.tag.rsplit("}", 1)[-1]
    if tag != "svg":
        print(f"root-invalid: expected svg, got {tag}", file=sys.stderr)
        return 1

    warnings: list[str] = []
    if "viewBox" not in root.attrib:
        warnings.append("missing viewBox")
    if "width" not in root.attrib or "height" not in root.attrib:
        warnings.append("missing width/height")
    if "data:image" in text:
        warnings.append("contains embedded raster data")

    print(f"svg-ok: {svg_path}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
