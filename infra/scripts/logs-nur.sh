#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="$ROOT/.nur-runtime"

redact='s/(OPENAI_API_KEY|api[_-]?key|secret|token|password)([=: ]+)[^ ]+/\1\2[redacted]/Ig; s/sk-[A-Za-z0-9_-]{20,}/[openai-key-redacted]/g'

for name in api worker beat web; do
  log="$RUNTIME/$name.log"
  if [[ -f "$log" ]]; then
    printf '\n===== %s =====\n' "$name"
    tail -n "${1:-120}" "$log" | sed -E "$redact"
  fi
done
