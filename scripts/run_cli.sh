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

provider="bianxie"
extra_args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --provider)
      provider="${2:-}"
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
  "$AUTOFIGURE_REPO/autofigure2.py"
  --method_file "$METHOD_FILE"
  --output_dir "$OUTPUT_DIR"
)

if [ -n "$api_key" ]; then
  cmd+=(--api_key "$api_key")
fi

has_sam_backend=0
for arg in "${extra_args[@]}"; do
  if [ "$arg" = "--sam_backend" ]; then
    has_sam_backend=1
    break
  fi
done

if [ "$has_sam_backend" -eq 0 ]; then
  if [ -n "${ROBOFLOW_API_KEY:-}" ]; then
    cmd+=(--sam_backend roboflow)
  elif [ -n "${FAL_KEY:-}" ]; then
    cmd+=(--sam_backend fal)
  fi
fi

cmd+=(--placeholder_mode label --optimize_iterations 0)
cmd+=("${extra_args[@]}")

exec "${cmd[@]}"
