"""Disaster-recovery backup manifest and restore verification.

NUR's durable state is two things: the Postgres database and the local-first
object store (``NUR_PROJECT_OBJECT_ROOT``, default ``.nur-runtime/project-objects``).
A backup that captures only the database silently loses every uploaded and
generated deliverable, and a restore that is never verified is not a restore —
it is a hope.

The shell wrappers ``infra/scripts/dr-backup.sh`` and ``infra/scripts/dr-restore.sh``
own the ``pg_dump``/``pg_restore`` mechanics; this module owns the integrity
contract so it lives in exactly one place and is unit-testable without a
database:

* :func:`build_manifest` records the applied Alembic revision, the database
  dump's size + SHA-256, and every object's relative path, size, and SHA-256.
* :func:`verify_restore` fails closed: it returns the concrete list of every
  discrepancy between a manifest and a restored target — a wrong migration
  revision, a missing/corrupted/extra object, or a mismatched dump — and an
  empty list only when the restore is byte-for-byte faithful.

Nothing here fabricates success: verification compares real recomputed digests,
never the manifest against itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MANIFEST_VERSION = 1
_CHUNK = 1 << 20


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_objects(object_root: Path):
    """Yield every regular file under ``object_root`` in stable order.

    Symlinks are skipped deliberately: the object store never writes them, and
    a symlink in a restore target must not be silently trusted as content.
    """
    if not object_root.exists():
        return
    for path in sorted(object_root.rglob("*")):
        if path.is_symlink():
            continue
        if path.is_file():
            yield path


def build_manifest(*, db_dump: Path, object_root: Path, alembic_revision: str) -> dict:
    """Build the backup manifest for a database dump plus an object store root."""
    objects: list[dict] = []
    total_bytes = 0
    for path in _iter_objects(object_root):
        size = path.stat().st_size
        total_bytes += size
        objects.append(
            {
                "path": path.relative_to(object_root).as_posix(),
                "bytes": size,
                "sha256": _sha256_file(path),
            }
        )
    return {
        "manifest_version": MANIFEST_VERSION,
        "alembic_revision": alembic_revision,
        "db_dump": {
            "name": db_dump.name,
            "bytes": db_dump.stat().st_size,
            "sha256": _sha256_file(db_dump),
        },
        "object_store": {
            "count": len(objects),
            "total_bytes": total_bytes,
            "objects": objects,
        },
    }


def verify_restore(
    *,
    manifest: dict,
    restored_object_root: Path,
    restored_alembic_revision: str,
    db_dump: Path | None = None,
) -> list[str]:
    """Return every discrepancy between ``manifest`` and a restored target.

    An empty list means the restore is verified. A non-empty list is the exact,
    ordered set of reasons it is not — the caller must treat any entry as a hard
    failure.
    """
    issues: list[str] = []

    expected_revision = manifest.get("alembic_revision")
    if restored_alembic_revision != expected_revision:
        issues.append(
            f"alembic revision mismatch: manifest={expected_revision!r} "
            f"restored={restored_alembic_revision!r}"
        )

    if db_dump is not None:
        expected = manifest.get("db_dump", {})
        if not db_dump.exists():
            issues.append(f"db dump missing at {db_dump}")
        else:
            actual_sha = _sha256_file(db_dump)
            if actual_sha != expected.get("sha256"):
                issues.append("db dump checksum mismatch")

    expected_objects = {
        obj["path"]: obj["sha256"]
        for obj in manifest.get("object_store", {}).get("objects", [])
    }
    found_objects = {
        path.relative_to(restored_object_root).as_posix(): _sha256_file(path)
        for path in _iter_objects(restored_object_root)
    }
    for rel_path, sha in expected_objects.items():
        if rel_path not in found_objects:
            issues.append(f"missing object: {rel_path}")
        elif found_objects[rel_path] != sha:
            issues.append(f"object checksum mismatch: {rel_path}")
    for rel_path in found_objects:
        if rel_path not in expected_objects:
            issues.append(f"unexpected object not in manifest: {rel_path}")

    return issues


def _cmd_build(args: argparse.Namespace) -> int:
    manifest = build_manifest(
        db_dump=Path(args.db_dump),
        object_root=Path(args.object_root),
        alembic_revision=args.alembic_revision,
    )
    Path(args.out).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    obj = manifest["object_store"]
    print(
        f"manifest: revision={manifest['alembic_revision']} "
        f"objects={obj['count']} object_bytes={obj['total_bytes']} "
        f"db_dump_sha={manifest['db_dump']['sha256'][:12]}",
        file=sys.stderr,
    )
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    manifest = json.loads(Path(args.manifest).read_text())
    issues = verify_restore(
        manifest=manifest,
        restored_object_root=Path(args.object_root),
        restored_alembic_revision=args.alembic_revision,
        db_dump=Path(args.db_dump) if args.db_dump else None,
    )
    if issues:
        print("RESTORE VERIFICATION FAILED:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1
    obj = manifest.get("object_store", {})
    print(
        "RESTORE VERIFIED: revision="
        f"{manifest.get('alembic_revision')} objects={obj.get('count')} "
        f"object_bytes={obj.get('total_bytes')}",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.services.dr")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="build a backup manifest")
    build.add_argument("--db-dump", required=True)
    build.add_argument("--object-root", required=True)
    build.add_argument("--alembic-revision", required=True)
    build.add_argument("--out", required=True)
    build.set_defaults(func=_cmd_build)

    verify = sub.add_parser("verify", help="verify a restored target against a manifest")
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--object-root", required=True)
    verify.add_argument("--alembic-revision", required=True)
    verify.add_argument("--db-dump", default=None)
    verify.set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
