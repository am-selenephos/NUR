"""Operator diagnostics surface (G15 Phase 2/9).

Proves the authenticated diagnostics endpoint reports truthful operational state
— migration revision, dependency checks, provider MODE (never asserted auth),
object-store writability — while requiring a session and leaking no secrets,
credentials, private content, or absolute paths.
"""
import json

from app.tests.conftest import register_user


async def test_diagnostics_requires_authentication(client):
    assert (await client.get("/api/v1/ops/diagnostics")).status_code == 401


async def test_diagnostics_reports_truthful_state_without_secrets(client):
    await register_user(client, chosen_name="Operator")
    resp = await client.get("/api/v1/ops/diagnostics")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["service"] == "nur-api"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["object_store"] == "ok"
    assert body["object_store_writable"] is True
    # Applied revision is best-effort (the runtime role may not be granted SELECT
    # on alembic_version); when present it is a valid revision, else null.
    assert body["migration_revision"] is None or body["migration_revision"].startswith("00")
    # Provider MODE is disabled in tests; auth is NEVER asserted as PASS.
    assert body["provider_mode"] == "disabled"
    assert body["provider_auth_state"] == "DISABLED"
    assert body["uptime_seconds"] >= 0

    # No secret VALUE, credential, private content, or absolute path may appear.
    # (Benign documentation words like "secret" in notes are fine; we look for
    # real leak signatures.)
    blob = json.dumps(body).lower()
    for forbidden in ("sk-", "openai_api_key", "authorization:", "password",
                      "x-csrf", "/home/", "set-cookie", "bearer "):
        assert forbidden not in blob, f"diagnostics leaked '{forbidden}'"


async def test_diagnostics_reports_configured_untested_for_openai_mode(client, monkeypatch):
    await register_user(client, chosen_name="Operator OpenAI")
    from app.core.config import get_settings
    # Simulate provider mode = openai WITHOUT proving authentication.
    monkeypatch.setattr(get_settings(), "ai_provider", "openai")
    body = (await client.get("/api/v1/ops/diagnostics")).json()
    assert body["provider_mode"] == "openai"
    assert body["provider_auth_state"] == "CONFIGURED_UNTESTED"  # not "PASS"
