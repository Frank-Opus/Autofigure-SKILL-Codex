# AutoFigure SKILL For Codex

This repository packages a Codex-oriented skill layer around `ResearAI/AutoFigure-Edit`.

Default behavior:

- keep the original image generation stage
- keep SAM segmentation
- keep RMBG background removal
- replace the multimodal SVG API stage with a local Codex SVG backend
- keep final SVG assembly and local preview export

## Main Entry Points

- `SKILL.md`
- `scripts/run_cli.sh`
- `scripts/run_codex_pipeline.py`
- `scripts/codex_svg_template.py`
- `scripts/sync_skill.sh`

## Install

```bash
cd /path/to/Autofigure-SKILL-Codex
./scripts/sync_skill.sh
~/.codex/skills/autofigure-edit/scripts/setup.sh
~/.codex/skills/autofigure-edit/scripts/doctor.sh
```

## Run

Default local SVG backend:

```bash
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh ./paper.txt ./outputs/demo \
  --provider gemini \
  --sam_backend roboflow
```

Force the original upstream SVG LLM path:

```bash
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh ./paper.txt ./outputs/demo \
  --provider gemini \
  --svg_backend llm \
  --sam_backend roboflow
```

## Credentials

- one image provider key:
  - `GEMINI_API_KEY`
  - `OPENROUTER_API_KEY`
  - `BIANXIE_API_KEY`
- one SAM key:
  - `ROBOFLOW_API_KEY`
  - `FAL_KEY`
- `HF_TOKEN` for `briaai/RMBG-2.0`

## Notes

- `setup.sh` installs `cairosvg` so the local pipeline can export `PNG/PDF` previews from generated SVG.
- `svg_backend=codex_local` is the default backend for this packaged skill.
