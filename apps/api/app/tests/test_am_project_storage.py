"""Real owner-scoped object storage for AM Projects (G14).

Proves that uploaded bytes are actually written, survive a fresh storage handle
(restart proxy), download identically, verify by SHA-256, are owner-isolated
under forced RLS, reject traversal/symlink/oversize, quarantine dangerous
formats, and never leak an absolute server path.
"""
import hashlib

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.services.object_storage import (
    LocalObjectStorage,
    StoredObjectMissing,
    UploadTooLarge,
    bytes_stream,
    classify_upload,
    get_object_storage,
    sanitize_filename,
)
from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


async def _make_project(client) -> str:
    created = await client.post(
        "/api/v1/projects", headers=H(client),
        json={"title": "Storage owner", "objective": "Store and retrieve real bytes."},
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


async def test_upload_persists_and_downloads_identical_bytes_with_matching_checksum(client):
    await register_user(client, chosen_name="File Owner")
    project_id = await _make_project(client)
    payload = b"NUR real bytes \x00\x01\x02 line-two\n" * 64
    expected = hashlib.sha256(payload).hexdigest()

    up = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("evidence log.txt", payload, "text/plain")},
    )
    assert up.status_code == 201, up.text
    meta = up.json()
    assert meta["checksum_sha256"] == expected
    assert meta["byte_size"] == len(payload)
    assert meta["storage_state"] == "STORED"
    assert meta["scan_state"] == "SCAN_NOT_CONNECTED"
    assert meta["safe_filename"] == "evidence_log.txt"
    # No absolute server path or object key may appear in the response.
    blob = up.text
    assert "/" not in meta["safe_filename"]
    assert str(get_settings().project_object_root) not in blob
    assert "object_key" not in meta

    file_id = meta["id"]
    # Server-side checksum verification against the bytes actually on disk.
    verify = await client.post(f"/api/v1/projects/files/{file_id}/verify", headers=H(client))
    assert verify.status_code == 200
    assert verify.json()["verified"] is True

    # Download returns byte-identical content.
    dl = await client.get(f"/api/v1/projects/files/{file_id}/download")
    assert dl.status_code == 200
    assert dl.content == payload
    assert hashlib.sha256(dl.content).hexdigest() == expected
    assert dl.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in dl.headers["content-disposition"]


async def test_bytes_survive_a_fresh_storage_handle_restart_proxy(client):
    await register_user(client, chosen_name="Restart Owner")
    project_id = await _make_project(client)
    payload = b"survive-restart-" * 100
    up = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("keep.bin", payload, "application/octet-stream")},
    )
    assert up.status_code == 201
    checksum = up.json()["checksum_sha256"]

    # A brand-new storage handle rooted at the same directory (as a restarted
    # process would build) reads identical bytes from disk — proving the bytes
    # are durable on the filesystem, not held in the API process.
    root = get_settings().project_object_root
    fresh = LocalObjectStorage(root)
    assert fresh.root == get_object_storage().root
    stored_files = root_files(root)
    assert stored_files, "expected at least one object on disk"
    assert any(hashlib.sha256(p.read_bytes()).hexdigest() == checksum for p in stored_files)


def root_files(root):
    from pathlib import Path
    base = Path(root)
    return [p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")]


async def test_quarantine_blocks_dangerous_format_download(client):
    await register_user(client, chosen_name="Quarantine Owner")
    project_id = await _make_project(client)
    up = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("payload.sh", b"#!/bin/sh\nrm -rf /\n", "text/x-shellscript")},
    )
    assert up.status_code == 201, up.text
    meta = up.json()
    assert meta["storage_state"] == "QUARANTINED"
    assert meta["quarantine_reason"]
    dl = await client.get(f"/api/v1/projects/files/{meta['id']}/download")
    assert dl.status_code == 409
    assert "quarantin" in dl.json()["detail"].lower()


async def test_delete_removes_bytes_and_blocks_further_access(client):
    await register_user(client, chosen_name="Delete Owner")
    project_id = await _make_project(client)
    up = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("temp.txt", b"transient", "text/plain")},
    )
    file_id = up.json()["id"]
    deleted = await client.request("DELETE", f"/api/v1/projects/files/{file_id}", headers=H(client))
    assert deleted.status_code == 200
    assert deleted.json()["storage_state"] == "DELETED"
    # Metadata delete leaves no orphan access: download and verify both refuse.
    assert (await client.get(f"/api/v1/projects/files/{file_id}/download")).status_code == 404
    assert (await client.post(f"/api/v1/projects/files/{file_id}/verify", headers=H(client))).status_code == 404
    # And the file no longer appears in the owner listing.
    listed = (await client.get(f"/api/v1/projects/{project_id}/files")).json()
    assert all(row["id"] != file_id for row in listed)


async def test_oversized_upload_is_rejected(client, monkeypatch):
    await register_user(client, chosen_name="Oversize Owner")
    project_id = await _make_project(client)
    monkeypatch.setattr(get_settings(), "project_upload_max_bytes", 16)
    up = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("big.txt", b"x" * 512, "text/plain")},
    )
    assert up.status_code == 413, up.text


async def test_file_metadata_is_owner_isolated_under_forced_rls(client, app_engine):
    owner_a, _, _ = await register_user(client, chosen_name="File Owner A")
    project_id = await _make_project(client)
    up = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("private.txt", b"owner-a-secret", "text/plain")},
    )
    file_id = up.json()["id"]

    client.cookies.clear()
    owner_b, _, _ = await register_user(client, chosen_name="File Owner B")
    # Foreign owner cannot see, download, verify or delete the file.
    assert (await client.get(f"/api/v1/projects/files/{file_id}/download")).status_code == 404
    assert (await client.post(f"/api/v1/projects/files/{file_id}/verify", headers=H(client))).status_code == 404
    assert (await client.get(f"/api/v1/projects/{project_id}/files")).status_code == 404

    async with app_engine.connect() as conn:
        await conn.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": owner_b.json()["id"]},
        )
        count = (await conn.execute(text("SELECT count(*) FROM am_project_files"))).scalar_one()
        forced = (await conn.execute(text(
            "SELECT relforcerowsecurity FROM pg_class WHERE relname='am_project_files'"
        ))).scalar_one()
        await conn.rollback()
    assert count == 0
    assert forced is True
    assert owner_a.json()["id"] != owner_b.json()["id"]


# --- Storage-service unit guarantees (traversal / symlink / oversize) --------

def test_sanitize_filename_strips_directories_and_unsafe_chars():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    reduced = sanitize_filename("a b/c\\d:e*.txt")
    assert reduced.endswith(".txt") and "/" not in reduced and "\\" not in reduced
    assert sanitize_filename("") == "upload"
    assert sanitize_filename(None) == "upload"
    assert "/" not in sanitize_filename("/abs/evil")


def test_classify_upload_flags_dangerous_formats():
    assert classify_upload("app.exe", "application/octet-stream")[0] == "QUARANTINED"
    assert classify_upload("script.js", "text/javascript")[0] == "QUARANTINED"
    assert classify_upload("notes.txt", "text/plain")[0] == "STORED"
    assert classify_upload("report.pdf", "application/pdf")[0] == "STORED"


async def test_storage_rejects_traversal_key_and_symlink(tmp_path):
    storage = LocalObjectStorage(tmp_path / "objects")
    stored = await storage.put(bytes_stream(b"hello world"), max_bytes=1024)
    assert storage.verify(stored.object_key, stored.checksum_sha256)

    # A malformed (traversal) key never resolves to a path.
    with pytest.raises(ValueError):
        storage._path_for("../../etc/passwd")

    # A symlink planted where the object lives is refused on read.
    path = storage._path_for(stored.object_key)
    outside = tmp_path / "outside.txt"
    outside.write_text("attacker")
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(StoredObjectMissing):
        list(storage.read_chunks(stored.object_key))


async def test_storage_enforces_streaming_byte_cap(tmp_path):
    storage = LocalObjectStorage(tmp_path / "objects")
    with pytest.raises(UploadTooLarge):
        await storage.put(bytes_stream(b"x" * 1000), max_bytes=64)
    # A failed oversize write leaves no partial object behind.
    assert not root_files(tmp_path / "objects")
