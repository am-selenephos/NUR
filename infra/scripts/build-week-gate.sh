#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

MODE="${1:-static}"
API_URL="${API_ORIGIN:-http://localhost:8000}"
WEB_URL="${WEB_ORIGIN:-http://localhost:5173}"

case "$MODE" in
  static|live|all) ;;
  *)
    printf 'Usage: bash infra/scripts/build-week-gate.sh [static|live|all]\n' >&2
    exit 2
    ;;
esac

section() {
  printf '\n================================================================\n'
  printf 'BUILD WEEK GATE — %s\n' "$1"
  printf '================================================================\n'
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'FAIL missing required tool: %s\n' "$1" >&2
    exit 1
  }
}

python_bin() {
  if [[ -x apps/api/.venv/bin/python ]]; then
    printf '%s\n' "apps/api/.venv/bin/python"
  else
    printf '%s\n' "python3"
  fi
}

run_static_gates() {
  section "tooling"
  require_tool bash
  require_tool node
  require_tool npm
  require_tool python3

  local py
  py="$(python_bin)"

  section "canonical V197 integrity"
  bash infra/scripts/check-v197-integrity.sh

  section "secret scan"
  bash infra/scripts/secret-scan.sh

  section "OpenAI local configuration safety"
  bash infra/tests/configure-openai-local.test.sh
  bash infra/tests/validate-openai-local.test.sh
  bash infra/tests/boot-openai-contract.test.sh

  section "API tests"
  "$py" -m pytest apps/api/app/tests -q

  section "web typecheck"
  npm --workspace apps/web run typecheck

  section "web unit tests"
  npm --workspace apps/web test -- --run

  section "production build"
  npm --workspace apps/web run build

  section "mocked Talk and visual readiness browser gates"
  npm --workspace apps/web run e2e -- \
    e2e/talk.spec.ts \
    e2e/visual-readiness.spec.ts \
    --project=chromium-desktop \
    --workers=1

  printf '\nSTATIC_GATE=PASS\n'
}

run_live_gates() {
  section "live service reachability"
  require_tool curl
  curl -fsS "${API_URL}/healthz" >/dev/null
  curl -fsS "${API_URL}/readyz" >/dev/null
  curl -fsS "${WEB_URL}" >/dev/null

  section "OpenAI provider mode"
  local provider
  provider="$(curl -fsS "${API_URL}/healthz" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("ai_provider", ""))')"
  if [[ "$provider" != "openai" ]]; then
    printf 'FAIL live Build Week gate requires ai_provider=openai; got %s\n' "${provider:-empty}" >&2
    printf 'Start the verified local system with: bash START_NUR.sh openai\n' >&2
    exit 1
  fi

  section "real OpenAI structured-output and persistence smoke"
  NUR_OPENAI_UI_SMOKE=1 bash infra/scripts/openai-smoke-local.sh

  section "two-account Context Capsule lifecycle"
  npm --workspace apps/web run e2e -- \
    e2e/capsule.spec.ts \
    --project=chromium-desktop \
    --workers=1

  printf '\nLIVE_GATE=PASS\n'
}

case "$MODE" in
  static)
    run_static_gates
    ;;
  live)
    run_live_gates
    ;;
  all)
    run_static_gates
    run_live_gates
    ;;
esac

printf '\nBUILD_WEEK_GATE=PASS mode=%s\n' "$MODE"
printf 'No submission-ready claim is valid for another commit until this gate is rerun.\n'
