#!/usr/bin/env bash
# Restore a dr-backup into an ISOLATED target and verify it byte-for-byte before
# declaring success. Fails closed: a wrong revision, a missing/corrupted/extra
# object, or a tampered dump makes this exit non-zero.
#
# Usage:
#   NUR_DR_RESTORE_DATABASE_URL=postgresql://user:pass@host:port/isolated_db \
#   NUR_DR_RESTORE_OBJECT_ROOT=/path/to/isolated/object-root \
#   dr-restore.sh <backup-dir>
#
# The target database and object root MUST be isolated (not production): restore
# is destructive to them (--clean).
set -euo pipefail

BACKUP_DIR="${1:?Usage: dr-restore.sh <backup-dir>}"
DB_URL="${NUR_DR_RESTORE_DATABASE_URL:-}"
OBJECT_ROOT="${NUR_DR_RESTORE_OBJECT_ROOT:-}"

if [[ -z "$DB_URL" || -z "$OBJECT_ROOT" ]]; then
  printf "Set NUR_DR_RESTORE_DATABASE_URL and NUR_DR_RESTORE_OBJECT_ROOT.\n" >&2
  exit 2
fi
DB_URL="${DB_URL/postgresql+asyncpg:/postgresql:}"

DUMP="$BACKUP_DIR/db.dump"
MANIFEST="$BACKUP_DIR/manifest.json"
OBJ_SRC="$BACKUP_DIR/objects"
for required in "$DUMP" "$MANIFEST"; do
  [[ -f "$required" ]] || { printf "Backup incomplete: missing %s\n" "$required" >&2; exit 2; }
done

# 0. Manifest integrity first — a tampered manifest cannot be trusted to verify.
if [[ -f "$MANIFEST.sha256" ]]; then
  ( cd "$BACKUP_DIR" && sha256sum -c manifest.json.sha256 >/dev/null ) \
    || { printf "Manifest checksum does not match — refusing restore.\n" >&2; exit 1; }
fi

# 1. Database — restore into the isolated target.
TMP_SQL="$(mktemp)"
trap 'rm -f "$TMP_SQL"' EXIT
pg_restore --clean --if-exists --no-owner --no-privileges --file "$TMP_SQL" "$DUMP"
# Strip a GUC newer pg_dump clients emit that older local servers reject; it is
# not schema or data state.
sed -i '/^SET transaction_timeout =/d' "$TMP_SQL"
psql "$DB_URL" -v ON_ERROR_STOP=1 -q -f "$TMP_SQL"

# 2. Object store — restore the tree into the isolated target root.
mkdir -p "$OBJECT_ROOT"
if [[ -d "$OBJ_SRC" ]]; then
  cp -a "$OBJ_SRC/." "$OBJECT_ROOT/" 2>/dev/null || true
fi

# 3. Verify — recompute everything against the manifest; fail closed.
RESTORED_REVISION="$(psql "$DB_URL" -tAc "SELECT version_num FROM alembic_version" 2>/dev/null | head -n1 | tr -d '[:space:]' || true)"
RESTORED_REVISION="${RESTORED_REVISION:-none}"

python -m app.services.dr verify \
  --manifest "$MANIFEST" \
  --object-root "$OBJECT_ROOT" \
  --alembic-revision "$RESTORED_REVISION"
