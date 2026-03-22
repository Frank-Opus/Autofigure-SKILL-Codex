#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ANCHOR_LIMIT = 17


def resolve_repo() -> Path:
    return Path(os.environ.get("AUTOFIGURE_EDIT_REPO", "/home/wanguancheng/AutoFigure-Edit")).resolve()


def load_autofigure_module(repo: Path):
    sys.path.insert(0, str(repo))
    import autofigure2  # type: ignore

    return autofigure2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AutoFigure-Edit with a local Codex SVG backend.")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--method_text", help="Paper method 文本内容")
    input_group.add_argument("--method_file", default="./paper.txt", help="包含 paper method 的文本文件路径")

    parser.add_argument("--output_dir", default="./output", help="输出目录（默认: ./output）")
    parser.add_argument("--provider", choices=["openrouter", "bianxie", "gemini"], default="gemini")
    parser.add_argument("--api_key", default=None, help="API Key")
    parser.add_argument("--base_url", default=None, help="API base URL")
    parser.add_argument("--image_model", default=None, help="生图模型")
    parser.add_argument("--svg_model", default=None, help="SVG生成模型（仅 llm backend 使用）")
    parser.add_argument("--sam_prompt", default="icon", help="SAM3 文本提示")
    parser.add_argument("--min_score", type=float, default=0.0, help="SAM3 最低置信度阈值")
    parser.add_argument("--sam_backend", choices=["local", "fal", "roboflow", "api"], default="roboflow")
    parser.add_argument("--sam_api_key", default=None, help="SAM3 API Key")
    parser.add_argument("--sam_max_masks", type=int, default=32, help="SAM3 API 最大 masks 数")
    parser.add_argument("--rmbg_model_path", default=None, help="RMBG 模型本地路径")
    parser.add_argument("--stop_after", type=int, choices=[1, 2, 3, 4, 5], default=5)
    parser.add_argument("--placeholder_mode", choices=["none", "box", "label"], default="label")
    parser.add_argument("--optimize_iterations", type=int, default=0)
    parser.add_argument("--merge_threshold", type=float, default=0.9)
    parser.add_argument("--svg_backend", choices=["codex_local", "llm"], default=os.environ.get("AUTOFIGURE_DEFAULT_SVG_BACKEND", "codex_local"))
    parser.add_argument("--use_reference_image", action="store_true")
    parser.add_argument("--reference_image_path", default=None)
    parser.add_argument("--figure_spec_json", default=None, help="Project-specific figure spec JSON")
    return parser.parse_args()


def resolve_api_key(provider: str, explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit
    env_map = {
        "openrouter": "OPENROUTER_API_KEY",
        "bianxie": "BIANXIE_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    return os.environ.get(env_map.get(provider, ""), None)


def export_previews(repo: Path, svg_path: Path) -> None:
    python_bin = repo / ".venv" / "bin" / "python"
    if not python_bin.exists():
        return
    code = (
        "import cairosvg,sys;"
        "src=sys.argv[1];"
        "cairosvg.svg2png(url=src, write_to=src[:-4]+'.png');"
        "cairosvg.svg2pdf(url=src, write_to=src[:-4]+'.pdf')"
    )
    try:
        subprocess.run([str(python_bin), "-c", code, str(svg_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def filter_icon_infos_for_codex(icon_infos: list[dict[str, Any]], figure_width: int, figure_height: int) -> list[dict[str, Any]]:
    canvas_area = figure_width * figure_height
    min_area = max(420.0, canvas_area * 0.00035)
    max_area = canvas_area * 0.012
    selected: list[dict[str, Any]] = []
    for item in icon_infos:
        width = float(item.get("width", 0))
        height = float(item.get("height", 0))
        area = width * height
        aspect = width / max(height, 1.0)
        if area < min_area or area > max_area:
            continue
        if width < 18 or height < 18:
            continue
        if aspect < 0.4 or aspect > 2.8:
            continue
        selected.append(item)
    if not selected:
        selected = sorted(
            icon_infos,
            key=lambda item: float(item.get("width", 0)) * float(item.get("height", 0)),
            reverse=True,
        )[:8]
    ordered = sorted(selected, key=lambda item: (float(item.get("y1", 0)), float(item.get("x1", 0))))
    return ordered[:ANCHOR_LIMIT]


def build_local_template(
    repo: Path,
    method_file: Path,
    boxlib_path: Path,
    icon_infos: list[dict[str, Any]],
    output_path: Path,
    figure_spec_json: Optional[str] = None,
) -> None:
    icon_infos_path = output_path.parent / "selected_icon_infos.json"
    icon_infos_path.write_text(json.dumps(icon_infos, indent=2, ensure_ascii=False), encoding="utf-8")
    script_path = Path(__file__).with_name("codex_svg_template.py")
    subprocess.run(
        [
            str(repo / ".venv" / "bin" / "python"),
            str(script_path),
            "--method_file",
            str(method_file),
            "--boxlib_path",
            str(boxlib_path),
            "--icon_infos_path",
            str(icon_infos_path),
            "--output_path",
            str(output_path),
        ] + (["--figure_spec_json", figure_spec_json] if figure_spec_json else []),
        check=True,
    )


def run_llm_backend(args: argparse.Namespace, repo: Path, api_key: str) -> int:
    autofigure2 = repo / "autofigure2.py"
    cmd = [
        str(repo / ".venv" / "bin" / "python"),
        str(autofigure2),
        "--output_dir",
        args.output_dir,
        "--provider",
        args.provider,
        "--api_key",
        api_key,
        "--sam_prompt",
        args.sam_prompt,
        "--min_score",
        str(args.min_score),
        "--sam_backend",
        args.sam_backend,
        "--sam_max_masks",
        str(args.sam_max_masks),
        "--stop_after",
        str(args.stop_after),
        "--placeholder_mode",
        args.placeholder_mode,
        "--optimize_iterations",
        str(args.optimize_iterations),
        "--merge_threshold",
        str(args.merge_threshold),
    ]
    if args.method_text:
        cmd.extend(["--method_text", args.method_text])
    else:
        cmd.extend(["--method_file", args.method_file])
    if args.base_url:
        cmd.extend(["--base_url", args.base_url])
    if args.image_model:
        cmd.extend(["--image_model", args.image_model])
    if args.svg_model:
        cmd.extend(["--svg_model", args.svg_model])
    if args.sam_api_key:
        cmd.extend(["--sam_api_key", args.sam_api_key])
    if args.rmbg_model_path:
        cmd.extend(["--rmbg_model_path", args.rmbg_model_path])
    if args.use_reference_image:
        cmd.append("--use_reference_image")
    if args.reference_image_path:
        cmd.extend(["--reference_image_path", args.reference_image_path])
    subprocess.run(cmd, check=True)
    return 0


def main() -> int:
    args = parse_args()
    repo = resolve_repo()
    autofigure2 = load_autofigure_module(repo)

    api_key = resolve_api_key(args.provider, args.api_key)
    if not api_key:
        raise SystemExit(f"missing api key for provider={args.provider}")

    if args.svg_backend == "llm":
        return run_llm_backend(args, repo, api_key)

    method_text = args.method_text
    method_file: Optional[Path] = None
    if method_text is None:
        method_file = Path(args.method_file).resolve()
        method_text = method_file.read_text(encoding="utf-8")
    else:
        method_file = Path(args.output_dir).resolve() / "method_text.txt"

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.method_text is not None:
        method_file.parent.mkdir(parents=True, exist_ok=True)
        method_file.write_text(method_text, encoding="utf-8")

    config = autofigure2.PROVIDER_CONFIGS[args.provider]
    base_url = args.base_url or config["base_url"]
    image_model = args.image_model or config["default_image_model"]
    svg_model = args.svg_model or config["default_svg_model"]

    print("\n" + "=" * 60)
    print("AutoFigure Codex Pipeline")
    print("=" * 60)
    print(f"svg_backend: {args.svg_backend}")
    print(f"provider: {args.provider}")
    print(f"output_dir: {output_dir}")
    print(f"image_model: {image_model}")
    print(f"svg_model: {svg_model} (unused in codex_local)")
    print(f"sam_prompt: {args.sam_prompt}")
    print(f"sam_backend: {args.sam_backend}")
    print(f"merge_threshold: {args.merge_threshold}")
    print("=" * 60)

    if args.stop_after >= 3:
        autofigure2._ensure_rmbg2_access_ready(args.rmbg_model_path)

    figure_path = output_dir / "figure.png"
    autofigure2.generate_figure_from_method(
        method_text=method_text,
        output_path=str(figure_path),
        api_key=api_key,
        model=image_model,
        base_url=base_url,
        provider=args.provider,
    )
    if args.stop_after == 1:
        return 0

    samed_path, boxlib_path, valid_boxes = autofigure2.segment_with_sam3(
        image_path=str(figure_path),
        output_dir=str(output_dir),
        text_prompts=args.sam_prompt,
        min_score=args.min_score,
        merge_threshold=args.merge_threshold,
        sam_backend="fal" if args.sam_backend == "api" else args.sam_backend,
        sam_api_key=args.sam_api_key,
        sam_max_masks=args.sam_max_masks,
    )
    if not valid_boxes:
        raise SystemExit("no valid boxes detected")
    if args.stop_after == 2:
        return 0

    icon_infos = autofigure2.crop_and_remove_background(
        image_path=str(figure_path),
        boxlib_path=boxlib_path,
        output_dir=str(output_dir),
        rmbg_model_path=args.rmbg_model_path,
    )
    figure_size = autofigure2.Image.open(figure_path).size
    selected_icon_infos = filter_icon_infos_for_codex(icon_infos, figure_size[0], figure_size[1])
    if args.stop_after == 3:
        return 0

    template_svg_path = output_dir / "template.svg"
    build_local_template(
        repo=repo,
        method_file=method_file,
        boxlib_path=Path(boxlib_path),
        icon_infos=selected_icon_infos,
        output_path=template_svg_path,
        figure_spec_json=args.figure_spec_json,
    )

    with template_svg_path.open("r", encoding="utf-8") as f:
        svg_code = f.read()
    is_valid, errors = autofigure2.validate_svg_syntax(svg_code)
    if not is_valid:
        raise SystemExit("generated local SVG is invalid:\n" + "\n".join(errors))

    optimized_template_path = output_dir / "optimized_template.svg"
    shutil.copyfile(template_svg_path, optimized_template_path)

    if args.stop_after == 4:
        export_previews(repo, template_svg_path)
        export_previews(repo, optimized_template_path)
        return 0

    figure_img = autofigure2.Image.open(figure_path)
    with optimized_template_path.open("r", encoding="utf-8") as f:
        optimized_svg = f.read()
    svg_width, svg_height = autofigure2.get_svg_dimensions(optimized_svg)
    if svg_width and svg_height:
        if abs(svg_width - figure_img.size[0]) < 1 and abs(svg_height - figure_img.size[1]) < 1:
            scale_factors = (1.0, 1.0)
        else:
            scale_factors = autofigure2.calculate_scale_factors(figure_img.size[0], figure_img.size[1], svg_width, svg_height)
    else:
        scale_factors = (1.0, 1.0)

    final_svg_path = output_dir / "final.svg"
    autofigure2.replace_icons_in_svg(
        template_svg_path=str(optimized_template_path),
        icon_infos=selected_icon_infos,
        output_path=str(final_svg_path),
        scale_factors=scale_factors,
        match_by_label=(args.placeholder_mode == "label"),
    )

    export_previews(repo, template_svg_path)
    export_previews(repo, optimized_template_path)
    export_previews(repo, final_svg_path)

    print("\n" + "=" * 60)
    print("Codex pipeline complete")
    print("=" * 60)
    print(f"figure_path={figure_path}")
    print(f"samed_path={samed_path}")
    print(f"boxlib_path={boxlib_path}")
    print(f"template_svg_path={template_svg_path}")
    print(f"optimized_template_path={optimized_template_path}")
    print(f"final_svg_path={final_svg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
