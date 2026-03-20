#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/common.sh"

ensure_repo_exists

python3 -m venv --clear --system-site-packages "$AUTOFIGURE_VENV"
"$AUTOFIGURE_PIP" install --upgrade pip
"$AUTOFIGURE_PIP" install fastapi "google-genai>=1.0,<2.0"
"$AUTOFIGURE_PIP" install --no-deps "torchvision==0.22.1" "timm>=0.9" "kornia>=0.7,<1.0" kornia_rs

if [ ! -f "$AUTOFIGURE_ENV" ] && [ -f "$AUTOFIGURE_REPO/.env.example" ]; then
  cp "$AUTOFIGURE_REPO/.env.example" "$AUTOFIGURE_ENV"
fi

cat <<EOF
AutoFigure-Edit setup complete.
repo: $AUTOFIGURE_REPO
python: $AUTOFIGURE_PYTHON
env: $AUTOFIGURE_ENV

Next:
  1. Edit $AUTOFIGURE_ENV and add HF_TOKEN plus one LLM key.
  2. Run ~/.codex/skills/autofigure-edit/scripts/doctor.sh
  3. Start the service with ~/.codex/skills/autofigure-edit/scripts/serve.sh
EOF
