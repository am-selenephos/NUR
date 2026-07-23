#!/usr/bin/env bash
# Full disaster-recovery backup: Postgres database + local object store + a
# verified manifest (applied Alembic revision, dump digest, per-object digests).
#
# Usage:
#   NUR_DR_DATABASE_URL=postgresql://user:pass@host:port/db \
#   NUR_DR_OBJECT_ROOT=/path/to/project-objects \
#   dr-backup.sh <backup-dir>
#
# The database URL should be a role that can read every row (a superuser or the
# schema owner); RLS-restricted roles produce an incomplete dump.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${1:?Usage: dr-backup.sh <backup-dir>}"
DB_URL="${NUR_DR_DATABASE_URL:-${DATABASE_URL:-}}"
OBJECT_ROOT="${NUR_DR_OBJECT_ROOT:-$ROOT/.nur-runtime/project-objects}"

if [[ -z "$DB_URL" ]]; then
  printf "Set NUR_DR_DATABASE_URL (or DATABASE_URL) before backup.\n" >&2
  exit 2
fi
DB_URL="${DB_URL/postgresql+asyncpg:/postgresql:}"

mkdir -p "$BACKUP_DIR"
DUMP="$BACKUP_DIR/db.dump"
OBJ_OUT="$BACKUP_DIR/objects"

# 1. Database — custom format, restore-friendly, ownerless.
pg_dump --format=custom --no-owner --no-privileges --file "$DUMP" "$DB_URL"

# 2. Applied migration revision (empty if the schema has no alembic_version).
REVISION="$(psql "$DB_URL" -tAc "SELECT version_num FROM alembic_version" 2>/dev/null | head -n1 | tr -d '[:space:]' || true)"
REVISION="${REVISION:-none}"

# 3. Object store — copy the tree faithfully (preserve structure; skip if empty).
mkdir -p "$OBJ_OUT"
if [[ -d "$OBJECT_ROOT" ]]; then
  # -a preserves the layout; the trailing dot copies contents, not the dir.
  cp -a "$OBJECT_ROOT/." "$OBJ_OUT/" 2>/dev/null || true
fi

# 4. Manifest — the integrity contract (Python owns it; unit-tested).
python -m app.services.dr build \
  --db-dump "$DUMP" \
  --object-root "$OBJ_OUT" \
  --alembic-revision "$REVISION" \
  --out "$BACKUP_DIR/manifest.json"

sha256sum "$BACKUP_DIR/manifest.json" > "$BACKUP_DIR/manifest.json.sha256"
printf "%s\n" "$BACKUP_DIR"
