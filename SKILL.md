---
name: autofigure-edit
description: Codex-first workflow for turning paper method text or existing figures into editable SVG scientific figures with the local AutoFigure-Edit repo. Use when the user wants AutoFigure-Edit installed, wants the local SVG editor/UI started, or wants Codex to directly draft or refine scientific SVG diagrams. Only use the upstream API-driven pipeline when the user explicitly asks to reproduce the original AutoFigure generation flow or style transfer.
---

# AutoFigure Edit

Use this skill only for the `ResearAI/AutoFigure-Edit` workflow on this machine.

## Repo And Runtime

- Default repo path: `/home/wanguancheng/AutoFigure-Edit`
- Default Python: `/home/wanguancheng/AutoFigure-Edit/.venv/bin/python`
- Override the repo path with `AUTOFIGURE_EDIT_REPO=/abs/path/to/AutoFigure-Edit`

## Default Mode

Default to a Codex-native workflow.

- Read the user's method text directly.
- Draft an editable SVG yourself.
- Validate it locally.
- Use the bundled web editor only for preview or manual refinement.

Do not request `OPENROUTER_API_KEY`, `BIANXIE_API_KEY`, or `GEMINI_API_KEY` unless the user explicitly asks for the original upstream AutoFigure multimodal generation pipeline.

## Modes

### 1. Codex-Native SVG Authoring

Use this by default.

- Input: method text, optional reference SVG or raster figure.
- Output: editable `draft.svg` or `final.svg`.
- No external LLM API required.
- Preferred for most "帮我画论文方法图" or "把这段方法写成 SVG 图" requests.

Workflow:

```bash
~/.codex/skills/autofigure-edit/scripts/new_job.sh /abs/path/job-dir /optional/method.txt
~/.codex/skills/autofigure-edit/scripts/validate_svg.py /abs/path/job-dir/draft.svg
```

Read [codex-native.md](/home/wanguancheng/.codex/skills/autofigure-edit/references/codex-native.md) before drafting or refactoring SVG output.

### 2. Local Editor / Refinement

Use when the user already has SVG output or wants an editor opened.

```bash
~/.codex/skills/autofigure-edit/scripts/serve.sh 8000
```

Then work against `http://127.0.0.1:8000`.

### 3. Upstream AutoFigure Reproduction

Use this only when the user explicitly wants one of these:

- Reproduce the original AutoFigure paper pipeline
- Text-to-raster generation before vectorization
- SAM3 API segmentation
- Style transfer based on a reference image

That mode uses the repo's original CLI:

```bash
~/.codex/skills/autofigure-edit/scripts/run_cli.sh /path/to/paper.txt /path/to/output-dir
```

Read [config.md](/home/wanguancheng/.codex/skills/autofigure-edit/references/config.md) before asking for credentials.

## Quick Workflow

1. Run setup once:

```bash
~/.codex/skills/autofigure-edit/scripts/setup.sh
```

2. Check config and missing secrets:

```bash
~/.codex/skills/autofigure-edit/scripts/doctor.sh
```

3. For Codex-native work, scaffold a job:

```bash
~/.codex/skills/autofigure-edit/scripts/new_job.sh /abs/path/job-dir
```

4. Validate a generated SVG:

```bash
~/.codex/skills/autofigure-edit/scripts/validate_svg.py /abs/path/job-dir/draft.svg
```

5. Start the web UI only when preview or manual editing helps:

```bash
~/.codex/skills/autofigure-edit/scripts/serve.sh
```

6. Use the upstream CLI only when explicitly requested:

```bash
~/.codex/skills/autofigure-edit/scripts/run_cli.sh /path/to/paper.txt /path/to/output-dir
```

## Practical Rules

- Prefer producing SVG directly over producing PNG first.
- Prefer semantic SVG elements such as `rect`, `line`, `path`, `text`, `marker`, `g`.
- Keep labels editable as text, not outlines.
- Keep each meaningful visual block in its own `<g id="...">`.
- If the user gives a raster figure, use it as a visual reference for manual SVG reconstruction first.
- Only escalate to SAM/RMBG/API mode if the user explicitly wants automated extraction or the figure is too complex for a direct Codex redraw.

## Configuration

- The repo `.env` file is at `/home/wanguancheng/AutoFigure-Edit/.env`.
- For Codex-native mode, API keys are optional.
- `HF_TOKEN` is only needed for upstream step-3 background removal with `briaai/RMBG-2.0`.
- One LLM key is only needed for upstream API generation:
  - `OPENROUTER_API_KEY`
  - `BIANXIE_API_KEY`
  - `GEMINI_API_KEY`
- One SAM backend key is only needed for upstream SAM3 API mode:
  - `ROBOFLOW_API_KEY`
  - `FAL_KEY`

## Defaults For This Machine

- Default to Codex-native mode.
- Prefer `roboflow` or `fal` for `--sam_backend` only in upstream mode.
- Do not default to local `sam3` here unless the user explicitly provides a separate Python 3.12+/CUDA setup for upstream SAM3.
- Optional SVG-to-PNG helper packages are not part of the local non-root install. If a task specifically needs those previews, prefer Docker or tell the user that extra system packages are required.

## Command Patterns

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
~/.codex/skills/autofigure-edit/scripts/run_cli.sh paper.txt outputs/demo \
  --provider openrouter \
  --sam_backend roboflow
```

- Upstream CLI with Gemini:

```bash
GEMINI_API_KEY=... \
~/.codex/skills/autofigure-edit/scripts/run_cli.sh paper.txt outputs/demo \
  --provider gemini \
  --sam_backend roboflow
```
