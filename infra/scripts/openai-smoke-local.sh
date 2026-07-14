#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ ! -f .env.local ]]; then
  printf 'OpenAI smoke requires ignored .env.local. Run: bash infra/scripts/configure-openai-local.sh\n' >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
# shellcheck disable=SC1091
source .env.local
set +a

if [[ "${NUR_AI_PROVIDER:-}" != "openai" ]]; then
  printf 'OpenAI smoke requires NUR_AI_PROVIDER=openai in the running server environment.\n' >&2
  exit 1
fi

apps/api/.venv/bin/python - <<'PY'
import os
import sys

import httpx

API = os.environ.get("API_ORIGIN", "http://localhost:8000")
email = f"openai-smoke-{os.getpid()}@nurapp.dev"
password = "openai-smoke-pass-123"

client = httpx.Client(timeout=60)

def csrf():
    token = client.cookies.get("nur_csrf")
    return {"X-CSRF-Token": token} if token else {}

r = client.post(f"{API}/api/v1/auth/register", json={
    "chosen_name": "Smoke",
    "email": email,
    "password": password,
    "consent": True,
})
if r.status_code != 201:
    login = client.post(f"{API}/api/v1/auth/login", json={"email": email, "password": password})
    if login.status_code != 200:
        print(f"openai smoke auth failed: {r.status_code}/{login.status_code}", file=sys.stderr)
        raise SystemExit(1)

health = client.get(f"{API}/healthz")
health.raise_for_status()
if health.json().get("ai_provider") != "openai":
    print("openai smoke failed: healthz is not openai", file=sys.stderr)
    raise SystemExit(1)

talk = client.post(f"{API}/api/v1/cognition/talk", headers=csrf(), json={
    "message": "Run a minimal provider smoke. Do not include private content.",
    "locale": "en",
    "mode": "talk",
})
if talk.status_code != 200:
    print(f"openai smoke request failed: {talk.status_code} {talk.text[:240]}", file=sys.stderr)
    raise SystemExit(1)
data = talk.json()
output = data.get("output") or {}
expected = {
    "direct_response",
    "observed",
    "inferred",
    "hypotheses",
    "uncertainty",
    "next_move",
    "memory_candidates",
    "source_refs",
}
schema_valid = (
    data.get("provider") == "openai"
    and data.get("provider_available") is True
    and bool(data.get("model_run_id"))
    and expected.issubset(output.keys())
    and isinstance(output.get("direct_response"), str)
    and all(isinstance(output.get(key), list) for key in ["observed", "inferred", "hypotheses", "uncertainty", "memory_candidates", "source_refs"])
)
source_refs = output.get("source_refs") or []
source_refs_valid = all(isinstance(ref, str) and ":" in ref for ref in source_refs)
thread = client.get(f"{API}/api/v1/cognition/talk-thread")
thread.raise_for_status()
rows = thread.json()
response_persisted = any(
    row.get("who") == "nur"
    and (row.get("structured_payload") or {}).get("model_run_id") == data.get("model_run_id")
    for row in rows
)
proof = {
    "provider": data.get("provider"),
    "provider_available": data.get("provider_available"),
    "model_run_id_present": bool(data.get("model_run_id")),
    "schema_valid": schema_valid,
    "source_refs_valid": source_refs_valid,
    "response_persisted": response_persisted,
    "response_length": len(output.get("direct_response") or ""),
    "key_printed": False,
}
print(proof)
if not (schema_valid and source_refs_valid and response_persisted):
    raise SystemExit(1)
PY

if [[ "${NUR_OPENAI_UI_SMOKE:-1}" == "1" ]]; then
  node infra/scripts/openai-ui-smoke.mjs
fi
