import asyncio
import json
import stat
import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import text

from app.core.config import Settings
from app.services.password_delivery import (
    LocalCapturePasswordResetDelivery,
    PasswordResetDispatch,
    SMTPPasswordResetDelivery,
)
from app.tests.conftest import register_user, unique_email


class RecordingDelivery:
    name = "test_capture"

    def __init__(self):
        self.messages = []

    async def deliver(self, message):
        self.messages.append(message)


class FailingDelivery:
    name = "test_failure"

    async def deliver(self, message):
        raise RuntimeError("mail provider unavailable")


async def issue_reset(client, email: str) -> tuple[str, RecordingDelivery, object]:
    delivery = RecordingDelivery()
    client.app.state.password_reset_delivery = delivery
    response = await client.post("/api/v1/auth/password/forgot", json={"email": email})
    assert response.status_code == 202
    assert len(delivery.messages) == 1
    token = parse_qs(urlparse(delivery.messages[0].reset_url).query)["token"][0]
    return token, delivery, response


async def test_forgot_is_enumeration_safe_and_stores_only_a_digest(client, super_engine, caplog):
    registered, email, _ = await register_user(client)
    user_id = registered.json()["id"]
    token, delivery, known = await issue_reset(client, email)

    unknown_delivery = RecordingDelivery()
    client.app.state.password_reset_delivery = unknown_delivery
    unknown = await client.post(
        "/api/v1/auth/password/forgot",
        json={"email": f"absent-{uuid.uuid4().hex}@nurapp.dev"},
    )

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert known.json()["accepted"] is True
    assert email not in known.text and token not in known.text
    assert unknown_delivery.messages == []
    assert delivery.messages[0].recipient == email

    async with super_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT token_digest, delivery_status FROM password_reset_challenges "
                    "WHERE user_id=:uid ORDER BY created_at DESC LIMIT 1"
                ),
                {"uid": user_id},
            )
        ).one()
        audit_count = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM audit_events WHERE actor_user_id=:uid "
                    "AND event_type='PASSWORD_RESET_REQUESTED'"
                ),
                {"uid": user_id},
            )
        ).scalar_one()
    assert row.delivery_status == "DELIVERED"
    assert len(row.token_digest) == 64
    assert token not in row.token_digest
    assert audit_count == 1
    assert token not in caplog.text


async def test_reset_is_single_use_and_revokes_every_prior_session(client, super_engine):
    registered, email, old_password = await register_user(client)
    user_id = registered.json()["id"]
    client.cookies.clear()
    assert (
        await client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    ).status_code == 200
    token, _, _ = await issue_reset(client, email)

    new_password = "new-orbit-passphrase-27"
    reset = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": new_password},
    )
    assert reset.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    replay = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "another-orbit-passphrase-28"},
    )
    assert replay.status_code == 400
    assert replay.json()["detail"] == "This reset link is invalid or has expired. Request a new one."

    client.cookies.clear()
    old_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": old_password}
    )
    new_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": new_password}
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200

    async with super_engine.connect() as conn:
        revoked = (
            await conn.execute(
                text("SELECT count(*) FROM sessions WHERE user_id=:uid AND revoked_at IS NOT NULL"),
                {"uid": user_id},
            )
        ).scalar_one()
        completed = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM audit_events WHERE actor_user_id=:uid "
                    "AND event_type='PASSWORD_RESET_COMPLETED'"
                ),
                {"uid": user_id},
            )
        ).scalar_one()
    assert revoked == 2
    assert completed == 1


async def test_expired_reset_is_rejected_without_changing_password(client, super_engine):
    registered, email, old_password = await register_user(client)
    token, _, _ = await issue_reset(client, email)
    async with super_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE password_reset_challenges "
                "SET created_at=now() - interval '2 seconds', "
                "expires_at=now() - interval '1 second' "
                "WHERE user_id=:uid"
            ),
            {"uid": registered.json()["id"]},
        )

    response = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "new-expired-passphrase-33"},
    )
    assert response.status_code == 400
    client.cookies.clear()
    assert (
        await client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    ).status_code == 200


async def test_parallel_reset_consumes_challenge_once(client, super_engine):
    registered, email, _ = await register_user(client)
    token, _, _ = await issue_reset(client, email)
    transport = ASGITransport(app=client.app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as first,
        AsyncClient(transport=transport, base_url="http://test") as second,
    ):
        responses = await asyncio.gather(
            first.post(
                "/api/v1/auth/password/reset",
                json={"token": token, "new_password": "parallel-passphrase-41"},
            ),
            second.post(
                "/api/v1/auth/password/reset",
                json={"token": token, "new_password": "parallel-passphrase-42"},
            ),
        )
    assert sorted(response.status_code for response in responses) == [204, 400]
    async with super_engine.connect() as conn:
        completed = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM audit_events WHERE actor_user_id=:uid "
                    "AND event_type='PASSWORD_RESET_COMPLETED'"
                ),
                {"uid": registered.json()["id"]},
            )
        ).scalar_one()
    assert completed == 1


async def test_reset_token_cannot_revoke_another_users_session(client):
    _, first_email, _ = await register_user(client)
    token, _, _ = await issue_reset(client, first_email)
    second, second_email, second_password = await register_user(client, chosen_name="Second")

    reset = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "first-account-new-password-52"},
    )
    assert reset.status_code == 204
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == second.json()["id"]
    client.cookies.clear()
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": second_email, "password": second_password},
        )
    ).status_code == 200


async def test_change_password_requires_csrf_current_password_and_revokes_sessions(client, super_engine):
    registered, email, old_password = await register_user(client)
    user_id = registered.json()["id"]
    client.cookies.clear()
    await client.post("/api/v1/auth/login", json={"email": email, "password": old_password})

    payload = {"current_password": old_password, "new_password": "changed-passphrase-61"}
    assert (await client.post("/api/v1/auth/password/change", json=payload)).status_code == 403
    csrf = client.cookies.get("nur_csrf")
    wrong = await client.post(
        "/api/v1/auth/password/change",
        headers={"x-csrf-token": csrf},
        json={"current_password": "incorrect-password", "new_password": payload["new_password"]},
    )
    assert wrong.status_code == 400
    assert (await client.get("/api/v1/auth/me")).status_code == 200

    changed = await client.post(
        "/api/v1/auth/password/change",
        headers={"x-csrf-token": csrf},
        json=payload,
    )
    assert changed.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    client.cookies.clear()
    assert (
        await client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login", json={"email": email, "password": payload["new_password"]}
        )
    ).status_code == 200
    async with super_engine.connect() as conn:
        revoked = (
            await conn.execute(
                text("SELECT count(*) FROM sessions WHERE user_id=:uid AND revoked_at IS NOT NULL"),
                {"uid": user_id},
            )
        ).scalar_one()
    assert revoked == 2


async def test_recovery_rejects_cross_site_origin_and_rate_limits(client):
    cross_site = await client.post(
        "/api/v1/auth/password/forgot",
        headers={"origin": "https://attacker.example", "sec-fetch-site": "cross-site"},
        json={"email": unique_email()},
    )
    assert cross_site.status_code == 403

    responses = []
    email = unique_email()
    for _ in range(6):
        responses.append(
            await client.post("/api/v1/auth/password/forgot", json={"email": email})
        )
    assert [response.status_code for response in responses] == [202, 202, 202, 202, 202, 429]


async def test_invalid_secret_lengths_are_rejected_without_echo(client):
    response = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": "raw-short-reset-secret", "new_password": "tiny"},
    )
    assert response.status_code == 400
    assert "raw-short-reset-secret" not in response.text
    assert "tiny" not in response.text


async def test_delivery_failure_remains_generic_and_revokes_challenge(client, super_engine):
    registered, email, _ = await register_user(client)
    client.app.state.password_reset_delivery = FailingDelivery()
    response = await client.post("/api/v1/auth/password/forgot", json={"email": email})
    assert response.status_code == 202
    assert response.json()["accepted"] is True
    async with super_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT delivery_status, revoked_at FROM password_reset_challenges "
                    "WHERE user_id=:uid ORDER BY created_at DESC LIMIT 1"
                ),
                {"uid": registered.json()["id"]},
            )
        ).one()
    assert row.delivery_status == "FAILED"
    assert row.revoked_at is not None


async def test_local_capture_is_explicit_and_mode_0600(tmp_path):
    delivery = LocalCapturePasswordResetDelivery(str(tmp_path / "mail"))
    challenge_id = uuid.uuid4()
    message = PasswordResetDispatch(
        challenge_id=challenge_id,
        user_id=uuid.uuid4(),
        recipient="local@example.com",
        reset_url="http://localhost:5173/reset-password?token=secret-for-local-test",
        expires_at_iso="2030-01-01T00:00:00+00:00",
    )
    await delivery.deliver(message)
    capture = tmp_path / "mail" / f"password-reset-{challenge_id}.json"
    payload = json.loads(capture.read_text())
    assert payload["kind"] == "DEVELOPMENT_ONLY_PASSWORD_RESET_CAPTURE"
    assert "secret-for-local-test" in payload["reset_url"]
    assert stat.S_IMODE(capture.stat().st_mode) == 0o600


async def test_smtp_adapter_uses_tls_auth_and_sends_reset_link(monkeypatch):
    observed = {"ehlo": 0}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            observed.update(host=host, port=port, timeout=timeout)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def ehlo(self):
            observed["ehlo"] += 1

        def starttls(self, *, context):
            observed["starttls"] = context is not None

        def login(self, username, password):
            observed["login"] = (username, password)

        def send_message(self, message):
            observed["message"] = message

    monkeypatch.setattr("app.services.password_delivery.smtplib.SMTP", FakeSMTP)
    settings = Settings(
        password_reset_delivery="smtp",
        password_reset_from_email="security@nur.example",
        password_reset_smtp_host="smtp.nur.example",
        password_reset_smtp_username="mailer",
        password_reset_smtp_password="smtp-secret",
    )
    dispatch = PasswordResetDispatch(
        challenge_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        recipient="owner@nur.example",
        reset_url="http://localhost:5173/reset-password?token=one-time-secret",
        expires_at_iso="2030-01-01T00:00:00+00:00",
    )
    await SMTPPasswordResetDelivery(settings).deliver(dispatch)

    assert observed["host"] == "smtp.nur.example"
    assert observed["port"] == 587
    assert observed["timeout"] == 15
    assert observed["ehlo"] == 2
    assert observed["starttls"] is True
    assert observed["login"] == ("mailer", "smtp-secret")
    assert observed["message"]["To"] == "owner@nur.example"
    assert dispatch.reset_url in observed["message"].get_content()


def test_production_rejects_local_capture():
    with pytest.raises(ValidationError, match="PASSWORD_RESET_DELIVERY=smtp"):
        Settings(
            app_env="production",
            session_secret="s" * 32,
            csrf_secret="c" * 32,
            web_origin="https://nur.example",
            password_reset_public_origin="https://nur.example",
            password_reset_delivery="local_capture",
        )


def test_production_accepts_complete_smtp_recovery_configuration():
    settings = Settings(
        app_env="production",
        session_secret="s" * 32,
        csrf_secret="c" * 32,
        web_origin="https://nur.example",
        password_reset_public_origin="https://nur.example",
        password_reset_delivery="smtp",
        password_reset_from_email="security@nur.example",
        password_reset_smtp_host="smtp.nur.example",
    )
    assert settings.password_reset_delivery == "smtp"
