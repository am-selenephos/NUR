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

WEB_URL="${WEB_ORIGIN:-http://localhost:5173}"
API_URL="${API_ORIGIN:-http://localhost:8000}"
COOKIE_JAR="$(mktemp)"
WEB_COOKIE_JAR="$(mktemp)"
LOGIN_BODY="$(mktemp)"
ME_BODY="$(mktemp)"
WEB_LOGIN_BODY="$(mktemp)"
WEB_ME_BODY="$(mktemp)"
trap 'rm -f "$COOKIE_JAR" "$WEB_COOKIE_JAR" "$LOGIN_BODY" "$ME_BODY" "$WEB_LOGIN_BODY" "$WEB_ME_BODY"' EXIT

fail() {
  printf '\nPRESENTATION RECOVERY FAILED: %s\n' "$1" >&2
  printf 'Run: bash RUN_NUR.sh logs\n' >&2
  exit 1
}

printf 'NUR presentation recovery: non-destructive restart in disabled-provider mode.\n'
printf 'Existing database data is preserved. No reset-demo is performed.\n\n'

bash RUN_NUR.sh stop
bash RUN_NUR.sh disabled

curl -fsS --max-time 8 "$API_URL/healthz" >/dev/null \
  || fail "API /healthz is unavailable."
curl -fsS --max-time 8 "$API_URL/readyz" >/dev/null \
  || fail "API /readyz is unavailable."
curl -fsS --max-time 8 "$WEB_URL" >/dev/null \
  || fail "Web interface is unavailable."

LOGIN_STATUS="$(curl -sS --max-time 8 -o "$LOGIN_BODY" -w '%{http_code}' \
  -c "$COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@nur.app","password":"owner-demo-pass-123"}' \
  "$API_URL/api/v1/auth/login")"
[[ "$LOGIN_STATUS" == "200" ]] \
  || fail "Demo login returned HTTP $LOGIN_STATUS."

ME_STATUS="$(curl -sS --max-time 8 -o "$ME_BODY" -w '%{http_code}' \
  -b "$COOKIE_JAR" "$API_URL/api/v1/auth/me")"
[[ "$ME_STATUS" == "200" ]] \
  || fail "Session verification returned HTTP $ME_STATUS."

WEB_LOGIN_STATUS="$(curl -sS --max-time 8 -o "$WEB_LOGIN_BODY" -w '%{http_code}' \
  -c "$WEB_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@nur.app","password":"owner-demo-pass-123"}' \
  "$WEB_URL/api/v1/auth/login")"
[[ "$WEB_LOGIN_STATUS" == "200" ]] \
  || fail "Web-origin login returned HTTP $WEB_LOGIN_STATUS."
grep -q $'\tnur_session\t' "$WEB_COOKIE_JAR" \
  || fail "Web-origin login did not retain the nur_session cookie."
grep -q $'\tnur_csrf\t' "$WEB_COOKIE_JAR" \
  || fail "Web-origin login did not retain the nur_csrf cookie."

WEB_ME_STATUS="$(curl -sS --max-time 8 -o "$WEB_ME_BODY" -w '%{http_code}' \
  -b "$WEB_COOKIE_JAR" "$WEB_URL/api/v1/auth/me")"
[[ "$WEB_ME_STATUS" == "200" ]] \
  || fail "Web-origin session verification returned HTTP $WEB_ME_STATUS."

WEB_ORIGIN="$WEB_URL" node infra/scripts/auth-runtime-browser-proof.mjs \
  || fail "Exact web-origin browser login/refresh/logout proof failed."

printf '\nPASS: direct API auth, exact web-origin cookie auth, /today, refresh, and logout verified.\n'
printf 'Open: %s\n' "$WEB_URL"
printf 'Presentation login: owner@nur.app / owner-demo-pass-123\n'
printf 'Provider mode: disabled (honest demo mode; no fake AI response).\n'
printf 'If the browser has stale state, use Ctrl+Shift+R once.\n'
