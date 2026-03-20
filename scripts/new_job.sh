#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <job-dir> [method-file]" >&2
  exit 1
fi

JOB_DIR="$1"
METHOD_FILE="${2:-}"

mkdir -p "$JOB_DIR"
mkdir -p "$JOB_DIR/assets"

if [ -n "$METHOD_FILE" ]; then
  cp "$METHOD_FILE" "$JOB_DIR/method.txt"
elif [ ! -f "$JOB_DIR/method.txt" ]; then
  : > "$JOB_DIR/method.txt"
fi

if [ ! -f "$JOB_DIR/draft.svg" ]; then
  cat > "$JOB_DIR/draft.svg" <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <rect width="1600" height="900" fill="#ffffff" />
  <text x="80" y="120" font-family="Arial, sans-serif" font-size="44" fill="#111111">Draft Figure</text>
  <text x="80" y="180" font-family="Arial, sans-serif" font-size="24" fill="#555555">Replace this scaffold with the actual scientific diagram.</text>
</svg>
EOF
fi

if [ ! -f "$JOB_DIR/final.svg" ]; then
  cp "$JOB_DIR/draft.svg" "$JOB_DIR/final.svg"
fi

echo "job_dir=$JOB_DIR"
echo "method_file=$JOB_DIR/method.txt"
echo "draft_svg=$JOB_DIR/draft.svg"
echo "final_svg=$JOB_DIR/final.svg"
