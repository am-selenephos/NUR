#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${NUR_OPENAI_ENV_FILE:-$ROOT/.env.local}"

fail() {
  printf 'OpenAI local configuration is invalid: %s\n' "$1" >&2
  exit 1
}

[[ -f "$ENV_FILE" ]] || fail "missing .env.local"
[[ ! -L "$ENV_FILE" ]] || fail ".env.local must not be a symbolic link"
[[ "$(stat -c '%a' "$ENV_FILE" 2>/dev/null || true)" == "600" ]] \
  || fail ".env.local must have mode 600"
bash -n "$ENV_FILE" >/dev/null 2>&1 || fail ".env.local has invalid shell syntax"

if ! (
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  [[ "${NUR_AI_PROVIDER-}" == "openai" \
    && -n "${NUR_OPENAI_MODEL-}" \
    && -n "${OPENAI_API_KEY-}" \
    && "$NUR_OPENAI_MODEL" != *$'\r'* \
    && "$NUR_OPENAI_MODEL" != *$'\n'* \
    && "$OPENAI_API_KEY" != *$'\r'* \
    && "$OPENAI_API_KEY" != *$'\n'* ]]
); then
  fail ".env.local must define openai provider, model, and key as single-line values"
fi

# Structural validation only. This checks file mode, syntax, and that the
# provider/model/key are present and single-line. It does NOT contact OpenAI and
# therefore does NOT prove the credential is valid or the model is reachable.
printf 'OpenAI configuration file is structurally valid. Live authentication has not yet been tested.\n'
printf 'Run the live provider smoke to prove the credential and model access.\n'
