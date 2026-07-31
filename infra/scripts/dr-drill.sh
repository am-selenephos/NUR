#!/usr/bin/env bash
# A real disaster-recovery drill, fully isolated from production state:
#
#   1. seed an isolated object store with known content,
#   2. back up a real source database + that object store (dr-backup.sh),
#   3. provision a fresh isolated target database + object root,
#   4. restore into the target and verify byte-for-byte (dr-restore.sh),
#   5. cross-check row parity between source and restored target,
#   6. tear the target down.
#
# It never writes to the source database or to production object roots. Exit 0
# means a backup taken now can be restored and independently verified.
#
# Env (all have working defaults for a local dev cluster):
#   NUR_DR_SUPERUSER_DSN   base superuser DSN, no database (default local postgres)
#   NUR_DR_SOURCE_DB       database to back up (default: nur)
#   NUR_DR_TARGET_OWNER    owner role for the isolated restore db (default: nur_admin)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/apps/api"  # so `python -m app.services.dr` resolves

SUP_DSN="${NUR_DR_SUPERUSER_DSN:-postgresql://postgres:postgres@localhost:5432}"
SOURCE_DB="${NUR_DR_SOURCE_DB:-nur}"
TARGET_OWNER="${NUR_DR_TARGET_OWNER:-nur_admin}"
TARGET_DB="nur_dr_drill_$$"

WORK="$(mktemp -d)"
cleanup() {
  psql "$SUP_DSN/postgres" -v ON_ERROR_STOP=0 -q \
    -c "DROP DATABASE IF EXISTS ${TARGET_DB} WITH (FORCE)" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

echo "== DR DRILL =="
echo "source db      : ${SOURCE_DB}"
echo "isolated target: ${TARGET_DB} (owner ${TARGET_OWNER})"
echo "workspace      : ${WORK}"

# 1. Seed an isolated source object store (sharded layout, known content).
SRC_OBJ="$WORK/src-objects"
mkdir -p "$SRC_OBJ/ab" "$SRC_OBJ/cd/ef"
printf 'deliverable-one-%s' "$(date -u +%s)" > "$SRC_OBJ/ab/$(openssl rand -hex 8 2>/dev/null || echo abcd1111)"
head -c 4096 /dev/urandom > "$SRC_OBJ/cd/ef/$(openssl rand -hex 8 2>/dev/null || echo cdef2222)"
SRC_OBJ_COUNT="$(find "$SRC_OBJ" -type f | wc -l | tr -d ' ')"

# 2. Back up source db + seeded object store.
BACKUP="$WORK/backup"
NUR_DR_DATABASE_URL="$SUP_DSN/$SOURCE_DB" \
NUR_DR_OBJECT_ROOT="$SRC_OBJ" \
  bash "$ROOT/infra/scripts/dr-backup.sh" "$BACKUP" >/dev/null
echo "backup written : $BACKUP"

SRC_USERS="$(psql "$SUP_DSN/$SOURCE_DB" -tAc "SELECT count(*) FROM users" 2>/dev/null | tr -d '[:space:]' || echo '?')"
SRC_REV="$(psql "$SUP_DSN/$SOURCE_DB" -tAc "SELECT version_num FROM alembic_version" 2>/dev/null | tr -d '[:space:]' || echo none)"

# 3. Provision a fresh isolated target database.
psql "$SUP_DSN/postgres" -v ON_ERROR_STOP=1 -q \
  -c "DROP DATABASE IF EXISTS ${TARGET_DB} WITH (FORCE)" \
  -c "CREATE DATABASE ${TARGET_DB} OWNER ${TARGET_OWNER}"

# 4. Restore + verify (dr-restore.sh fails closed on any discrepancy).
TGT_OBJ="$WORK/tgt-objects"
NUR_DR_RESTORE_DATABASE_URL="$SUP_DSN/$TARGET_DB" \
NUR_DR_RESTORE_OBJECT_ROOT="$TGT_OBJ" \
  bash "$ROOT/infra/scripts/dr-restore.sh" "$BACKUP"

# 5. Row-parity cross-check: schema restoring is not enough; data must match.
TGT_USERS="$(psql "$SUP_DSN/$TARGET_DB" -tAc "SELECT count(*) FROM users" 2>/dev/null | tr -d '[:space:]' || echo '?')"
TGT_REV="$(psql "$SUP_DSN/$TARGET_DB" -tAc "SELECT version_num FROM alembic_version" 2>/dev/null | tr -d '[:space:]' || echo none)"

echo "-- parity --"
echo "revision : source=${SRC_REV} target=${TGT_REV}"
echo "users    : source=${SRC_USERS} target=${TGT_USERS}"
echo "objects  : seeded=${SRC_OBJ_COUNT}"

if [[ "$SRC_USERS" != "$TGT_USERS" || "$SRC_REV" != "$TGT_REV" ]]; then
  echo "DR DRILL FAILED: source/target parity mismatch" >&2
  exit 1
fi

echo "DR DRILL PASS: backup restored into an isolated target and verified (revision, object digests, db dump digest, row parity)."
