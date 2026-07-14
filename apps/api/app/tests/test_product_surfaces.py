from sqlalchemy import text

from app.tests.conftest import register_user


def H(c) -> dict:
    return {"X-CSRF-Token": c.cookies.get("nur_csrf")}


async def test_research_community_web_signal_surfaces_emit_owner_timeline_events(client):
    await register_user(client)
    orbit_id = (await client.get("/api/v1/orbits")).json()[0]["id"]

    brief = (await client.post(
        "/api/v1/research/briefs",
        headers=H(client),
        json={"question": "Which source verifies NUR?", "summary": "local only", "orbit_id": orbit_id},
    )).json()
    source_note = (await client.post(
        "/api/v1/research/source-notes",
        headers=H(client),
        json={"title": "Owner source note", "note": "source is staged locally", "orbit_id": orbit_id, "research_brief_id": brief["id"]},
    )).json()
    community = (await client.post(
        "/api/v1/community/consultation-notes",
        headers=H(client),
        json={"title": "Collaborator question", "note": "Ask a reviewer about the boundary.", "orbit_id": orbit_id},
    )).json()
    web_question = (await client.post(
        "/api/v1/web-signals/questions",
        headers=H(client),
        json={"question": "What market signal should be checked?", "orbit_id": orbit_id},
    )).json()
    web_note = (await client.post(
        "/api/v1/web-signals/notes",
        headers=H(client),
        json={"title": "Signal note", "note": "No live fetch performed.", "orbit_id": orbit_id, "web_signal_question_id": web_question["id"]},
    )).json()

    assert brief["provenance_label"] == "OWNER_WRITTEN"
    assert source_note["trust_state"] == "OWNER_SUPPLIED"
    assert community["status"] == "LOCAL_NOTE"
    assert web_question["provider_status"] == "NOT_CONNECTED"
    assert web_note["provenance_label"] == "OWNER_WRITTEN"

    timeline = (await client.get("/api/v1/universe/timeline")).json()["items"]
    kinds = {row["kind"] for row in timeline}
    assert {
        "RESEARCH_BRIEF_CREATED",
        "RESEARCH_SOURCE_NOTE_ADDED",
        "COMMUNITY_NOTE_CREATED",
        "WEB_SIGNAL_QUESTION_STAGED",
        "WEB_SIGNAL_NOTE_ADDED",
    } <= kinds

    caps = (await client.get("/api/v1/provider-capabilities")).json()
    assert any(row["capability_key"] == "live_web_research" and row["status"] == "NOT_CONNECTED" for row in caps)
    assert any(row["capability_key"] == "research_notes" and row["status"] == "AVAILABLE" for row in caps)


async def test_product_surface_rows_are_owner_isolated(client):
    await register_user(client)
    orbit_id = (await client.get("/api/v1/orbits")).json()[0]["id"]
    await client.post(
        "/api/v1/research/briefs",
        headers=H(client),
        json={"question": "Owner A only research", "orbit_id": orbit_id},
    )
    await client.post(
        "/api/v1/community/consultation-notes",
        headers=H(client),
        json={"title": "Owner A community", "note": "private", "orbit_id": orbit_id},
    )
    await client.post(
        "/api/v1/web-signals/questions",
        headers=H(client),
        json={"question": "Owner A web signal", "orbit_id": orbit_id},
    )

    client.cookies.clear()
    await register_user(client, chosen_name="Bee")
    assert (await client.get("/api/v1/research/briefs")).json() == []
    assert (await client.get("/api/v1/community/consultation-notes")).json() == []
    assert (await client.get("/api/v1/web-signals/questions")).json() == []


async def test_product_surface_rls_denies_recipient_direct_reads(client, app_engine, super_engine):
    ra, _, _ = await register_user(client)
    client.cookies.clear()
    rb, _, _ = await register_user(client, chosen_name="Recipient")
    uid_a, uid_b = ra.json()["id"], rb.json()["id"]
    tables = [
        ("research_briefs", "question", "'owner-only research'"),
        ("research_source_notes", "title, note", "'owner source', 'secret note'"),
        ("community_consultation_notes", "title, note", "'owner community', 'secret note'"),
        ("web_signal_questions", "question", "'owner-only web signal'"),
        ("web_signal_notes", "title, note", "'owner web note', 'secret note'"),
        ("provider_capabilities", "provider_name, capability_key, reason", "'local', 'owner-only', 'secret reason'"),
    ]
    async with super_engine.begin() as conn:
        for table, cols, vals in tables:
            await conn.execute(text(f"INSERT INTO {table}(owner_user_id, {cols}) VALUES (:u, {vals})"), {"u": uid_a})

    async with app_engine.connect() as conn:
        await conn.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": uid_b})
        counts = {
            table: (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
            for table, _, _ in tables
        }
        await conn.rollback()

    assert all(value == 0 for value in counts.values())
