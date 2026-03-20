#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/common.sh"

ensure_repo_exists
load_repo_env

export AUTOFIGURE_PYTHON="$AUTOFIGURE_PYTHON"

cd "$AUTOFIGURE_REPO"
exec "$AUTOFIGURE_PYTHON" -m uvicorn server:app --host 0.0.0.0 --port "$PORT" --no-access-log
