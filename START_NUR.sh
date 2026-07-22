#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

WEB_URL="${WEB_ORIGIN:-http://localhost:5173}"
API_URL="${API_ORIGIN:-http://localhost:8000}"

open_nur() {
  bash "$ROOT/infra/scripts/open-nur.sh" >/dev/null 2>&1 || true
}

configured_openai() {
  bash "$ROOT/infra/scripts/validate-openai-local.sh" >/dev/null 2>&1
}

running_provider() {
  curl -fsS --max-time 2 "$API_URL/healthz" 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("ai_provider", ""))' 2>/dev/null \
    || true
}

MODE="${1:-auto}"
if [[ "$MODE" == "auto" ]]; then
  if configured_openai; then
    MODE="openai"
  elif [[ -t 0 && -t 1 ]]; then
    cat <<'TXT'
NUR first-time AI setup
The real chatbot needs an OpenAI API key stored only on this computer.
The key will be hidden while typed and saved to ignored .env.local with mode 600.
It is never put in the browser, source package, screenshots, or logs.
TXT
    printf 'Press Enter to configure real Talk, or Ctrl+C to stop: '
    read -r _
    bash "$ROOT/infra/scripts/configure-openai-local.sh"
    configured_openai || {
      printf 'OpenAI setup did not complete. NUR was not started with a fake chatbot.\n' >&2
      exit 1
    }
    MODE="openai"
  else
    cat >&2 <<'TXT'
NUR real Talk is not configured yet. Run interactively:
  bash START_NUR.sh
or configure first:
  bash infra/scripts/configure-openai-local.sh
  bash START_NUR.sh
Use `bash START_NUR.sh disabled` only for an honest chatbot-less demo.
TXT
    exit 1
  fi
fi

case "$MODE" in
  openai|disabled)
    if [[ "$MODE" == "openai" ]] && ! configured_openai; then
      printf 'OpenAI mode requires a valid mode-600 .env.local. Run: bash START_NUR.sh setup\n' >&2
      exit 1
    fi
    current="$(running_provider)"
    if [[ "$current" == "$MODE" ]] && curl -fsS --max-time 2 "$WEB_URL" >/dev/null 2>&1; then
      printf 'NUR is already running in %s mode. Opening %s\n' "$MODE" "$WEB_URL"
      bash "$ROOT/RUN_NUR.sh" status
      open_nur
      exit 0
    fi
    if [[ "$MODE" == "openai" ]]; then
      printf 'Starting the complete NUR universe with the configured local OpenAI provider.\n'
    else
      printf 'Starting the complete NUR universe in honest disabled-provider mode.\n'
      printf 'To enable real Talk later: bash infra/scripts/configure-openai-local.sh\n'
    fi
    exec bash "$ROOT/RUN_NUR.sh" "$MODE"
    ;;
  setup)
    bash "$ROOT/infra/scripts/configure-openai-local.sh"
    exec bash "$ROOT/START_NUR.sh" openai
    ;;
  status|stop|logs|doctor|seed|reset-demo|package)
    exec bash "$ROOT/RUN_NUR.sh" "$MODE"
    ;;
  *)
    printf 'Unknown mode: %s\n' "$MODE" >&2
    printf 'Use: auto, setup, openai, disabled, status, stop, logs, doctor, seed, reset-demo, or package.\n' >&2
    exit 2
    ;;
esac
