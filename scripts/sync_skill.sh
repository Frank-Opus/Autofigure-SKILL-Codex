#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/skills/autofigure-edit"

mkdir -p "$(dirname "$TARGET_DIR")"
rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"

rsync -a \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "$REPO_ROOT"/ "$TARGET_DIR"/

echo "Synced skill to: $TARGET_DIR"
