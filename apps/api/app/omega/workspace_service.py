import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OmegaClaim, OmegaContradiction, OmegaExperience, OmegaPrediction, OmegaWorkspaceFrame
from app.omega.schemas import OmegaTalkSummary


async def build_workspace_frame(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    task_mode: str,
    active_question: str,
    orbit_id: uuid.UUID | None = None,
    trigger_event_id: uuid.UUID | None = None,
) -> OmegaWorkspaceFrame:
    claims = (await db.execute(
        select(OmegaClaim)
        .where(
            OmegaClaim.owner_user_id == owner_user_id,
            OmegaClaim.truth_status.in_(["OBSERVED", "INFERRED", "HYPOTHESIS"]),
        )
        .order_by(OmegaClaim.updated_at.desc())
        .limit(6)
    )).scalars().all()
    experiences = (await db.execute(
        select(OmegaExperience)
        .where(
            OmegaExperience.owner_user_id == owner_user_id,
            OmegaExperience.sensitivity != "SECRET_EXCLUDED",
        )
        .order_by(OmegaExperience.created_at.desc())
        .limit(6)
    )).scalars().all()
    contradictions = (await db.execute(
        select(OmegaContradiction)
        .where(OmegaContradiction.owner_user_id == owner_user_id, OmegaContradiction.status == "OPEN")
        .order_by(OmegaContradiction.created_at.desc())
        .limit(3)
    )).scalars().all()
    risk_flags = ["omega_context_owner_only"]
    if any(c.severity == "CRITICAL" for c in contradictions):
        risk_flags.append("critical_contradiction_blocks_affected_claims")
    frame = OmegaWorkspaceFrame(
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        task_mode=task_mode,
        trigger_event_id=trigger_event_id,
        active_question=active_question[:800],
        attention_items={
            "claim_summaries": [c.claim_text[:180] for c in claims],
            "experience_summaries": [e.summary[:180] for e in experiences],
            "contradiction_summaries": [c.description[:220] for c in contradictions],
        },
        retrieved_claim_ids=[c.id for c in claims],
        retrieved_experience_ids=[e.id for e in experiences],
        active_hypothesis_ids=[c.id for c in claims if c.truth_status == "HYPOTHESIS"][:3],
        active_contradiction_ids=[c.id for c in contradictions],
        risk_flags=risk_flags,
        scope_statement="Owner-only Omega workspace frame; no chain-of-thought, no raw journal dump, no capsule-recipient data.",
    )
    db.add(frame)
    await db.flush()
    return frame


async def mark_frame_used(db: AsyncSession, frame: OmegaWorkspaceFrame) -> None:
    frame.status = "USED"
    await db.flush()


async def talk_summary(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    workspace_frame_id: uuid.UUID | None,
) -> OmegaTalkSummary:
    claims = (await db.execute(
        select(OmegaClaim)
        .where(OmegaClaim.owner_user_id == owner_user_id, OmegaClaim.support_count > 0)
        .order_by(OmegaClaim.updated_at.desc())
        .limit(1)
    )).scalars().all()
    contradictions = (await db.execute(
        select(OmegaContradiction)
        .where(OmegaContradiction.owner_user_id == owner_user_id, OmegaContradiction.status == "OPEN")
        .order_by(OmegaContradiction.created_at.desc())
        .limit(1)
    )).scalars().all()
    predictions = (await db.execute(
        select(OmegaPrediction)
        .where(OmegaPrediction.owner_user_id == owner_user_id, OmegaPrediction.status == "OPEN")
        .order_by(OmegaPrediction.created_at.desc())
        .limit(1)
    )).scalars().all()
    return OmegaTalkSummary(
        workspace_frame_id=workspace_frame_id,
        what_changed=[f"Claim strengthened: {c.claim_text}" for c in claims],
        open_contradictions=[c.description for c in contradictions],
        unresolved_predictions=[p.prediction_text for p in predictions],
    )
