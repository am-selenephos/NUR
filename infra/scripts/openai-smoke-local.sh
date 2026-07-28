#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

bash infra/scripts/validate-openai-local.sh >/dev/null

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
import json
import uuid

import httpx

API = os.environ.get("API_ORIGIN", "http://localhost:8000")
email = f"openai-smoke-{os.getpid()}@nurapp.dev"
password = "openai-smoke-pass-123"

client = httpx.Client(timeout=90)

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

request_id = str(uuid.uuid4())
talk = client.post(f"{API}/api/v1/cognition/talk/stream", headers=csrf(), json={
    "request_id": request_id,
    "message": "Run a minimal provider smoke. Do not include private content.",
    "locale": "en",
    "writing_preference": "default",
    "mode": "talk",
})
if talk.status_code != 200:
    print(f"openai smoke request failed: {talk.status_code} {talk.text[:240]}", file=sys.stderr)
    raise SystemExit(1)

events = []
for block in talk.text.replace("\r\n", "\n").split("\n\n"):
    event_name = "message"
    data_lines = []
    for line in block.splitlines():
        if line.startswith("event: "):
            event_name = line.removeprefix("event: ")
        elif line.startswith("data: "):
            data_lines.append(line.removeprefix("data: "))
    if data_lines:
        events.append((event_name, json.loads("\n".join(data_lines))))

completed_rows = [payload for name, payload in events if name == "talk.completed"]
if len(completed_rows) != 1:
    names = [name for name, _ in events]
    print(f"openai smoke stream failed closed: events={names}", file=sys.stderr)
    raise SystemExit(1)
data = completed_rows[0]["result"]
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
event_names = [name for name, _ in events]
semantic_stream_valid = (
    "provider.created" in event_names
    and "response.text.delta" in event_names
    and "talk.validated" in event_names
    and "talk.error" not in event_names
)
status_response = client.get(f"{API}/api/v1/cognition/talk-runs/{request_id}")
status_response.raise_for_status()
status = status_response.json()
model_run_persisted = (
    status.get("status") == "COMPLETED"
    and status.get("model_run_id") == data.get("model_run_id")
    and status.get("schema_valid") is True
    and status.get("provider_response_id_present") is True
    and status.get("usage_recorded") is True
)
evidence_persisted = (
    isinstance(status.get("evidence_digest"), str)
    and len(status["evidence_digest"]) == 64
    and status.get("evidence_source_count") == len((data.get("evidence") or {}).get("retrieval") or [])
)
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
    "semantic_stream_valid": semantic_stream_valid,
    "model_run_persisted": model_run_persisted,
    "evidence_persisted": evidence_persisted,
    "response_persisted": response_persisted,
    "response_visible_after_refresh": response_persisted,
    "model": status.get("model"),
    "response_length": len(output.get("direct_response") or ""),
    "key_printed": False,
}
print(proof)
if not (
    schema_valid
    and source_refs_valid
    and semantic_stream_valid
    and model_run_persisted
    and evidence_persisted
    and response_persisted
):
    raise SystemExit(1)
PY

if [[ "${NUR_OPENAI_UI_SMOKE:-1}" == "1" ]]; then
  node infra/scripts/openai-ui-smoke.mjs
fi
