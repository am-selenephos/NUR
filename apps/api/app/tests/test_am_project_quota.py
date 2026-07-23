"""Per-owner storage quota and upload rate limiting (Phase 4).

A per-file byte cap does not bound total storage — an owner can grow it without
limit one small file at a time — and the upload path is an expensive write with
no per-owner throttle beyond the auth endpoints. These prove both are now
enforced, that a rejected upload persists nothing, and that normal use still
works.
"""

from app.core.config import get_settings
from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


async def _make_project(client) -> str:
    created = await client.post(
        "/api/v1/projects", headers=H(client),
        json={"title": "Quota owner", "objective": "Bound storage and upload rate."},
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


async def test_storage_quota_blocks_upload_that_would_exceed_total(client, monkeypatch):
    await register_user(client, chosen_name="Quota Owner")
    project_id = await _make_project(client)
    # A tiny quota so a second small file pushes the total over it.
    monkeypatch.setattr(get_settings(), "project_storage_quota_bytes", 40)

    first = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("a.txt", b"x" * 30, "text/plain")},
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("b.txt", b"y" * 30, "text/plain")},
    )
    assert second.status_code == 413, second.text
    assert "quota" in second.text.lower()

    # The rejected upload left no residue: only the first file persists.
    listed = await client.get(f"/api/v1/projects/{project_id}/files", headers=H(client))
    assert listed.status_code == 200
    files = listed.json()
    assert len(files) == 1
    assert sum(f["byte_size"] for f in files) == 30


async def test_storage_quota_rejects_when_already_at_cap(client, monkeypatch):
    await register_user(client, chosen_name="At Cap")
    project_id = await _make_project(client)
    monkeypatch.setattr(get_settings(), "project_storage_quota_bytes", 20)

    first = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("a.txt", b"z" * 20, "text/plain")},
    )
    assert first.status_code == 201, first.text

    # At exactly the cap, a further upload is rejected before its body is read.
    again = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("b.txt", b"q", "text/plain")},
    )
    assert again.status_code == 413, again.text


async def test_owner_upload_rate_limit_returns_429(client, monkeypatch):
    await register_user(client, chosen_name="Rate Owner")
    project_id = await _make_project(client)
    monkeypatch.setattr(get_settings(), "upload_rate_limit_max", 2)
    monkeypatch.setattr(get_settings(), "upload_rate_limit_window_seconds", 300)

    for i in (1, 2):
        ok = await client.post(
            f"/api/v1/projects/{project_id}/files", headers=H(client),
            files={"upload": (f"{i}.txt", b"a", "text/plain")},
        )
        assert ok.status_code == 201, ok.text

    blocked = await client.post(
        f"/api/v1/projects/{project_id}/files", headers=H(client),
        files={"upload": ("3.txt", b"c", "text/plain")},
    )
    assert blocked.status_code == 429, blocked.text
    assert "rate limit" in blocked.text.lower()
