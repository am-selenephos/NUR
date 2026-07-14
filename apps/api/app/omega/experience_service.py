import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CognitiveEvent, OmegaExperience
from app.omega.safety_law import redact_secrets, sensitivity_for_summary
from app.omega.schemas import OmegaExperienceIn


async def ingest_experience(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    payload: OmegaExperienceIn,
) -> OmegaExperience:
    summary, secret_found = redact_secrets(payload.summary)
    sensitivity = "SECRET_EXCLUDED" if secret_found else sensitivity_for_summary(summary, payload.sensitivity)
    row = OmegaExperience(
        owner_user_id=owner_user_id,
        source_kind=payload.source_kind,
        source_id=payload.source_id,
        orbit_id=payload.orbit_id,
        event_kind=payload.event_kind,
        scope=payload.scope,
        language_tag=payload.language_tag,
        summary=summary,
        raw_ref=payload.raw_ref,
        provenance_label=payload.provenance_label,
        sensitivity=sensitivity,
        confidence=payload.confidence,
    )
    db.add(row)
    await db.flush()
    return row


async def ingest_from_cognitive_event(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    event: CognitiveEvent,
    provenance_label: str | None = None,
) -> OmegaExperience:
    label = provenance_label or {
        "TALK_TURN": "OWNER_WRITTEN",
        "JOURNAL_ENTRY": "OWNER_WRITTEN",
        "PLAN_CREATED": "OWNER_WRITTEN",
        "PLAN_STEP": "SYSTEM_MEASURED",
        "OUTCOME_REPORTED": "OBSERVED_OUTCOME",
        "USER_CORRECTION": "USER_CORRECTION",
        "MODEL_RESPONSE": "MODEL_GENERATED",
        "EVALUATION_EVENT": "SYSTEM_MEASURED",
    }.get(event.event_kind, "SYSTEM_MEASURED")
    return await ingest_experience(
        db,
        owner_user_id=owner_user_id,
        payload=OmegaExperienceIn(
            source_kind="COGNITIVE_EVENT",
            source_id=event.id,
            orbit_id=event.orbit_id,
            event_kind=event.event_kind,
            scope=event.scope,
            summary=event.content_text or str(event.structured_payload)[:900],
            raw_ref={"table": "cognitive_events", "id": str(event.id)},
            provenance_label=label,
        ),
    )


async def list_experiences(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None = None,
    kind: str | None = None,
    limit: int = 50,
) -> list[OmegaExperience]:
    q = (
        select(OmegaExperience)
        .where(OmegaExperience.owner_user_id == owner_user_id)
        .order_by(OmegaExperience.created_at.desc())
        .limit(min(limit, 200))
    )
    if orbit_id:
        q = q.where(OmegaExperience.orbit_id == orbit_id)
    if kind:
        q = q.where(OmegaExperience.event_kind == kind)
    return list((await db.execute(q)).scalars())

