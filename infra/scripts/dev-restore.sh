#!/usr/bin/env bash
set -euo pipefail

BACKUP="${1:-}"
DB_URL="${NUR_RESTORE_DATABASE_URL:-${DATABASE_URL:-}}"

if [[ -z "$BACKUP" || ! -f "$BACKUP" ]]; then
  printf "Usage: NUR_RESTORE_DATABASE_URL=postgresql://... %s backup.dump\n" "$0" >&2
  exit 2
fi
if [[ -z "$DB_URL" ]]; then
  printf "Set NUR_RESTORE_DATABASE_URL or DATABASE_URL before running restore.\n" >&2
  exit 2
fi

DB_URL="${DB_URL/postgresql+asyncpg:/postgresql:}"
TMP_SQL="$(mktemp)"
trap 'rm -f "$TMP_SQL"' EXIT
pg_restore --clean --if-exists --no-owner --no-privileges --file "$TMP_SQL" "$BACKUP"
# Newer pg_dump clients may emit SET transaction_timeout for older local
# Postgres servers that do not know that GUC. It is not schema/data state.
sed -i '/^SET transaction_timeout =/d' "$TMP_SQL"
psql "$DB_URL" -v ON_ERROR_STOP=1 -q -f "$TMP_SQL"
printf "Restored %s into configured development database.\n" "$BACKUP"
