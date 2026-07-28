#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -r -- "$TEST_ROOT"' EXIT HUP INT TERM

mkdir -p "$TEST_ROOT/infra/scripts"
cp "$ROOT/START_NUR.sh" "$ROOT/RUN_NUR.sh" "$TEST_ROOT/"
cp "$ROOT/infra/scripts/validate-openai-local.sh" "$TEST_ROOT/infra/scripts/"

set +e
START_OUTPUT="$(cd "$TEST_ROOT" && bash START_NUR.sh openai 2>&1)"
START_STATUS=$?
RUN_OUTPUT="$(cd "$TEST_ROOT" && bash RUN_NUR.sh openai 2>&1)"
RUN_STATUS=$?
set -e

[[ "$START_STATUS" -ne 0 ]]
[[ "$RUN_STATUS" -ne 0 ]]
[[ "$START_OUTPUT" == *"valid mode-600 .env.local"* ]]
[[ "$RUN_OUTPUT" == *"valid mode-600 local .env.local"* ]]
[[ ! -e "$TEST_ROOT/.env" ]]
[[ ! -e "$TEST_ROOT/.nur-runtime" ]]

printf 'boot OpenAI fail-closed regression passed.\n'
