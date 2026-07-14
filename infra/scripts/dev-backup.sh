#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${1:-$ROOT/proof/100/dev-backup-$STAMP.dump}"
DB_URL="${NUR_BACKUP_DATABASE_URL:-${DATABASE_URL:-}}"

if [[ -z "$DB_URL" ]]; then
  printf "Set NUR_BACKUP_DATABASE_URL or DATABASE_URL before running backup.\n" >&2
  exit 2
fi

DB_URL="${DB_URL/postgresql+asyncpg:/postgresql:}"
mkdir -p "$(dirname "$OUT")"
pg_dump --format=custom --no-owner --no-privileges --file "$OUT" "$DB_URL"
sha256sum "$OUT" > "$OUT.sha256"
printf "%s\n" "$OUT"
