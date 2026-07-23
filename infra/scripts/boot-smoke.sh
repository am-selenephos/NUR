#!/usr/bin/env bash
# Clean-boot + graceful-shutdown smoke (Phase 15).
#
# Boots the real API process against a configured Postgres + Redis, waits for
# readiness, checks the live public surfaces, then sends SIGTERM and confirms the
# process drains and exits cleanly (the Phase 3 graceful shutdown) within a
# deadline rather than being force-killed. Exit 0 means the packaged service
# starts from cold and stops cleanly.
#
# Env:
#   DATABASE_URL / REDIS_URL   connection strings (defaults to local dev)
#   NUR_SMOKE_PORT             port to bind (default 8099)
#   NUR_SMOKE_PYTHON           python to use (default: python)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/apps/api"

PORT="${NUR_SMOKE_PORT:-8099}"
PY="${NUR_SMOKE_PYTHON:-python}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://nur_app:change_me@localhost:5432/nur}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
BASE="http://127.0.0.1:${PORT}"

"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --log-level warning &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT

echo "== BOOT SMOKE =="
echo "pid ${PID} on ${BASE}"

ready=0
for _ in $(seq 1 60); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "BOOT SMOKE FAIL: process exited before becoming ready" >&2; exit 1
  fi
  if [[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/readyz" || true)" == "200" ]]; then
    ready=1; break
  fi
  sleep 0.5
done
[[ "$ready" == "1" ]] || { echo "BOOT SMOKE FAIL: /readyz never returned 200" >&2; exit 1; }
echo "ready: /readyz 200"

for path in /healthz /metrics; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "${BASE}${path}")"
  [[ "$code" == "200" ]] || { echo "BOOT SMOKE FAIL: ${path} -> ${code}" >&2; exit 1; }
  echo "ok: ${path} 200"
done

# Graceful shutdown: SIGTERM must drain and exit within the deadline.
echo "sending SIGTERM..."
kill -TERM "$PID"
deadline=$(( SECONDS + 15 ))
while kill -0 "$PID" 2>/dev/null; do
  (( SECONDS < deadline )) || { echo "BOOT SMOKE FAIL: no clean exit within 15s of SIGTERM" >&2; exit 1; }
  sleep 0.3
done
trap - EXIT
wait "$PID" 2>/dev/null && rc=0 || rc=$?
echo "graceful shutdown: exited within deadline (rc=${rc})"
echo "BOOT SMOKE PASS: clean cold boot, live /readyz + /healthz + /metrics, graceful SIGTERM shutdown."
