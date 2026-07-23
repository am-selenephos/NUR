"""Storage hygiene: orphan reconciliation and deleted-record retention.

Two kinds of drift accumulate between the object store and the database:

* **orphans** — bytes on disk with no owning ``AMProjectFile`` row (a crash
  between the disk write and the row commit, or a rejected upload whose cleanup
  did not land), which waste space forever; and
* **dangling** rows — a file row whose bytes have vanished from disk, which must
  be surfaced rather than silently downloaded as a 404.

Orphan reconciliation compares the *complete* on-disk key set against the
*complete* database key set, so it is a maintenance operation that must run with
a database role able to read every owner's rows (like the DR tooling) — never as
the RLS-scoped app role, which sees only one owner and would wrongly delete
another owner's live objects. The pure reconciliation is unit-tested; the sweep
only deletes when explicitly asked.

Retention purge is owner-scoped and RLS-safe: it hard-deletes this owner's file
rows that were marked DELETED long enough ago.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AMProjectFile
from app.models._mixins import now_utc
from app.services.object_storage import LocalObjectStorage


@dataclass
class ReconcileReport:
    orphans: list[str]   # on disk, no database row
    dangling: list[str]  # database row, missing on disk

    @property
    def clean(self) -> bool:
        return not self.orphans and not self.dangling


def reconcile_object_index(
    *, db_object_keys: Iterable[str], disk_object_keys: Iterable[str]
) -> ReconcileReport:
    """Compare the database and on-disk key sets. Pure; no I/O."""
    db = set(db_object_keys)
    disk = set(disk_object_keys)
    return ReconcileReport(orphans=sorted(disk - db), dangling=sorted(db - disk))


def sweep_orphan_objects(
    storage: LocalObjectStorage, *, db_object_keys: Iterable[str], delete_orphans: bool = False
) -> ReconcileReport:
    """Reconcile the store against the given database key set.

    ``db_object_keys`` MUST be every owner's keys (a full, un-scoped read), or a
    live object will be misjudged an orphan. Deletes orphaned bytes only when
    ``delete_orphans`` is set; dangling rows are reported, never fabricated away.
    """
    report = reconcile_object_index(
        db_object_keys=db_object_keys, disk_object_keys=storage.iter_object_keys()
    )
    if delete_orphans:
        for key in report.orphans:
            storage.delete(key)
    return report


async def all_object_keys(db: AsyncSession) -> list[str]:
    """Every ``object_key`` visible to this session (RLS-scoped for the app role;
    every owner's for an elevated maintenance role)."""
    return list((await db.execute(select(AMProjectFile.object_key))).scalars().all())


async def purge_deleted_files(
    db: AsyncSession, *, older_than_seconds: int, now: dt.datetime | None = None
) -> int:
    """Hard-delete this owner's file rows marked DELETED before the retention
    cutoff. Owner-scoped under RLS. Returns the number of rows purged."""
    now = now or now_utc()
    cutoff = now - dt.timedelta(seconds=older_than_seconds)
    result = await db.execute(
        delete(AMProjectFile).where(
            AMProjectFile.storage_state == "DELETED",
            AMProjectFile.updated_at < cutoff,
        )
    )
    await db.commit()
    return result.rowcount or 0


async def _run_reconcile(*, database_url: str, object_root: str, delete_orphans: bool) -> int:
    """Cross-owner orphan reconciliation for a maintenance context.

    ``database_url`` must be an elevated role that reads every owner's rows;
    running this with the RLS-scoped app role would misjudge live objects as
    orphans. Prints a report and, with ``--delete``, removes orphaned bytes.
    """
    import sys

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    engine = create_async_engine(database_url)
    try:
        async with AsyncSession(engine) as db:
            db_keys = await all_object_keys(db)
    finally:
        await engine.dispose()

    storage = LocalObjectStorage(object_root)
    report = sweep_orphan_objects(
        storage, db_object_keys=db_keys, delete_orphans=delete_orphans
    )
    print(
        f"reconcile: db_rows={len(set(db_keys))} orphans={len(report.orphans)} "
        f"dangling={len(report.dangling)} "
        f"deleted={len(report.orphans) if delete_orphans else 0}",
        file=sys.stderr,
    )
    for key in report.dangling:
        print(f"DANGLING {key}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(prog="python -m app.services.storage_hygiene")
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("reconcile", help="reconcile object store against the database")
    rec.add_argument("--database-url", required=True, help="elevated (cross-owner) DSN")
    rec.add_argument("--object-root", required=True)
    rec.add_argument("--delete", action="store_true", help="delete orphaned bytes")
    args = parser.parse_args(argv)
    url = args.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return asyncio.run(
        _run_reconcile(database_url=url, object_root=args.object_root, delete_orphans=args.delete)
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
