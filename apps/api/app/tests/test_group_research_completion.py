import pytest
from sqlalchemy import text

from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


def save_cookies(client) -> dict[str, str]:
    return dict(client.cookies)


def use_cookies(client, cookies: dict[str, str]) -> None:
    client.cookies.clear()
    for name, value in cookies.items():
        client.cookies.set(name, value)


async def test_group_nur_versions_preserve_sources_minority_and_room_boundary(
    client,
    app_engine,
):
    owner_response, _, _ = await register_user(client, chosen_name="Group Owner")
    owner_id = owner_response.json()["id"]
    owner_cookies = save_cookies(client)
    room_response = await client.post(
        "/api/v1/community/rooms",
        headers=H(client),
        json={"title": "Group intelligence room", "room_kind": "GROUP"},
    )
    assert room_response.status_code == 201, room_response.text
    room_id = room_response.json()["id"]

    client.cookies.clear()
    member_response, member_email, _ = await register_user(client, chosen_name="Group Member")
    member_id = member_response.json()["id"]
    member_cookies = save_cookies(client)

    client.cookies.clear()
    outsider_response, _, _ = await register_user(client, chosen_name="Group Outsider")
    outsider_cookies = save_cookies(client)

    use_cookies(client, owner_cookies)
    added = await client.post(
        f"/api/v1/community/rooms/{room_id}/members",
        headers=H(client),
        json={"email": member_email, "role": "MEMBER"},
    )
    assert added.status_code == 201, added.text
    message_response = await client.post(
        f"/api/v1/community/rooms/{room_id}/messages",
        headers=H(client),
        json={"body": "The minority view needs one more privacy run."},
    )
    assert message_response.status_code == 201, message_response.text
    message_id = message_response.json()["id"]
    consultation_response = await client.post(
        "/api/v1/consultations",
        headers=H(client),
        json={
            "title": "Release boundary",
            "question": "Should the room release?",
            "purpose": "Decide without erasing disagreement.",
            "desired_outcome": "One bounded move.",
            "scope_statement": "Only this room and linked evidence.",
            "room_id": room_id,
        },
    )
    assert consultation_response.status_code == 201, consultation_response.text
    consultation_id = consultation_response.json()["id"]

    use_cookies(client, member_cookies)
    contribution_response = await client.post(
        f"/api/v1/consultations/{consultation_id}/contributions",
        headers=H(client),
        json={
            "contribution_type": "DISAGREEMENT",
            "body": "Hold until the privacy evidence is repeated.",
            "evidence": ["member-observed test result"],
        },
    )
    assert contribution_response.status_code == 201, contribution_response.text
    contribution_id = contribution_response.json()["id"]
    denied = await client.post(
        f"/api/v1/group-nur/rooms/{room_id}/syntheses",
        headers=H(client),
        json={
            "summary": "A member cannot publish this.",
            "current_question": "Release?",
            "what_may_be_wrong": "Incomplete evidence.",
        },
    )
    assert denied.status_code == 403

    use_cookies(client, owner_cookies)
    invalid_stage = await client.post(
        f"/api/v1/consultations/{consultation_id}/stages/ORIENT",
        headers=H(client),
        json={"payload": {"actual_question": "Missing affected people"}},
    )
    assert invalid_stage.status_code == 422
    async with app_engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :uid, false)"),
            {"uid": owner_id},
        )
        with pytest.raises(Exception):
            await connection.execute(text("""
                INSERT INTO consultation_stage_records(
                    consultation_id, consultation_owner_user_id, owner_user_id,
                    stage, stage_payload
                ) VALUES (
                    :consultation_id, :owner_id, :owner_id,
                    'ORIENT', '{"actual_question":"still malformed"}'::jsonb
                )
            """), {"consultation_id": consultation_id, "owner_id": owner_id})

    synthesis_payload = {
        "consultation_id": consultation_id,
        "summary": "The room favors release after one repeated privacy run.",
        "current_question": "Does the repeated privacy run pass?",
        "decisions": [{"decision": "Hold for one run", "owner": "room owner"}],
        "tensions": ["Speed versus privacy evidence"],
        "minority_positions": ["A full browser matrix should run again"],
        "evidence": [{"source": message_id, "claim": "A repeat was requested"}],
        "counterevidence": ["The current run is already green"],
        "unresolved_questions": ["Will the repeat stay green?"],
        "tasks": [{"task": "Repeat privacy suite", "owner": "room owner"}],
        "source_message_ids": [message_id],
        "source_contribution_ids": [contribution_id],
        "what_may_be_wrong": "The room may be over-weighting one failure mode.",
    }
    first = await client.post(
        f"/api/v1/group-nur/rooms/{room_id}/syntheses",
        headers=H(client),
        json=synthesis_payload,
    )
    assert first.status_code == 201, first.text
    assert first.json()["version"] == 1
    assert first.json()["minority_positions"]

    corrected_payload = {
        **synthesis_payload,
        "supersedes_id": first.json()["id"],
        "summary": "The repeated run passed; the room can release with rollback ready.",
        "correction_reason": "New persisted privacy evidence changed the decision.",
    }
    second = await client.post(
        f"/api/v1/group-nur/rooms/{room_id}/syntheses",
        headers=H(client),
        json=corrected_payload,
    )
    assert second.status_code == 201, second.text
    assert second.json()["version"] == 2
    assert second.json()["trigger_kind"] == "CORRECTION"

    use_cookies(client, member_cookies)
    visible = await client.get(f"/api/v1/group-nur/rooms/{room_id}/syntheses")
    assert visible.status_code == 200, visible.text
    assert [row["version"] for row in visible.json()] == [2, 1]
    assert visible.json()[1]["status"] == "CORRECTED"
    assert all("Private owner context" not in str(row) for row in visible.json())

    use_cookies(client, outsider_cookies)
    assert (await client.get(
        f"/api/v1/group-nur/rooms/{room_id}/syntheses"
    )).status_code == 404
    assert member_id != outsider_response.json()["id"]


async def test_research_watchlist_and_tender_require_real_sources_and_revisions(
    client,
    app_engine,
    super_engine,
):
    owner_response, _, _ = await register_user(client, chosen_name="Research Owner")
    owner_id = owner_response.json()["id"]
    orbit_id = owner_response.json()["orbit"]["id"]
    brief_response = await client.post(
        "/api/v1/research/briefs",
        headers=H(client),
        json={"question": "What evidence supports release?", "orbit_id": orbit_id},
    )
    assert brief_response.status_code == 201, brief_response.text
    brief_id = brief_response.json()["id"]

    unavailable = await client.post(
        "/api/v1/research/jobs",
        headers=H(client),
        json={
            "research_brief_id": brief_id,
            "mode": "QUICK",
            "provider_name": "EXTERNAL_WEB",
            "query_preview": "NUR release evidence",
            "external_scope_approved": True,
        },
    )
    assert unavailable.status_code == 201, unavailable.text
    assert unavailable.json()["status"] == "NOT_CONNECTED"
    assert unavailable.json()["failure_code"] == "EXTERNAL_WEB_CONNECTOR_DISABLED"

    manual_job = await client.post(
        "/api/v1/research/jobs",
        headers=H(client),
        json={
            "research_brief_id": brief_id,
            "mode": "DEEP",
            "provider_name": "OWNER_SOURCES",
            "query_preview": "Compare release and hold evidence",
        },
    )
    assert manual_job.status_code == 201, manual_job.text
    job_id = manual_job.json()["id"]
    assert manual_job.json()["status"] == "RUNNING"

    async def add_source(title: str, url: str, excerpt: str, authority: str) -> dict:
        response = await client.post(
            "/api/v1/research/sources",
            headers=H(client),
            json={
                "research_brief_id": brief_id,
                "research_job_id": job_id,
                "title": title,
                "url": url,
                "publisher": "Owner-reviewed source",
                "source_kind": "WEB",
                "authority": authority,
                "reliability": "HIGH",
                "excerpt": excerpt,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    support = await add_source(
        "Release suite",
        "https://evidence.example/release-suite",
        "The persisted privacy and migration suites passed.",
        "PRIMARY",
    )
    counter = await add_source(
        "Residual risk review",
        "https://evidence.example/residual-risk",
        "Live external retrieval and staging restore remain unproven.",
        "SECONDARY",
    )
    claim_response = await client.post(
        "/api/v1/research/claims",
        headers=H(client),
        json={
            "research_brief_id": brief_id,
            "claim_text": "The local release suite is green, with external proof still pending.",
            "uncertainty": "Staging and external connector evidence are outside this result.",
            "citation_alignment": "HIGH",
            "citations": [
                {"source_id": support["id"], "relationship": "SUPPORTS", "locator": "suite"},
                {"source_id": counter["id"], "relationship": "COUNTERS", "locator": "limits"},
            ],
        },
    )
    assert claim_response.status_code == 201, claim_response.text
    claim_id = claim_response.json()["id"]
    assert {item["relationship"] for item in claim_response.json()["citations"]} == {
        "SUPPORTS", "COUNTERS",
    }
    completed = await client.post(
        f"/api/v1/research/jobs/{job_id}/complete",
        headers=H(client),
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "SUCCEEDED"
    cancellable = await client.post(
        "/api/v1/research/jobs",
        headers=H(client),
        json={
            "research_brief_id": brief_id,
            "mode": "QUICK",
            "provider_name": "OWNER_SOURCES",
            "query_preview": "A deliberately cancelled follow-up",
        },
    )
    cancelled = await client.post(
        f"/api/v1/research/jobs/{cancellable.json()['id']}/cancel",
        headers=H(client),
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "CANCELLED"

    corrected = await client.post(
        f"/api/v1/research/claims/{claim_id}/corrections",
        headers=H(client),
        json={
            "claim_text": "The owner-reviewed local evidence is green; it is not live-source proof.",
            "uncertainty": "No external connector or staging evidence is represented.",
            "citation_alignment": "HIGH",
            "correction_reason": "The original wording could imply broader source coverage.",
            "citations": [
                {"source_id": support["id"], "relationship": "SUPPORTS"},
                {"source_id": counter["id"], "relationship": "COUNTERS"},
            ],
        },
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["revision_number"] == 2
    async with super_engine.connect() as connection:
        revision = (await connection.execute(text("""
            SELECT correction_reason FROM research_claim_revisions
            WHERE claim_id = :claim_id
        """), {"claim_id": claim_id})).scalar_one()
        assert "broader source coverage" in revision

    question = await client.post(
        "/api/v1/web-signals/questions",
        headers=H(client),
        json={"question": "Did the release evidence change?", "orbit_id": orbit_id},
    )
    watchlist = await client.post(
        "/api/v1/web-signals/watchlists",
        headers=H(client),
        json={
            "web_signal_question_id": question.json()["id"],
            "name": "Release evidence",
            "source_url": "https://evidence.example/release-suite",
            "schedule": "DAILY",
            "alert_enabled": True,
            "relevance_scope": {"orbit_id": orbit_id},
        },
    )
    assert watchlist.status_code == 201, watchlist.text
    assert watchlist.json()["connector_status"] == "NOT_CONNECTED"
    watchlist_id = watchlist.json()["id"]
    first_capture = await client.post(
        f"/api/v1/web-signals/watchlists/{watchlist_id}/owner-captures",
        headers=H(client),
        json={"title": "Run one", "summary": "The privacy suite passed once."},
    )
    assert first_capture.status_code == 201, first_capture.text
    assert first_capture.json()["changed_from_previous"] is False
    second_capture = await client.post(
        f"/api/v1/web-signals/watchlists/{watchlist_id}/owner-captures",
        headers=H(client),
        json={
            "title": "Run two",
            "summary": "The privacy suite passed twice.",
            "change_summary": "A second persisted run now exists.",
        },
    )
    assert second_capture.status_code == 201, second_capture.text
    assert second_capture.json()["changed_from_previous"] is True
    alerts = await client.get("/api/v1/web-signals/alerts")
    assert len(alerts.json()) == 1
    assert alerts.json()[0]["status"] == "UNREAD"
    paused = await client.patch(
        f"/api/v1/web-signals/watchlists/{watchlist_id}",
        headers=H(client),
        json={"status": "PAUSED", "alert_enabled": False, "schedule": "WEEKLY"},
    )
    assert paused.status_code == 200, paused.text
    assert paused.json()["status"] == "PAUSED"
    assert paused.json()["alert_enabled"] is False
    assert paused.json()["connector_status"] == "NOT_CONNECTED"

    tender = await client.post(
        "/api/v1/tender-insights",
        headers=H(client),
        json={
            "scope_kind": "GENERAL",
            "insight": "You may be treating local proof as the whole release.",
            "uncertainty": "Only owner-reviewed sources are represented.",
            "counterexample": "The release may intentionally be local-only.",
            "conditions": ["External connector stays disabled"],
            "source_ids": [support["id"], counter["id"]],
        },
    )
    assert tender.status_code == 201, tender.text
    kept = await client.patch(
        f"/api/v1/tender-insights/{tender.json()['id']}/status",
        headers=H(client),
        json={"action": "KEEP"},
    )
    assert kept.json()["status"] == "KEPT"
    tender_correction = await client.post(
        f"/api/v1/tender-insights/{tender.json()['id']}/corrections",
        headers=H(client),
        json={
            "scope_kind": "GENERAL",
            "insight": "Local proof is strong, while release-wide proof remains bounded.",
            "uncertainty": "Staging is not represented.",
            "counterexample": "A local cohort may need no external source.",
            "conditions": ["Keep the claim explicitly local"],
            "source_ids": [support["id"], counter["id"]],
            "correction_reason": "The first insight was too absolute.",
        },
    )
    assert tender_correction.status_code == 201, tender_correction.text
    assert tender_correction.json()["version"] == 2

    client.cookies.clear()
    outsider_response, _, _ = await register_user(client, chosen_name="Research Outsider")
    assert (await client.get("/api/v1/research/jobs")).json() == []
    assert (await client.get("/api/v1/research/sources")).json() == []
    assert (await client.get("/api/v1/research/claims")).json() == []
    assert (await client.get("/api/v1/web-signals/watchlists")).json() == []
    assert (await client.get("/api/v1/tender-insights")).json() == []
    async with app_engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :uid, false)"),
            {"uid": outsider_response.json()["id"]},
        )
        with pytest.raises(Exception):
            await connection.execute(text("""
                INSERT INTO research_jobs(
                    owner_user_id, research_brief_id, mode, provider_name,
                    status, query_preview, started_at
                ) VALUES (
                    :outsider_id, :brief_id, 'QUICK', 'OWNER_SOURCES',
                    'RUNNING', 'cross-owner link attempt', now()
                )
            """), {
                "outsider_id": outsider_response.json()["id"],
                "brief_id": brief_id,
            })
    assert owner_id != outsider_response.json()["id"]


async def test_expert_peer_attestation_and_room_moderation_are_explicit(client):
    owner_response, owner_email, _ = await register_user(client, chosen_name="Room Moderator")
    owner_cookies = save_cookies(client)
    room_response = await client.post(
        "/api/v1/community/rooms",
        headers=H(client),
        json={"title": "Expert review room", "room_kind": "GROUP"},
    )
    room_id = room_response.json()["id"]

    client.cookies.clear()
    expert_response, expert_email, _ = await register_user(client, chosen_name="Expert Member")
    expert_cookies = save_cookies(client)

    client.cookies.clear()
    _, observer_email, _ = await register_user(client, chosen_name="Room Observer")
    observer_cookies = save_cookies(client)

    client.cookies.clear()
    await register_user(client, chosen_name="Expert Outsider")
    outsider_cookies = save_cookies(client)

    use_cookies(client, owner_cookies)
    for email in (expert_email, observer_email):
        response = await client.post(
            f"/api/v1/community/rooms/{room_id}/members",
            headers=H(client),
            json={"email": email, "role": "MEMBER"},
        )
        assert response.status_code == 201, response.text

    use_cookies(client, expert_cookies)
    profile_response = await client.post(
        "/api/v1/experts/profiles",
        headers=H(client),
        json={
            "display_name": "Evidence Reviewer",
            "bio": "Reviews privacy test evidence.",
            "domains": ["privacy testing"],
            "conflicts": ["Contributed to the test plan"],
        },
    )
    assert profile_response.status_code == 201, profile_response.text
    profile_id = profile_response.json()["id"]
    assert profile_response.json()["verification_status"] == "UNVERIFIED"
    verification_response = await client.post(
        f"/api/v1/experts/profiles/{profile_id}/verifications",
        headers=H(client),
        json={
            "verifier_email": owner_email,
            "claim_type": "CREDENTIAL",
            "claim": "Reviewed the persisted privacy test plan.",
            "evidence_url": "https://evidence.example/reviewer-record",
        },
    )
    assert verification_response.status_code == 201, verification_response.text
    verification_id = verification_response.json()["id"]
    assert verification_response.json()["method"] == "PEER_ATTESTATION"

    brief = await client.post(
        "/api/v1/research/briefs",
        headers=H(client),
        json={"question": "What supports the expert contribution?"},
    )
    source = await client.post(
        "/api/v1/research/sources",
        headers=H(client),
        json={
            "research_brief_id": brief.json()["id"],
            "title": "Reviewer record",
            "url": "https://evidence.example/reviewer-record",
            "source_kind": "DOCUMENT",
            "authority": "PRIMARY",
            "reliability": "HIGH",
            "excerpt": "The member reviewed the privacy test plan.",
        },
    )
    assert source.status_code == 201, source.text

    use_cookies(client, owner_cookies)
    review = await client.post(
        f"/api/v1/experts/verifications/{verification_id}/review",
        headers=H(client),
        json={"decision": "ATTEST", "reviewer_note": "I attest only that this review occurred."},
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "ATTESTED"

    use_cookies(client, expert_cookies)
    profile = (await client.get("/api/v1/experts/profiles")).json()[0]
    assert profile["verification_status"] == "PEER_ATTESTED"
    assert profile["verification_scope"] == "PEER_ATTESTATION_ONLY"
    contribution = await client.post(
        f"/api/v1/experts/rooms/{room_id}/contributions",
        headers=H(client),
        json={
            "profile_id": profile_id,
            "body": "The repeat test reduces, but does not eliminate, privacy risk.",
            "source_ids": [source.json()["id"]],
            "conflict_disclosure": "I contributed to the test plan being reviewed.",
        },
    )
    assert contribution.status_code == 201, contribution.text
    contribution_id = contribution.json()["id"]
    assert contribution.json()["verification_label"] == "PEER_ATTESTED_NOT_CREDENTIAL_VERIFIED"
    assert contribution.json()["moderation_state"] == "PENDING"

    use_cookies(client, observer_cookies)
    pending_hidden = await client.get(f"/api/v1/experts/rooms/{room_id}/contributions")
    assert pending_hidden.status_code == 200
    assert pending_hidden.json() == []

    use_cookies(client, owner_cookies)
    moderator_view = await client.get(f"/api/v1/experts/rooms/{room_id}/contributions")
    assert [row["id"] for row in moderator_view.json()] == [contribution_id]
    approved = await client.post(
        f"/api/v1/experts/contributions/{contribution_id}/moderate",
        headers=H(client),
        json={"decision": "APPROVE", "note": "Scope and conflict label are visible."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["moderation_state"] == "APPROVED"

    use_cookies(client, observer_cookies)
    visible = await client.get(f"/api/v1/experts/rooms/{room_id}/contributions")
    assert [row["id"] for row in visible.json()] == [contribution_id]

    use_cookies(client, outsider_cookies)
    assert (await client.get(
        f"/api/v1/experts/rooms/{room_id}/contributions"
    )).status_code == 404
    assert expert_response.json()["id"] != owner_response.json()["id"]


async def test_g13_tables_force_rls_and_hide_all_rows_from_unrelated_owner(
    client,
    app_engine,
):
    outsider_response, _, _ = await register_user(client, chosen_name="Raw RLS Outsider")
    outsider_id = outsider_response.json()["id"]
    tables = [
        "group_nur_syntheses",
        "research_jobs",
        "research_sources",
        "research_claims",
        "research_citations",
        "research_claim_revisions",
        "web_watchlists",
        "web_signal_snapshots",
        "web_signal_alerts",
        "expert_profiles",
        "expert_verifications",
        "expert_contributions",
        "tender_insights",
    ]
    async with app_engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :uid, false)"),
            {"uid": outsider_id},
        )
        flags = (await connection.execute(text("""
            SELECT relname, relrowsecurity, relforcerowsecurity
            FROM pg_class WHERE relname = ANY(:tables) ORDER BY relname
        """), {"tables": tables})).all()
        assert len(flags) == len(tables)
        assert all(row.relrowsecurity and row.relforcerowsecurity for row in flags)
        counts = {
            table: (await connection.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
            for table in tables
        }
    assert all(value == 0 for value in counts.values()), counts
