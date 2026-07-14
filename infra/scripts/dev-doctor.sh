#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

fail=0
check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf 'PASS %s\n' "$label"
  else
    printf 'FAIL %s\n' "$label"
    fail=1
  fi
}

if docker --version >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  printf 'PASS docker compose available\n'
else
  printf 'INFO docker compose unavailable; local runtime can still boot NUR\n'
fi
if command -v initdb >/dev/null 2>&1 \
  && command -v pg_ctl >/dev/null 2>&1 \
  && command -v postgres >/dev/null 2>&1; then
  printf 'PASS local Postgres runtime available\n'
else
  printf 'FAIL local Postgres runtime unavailable\n'
  fail=1
fi
if command -v valkey-server >/dev/null 2>&1 || command -v redis-server >/dev/null 2>&1; then
  printf 'PASS local Redis-compatible runtime available\n'
else
  printf 'FAIL local Redis-compatible runtime unavailable\n'
  fail=1
fi
check "node" node --version
check "npm" npm --version
check "python3" python3 --version
if psql --version >/dev/null 2>&1; then
  printf 'PASS psql client optional\n'
else
  printf 'INFO psql client missing; bootstrap uses docker compose exec psql\n'
fi

if [[ -f .env ]]; then
  printf 'PASS .env exists\n'
else
  printf 'FAIL .env missing: run cp .env.example .env\n'
  fail=1
fi

if [[ -f .env.local ]]; then
  mode="$(stat -c '%a' .env.local 2>/dev/null || echo unknown)"
  if [[ "$mode" == "600" ]]; then
    printf 'PASS .env.local exists with mode 600\n'
  else
    printf 'FAIL .env.local exists but mode is %s; run chmod 600 .env.local\n' "$mode"
    fail=1
  fi
else
  printf 'PASS .env.local absent; OpenAI mode will stay disabled\n'
fi

if rg -n --pcre2 "sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY[[:space:]]*=[[:space:]]*[^[:space:]#]+" apps/web packages --glob '!node_modules' >/tmp/nur-doctor-secret-hit.txt 2>/dev/null; then
  printf 'FAIL possible frontend secret reference:\n'
  sed -n '1,10p' /tmp/nur-doctor-secret-hit.txt
  fail=1
else
  printf 'PASS no frontend OpenAI key reference\n'
fi

for port in "${NUR_POSTGRES_PORT:-5432}" "${NUR_REDIS_PORT:-6379}" 8000 5173; do
  if ss -ltn "( sport = :$port )" 2>/dev/null | grep -q ":$port"; then
    printf 'INFO port %s is already listening\n' "$port"
  else
    printf 'PASS port %s currently free\n' "$port"
  fi
done

exit "$fail"
