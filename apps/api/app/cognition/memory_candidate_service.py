import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import NURTalkOutput
from app.models import MemoryCandidate


async def persist_memory_candidates(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    source_event_id: uuid.UUID,
    user_message_event_id: uuid.UUID,
    model_run_id: uuid.UUID,
    request_id: uuid.UUID | None,
    evidence_digest: str,
    evidence_sources: list[dict],
    output: NURTalkOutput,
) -> list[MemoryCandidate]:
    from app.omega.safety_law import sensitivity_for_summary

    rows: list[MemoryCandidate] = []
    for text in output.memory_candidates[:5]:
        candidate = text.strip()
        if not candidate:
            continue
        sensitivity = sensitivity_for_summary(candidate)
        if sensitivity == "SECRET_EXCLUDED":
            continue
        row = MemoryCandidate(
            owner_user_id=owner_user_id,
            orbit_id=orbit_id,
            source_event_id=source_event_id,
            candidate_text=candidate,
            original_text=candidate,
            scope="LEARNING_CANDIDATE",
            memory_type="SEMANTIC",
            provenance_label="MODEL_GENERATED",
            confidence=0.5,
            sensitivity=sensitivity,
            created_by="MODEL",
            source_object_ids={
                "request_id": str(request_id) if request_id else None,
                "user_message_event_id": str(user_message_event_id),
                "assistant_message_event_id": str(source_event_id),
                "model_run_id": str(model_run_id),
                "evidence_digest": evidence_digest,
                "evidence_sources": evidence_sources,
                "source_refs": output.source_refs,
                "originating_system": "TALK",
            },
        )
        db.add(row)
        rows.append(row)
    if rows:
        await db.flush()
    return rows
