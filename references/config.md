# AutoFigure-Edit Config Notes

## Files

- Repo: `/home/wanguancheng/AutoFigure-Edit`
- Environment file: `/home/wanguancheng/AutoFigure-Edit/.env`
- Outputs: `/home/wanguancheng/AutoFigure-Edit/outputs`
- Uploads: `/home/wanguancheng/AutoFigure-Edit/uploads`

## Two Different Operating Modes

### Codex-Native Mode

This is the default mode for the skill.

- Codex reads the method text directly.
- Codex writes editable SVG directly.
- No external LLM provider key is required.
- Use the local web UI only as an editor or preview surface.

### Upstream AutoFigure Mode

This reproduces the original repo pipeline and does require credentials.

You need secrets for two separate layers:

1. LLM provider for figure and SVG generation
- `OPENROUTER_API_KEY`
- `BIANXIE_API_KEY`
- `GEMINI_API_KEY`

2. Background removal and SAM
- `HF_TOKEN` for gated `briaai/RMBG-2.0`
- `ROBOFLOW_API_KEY` or `FAL_KEY` for API-based SAM

## Provider Mapping

- `--provider openrouter` uses `OPENROUTER_API_KEY`
- `--provider bianxie` uses `BIANXIE_API_KEY`
- `--provider gemini` uses `GEMINI_API_KEY`

The helper CLI script maps those env vars into the repo's `--api_key` flag automatically when the flag is not passed explicitly.

## Recommended Defaults

For Codex-native mode:

- Draft SVG directly instead of generating a PNG first
- Keep text as `<text>`
- Use semantic groups and ids
- Validate syntax locally before handing off to the editor

For upstream mode:

- `--sam_backend roboflow`
- `--optimize_iterations 0`
- `--placeholder_mode label`

These defaults reduce moving parts and match the current host constraints.

## Important Constraint

The upstream README says local `sam3` is not vendored and currently targets newer Python/CUDA stacks than this host's default Python 3.10 environment. On this machine, use `roboflow` or `fal` unless the user explicitly asks to provision a separate local SAM3 runtime.
