#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-disabled}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="$ROOT/.nur-runtime"
mkdir -p "$RUNTIME"
cd "$ROOT"

if [[ ! -f .env ]]; then
  printf 'Missing .env. Run: cp .env.example .env\n' >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
if [[ "$MODE" == "openai" ]]; then
  bash infra/scripts/validate-openai-local.sh >/dev/null
  # shellcheck disable=SC1091
  source .env.local
else
  export NUR_AI_PROVIDER=disabled
fi
export VITE_NUR_ENABLE_OMEGA_RESEARCH="${VITE_NUR_ENABLE_OMEGA_RESEARCH:-true}"
set +a

PG_HOST="${NUR_POSTGRES_HOST:-127.0.0.1}"
PG_PORT="${NUR_POSTGRES_PORT:-5432}"
REDIS_HOST="${NUR_REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${NUR_REDIS_PORT:-6379}"
if ! PGPASSWORD=postgres pg_isready -h "$PG_HOST" -p "$PG_PORT" -U postgres -d postgres >/dev/null 2>&1 \
  || ! timeout 5s bash -c "</dev/tcp/${REDIS_HOST}/${REDIS_PORT}" >/dev/null 2>&1; then
  bash infra/scripts/bootstrap-dev.sh
fi
# A fresh local boot must not inherit burned per-IP auth limiter windows
# (rl:* keys) from an earlier session or an e2e battery on this machine.
# The limiter itself stays fully active for the new session.
if command -v redis-cli >/dev/null 2>&1; then
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern 'rl:*' \
    | xargs -r redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" del >/dev/null
fi
(cd apps/api && .venv/bin/python -m alembic.config upgrade head)

start_proc() {
  local name="$1"
  shift
  local pidfile="$RUNTIME/$name.pid"
  local logfile="$RUNTIME/$name.log"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" >/dev/null 2>&1; then
    printf '%s already running pid %s\n' "$name" "$(cat "$pidfile")"
    return
  fi
  if command -v setsid >/dev/null 2>&1; then
    setsid bash -c 'echo $$ > "$1"; shift; exec "$@"' nur-child "$pidfile" "$@" >"$logfile" 2>&1 < /dev/null &
  else
    nohup bash -c 'echo $$ > "$1"; shift; exec "$@"' nur-child "$pidfile" "$@" >"$logfile" 2>&1 < /dev/null &
  fi
  for _ in $(seq 1 20); do
    [[ -s "$pidfile" ]] && break
    sleep 0.1
  done
  printf 'Started %s pid %s log %s\n' "$name" "$(cat "$pidfile")" "$logfile"
}

start_proc api bash -lc "cd '$ROOT/apps/api' && .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start_proc worker bash -lc "cd '$ROOT/apps/api' && .venv/bin/celery -A app.workers.celery_app.celery worker --loglevel=INFO"
start_proc beat bash -lc "cd '$ROOT/apps/api' && .venv/bin/celery -A app.workers.celery_app.celery beat --loglevel=INFO"
start_proc web bash -lc "cd '$ROOT' && npm --workspace apps/web run dev -- --host 0.0.0.0 --port 5173"

printf 'NUR starting in %s mode. Check: bash infra/scripts/status-nur.sh\n' "$MODE"
