---
name: autofigure-edit
description: Full AutoFigure-Edit workflow for turning paper method text, PDFs, reference figures, and descriptions into editable scientific figures. Use when the user wants the local AutoFigure-Edit repo installed, wants the full upstream AutoFigure pipeline preserved, or wants Codex to orchestrate method extraction, SVG refinement, editor use, and optional fallback direct SVG drafting. For best results, preserve the original API-driven image generation, SAM segmentation, RMBG background removal, SVG validation, and iterative optimization pipeline.
---

# AutoFigure Edit

Use this skill only for the `ResearAI/AutoFigure-Edit` workflow on this machine.

## Repo And Runtime

- Default repo path: `/home/wanguancheng/AutoFigure-Edit`
- Default Python: `/home/wanguancheng/AutoFigure-Edit/.venv/bin/python`
- Override the repo path with `AUTOFIGURE_EDIT_REPO=/abs/path/to/AutoFigure-Edit`

## Priority Order

When the user asks for "AutoFigure", "完整流程", "最好的结果", "不要省略", or wants style transfer / segmentation / original paper behavior:

1. Use **Full AutoFigure Mode** first.
2. Use **Hybrid Mode** if Codex should help with extraction, review, or SVG correction around the upstream pipeline.
3. Use **Codex-Native Mode** only as a fallback when the user does not have the required keys or explicitly wants direct SVG authoring without the upstream generation stack.

Do not silently downgrade a request for AutoFigure into a Codex-only SVG workflow.

## Modes

### 1. Full AutoFigure Mode

This is the canonical mode for best quality and for faithful reproduction of the original project.

- Input:
  - paper PDF / markdown / method text
  - optional reference image
  - optional text instruction
- Pipeline:
  - optional method extraction
  - LLM image generation
  - SAM3 segmentation
  - RMBG background removal
  - SVG template generation
  - SVG syntax validation and repair
  - iterative SVG optimization
  - final assembled SVG
- Output:
  - editable SVG
  - intermediate artifacts
  - optional previews from the web UI

Run:

```bash
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh /path/to/method.txt /path/to/output-dir
```

Read [full-pipeline.md](/home/wanguancheng/.codex/skills/autofigure-edit/references/full-pipeline.md) before deciding to skip any stage.

### 2. Hybrid Mode

Use this when the full upstream pipeline should stay intact, but Codex should assist around it.

Examples:

- extract the method section from a PDF or markdown before calling AutoFigure
- inspect and fix broken SVG outputs after upstream generation
- adjust labels, colors, grouping, or layout in the generated SVG
- open the local editor for manual refinement after the upstream run

Typical hybrid flow:

```bash
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh /path/to/method.txt /path/to/output-dir
~/.codex/skills/autofigure-edit/scripts/validate_svg.py /path/to/output-dir/final.svg
~/.codex/skills/autofigure-edit/scripts/serve.sh 8000
```

### 3. Codex-Native SVG Authoring

Use this only when:

- the user explicitly wants a direct SVG drafted by Codex
- the user lacks required upstream credentials
- the task is a lightweight redraw or edit rather than full AutoFigure generation

Workflow:

```bash
~/.codex/skills/autofigure-edit/scripts/new_job.sh /abs/path/job-dir /optional/method.txt
~/.codex/skills/autofigure-edit/scripts/validate_svg.py /abs/path/job-dir/draft.svg
```

Read [codex-native.md](/home/wanguancheng/.codex/skills/autofigure-edit/references/codex-native.md) before drafting or refactoring SVG output.

### 4. Local Editor / Refinement

Use when the user already has SVG output or wants an editor opened.

```bash
~/.codex/skills/autofigure-edit/scripts/serve.sh 8000
```

Then work against `http://127.0.0.1:8000`.

## Quick Workflow

1. Run setup once:

```bash
~/.codex/skills/autofigure-edit/scripts/setup.sh
```

2. Check config and missing secrets:

```bash
~/.codex/skills/autofigure-edit/scripts/doctor.sh
```

3. For the full upstream pipeline, verify credentials and run:

```bash
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh /path/to/method.txt /path/to/output-dir
```

4. For Codex-native fallback work, scaffold a job:

```bash
~/.codex/skills/autofigure-edit/scripts/new_job.sh /abs/path/job-dir
```

5. Validate a generated SVG:

```bash
~/.codex/skills/autofigure-edit/scripts/validate_svg.py /abs/path/job-dir/draft.svg
```

6. Start the web UI when preview or manual editing helps:

```bash
~/.codex/skills/autofigure-edit/scripts/serve.sh
```

## Practical Rules

- If the user asks for the best AutoFigure result, preserve the full upstream pipeline.
- Do not omit SAM3, RMBG, SVG validation, or optimization unless the user explicitly accepts a degraded path.
- Prefer producing SVG directly over producing PNG first.
- Prefer semantic SVG elements such as `rect`, `line`, `path`, `text`, `marker`, `g`.
- Keep labels editable as text, not outlines.
- Keep each meaningful visual block in its own `<g id="...">`.
- If the user gives a raster figure, use it as a visual reference for manual SVG reconstruction first.
- Only fall back to Codex-native direct redraw if the user accepts not using the original generation stack or if credentials are unavailable.

## Configuration

- The repo `.env` file is at `/home/wanguancheng/AutoFigure-Edit/.env`.
- For **Full AutoFigure Mode**, these are required:
  - `HF_TOKEN`
  - one provider key:
  - `OPENROUTER_API_KEY`
  - `BIANXIE_API_KEY`
  - `GEMINI_API_KEY`
  - one SAM backend key:
  - `ROBOFLOW_API_KEY`
  - `FAL_KEY`
- For **Codex-Native Mode**, API keys are optional.

## Defaults For This Machine

- Default to **Full AutoFigure Mode** when the user asks for AutoFigure or best quality.
- Prefer `roboflow` or `fal` for `--sam_backend` in upstream mode.
- Do not default to local `sam3` here unless the user explicitly provides a separate Python 3.12+/CUDA setup for upstream SAM3.
- Optional SVG-to-PNG helper packages are not part of the local non-root install. If a task specifically needs those previews, prefer Docker or tell the user that extra system packages are required.

## Command Patterns

- Full upstream pipeline:

```bash
OPENROUTER_API_KEY=... HF_TOKEN=... ROBOFLOW_API_KEY=... \
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh ./paper.txt ./outputs/demo
```

- Codex-native job:

```bash
~/.codex/skills/autofigure-edit/scripts/new_job.sh ./jobs/figure-a ./paper.txt
~/.codex/skills/autofigure-edit/scripts/validate_svg.py ./jobs/figure-a/draft.svg
```

- Web editor:

```bash
~/.codex/skills/autofigure-edit/scripts/serve.sh 8000
```

- Upstream CLI with OpenRouter:

```bash
OPENROUTER_API_KEY=... \
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh paper.txt outputs/demo \
  --provider openrouter \
  --sam_backend roboflow
```

- Upstream CLI with Gemini:

```bash
GEMINI_API_KEY=... \
~/.codex/skills/autofigure-edit/scripts/run_full_pipeline.sh paper.txt outputs/demo \
  --provider gemini \
  --sam_backend roboflow
```
