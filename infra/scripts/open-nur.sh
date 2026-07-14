#!/usr/bin/env bash
set -euo pipefail

URL="${NUR_WEB_URL:-http://localhost:5173}"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 &
else
  printf 'Open %s\n' "$URL"
fi
