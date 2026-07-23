"""Disaster-recovery manifest + restore-verification contract.

Proves the integrity checks are real: a manifest captures the applied revision,
the database dump digest, and every object digest; and verification fails closed
on a wrong revision, a corrupted/missing/extra object, or a tampered dump — and
passes only on a byte-for-byte faithful restore.
"""

from pathlib import Path

from app.services.dr import build_manifest, verify_restore


def _seed_object_store(root: Path) -> None:
    # A sharded layout like the real object store: nested dirs, opaque names.
    (root / "ab").mkdir(parents=True)
    (root / "cd" / "ef").mkdir(parents=True)
    (root / "ab" / "abcd1111").write_bytes(b"first deliverable bytes")
    (root / "cd" / "ef" / "cdef2222").write_bytes(b"second deliverable, longer bytes\n" * 4)


def _write_dump(path: Path) -> None:
    path.write_bytes(b"PGDMP fake custom-format dump payload")


def test_build_manifest_captures_db_and_every_object(tmp_path: Path) -> None:
    root = tmp_path / "objects"
    _seed_object_store(root)
    dump = tmp_path / "db.dump"
    _write_dump(dump)

    manifest = build_manifest(db_dump=dump, object_root=root, alembic_revision="0030_project_execution_storage")

    assert manifest["alembic_revision"] == "0030_project_execution_storage"
    assert manifest["db_dump"]["bytes"] == dump.stat().st_size
    assert len(manifest["db_dump"]["sha256"]) == 64
    store = manifest["object_store"]
    assert store["count"] == 2
    assert store["total_bytes"] == sum(o["bytes"] for o in store["objects"])
    # Paths are relative + posix, never absolute server paths.
    paths = {o["path"] for o in store["objects"]}
    assert paths == {"ab/abcd1111", "cd/ef/cdef2222"}
    assert all(not o["path"].startswith("/") for o in store["objects"])


def test_verify_restore_passes_on_faithful_copy(tmp_path: Path) -> None:
    source = tmp_path / "src"
    _seed_object_store(source)
    dump = tmp_path / "db.dump"
    _write_dump(dump)
    manifest = build_manifest(db_dump=dump, object_root=source, alembic_revision="0030")

    # A faithful restore is the same tree + same dump + same revision.
    target = tmp_path / "restored"
    _seed_object_store(target)

    issues = verify_restore(
        manifest=manifest,
        restored_object_root=target,
        restored_alembic_revision="0030",
        db_dump=dump,
    )
    assert issues == []


def test_verify_restore_fails_on_wrong_revision(tmp_path: Path) -> None:
    root = tmp_path / "objects"
    _seed_object_store(root)
    dump = tmp_path / "db.dump"
    _write_dump(dump)
    manifest = build_manifest(db_dump=dump, object_root=root, alembic_revision="0030")

    issues = verify_restore(
        manifest=manifest,
        restored_object_root=root,
        restored_alembic_revision="0024",
    )
    assert any("revision mismatch" in issue for issue in issues)


def test_verify_restore_detects_corrupted_object(tmp_path: Path) -> None:
    source = tmp_path / "src"
    _seed_object_store(source)
    dump = tmp_path / "db.dump"
    _write_dump(dump)
    manifest = build_manifest(db_dump=dump, object_root=source, alembic_revision="0030")

    target = tmp_path / "restored"
    _seed_object_store(target)
    (target / "ab" / "abcd1111").write_bytes(b"silently corrupted during restore")

    issues = verify_restore(manifest=manifest, restored_object_root=target, restored_alembic_revision="0030")
    assert any("checksum mismatch: ab/abcd1111" in issue for issue in issues)


def test_verify_restore_detects_missing_and_extra_objects(tmp_path: Path) -> None:
    source = tmp_path / "src"
    _seed_object_store(source)
    dump = tmp_path / "db.dump"
    _write_dump(dump)
    manifest = build_manifest(db_dump=dump, object_root=source, alembic_revision="0030")

    target = tmp_path / "restored"
    _seed_object_store(target)
    (target / "cd" / "ef" / "cdef2222").unlink()  # lost in restore
    (target / "ab" / "zzzz9999").write_bytes(b"object not in the backup")  # stray

    issues = verify_restore(manifest=manifest, restored_object_root=target, restored_alembic_revision="0030")
    assert any("missing object: cd/ef/cdef2222" in issue for issue in issues)
    assert any("unexpected object not in manifest: ab/zzzz9999" in issue for issue in issues)


def test_verify_restore_detects_tampered_dump(tmp_path: Path) -> None:
    root = tmp_path / "objects"
    _seed_object_store(root)
    dump = tmp_path / "db.dump"
    _write_dump(dump)
    manifest = build_manifest(db_dump=dump, object_root=root, alembic_revision="0030")

    dump.write_bytes(b"PGDMP different payload after tampering")
    issues = verify_restore(
        manifest=manifest,
        restored_object_root=root,
        restored_alembic_revision="0030",
        db_dump=dump,
    )
    assert any("db dump checksum mismatch" in issue for issue in issues)


def test_symlink_in_restore_target_is_not_trusted_as_content(tmp_path: Path) -> None:
    source = tmp_path / "src"
    _seed_object_store(source)
    dump = tmp_path / "db.dump"
    _write_dump(dump)
    manifest = build_manifest(db_dump=dump, object_root=source, alembic_revision="0030")

    target = tmp_path / "restored"
    _seed_object_store(target)
    # An attacker-planted symlink standing in for a real object must be ignored,
    # surfacing as a missing object rather than being followed and trusted.
    real = target / "ab" / "abcd1111"
    real.unlink()
    real.symlink_to(dump)

    issues = verify_restore(manifest=manifest, restored_object_root=target, restored_alembic_revision="0030")
    assert any("missing object: ab/abcd1111" in issue for issue in issues)
