# Codex-Native SVG Workflow

Use this workflow by default instead of the upstream API pipeline.

## Goal

Turn method text, a rough sketch, or an existing figure into an editable SVG without calling an external image-generation or SVG-generation API.

## Recommended Process

1. Read the method text and extract:
- main stages
- entities and artifacts
- data flow directions
- repeated motifs
- constraints from the paper domain

2. Decide the figure structure:
- linear pipeline
- two-column comparison
- encoder-decoder
- feedback loop
- multi-branch system

3. Draft SVG directly:
- set an explicit canvas size
- create semantic `<g id="...">` groups
- keep labels in `<text>`
- use simple shapes before decorative details

4. Validate:

```bash
~/.codex/skills/autofigure-edit/scripts/validate_svg.py /abs/path/to/file.svg
```

5. If needed, launch the editor:

```bash
~/.codex/skills/autofigure-edit/scripts/serve.sh
```

## Output Contract

- Prefer `viewBox` plus width/height.
- Prefer editable primitives over flattened paths.
- Use consistent ids such as `stage-1`, `arrow-a`, `label-input`.
- Use ASCII ids and attribute names.
- Keep text selectable.
- Avoid embedding large base64 raster assets unless the user explicitly wants that.

## When To Escalate To Upstream Mode

Use the original API-driven pipeline only when one of these is true:

- the user explicitly asks to reproduce AutoFigure's research pipeline
- the user explicitly wants text-to-raster generation
- the user explicitly wants reference-image style transfer
- the user explicitly wants automated icon segmentation with SAM3 and RMBG
