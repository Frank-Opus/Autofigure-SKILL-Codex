# AutoFigure-Edit Config Notes

## Files

- Repo: `/home/wanguancheng/AutoFigure-Edit`
- Environment file: `/home/wanguancheng/AutoFigure-Edit/.env`
- Outputs: `/home/wanguancheng/AutoFigure-Edit/outputs`
- Uploads: `/home/wanguancheng/AutoFigure-Edit/uploads`

## Two Different Operating Modes

### Full AutoFigure Mode

This is the recommended mode when the user wants the original project behavior or the best result.

- Preserves the original upstream pipeline.
- Requires external services and model access.
- Uses a local Codex SVG backend by default for the template stage.

Required:

- LLM provider for figure generation
- `OPENROUTER_API_KEY`
- `BIANXIE_API_KEY`
- `GEMINI_API_KEY`
- Background removal and SAM
- `HF_TOKEN` for gated `briaai/RMBG-2.0`
- `ROBOFLOW_API_KEY` or `FAL_KEY` for API-based SAM

### Codex-Native Mode

This is the fallback mode.

- Codex reads the method text directly.
- Codex writes editable SVG directly.
- No external LLM provider key is required.
- Use the local web UI as an editor or preview surface.
- This is useful, but it is not a full reproduction of the upstream AutoFigure stack.

## Provider Mapping

- `--provider openrouter` uses `OPENROUTER_API_KEY`
- `--provider bianxie` uses `BIANXIE_API_KEY`
- `--provider gemini` uses `GEMINI_API_KEY`

The helper CLI script maps those env vars into the repo's `--api_key` flag automatically when the flag is not passed explicitly.

## Recommended Defaults

For Full AutoFigure mode:

- preserve all original major stages
- default `AUTOFIGURE_DEFAULT_SVG_BACKEND=codex_local`
- use real provider credentials
- use `--sam_backend roboflow` unless the user wants `fal`
- use `--svg_backend llm` only when the user explicitly wants the upstream multimodal SVG stage

For Codex-native mode:

- Draft SVG directly instead of generating a PNG first
- Keep text as `<text>`
- Use semantic groups and ids
- Validate syntax locally before handing off to the editor

## Important Constraint

The upstream README says local `sam3` is not vendored and currently targets newer Python/CUDA stacks than this host's default Python 3.10 environment. On this machine, use `roboflow` or `fal` unless the user explicitly asks to provision a separate local SAM3 runtime.
