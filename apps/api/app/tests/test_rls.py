"""Test 10: the database itself must refuse cross-user access for the runtime
role — not the ORM, not the service layer. Uses the real nur_app role."""
from sqlalchemy import text

from app.tests.conftest import register_user

SET_USER = "SELECT set_config('app.current_user_id', :uid, true)"


async def test_rls_denies_cross_user_access(client, app_engine):
    ra, _, _ = await register_user(client)
    client.cookies.clear()
    rb, _, _ = await register_user(client)
    uid_a, uid_b = ra.json()["id"], rb.json()["id"]

    async with app_engine.connect() as conn:
        # context = user A
        await conn.execute(text(SET_USER), {"uid": uid_a})
        own = (await conn.execute(text("SELECT count(*) FROM profiles WHERE user_id=:u"),
                                  {"u": uid_a})).scalar_one()
        cross = (await conn.execute(text("SELECT count(*) FROM profiles WHERE user_id=:u"),
                                    {"u": uid_b})).scalar_one()
        cross_orbit = (await conn.execute(text("SELECT count(*) FROM orbits WHERE owner_user_id=:u"),
                                          {"u": uid_b})).scalar_one()
        cross_sessions = (await conn.execute(text("SELECT count(*) FROM sessions WHERE user_id=:u"),
                                             {"u": uid_b})).scalar_one()
        # write attempt against B's orbit must silently affect zero rows
        upd = await conn.execute(text("UPDATE orbits SET active_focus_area='hijack' WHERE owner_user_id=:u"),
                                 {"u": uid_b})
        visible_users = (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one()
        await conn.rollback()

    assert own == 1
    assert cross == 0 and cross_orbit == 0 and cross_sessions == 0
    assert upd.rowcount == 0
    assert visible_users == 1  # A sees exactly A


async def test_rls_default_deny_without_context(client, app_engine):
    await register_user(client)
    async with app_engine.connect() as conn:
        users = (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one()
        profiles = (await conn.execute(text("SELECT count(*) FROM profiles"))).scalar_one()
        await conn.rollback()
    assert users == 0 and profiles == 0


async def test_rls_app_role_cannot_read_audit_log(client, app_engine):
    ra, _, _ = await register_user(client)
    async with app_engine.connect() as conn:
        await conn.execute(text(SET_USER), {"uid": ra.json()["id"]})
        try:
            await conn.execute(text("SELECT count(*) FROM audit_events"))
            readable = True
        except Exception:
            readable = False
        await conn.rollback()
    assert readable is False  # append-only: no SELECT grant, no SELECT policy


async def test_policies_survive_guc_reset_on_pooled_connection(client, app_engine):
    """After a tx-local set_config ends, the custom GUC lingers as '' on the
    session. Policies must not blow up casting ''::uuid on the next request."""
    await register_user(client)
    async with app_engine.connect() as conn:
        await conn.execute(text("SELECT set_config('app.auth_context','on',true)"))
        await conn.commit()  # GUC now '' at session level on this pooled conn
        count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one()
        await conn.rollback()
    assert count == 0  # no crash, and default-deny still holds


async def test_revoke_session_is_constrained_to_owner(client, app_engine, super_engine):
    """Fix-6 regression: even if a future service mistakenly passes a FOREIGN
    session id, revoke_session(session_id, user_id) must not revoke it, because
    the UPDATE is constrained by BOTH columns."""
    import uuid as _uuid

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.services import auth_service

    ra, _, _ = await register_user(client)
    client.cookies.clear()
    rb, _, _ = await register_user(client)
    uid_a = _uuid.UUID(ra.json()["id"])
    uid_b = _uuid.UUID(rb.json()["id"])

    async with super_engine.connect() as conn:
        sid_b = (await conn.execute(
            text("SELECT id FROM sessions WHERE user_id=:u AND revoked_at IS NULL"),
            {"u": str(uid_b)})).scalar_one()

    sm = async_sessionmaker(app_engine, expire_on_commit=False)

    # Buggy-caller simulation: user A's id with user B's session id -> no-op.
    async with sm() as db:
        await auth_service.revoke_session(db, session_id=sid_b, user_id=uid_a)
    async with super_engine.connect() as conn:
        still_live = (await conn.execute(
            text("SELECT revoked_at IS NULL FROM sessions WHERE id=:s"),
            {"s": str(sid_b)})).scalar_one()
    assert still_live, "foreign session must NOT be revocable with a mismatched user_id"

    # Legitimate owner path still works, proving the constraint is the only gate.
    async with sm() as db:
        await auth_service.revoke_session(db, session_id=sid_b, user_id=uid_b)
    async with super_engine.connect() as conn:
        now_revoked = (await conn.execute(
            text("SELECT revoked_at IS NOT NULL FROM sessions WHERE id=:s"),
            {"s": str(sid_b)})).scalar_one()
    assert now_revoked, "owner-scoped revocation must still succeed"


async def test_model_run_ledgers_are_owner_isolated(client, app_engine, super_engine):
    ra, _, _ = await register_user(client)
    client.cookies.clear()
    rb, _, _ = await register_user(client)
    uid_a, uid_b = ra.json()["id"], rb.json()["id"]

    async with super_engine.begin() as conn:
        run_id = (await conn.execute(text("""
            INSERT INTO model_runs(owner_user_id, provider, mode, status)
            VALUES (:u, 'disabled', 'talk', 'COMPLETED') RETURNING id
        """), {"u": uid_a})).scalar_one()
        await conn.execute(text("""
            INSERT INTO model_run_sources(owner_user_id, model_run_id, source_kind, excerpt)
            VALUES (:u, :r, 'DECISION', 'owner-only source')
        """), {"u": uid_a, "r": run_id})
        await conn.execute(text("""
            INSERT INTO model_evaluations(owner_user_id, model_run_id, verdict, checks)
            VALUES (:u, :r, 'PASS', '{}'::jsonb)
        """), {"u": uid_a, "r": run_id})
        await conn.execute(text("""
            INSERT INTO memory_candidates(owner_user_id, candidate_text)
            VALUES (:u, 'owner-only memory')
        """), {"u": uid_a})
        await conn.execute(text("""
            INSERT INTO predictions(owner_user_id, statement)
            VALUES (:u, 'owner-only prediction')
        """), {"u": uid_a})
        await conn.execute(text("""
            INSERT INTO user_corrections(owner_user_id, correction_text)
            VALUES (:u, 'owner-only correction')
        """), {"u": uid_a})

    tables = [
        "model_runs", "model_run_sources", "model_evaluations",
        "memory_candidates", "predictions", "user_corrections",
    ]
    async with app_engine.connect() as conn:
        await conn.execute(text(SET_USER), {"uid": uid_b})
        b_counts = {
            table: (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
            for table in tables
        }
        await conn.rollback()

        await conn.execute(text(SET_USER), {"uid": uid_a})
        a_counts = {
            table: (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
            for table in tables
        }
        await conn.rollback()

    assert all(count == 0 for count in b_counts.values())
    assert all(count >= 1 for count in a_counts.values())
