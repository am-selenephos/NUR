#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT/.env.local"
DEFAULT_MODEL="${NUR_OPENAI_MODEL:-gpt-4.1}"

contains_line_break() {
  [[ "$1" == *$'\r'* || "$1" == *$'\n'* ]]
}

TMP=""
cleanup() {
  if [[ -n "$TMP" && -e "$TMP" ]]; then
    rm -f -- "$TMP"
  fi
}
trap cleanup EXIT HUP INT TERM

printf "NUR local OpenAI configuration\n"
printf "Model name (default: %s): " "$DEFAULT_MODEL"
IFS= read -r MODEL
printf "OpenAI API key (input hidden): "
IFS= read -r -s OPENAI_KEY
printf "\n"

if [[ -z "${OPENAI_KEY}" ]]; then
  printf "No key entered. Leaving %s unchanged.\n" "$ENV_FILE" >&2
  exit 1
fi
if [[ -z "${MODEL}" ]]; then
  MODEL="$DEFAULT_MODEL"
fi
if contains_line_break "$MODEL" || contains_line_break "$OPENAI_KEY"; then
  printf "Model and key must each be a single line. Leaving %s unchanged.\n" "$ENV_FILE" >&2
  exit 1
fi

umask 177
TMP="$(mktemp "$ENV_FILE.tmp.XXXXXX")"
chmod 600 "$TMP"
{
  printf 'NUR_AI_PROVIDER=%q\n' "openai"
  printf '%s=%q\n' "OPENAI_API_KEY" "$OPENAI_KEY"
  printf 'NUR_OPENAI_MODEL=%q\n' "$MODEL"
  printf 'NUR_OPENAI_REASONING_EFFORT=%q\n' "high"
  printf 'NUR_OPENAI_CRITICAL_REASONING_EFFORT=%q\n' "high"
  printf 'NUR_AI_ALLOW_EXTERNAL_WEB_RESEARCH=%q\n' "false"
  printf 'NUR_AI_LOG_PROMPTS=%q\n' "false"
} > "$TMP"

if ! bash -n "$TMP" >/dev/null; then
  printf "Generated settings failed shell validation. Leaving %s unchanged.\n" "$ENV_FILE" >&2
  exit 1
fi

if ! NUR_CONFIG_EXPECTED_MODEL="$MODEL" NUR_CONFIG_EXPECTED_KEY="$OPENAI_KEY" \
  bash -c '
    set -euo pipefail
    source "$1"
    [[ "${NUR_AI_PROVIDER-}" == "openai" ]]
    [[ "${NUR_OPENAI_MODEL-}" == "$NUR_CONFIG_EXPECTED_MODEL" ]]
    [[ "${OPENAI_API_KEY-}" == "$NUR_CONFIG_EXPECTED_KEY" ]]
  ' _ "$TMP"; then
  printf "Generated settings failed value validation. Leaving %s unchanged.\n" "$ENV_FILE" >&2
  exit 1
fi

mv -f -- "$TMP" "$ENV_FILE"
TMP=""
chmod 600 "$ENV_FILE"
printf "Wrote server-only AI settings to %s with mode 600. The key was not printed.\n" "$ENV_FILE"
