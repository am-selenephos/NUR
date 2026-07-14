#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT/.env.local"
DEFAULT_MODEL="${NUR_OPENAI_MODEL:-gpt-4.1-mini}"

printf "NUR local OpenAI configuration\n"
printf "Model name (default: %s): " "$DEFAULT_MODEL"
read -r MODEL
printf "OpenAI API key (input hidden): "
read -r -s OPENAI_KEY
printf "\n"

if [[ -z "${OPENAI_KEY}" ]]; then
  printf "No key entered. Leaving %s unchanged.\n" "$ENV_FILE" >&2
  exit 1
fi
if [[ -z "${MODEL}" ]]; then
  MODEL="$DEFAULT_MODEL"
fi

umask 177
TMP="$(mktemp "$ENV_FILE.tmp.XXXXXX")"
{
  printf "NUR_AI_PROVIDER=openai\n"
  printf "%s=%s\n" "OPENAI_API_KEY" "$OPENAI_KEY"
  printf "NUR_OPENAI_MODEL=%s\n" "$MODEL"
  printf "NUR_OPENAI_REASONING_EFFORT=high\n"
  printf "NUR_OPENAI_CRITICAL_REASONING_EFFORT=high\n"
  printf "NUR_AI_ALLOW_EXTERNAL_WEB_RESEARCH=false\n"
  printf "NUR_AI_LOG_PROMPTS=false\n"
} > "$TMP"
mv "$TMP" "$ENV_FILE"
chmod 600 "$ENV_FILE"
printf "Wrote server-only AI settings to %s with mode 600. The key was not printed.\n" "$ENV_FILE"
