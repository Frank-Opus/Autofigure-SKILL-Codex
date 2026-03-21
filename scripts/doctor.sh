#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/common.sh"

ensure_repo_exists
load_repo_env

echo "repo=$AUTOFIGURE_REPO"
echo "python=$AUTOFIGURE_PYTHON"
echo "env=$AUTOFIGURE_ENV"
echo

if [ -x "$AUTOFIGURE_PYTHON" ]; then
  "$AUTOFIGURE_PYTHON" --version
else
  echo "python-missing"
fi

echo
echo "mode-status:"
echo "  codex_native=ready"
echo "  codex_svg_backend=${AUTOFIGURE_DEFAULT_SVG_BACKEND:-codex_local}"
if [ -n "${HF_TOKEN:-}" ]; then
  echo "  full_pipeline_rmbg=ready"
else
  echo "  full_pipeline_rmbg=missing HF_TOKEN"
fi
if [ -n "${ROBOFLOW_API_KEY:-}" ] || [ -n "${FAL_KEY:-}" ]; then
  echo "  full_pipeline_sam=ready"
else
  echo "  full_pipeline_sam=missing ROBOFLOW_API_KEY or FAL_KEY"
fi
if [ -n "${OPENROUTER_API_KEY:-}" ] || [ -n "${BIANXIE_API_KEY:-}" ] || [ -n "${GEMINI_API_KEY:-}" ]; then
  echo "  full_pipeline_llm=ready"
else
  echo "  full_pipeline_llm=missing provider key"
fi

if [ -n "${HF_TOKEN:-}" ] && { [ -n "${ROBOFLOW_API_KEY:-}" ] || [ -n "${FAL_KEY:-}" ]; } && { [ -n "${OPENROUTER_API_KEY:-}" ] || [ -n "${BIANXIE_API_KEY:-}" ] || [ -n "${GEMINI_API_KEY:-}" ]; }; then
  echo "  full_pipeline=ready"
else
  echo "  full_pipeline=blocked"
fi

echo
echo "env-status:"
for key in HF_TOKEN ROBOFLOW_API_KEY FAL_KEY OPENROUTER_API_KEY BIANXIE_API_KEY GEMINI_API_KEY; do
  if [ -n "${!key:-}" ]; then
    echo "  $key=set"
  else
    echo "  $key=unset"
  fi
done

echo
echo "import-check:"
"$AUTOFIGURE_PYTHON" - <<'PY'
mods = ["fastapi", "uvicorn", "google.genai", "torchvision", "timm", "kornia", "lxml", "openai", "transformers", "torch"]
for name in mods:
    try:
        __import__(name)
        print(f"  {name}=ok")
    except Exception as exc:
        print(f"  {name}=missing: {type(exc).__name__}: {exc}")
PY
