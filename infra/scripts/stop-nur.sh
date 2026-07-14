#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="$ROOT/.nur-runtime"
cd "$ROOT"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

kill_tree() {
  local pid="$1"
  local label="$2"
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill -- "-$pid" >/dev/null 2>&1 || kill "$pid" >/dev/null 2>&1 || true
    printf 'Stopped %s pid %s\n' "$label" "$pid"
  fi
}

for name in web beat worker api; do
  pidfile="$RUNTIME/$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    kill_tree "$pid" "$name"
    rm -f "$pidfile"
  fi
done

for pattern in \
  "$ROOT/apps/api.*uvicorn app.main:app --host 0.0.0.0 --port 8000" \
  "$ROOT/apps/api.*celery -A app.workers.celery_app.celery worker" \
  "$ROOT/apps/api.*celery -A app.workers.celery_app.celery beat" \
  "$ROOT/node_modules/.bin/vite --host 0.0.0.0 --port 5173"
do
  while read -r pid; do
    [[ -n "$pid" ]] && kill_tree "$pid" "orphan"
  done < <(pgrep -f "$pattern" || true)
done

for port in 8000 5173; do
  while read -r pid; do
    [[ -n "$pid" ]] && kill_tree "$pid" "port-$port"
  done < <(fuser "${port}/tcp" 2>&1 | awk '{ for (i = 1; i <= NF; i++) if ($i ~ /^[0-9]+$/) print $i }' || true)
done

if [[ -s "$RUNTIME/redis.pid" ]]; then
  redis_pid="$(cat "$RUNTIME/redis.pid")"
  if kill -0 "$redis_pid" >/dev/null 2>&1; then
    kill "$redis_pid" >/dev/null 2>&1 || true
    printf 'Stopped Redis-compatible pid %s\n' "$redis_pid"
  fi
  rm -f "$RUNTIME/redis.pid"
fi
if [[ -s "$RUNTIME/postgres-data/PG_VERSION" ]] && pg_ctl -D "$RUNTIME/postgres-data" status >/dev/null 2>&1; then
  pg_ctl -D "$RUNTIME/postgres-data" -m fast -w -t 30 stop >/dev/null || true
  printf 'Stopped local Postgres runtime\n'
fi

for container in "${NUR_POSTGRES_CONTAINER_NAME:-}" "${NUR_REDIS_CONTAINER_NAME:-}"; do
  if [[ -n "$container" ]] && timeout 5s docker ps --filter "name=^/${container}$" --format '{{.Names}}' | grep -qx "$container"; then
    timeout 15s docker stop "$container" >/dev/null || printf 'Timed out stopping %s; it will be reused or replaced on next boot.\n' "$container" >&2
  fi
done
printf 'NUR stopped.\n'
