"""Gate 3 proof — the amendment §8 backend battery, all ten requirements."""

import asyncio

from httpx import ASGITransport, AsyncClient

from app.tests.conftest import register_user


def H(c: AsyncClient) -> dict:
    return {"X-CSRF-Token": c.cookies.get("nur_csrf")}


def other_client(client) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=client.app), base_url="http://test")


async def _project_with_sources(owner):
    """Owner: project orbit + decision/reference/journal, all three attached
    as orbit_sources. Returns ids."""
    r = await owner.post("/api/v1/orbits", headers=H(owner),
                         json={"title": "NUR Build", "kind": "PROJECT",
                               "description": "The first paid room."})
    orbit = r.json()["id"]
    d = (await owner.post(f"/api/v1/orbits/{orbit}/decisions", headers=H(owner),
                          json={"statement": "Postgres RLS is the trust boundary.",
                                "rationale": "Recipient access must be grant-scoped."})).json()
    ref = (await owner.post(f"/api/v1/orbits/{orbit}/references", headers=H(owner),
                            json={"title": "Capsule spectrum palette",
                                  "body": "Mango 26E through pearl FFF2D3, zephyr-secret-token."})).json()
    j = (await owner.post("/api/v1/journal", headers=H(owner),
                          json={"body": "Privately: gratitude-marker-qq77 kept out of every capsule."})).json()
    srcs = {}
    for kind, sid in [("DECISION", d["id"]), ("REFERENCE", ref["id"]), ("JOURNAL_ENTRY", j["id"])]:
        rr = await owner.post(f"/api/v1/orbits/{orbit}/sources", headers=H(owner),
                              json={"source_kind": kind, "source_id": sid})
        assert rr.status_code == 201, rr.text
        srcs[kind] = rr.json()["id"]
    return orbit, srcs, {"decision": d, "reference": ref, "journal": j}


async def test_owner_only_capsule_creation_from_owned_sources(client):
    await register_user(client)
    orbit, srcs, _ = await _project_with_sources(client)
    async with other_client(client) as b:
        await register_user(b, chosen_name="Bee")
        # §8.1 — B cannot mint a capsule from A's orbit/sources
        r = await b.post(f"/api/v1/orbits/{orbit}/capsules", headers=H(b),
                         json={"title": "steal", "purpose": "x",
                               "orbit_source_ids": [srcs["DECISION"]]})
        assert r.status_code in (403, 404)
        # §8.5 — B cannot enumerate A's orbits
        assert orbit not in {o["id"] for o in (await b.get("/api/v1/orbits")).json()}


async def test_capsule_room_scoping_provenance_versioning_audit(client):
    await register_user(client)
    orbit, srcs, items = await _project_with_sources(client)

    async with other_client(client) as b:
        _, b_email, _ = await register_user(b, chosen_name="Bee")

        # capsule: decision FULL + reference METADATA_ONLY; journal EXCLUDED
        r = await client.post(f"/api/v1/orbits/{orbit}/capsules", headers=H(client),
                              json={"title": "Collaborator onboarding",
                                    "purpose": "Get a designer useful in 20 minutes.",
                                    "capability": "ASK_SCOPED_QUESTIONS",
                                    "orbit_source_ids": [srcs["DECISION"], srcs["REFERENCE"]],
                                    "representations": {srcs["REFERENCE"]: "METADATA_ONLY"}})
        assert r.status_code == 201, r.text
        cap = r.json()["id"]
        assert (await client.post(f"/api/v1/capsules/{cap}/grants", headers=H(client),
                                  json={"recipient_email": b_email,
                                        "capability": "ASK_SCOPED_QUESTIONS"})).status_code == 201

        # §8.2 — recipient sees included, never the journal
        view = (await b.get(f"/api/v1/capsules/{cap}/view")).json()
        assert view["state"] == "ACTIVE"
        assert "does not speak for" in view["safety_copy"]
        kinds = {s["source_kind"] for s in view["included"]}
        assert kinds == {"DECISION", "REFERENCE"}
        assert "gratitude-marker-qq77" not in str(view)
        assert any(e["source_kind"] == "JOURNAL_ENTRY" for e in view["excluded_summary"])

        # §8.7 — METADATA_ONLY body never crosses
        ref_row = [s for s in view["included"] if s["source_kind"] == "REFERENCE"][0]
        assert ref_row["representation"] == "METADATA_ONLY" and ref_row["body"] == ""
        assert "zephyr-secret-token" not in str(view)

        # ask about the decision -> owner's own words, cited
        ans = (await b.post(f"/api/v1/capsules/{cap}/questions", headers=H(b),
                            json={"question": "What did you decide about Postgres RLS as the trust boundary?"})).json()
        assert ans["answer_mode"] == "DIRECT_STATEMENT"
        assert "trust boundary" in ans["answer_text"]
        assert ans["policy_explanation"] and "INFERENCE" in ans["policy_explanation"]
        included_ids = {s["source_id"] for s in view["included"]}
        # §8.8 — every citation belongs to the current capsule version
        assert ans["source_refs"] and all(rf["source_id"] in included_ids for rf in ans["source_refs"])

        # metadata-only reference: title matches, body cannot leak into the answer
        ans2 = (await b.post(f"/api/v1/capsules/{cap}/questions", headers=H(b),
                             json={"question": "What is the capsule spectrum palette?"})).json()
        assert "zephyr-secret-token" not in ans2["answer_text"]

        # §8.2b/§8.6 — excluded content is NOT reachable through questions
        na = (await b.post(f"/api/v1/capsules/{cap}/questions", headers=H(b),
                           json={"question": "What gratitude did they write privately? gratitude-marker-qq77"})).json()
        assert na["answer_mode"] == "NOT_AVAILABLE"
        assert "gratitude-marker-qq77" not in na["answer_text"]
        # and no general retrieval path exists for the recipient
        assert all("gratitude" not in (e.get("content_text") or "")
                   for e in (await b.get("/api/v1/cognition/events")).json())

        # §8.9 — the version-1 source set is immutable
        d2 = (await client.post(f"/api/v1/orbits/{orbit}/decisions", headers=H(client),
                                json={"statement": "Later decision, never in v1."})).json()
        await client.post(f"/api/v1/orbits/{orbit}/sources", headers=H(client),
                          json={"source_kind": "DECISION", "source_id": d2["id"]})
        view2 = (await b.get(f"/api/v1/capsules/{cap}/view")).json()
        assert len(view2["included"]) == 2
        assert "Later decision" not in str(view2["included"])

        # §8.3 — revoke bites immediately
        assert (await client.post(f"/api/v1/capsules/{cap}/revoke", headers=H(client))).status_code == 200
        rev = (await b.get(f"/api/v1/capsules/{cap}/view")).json()
        assert rev["state"] == "REVOKED" and rev["included"] == []
        assert (await b.post(f"/api/v1/capsules/{cap}/questions", headers=H(b),
                             json={"question": "anything"})).status_code == 410

        # §8.10 — the audit trail covers the whole life
        audit_kinds = {a["event_kind"] for a in (await client.get(f"/api/v1/capsules/{cap}/audit")).json()}
        assert {"VIEWED", "QUESTION_ASKED", "ANSWER_SHOWN", "REVOKED"} <= audit_kinds

        # Gate 4 — collaboration outcome capture
        assert (await client.post(f"/api/v1/capsules/{cap}/collaboration-outcome", headers=H(client),
                                  json={"onboarding_faster": True, "time_saved_minutes": 45,
                                        "notes": "Bee shipped without one repeat explanation."})).status_code == 201


async def test_expired_grant_blocks_immediately(client):
    await register_user(client)
    orbit, srcs, _ = await _project_with_sources(client)
    async with other_client(client) as b:
        _, b_email, _ = await register_user(b, chosen_name="Bee")
        cap = (await client.post(f"/api/v1/orbits/{orbit}/capsules", headers=H(client),
                                 json={"title": "t", "purpose": "p", "capability": "ASK_SCOPED_QUESTIONS",
                                       "orbit_source_ids": [srcs["DECISION"]]})).json()["id"]
        assert (await client.post(f"/api/v1/capsules/{cap}/grants", headers=H(client),
                                  json={"recipient_email": b_email,
                                        "capability": "ASK_SCOPED_QUESTIONS",
                                        "expires_at": "2020-01-01T00:00:00Z"})).status_code == 201
        # §8.4 — expired is a distinct, content-free state
        v = (await b.get(f"/api/v1/capsules/{cap}/view")).json()
        assert v["state"] == "EXPIRED" and v["included"] == []
        assert (await b.post(f"/api/v1/capsules/{cap}/questions", headers=H(b),
                             json={"question": "x"})).status_code == 410


async def test_revoked_capsule_hides_prior_answers_at_rls_layer(client, app_engine):
    from sqlalchemy import text

    await register_user(client)
    orbit, srcs, _ = await _project_with_sources(client)
    async with other_client(client) as b:
        rb, b_email, _ = await register_user(b, chosen_name="Bee")
        cap = (await client.post(f"/api/v1/orbits/{orbit}/capsules", headers=H(client),
                                 json={"title": "t", "purpose": "p", "capability": "ASK_SCOPED_QUESTIONS",
                                       "orbit_source_ids": [srcs["DECISION"]]})).json()["id"]
        await client.post(f"/api/v1/capsules/{cap}/grants", headers=H(client),
                          json={"recipient_email": b_email, "capability": "ASK_SCOPED_QUESTIONS"})
        ans = await b.post(f"/api/v1/capsules/{cap}/questions", headers=H(b),
                           json={"question": "What is the trust boundary?"})
        assert ans.status_code == 201

        async with app_engine.connect() as conn:
            await conn.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": rb.json()["id"]})
            visible_before = (await conn.execute(text("SELECT count(*) FROM capsule_answers"))).scalar_one()
            await conn.rollback()
        assert visible_before == 1

        assert (await client.post(f"/api/v1/capsules/{cap}/revoke", headers=H(client))).status_code == 200
        async with app_engine.connect() as conn:
            await conn.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": rb.json()["id"]})
            visible_after = (await conn.execute(text("SELECT count(*) FROM capsule_answers"))).scalar_one()
            await conn.rollback()
        assert visible_after == 0


async def test_revoke_ask_race_loop_never_returns_answer_after_revoke(client):
    await register_user(client)
    orbit, srcs, _ = await _project_with_sources(client)
    async with other_client(client) as b:
        _, b_email, _ = await register_user(b, chosen_name="Bee")
        outcomes = []

        for i in range(25):
            cap = (await client.post(
                f"/api/v1/orbits/{orbit}/capsules",
                headers=H(client),
                json={
                    "title": f"race {i}",
                    "purpose": "Race safety proof",
                    "capability": "ASK_SCOPED_QUESTIONS",
                    "orbit_source_ids": [srcs["DECISION"]],
                },
            )).json()["id"]
            grant = await client.post(
                f"/api/v1/capsules/{cap}/grants",
                headers=H(client),
                json={"recipient_email": b_email, "capability": "ASK_SCOPED_QUESTIONS"},
            )
            assert grant.status_code == 201, grant.text

            start = asyncio.Event()

            async def revoke_once():
                await start.wait()
                return await client.post(f"/api/v1/capsules/{cap}/revoke", headers=H(client))

            async def ask_once():
                await start.wait()
                return await b.post(
                    f"/api/v1/capsules/{cap}/questions",
                    headers=H(b),
                    json={"question": "What is the trust boundary?"},
                )

            revoke_task = asyncio.create_task(revoke_once())
            ask_task = asyncio.create_task(ask_once())
            start.set()
            revoke_response, ask_response = await asyncio.gather(revoke_task, ask_task)
            assert revoke_response.status_code == 200, revoke_response.text
            assert ask_response.status_code in (201, 410), ask_response.text

            after = await b.post(
                f"/api/v1/capsules/{cap}/questions",
                headers=H(b),
                json={"question": "Can anything remain after revoke?"},
            )
            assert after.status_code == 410, after.text
            view = (await b.get(f"/api/v1/capsules/{cap}/view")).json()
            assert view["state"] == "REVOKED"
            assert view["included"] == []
            outcomes.append({"iteration": i, "racing_ask_status": ask_response.status_code})

        assert len(outcomes) == 25
