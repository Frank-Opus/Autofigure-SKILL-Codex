#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <method-file> <output-dir> [extra autofigure2 args...]" >&2
  exit 1
fi

METHOD_FILE="$1"
OUTPUT_DIR="$2"
shift 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/common.sh"

ensure_repo_exists
load_repo_env

provider="${AUTOFIGURE_DEFAULT_PROVIDER:-gemini}"
svg_backend="${AUTOFIGURE_DEFAULT_SVG_BACKEND:-llm}"
extra_args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --provider)
      provider="${2:-}"
      extra_args+=("$1" "$2")
      shift 2
      ;;
    --svg_backend)
      svg_backend="${2:-}"
      extra_args+=("$1" "$2")
      shift 2
      ;;
    *)
      extra_args+=("$1")
      shift
      ;;
  esac
done

api_key="$(resolve_api_key "$provider")"
cmd=(
  "$AUTOFIGURE_PYTHON"
  "$SCRIPT_DIR/run_codex_pipeline.py"
  --method_file "$METHOD_FILE"
  --output_dir "$OUTPUT_DIR"
  --provider "$provider"
  --svg_backend "$svg_backend"
)

if [ -n "$api_key" ]; then
  cmd+=(--api_key "$api_key")
fi

has_sam_backend=0
has_base_url=0
has_image_model=0
has_svg_model=0
has_placeholder_mode=0
has_optimize_iterations=0
for arg in "${extra_args[@]}"; do
  if [ "$arg" = "--sam_backend" ]; then
    has_sam_backend=1
  elif [ "$arg" = "--base_url" ]; then
    has_base_url=1
  elif [ "$arg" = "--image_model" ]; then
    has_image_model=1
  elif [ "$arg" = "--svg_model" ]; then
    has_svg_model=1
  elif [ "$arg" = "--placeholder_mode" ]; then
    has_placeholder_mode=1
  elif [ "$arg" = "--optimize_iterations" ]; then
    has_optimize_iterations=1
  fi
done

if [ "$has_sam_backend" -eq 0 ]; then
  if [ -n "${AUTOFIGURE_DEFAULT_SAM_BACKEND:-}" ]; then
    cmd+=(--sam_backend "$AUTOFIGURE_DEFAULT_SAM_BACKEND")
  elif [ -n "${ROBOFLOW_API_KEY:-}" ]; then
    cmd+=(--sam_backend roboflow)
  elif [ -n "${FAL_KEY:-}" ]; then
    cmd+=(--sam_backend fal)
  fi
fi

if [ "$has_base_url" -eq 0 ] && [ -n "${AUTOFIGURE_DEFAULT_BASE_URL:-}" ]; then
  cmd+=(--base_url "$AUTOFIGURE_DEFAULT_BASE_URL")
fi
if [ "$has_image_model" -eq 0 ] && [ -n "${AUTOFIGURE_DEFAULT_IMAGE_MODEL:-}" ]; then
  cmd+=(--image_model "$AUTOFIGURE_DEFAULT_IMAGE_MODEL")
fi
if [ "$has_svg_model" -eq 0 ] && [ -n "${AUTOFIGURE_DEFAULT_SVG_MODEL:-}" ]; then
  cmd+=(--svg_model "$AUTOFIGURE_DEFAULT_SVG_MODEL")
fi
if [ "$has_placeholder_mode" -eq 0 ]; then
  cmd+=(--placeholder_mode label)
fi
if [ "$has_optimize_iterations" -eq 0 ]; then
  cmd+=(--optimize_iterations 2)
fi

cmd+=("${extra_args[@]}")

exec "${cmd[@]}"
