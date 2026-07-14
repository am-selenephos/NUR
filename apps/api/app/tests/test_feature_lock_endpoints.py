from httpx import ASGITransport, AsyncClient

from app.tests.conftest import register_user


def H(c: AsyncClient) -> dict:
    return {"X-CSRF-Token": c.cookies.get("nur_csrf")}


def other_client(client) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=client.app), base_url="http://test")


async def test_universe_summary_search_and_scheduler_endpoints_are_owner_scoped(client):
    await register_user(client)
    orbit_id = (await client.get("/api/v1/orbits")).json()[0]["id"]
    await client.post(
        f"/api/v1/orbits/{orbit_id}/decisions",
        headers=H(client),
        json={"statement": "Feature lock has a real backend endpoint.", "rationale": "No decorative buttons."},
    )
    await client.post(
        "/api/v1/research-drafts",
        headers=H(client),
        json={"question": "Which interaction is wired?", "orbit_id": orbit_id},
    )

    for path in (
        "/api/v1/universe/map-summary",
        "/api/v1/universe/orbits-summary",
        "/api/v1/universe/timeline",
        "/api/v1/universe/insights-summary",
        "/api/v1/omega/scheduler-status",
    ):
        r = await client.get(path)
        assert r.status_code == 200, path
        assert r.json()["provenance_label"] == "owner_ledger" or r.json()["provenance_label"] == "omega_owner_ledger"

    hits = (await client.get("/api/v1/universe/search?q=feature%20lock")).json()
    assert any(hit["kind"] == "decision" and "Feature lock" in hit["label"] for hit in hits)

    async with other_client(client) as b:
        await register_user(b, chosen_name="Bee")
        b_hits = (await b.get("/api/v1/universe/search?q=feature%20lock")).json()
        assert b_hits == []
        b_map = (await b.get("/api/v1/universe/map-summary")).json()
        assert all("Feature lock" not in node["title"] for node in b_map["nodes"])


async def test_profile_preferences_persist_and_reject_foreign_orbit(client):
    ra, _, _ = await register_user(client)
    orbit_a = (await client.get("/api/v1/orbits")).json()[0]["id"]
    patched = (await client.patch(
        "/api/v1/profile/preferences",
        headers=H(client),
        json={"locale": "ur", "sound_enabled": True, "active_orbit_id": orbit_a},
    )).json()
    assert patched["locale"] == "ur"
    assert patched["sound_enabled"] is True
    assert patched["active_orbit_id"] == orbit_a
    assert (await client.get("/api/v1/profile/preferences")).json()["locale"] == "ur"

    client.cookies.clear()
    await register_user(client, chosen_name="Bee")
    foreign = await client.patch(
        "/api/v1/profile/preferences",
        headers=H(client),
        json={"active_orbit_id": orbit_a},
    )
    assert foreign.status_code == 404
    assert ra.json()["id"] != (await client.get("/api/v1/auth/me")).json()["id"]


async def test_journal_and_research_convert_to_orbit_sources(client):
    await register_user(client)
    orbit_id = (await client.get("/api/v1/orbits")).json()[0]["id"]
    journal = (await client.post(
        "/api/v1/journal",
        headers=H(client),
        json={"body": "Turn this journal entry into a decision.", "orbit_id": orbit_id},
    )).json()
    converted = (await client.post(
        f"/api/v1/journal/{journal['id']}/convert",
        headers=H(client),
        json={"orbit_id": orbit_id, "kind": "DECISION"},
    )).json()
    assert converted["source_kind"] == "JOURNAL_ENTRY"
    assert converted["target_kind"] == "DECISION"
    assert converted["orbit_id"] == orbit_id

    research = (await client.post(
        "/api/v1/research-drafts",
        headers=H(client),
        json={"question": "What outside source verifies the decision?", "orbit_id": orbit_id},
    )).json()
    converted_research = (await client.post(
        f"/api/v1/research-drafts/{research['id']}/convert",
        headers=H(client),
        json={"orbit_id": orbit_id, "kind": "OPEN_QUESTION"},
    )).json()
    assert converted_research["source_kind"] == "RESEARCH_DRAFT"
    assert converted_research["target_kind"] == "OPEN_QUESTION"

    sources = (await client.get(f"/api/v1/orbits/{orbit_id}/sources")).json()
    assert {row["id"] for row in sources} >= {converted["orbit_source_id"], converted_research["orbit_source_id"]}

