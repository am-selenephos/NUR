import json
import uuid

from sqlalchemy import text

from app.ai.schemas import AIProviderResult, NURTalkOutput
from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


def sse_events(raw: str) -> list[tuple[str, dict]]:
    events = []
    for block in raw.replace("\r\n", "\n").split("\n\n"):
        name = None
        data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line.removeprefix("event: ")
            if line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))
        if name and data is not None:
            events.append((name, data))
    return events


class CandidateProvider:
    name = "openai"

    def __init__(self, candidate: str | None = "Owner prefers sunrise planning rituals."):
        self.candidate = candidate
        self.requests = []

    async def complete_private_talk(self, request, event_sink=None):
        self.requests.append(request)
        if event_sink:
            await event_sink("provider.created", {"response_id": f"resp_{len(self.requests)}"})
        return AIProviderResult(
            provider="openai",
            model="memory-test-model",
            available=True,
            raw_response_id=f"resp_{len(self.requests)}",
            usage={"input_tokens": 12, "output_tokens": 8},
            output=NURTalkOutput(
                direct_response="I can hold that as a candidate for your review.",
                observed=[],
                inferred=[],
                hypotheses=[],
                uncertainty=[],
                next_move="Review the candidate before it becomes memory.",
                memory_candidates=[self.candidate] if self.candidate else [],
                source_refs=[],
            ),
        )


async def create_review_candidate(client, monkeypatch, *, candidate: str | None = None):
    provider = CandidateProvider(candidate or "Owner prefers sunrise planning rituals.")
    monkeypatch.setattr("app.cognition.intelligence_kernel.get_ai_provider", lambda: provider)
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/cognition/talk/stream",
        headers=H(client),
        json={
            "request_id": request_id,
            "message": "Please propose my sunrise planning preference for review.",
            "locale": "en",
            "memory_mode": "REVIEW",
        },
    )
    assert response.status_code == 200
    events = sse_events(response.text)
    candidate_event = next(data for name, data in events if name == "memory.candidate")
    assert set(candidate_event) == {"candidate_id", "status", "requires_owner_approval"}
    assert candidate_event["requires_owner_approval"] is True
    return candidate_event["candidate_id"], request_id, events, provider


async def test_talk_memory_mode_is_explicit_and_approval_is_versioned(
    client,
    monkeypatch,
    super_engine,
):
    registered, _, _ = await register_user(client)
    owner_id = registered.json()["id"]
    ephemeral_provider = CandidateProvider()
    monkeypatch.setattr(
        "app.cognition.intelligence_kernel.get_ai_provider",
        lambda: ephemeral_provider,
    )
    ephemeral = await client.post(
        "/api/v1/cognition/talk",
        headers=H(client),
        json={"message": "Do not keep this automatically.", "locale": "en"},
    )
    assert ephemeral.status_code == 200
    assert (await client.get("/api/v1/memory-candidates")).json() == []

    candidate_id, request_id, events, _ = await create_review_candidate(client, monkeypatch)
    assert [name for name, _ in events].index("memory.candidate") < [
        name for name, _ in events
    ].index("talk.validated")
    candidate = (await client.get(f"/api/v1/memory-candidates/{candidate_id}")).json()
    assert candidate["status"] == "CANDIDATE"
    assert candidate["provenance_label"] == "MODEL_GENERATED"
    assert candidate["created_by"] == "MODEL"
    assert candidate["approved_memory_id"] is None
    sources = candidate["source_object_ids"]
    assert sources["request_id"] == request_id
    assert sources["model_run_id"]
    assert sources["user_message_event_id"]
    assert sources["assistant_message_event_id"]
    assert len(sources["evidence_digest"]) == 64

    approved = await client.post(
        f"/api/v1/memory-candidates/{candidate_id}/approve",
        headers=H(client),
        json={"review_note": "Yes, keep this preference."},
    )
    assert approved.status_code == 200
    memory = approved.json()
    assert memory["canonical_text"] == "Owner prefers sunrise planning rituals."
    assert memory["provenance_label"] == "MODEL_GENERATED"
    assert memory["created_by"] == "OWNER"
    assert memory["version"] == 1
    replay = await client.post(
        f"/api/v1/memory-candidates/{candidate_id}/approve",
        headers=H(client),
        json={},
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == memory["id"]

    detail = (await client.get(f"/api/v1/memories/{memory['id']}")).json()
    assert len(detail["versions"]) == 1
    assert detail["versions"][0]["change_kind"] == "APPROVED"

    retrieval_provider = CandidateProvider(candidate=None)
    monkeypatch.setattr(
        "app.cognition.intelligence_kernel.get_ai_provider",
        lambda: retrieval_provider,
    )
    retrieved = await client.post(
        "/api/v1/cognition/talk",
        headers=H(client),
        json={"message": "What are my sunrise planning rituals?", "locale": "en"},
    )
    assert retrieved.status_code == 200
    assert any(ref.kind == "MEMORY" and ref.id == memory["id"] for ref in retrieval_provider.requests[0].retrieval)

    async with super_engine.connect() as conn:
        counts = {}
        for name, sql in {
            "memory": "SELECT count(*) FROM memories WHERE owner_user_id=:uid AND status='APPROVED'",
            "version": "SELECT count(*) FROM memory_versions WHERE owner_user_id=:uid",
            "edges": "SELECT count(*) FROM memory_edges WHERE owner_user_id=:uid",
            "access": "SELECT count(*) FROM memory_access_events WHERE owner_user_id=:uid AND access_kind='RETRIEVED'",
            "event": "SELECT count(*) FROM domain_events WHERE owner_user_id=:uid AND event_type='memory.approved'",
            "audit": "SELECT count(*) FROM audit_events WHERE actor_user_id=:uid AND event_type='MEMORY_APPROVED'",
        }.items():
            counts[name] = (await conn.execute(text(sql), {"uid": owner_id})).scalar_one()
        event_payload = (
            await conn.execute(
                text(
                    "SELECT event_payload::text FROM domain_events "
                    "WHERE owner_user_id=:uid AND event_type='memory.approved'"
                ),
                {"uid": owner_id},
            )
        ).scalar_one()
    assert counts["memory"] == 1
    assert counts["version"] == 1
    assert counts["edges"] >= 3
    assert counts["access"] == 1
    assert counts["event"] == 1
    assert counts["audit"] == 1
    assert "sunrise" not in event_payload.lower()


async def test_candidate_correct_reject_and_secret_exclusion(client, monkeypatch):
    await register_user(client)
    candidate_id, _, _, _ = await create_review_candidate(
        client,
        monkeypatch,
        candidate="Model guessed that mornings are always best.",
    )
    corrected = await client.post(
        f"/api/v1/memory-candidates/{candidate_id}/correct",
        headers=H(client),
        json={
            "canonical_text": "Late afternoons are usually best for focused planning.",
            "correction_reason": "The model guessed the wrong time.",
            "memory_type": "SEMANTIC",
        },
    )
    assert corrected.status_code == 200
    assert corrected.json()["status"] == "CORRECTED"
    assert corrected.json()["provenance_label"] == "USER_CORRECTION"
    assert corrected.json()["original_text"].startswith("Model guessed")
    approved = await client.post(
        f"/api/v1/memory-candidates/{candidate_id}/approve",
        headers=H(client),
        json={},
    )
    assert approved.status_code == 200
    assert approved.json()["provenance_label"] == "USER_CORRECTION"
    assert approved.json()["canonical_text"].startswith("Late afternoons")

    rejected_id, _, _, _ = await create_review_candidate(
        client,
        monkeypatch,
        candidate="A second untrusted model guess.",
    )
    rejected = await client.post(
        f"/api/v1/memory-candidates/{rejected_id}/reject",
        headers=H(client),
        json={"review_note": "Do not keep this."},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"
    cannot_approve = await client.post(
        f"/api/v1/memory-candidates/{rejected_id}/approve",
        headers=H(client),
        json={},
    )
    assert cannot_approve.status_code == 409

    secret_provider = CandidateProvider(candidate="password: this-must-not-enter-memory")
    monkeypatch.setattr(
        "app.cognition.intelligence_kernel.get_ai_provider",
        lambda: secret_provider,
    )
    secret = await client.post(
        "/api/v1/cognition/talk",
        headers=H(client),
        json={"message": "Keep a secret?", "memory_mode": "REVIEW"},
    )
    assert secret.status_code == 200
    candidates = (await client.get("/api/v1/memory-candidates")).json()
    assert "this-must-not-enter-memory" not in str(candidates)


async def test_owner_memory_crud_export_and_content_purge(client, super_engine):
    registered, _, _ = await register_user(client)
    owner_id = registered.json()["id"]
    original = "Private memory marker delta-731 must be removable."
    created = await client.post(
        "/api/v1/memories",
        headers=H(client),
        json={
            "canonical_text": original,
            "memory_type": "EPISODIC",
            "sensitivity": "SENSITIVE",
            "structured_value": {"owner_selected": True},
        },
    )
    assert created.status_code == 201
    memory_id = created.json()["id"]
    assert created.json()["provenance_label"] == "OWNER_WRITTEN"

    patched = await client.patch(
        f"/api/v1/memories/{memory_id}",
        headers=H(client),
        json={
            "canonical_text": "Corrected removable marker delta-731.",
            "correction_reason": "Owner corrected the wording.",
        },
    )
    assert patched.status_code == 200
    assert patched.json()["version"] == 2
    assert patched.json()["provenance_label"] == "OWNER_WRITTEN"
    detail = (await client.get(f"/api/v1/memories/{memory_id}")).json()
    assert [version["version"] for version in detail["versions"]] == [1, 2]

    exported = (await client.get("/api/v1/memories/export")).json()
    assert exported["safety"]["chain_of_thought_excluded"] is True
    assert exported["memories"][0]["versions"][0]["canonical_text"] == original

    deleted = await client.delete(f"/api/v1/memories/{memory_id}", headers=H(client))
    assert deleted.status_code == 204
    assert (await client.get(f"/api/v1/memories/{memory_id}")).status_code == 404
    assert (await client.get("/api/v1/memories")).json() == []
    after = (await client.get("/api/v1/memories/export")).json()
    retired = next(memory for memory in after["memories"] if memory["id"] == memory_id)
    assert retired["status"] == "RETIRED"
    assert retired["canonical_text"] == ""
    assert [version["canonical_text"] for version in retired["versions"]] == [""]

    async with super_engine.connect() as conn:
        memory_text = (
            await conn.execute(
                text("SELECT canonical_text FROM memories WHERE id=:id"),
                {"id": memory_id},
            )
        ).scalar_one()
        version_texts = (
            await conn.execute(
                text("SELECT canonical_text FROM memory_versions WHERE memory_id=:id"),
                {"id": memory_id},
            )
        ).scalars().all()
        raw_event_count = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM domain_events WHERE owner_user_id=:uid "
                    "AND event_payload::text ILIKE '%delta-731%'"
                ),
                {"uid": owner_id},
            )
        ).scalar_one()
    assert memory_text == ""
    assert version_texts == [""]
    assert raw_event_count == 0


async def test_memory_routes_and_rls_hide_foreign_owner_data(client, app_engine, monkeypatch):
    first, first_email, first_password = await register_user(client)
    first_id = first.json()["id"]
    candidate_id, _, _, _ = await create_review_candidate(client, monkeypatch)
    memory = await client.post(
        f"/api/v1/memory-candidates/{candidate_id}/approve",
        headers=H(client),
        json={},
    )
    memory_id = memory.json()["id"]

    client.cookies.clear()
    second, _, _ = await register_user(client, chosen_name="Other Memory Owner")
    second_id = second.json()["id"]
    assert (await client.get("/api/v1/memory-candidates")).json() == []
    assert (await client.get(f"/api/v1/memory-candidates/{candidate_id}")).status_code == 404
    assert (await client.get(f"/api/v1/memories/{memory_id}")).status_code == 404
    assert (
        await client.post(
            f"/api/v1/memory-candidates/{candidate_id}/approve",
            headers=H(client),
            json={},
        )
    ).status_code == 404

    async with app_engine.connect() as conn:
        await conn.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": second_id},
        )
        hidden = {}
        for table in (
            "memories",
            "memory_versions",
            "memory_edges",
            "memory_access_events",
            "domain_events",
            "memory_candidates",
        ):
            hidden[table] = (
                await conn.execute(text(f"SELECT count(*) FROM {table}"))
            ).scalar_one()
        update_result = await conn.execute(
            text("UPDATE memories SET canonical_text='cross-owner-write' WHERE id=:id"),
            {"id": memory_id},
        )
        await conn.rollback()
    assert all(count == 0 for count in hidden.values())
    assert update_result.rowcount == 0

    client.cookies.clear()
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": first_email, "password": first_password},
        )
    ).status_code == 200
    assert (await client.get(f"/api/v1/memories/{memory_id}")).status_code == 200
    assert first_id != second_id
