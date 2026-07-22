#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -r -- "$TEST_ROOT"' EXIT HUP INT TERM

mkdir -p "$TEST_ROOT/infra/scripts"
cp "$ROOT/infra/scripts/configure-openai-local.sh" "$TEST_ROOT/infra/scripts/"
SCRIPT="$TEST_ROOT/infra/scripts/configure-openai-local.sh"
ENV_FILE="$TEST_ROOT/.env.local"
SENTINEL="$TEST_ROOT/injected"

MODEL=$'gpt-test model "quoted" \'single\' $tier \\route=one;two&three() unicode-\u2603'
KEY=$'fake key "double" \'single\' $dollar \\slash equals= semi; amp& parens() unicode-\u2603'
KEY+=" \$(touch $SENTINEL)"

OUTPUT="$(printf '%s\n%s\n' "$MODEL" "$KEY" | bash "$SCRIPT" 2>&1)"

[[ "$OUTPUT" != *"$KEY"* ]]
[[ ! -e "$SENTINEL" ]]
[[ "$(stat -c '%a' "$ENV_FILE")" == "600" ]]
bash -n "$ENV_FILE"

(
  set -euo pipefail
  source "$ENV_FILE"
  [[ "$NUR_AI_PROVIDER" == "openai" ]]
  [[ "$NUR_OPENAI_MODEL" == "$MODEL" ]]
  [[ "$OPENAI_API_KEY" == "$KEY" ]]
)

BEFORE="$(sha256sum "$ENV_FILE")"
set +e
INVALID_OUTPUT="$(printf '%s\n%s\n' "gpt-test" $'invalid\rkey' | bash "$SCRIPT" 2>&1)"
INVALID_STATUS=$?
set -e

[[ "$INVALID_STATUS" -ne 0 ]]
[[ "$INVALID_OUTPUT" != *$'invalid\rkey'* ]]
[[ "$(sha256sum "$ENV_FILE")" == "$BEFORE" ]]
[[ "$(stat -c '%a' "$ENV_FILE")" == "600" ]]

set +e
LF_STATUS=0
printf '\n%s\n' "$KEY" \
  | NUR_OPENAI_MODEL=$'invalid\nmodel' bash "$SCRIPT" >/dev/null 2>&1 \
  || LF_STATUS=$?
EMPTY_STATUS=0
printf '%s\n\n' "gpt-test" | bash "$SCRIPT" >/dev/null 2>&1 || EMPTY_STATUS=$?
set -e

[[ "$LF_STATUS" -ne 0 ]]
[[ "$EMPTY_STATUS" -ne 0 ]]
[[ "$(sha256sum "$ENV_FILE")" == "$BEFORE" ]]
if compgen -G "$ENV_FILE.tmp.*" >/dev/null; then
  printf 'Temporary configuration file was not cleaned up.\n' >&2
  exit 1
fi

printf 'configure-openai-local regression passed.\n'
