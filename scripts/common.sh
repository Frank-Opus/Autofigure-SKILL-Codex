#!/usr/bin/env bash
set -euo pipefail

DEFAULT_AUTOFIGURE_REPO="/home/wanguancheng/AutoFigure-Edit"
AUTOFIGURE_REPO="${AUTOFIGURE_EDIT_REPO:-$DEFAULT_AUTOFIGURE_REPO}"
AUTOFIGURE_VENV="$AUTOFIGURE_REPO/.venv"
AUTOFIGURE_PYTHON="$AUTOFIGURE_VENV/bin/python"
AUTOFIGURE_PIP="$AUTOFIGURE_VENV/bin/pip"
AUTOFIGURE_ENV="$AUTOFIGURE_REPO/.env"

ensure_repo_exists() {
  if [ ! -d "$AUTOFIGURE_REPO" ]; then
    echo "Repo not found: $AUTOFIGURE_REPO" >&2
    echo "Clone https://github.com/ResearAI/AutoFigure-Edit first or set AUTOFIGURE_EDIT_REPO." >&2
    exit 1
  fi
}

load_repo_env() {
  if [ -f "$AUTOFIGURE_ENV" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in
        ''|'#'*) continue ;;
      esac

      if [[ "$line" != *=* ]]; then
        continue
      fi

      key="${line%%=*}"
      value="${line#*=}"

      if [ -n "${!key+x}" ] && [ -n "${!key}" ]; then
        continue
      fi

      export "$key=$value"
    done < "$AUTOFIGURE_ENV"
  fi
}

resolve_api_key() {
  local provider="${1:-bianxie}"
  case "$provider" in
    openrouter) printf '%s' "${OPENROUTER_API_KEY:-}" ;;
    bianxie) printf '%s' "${BIANXIE_API_KEY:-}" ;;
    gemini) printf '%s' "${GEMINI_API_KEY:-}" ;;
    *) printf '%s' "" ;;
  esac
}
