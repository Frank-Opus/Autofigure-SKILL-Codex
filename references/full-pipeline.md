# Full AutoFigure Pipeline

Do not omit these stages when the user asks for the original AutoFigure behavior or the best result.

## Stage Mapping

1. Input
- paper PDF / markdown
- reference image
- text description

2. Method extraction
- optional
- Codex may assist by extracting the method section from PDF or markdown locally
- this stage should not reduce or replace later upstream generation stages

3. Core generation loop
- LLM generates initial figure or structural code
- syntax validation
- automatic repair
- iterative review / optimization

For this packaged Codex skill:

- image generation stays external
- SAM stays external or local depending on backend
- RMBG stays local via Hugging Face weights
- SVG template generation defaults to a local Codex backend
- the original multimodal SVG API stage is still available via `--svg_backend llm`

In the upstream repo, this is represented by:
- image generation
- SVG generation
- SVG validation and repair
- iterative SVG optimization

4. Image enhancement
- optional but legitimate
- style transfer
- variant generation
- more detailed prompting

5. Outputs
- SVG
- previews
- intermediate artifacts
- quality judgments if available

## What Requires External Support

- Text-to-image generation: provider API key
- SVG multimodal generation and repair: provider API key
- SAM segmentation: `ROBOFLOW_API_KEY` or `FAL_KEY`, or a separate local SAM3 install
- RMBG background removal: `HF_TOKEN` for gated `briaai/RMBG-2.0`

## What Codex Can Replace Or Assist

- method extraction from PDF / markdown
- wrapper orchestration
- local validation
- SVG cleanup and refactoring
- post-generation editing
- direct SVG drafting when the user accepts a fallback path

## Rule

If the user asks for the best AutoFigure result, do not replace the external-generation stages with a direct Codex-only SVG draft unless the user explicitly accepts that tradeoff.
