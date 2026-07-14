import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import CognitiveEvent, OmegaClaim, OmegaConsolidationRun, OmegaExperience, Outcome, UserCorrection
from app.omega.claim_service import weaken_claim_for_correction
from app.omega.contradiction_service import detect_claim_contradictions
from app.omega.experience_service import ingest_from_cognitive_event
from app.omega.learning_proposal_service import create_learning_proposal
from app.omega.prediction_ledger import resolve_predictions_from_outcome
from app.omega.schemas import OmegaLearningProposalIn
from app.omega.semantic_extraction_service import extract_or_queue_claims


async def consolidate_owner(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None = None,
    run_kind: str = "MANUAL",
    max_recent: int = 50,
) -> OmegaConsolidationRun:
    await _ensure_no_active_run(db, owner_user_id=owner_user_id, orbit_id=orbit_id)
    run = OmegaConsolidationRun(owner_user_id=owner_user_id, orbit_id=orbit_id, run_kind=run_kind, status="STARTED")
    db.add(run)
    await db.flush()
    try:
        if max_recent < 0:
            raise ValueError("max_recent must be non-negative")
        recent_events = await _recent_events(db, owner_user_id=owner_user_id, orbit_id=orbit_id, limit=max_recent)
        created_experiences = 0
        created_claims = 0
        queued_review_items = 0
        for event in recent_events:
            existing = (await db.execute(select(func.count()).select_from(OmegaExperience).where(
                OmegaExperience.owner_user_id == owner_user_id,
                OmegaExperience.source_kind == "COGNITIVE_EVENT",
                OmegaExperience.source_id == event.id,
            ))).scalar_one()
            if not existing:
                exp = await ingest_from_cognitive_event(db, owner_user_id=owner_user_id, event=event)
                created_experiences += 1
                next_claims, next_review = await extract_or_queue_claims(db, owner_user_id=owner_user_id, experience=exp)
                created_claims += next_claims
                queued_review_items += next_review

        predictions_resolved = 0
        outcomes = (await db.execute(select(Outcome).where(Outcome.owner_user_id == owner_user_id).order_by(Outcome.created_at.desc()).limit(20))).scalars()
        for outcome in outcomes:
            predictions_resolved += await resolve_predictions_from_outcome(db, owner_user_id=owner_user_id, outcome=outcome)

        updated_claims = await _apply_recent_corrections(db, owner_user_id=owner_user_id, orbit_id=orbit_id)
        contradictions = await detect_claim_contradictions(db, owner_user_id=owner_user_id, orbit_id=orbit_id)
        proposals_created = 0
        if contradictions:
            await create_learning_proposal(
                db,
                owner_user_id=owner_user_id,
                payload=OmegaLearningProposalIn(
                    proposal_kind="PLANNING_HEURISTIC",
                    description="When an open Omega contradiction exists, ask the owner to resolve or narrow the next plan before continuing.",
                    evidence_summary=f"{len(contradictions)} open contradiction(s) found during consolidation.",
                ),
            )
            proposals_created = 1

        run.input_counts = {
            "recent_events": len(recent_events),
            "created_experiences": created_experiences,
            "queued_review_items": queued_review_items,
            "max_recent": max_recent,
            "summary": "Counts only; no raw private dump stored in consolidation metadata.",
        }
        run.created_claims = created_claims
        run.updated_claims = updated_claims
        run.contradictions_found = len(contradictions)
        run.predictions_resolved = predictions_resolved
        run.proposals_created = proposals_created
        run.status = "COMPLETED"
        run.completed_at = dt.datetime.now(dt.timezone.utc)
    except Exception as exc:
        run.status = "FAILED"
        run.error_class = exc.__class__.__name__
        run.completed_at = dt.datetime.now(dt.timezone.utc)
        raise
    finally:
        await db.flush()
    return run


async def list_consolidation_runs(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    limit: int = 20,
) -> list[OmegaConsolidationRun]:
    q = (
        select(OmegaConsolidationRun)
        .where(OmegaConsolidationRun.owner_user_id == owner_user_id)
        .order_by(OmegaConsolidationRun.created_at.desc())
        .limit(min(limit, 100))
    )
    return list((await db.execute(q)).scalars())


async def _ensure_no_active_run(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
) -> None:
    interval = max(1, int(get_settings().omega_consolidation_interval_hours))
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=interval)
    q = select(OmegaConsolidationRun.id).where(
        OmegaConsolidationRun.owner_user_id == owner_user_id,
        OmegaConsolidationRun.status == "STARTED",
        OmegaConsolidationRun.created_at >= cutoff,
    )
    if orbit_id:
        q = q.where(OmegaConsolidationRun.orbit_id == orbit_id)
    active = (await db.execute(q.limit(1))).scalar_one_or_none()
    if active:
        raise RuntimeError("Omega consolidation already running for this owner.")


async def _recent_events(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    limit: int,
) -> list[CognitiveEvent]:
    q = (
        select(CognitiveEvent)
        .where(CognitiveEvent.owner_user_id == owner_user_id)
        .order_by(CognitiveEvent.created_at.desc())
        .limit(limit)
    )
    if orbit_id:
        q = q.where(CognitiveEvent.orbit_id == orbit_id)
    return list((await db.execute(q)).scalars())


def _claim_type(event_kind: str, summary: str) -> str | None:
    lowered = f"{event_kind} {summary}".lower()
    if "constraint" in lowered or "must not" in lowered or "never" in lowered:
        return "CONSTRAINT"
    if event_kind in {"PLAN_CREATED", "PLAN_STEP"}:
        return "DECISION"
    if "decision" in lowered or "decide" in lowered:
        return "DECISION"
    if event_kind == "OUTCOME_REPORTED":
        return "PATTERN"
    if event_kind == "USER_CORRECTION":
        return "RISK"
    if event_kind == "MODEL_RESPONSE":
        return "HYPOTHESIS"
    return None


async def _apply_recent_corrections(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
) -> int:
    q = select(UserCorrection).where(UserCorrection.owner_user_id == owner_user_id).order_by(UserCorrection.created_at.desc()).limit(10)
    if orbit_id:
        q = q.where(UserCorrection.orbit_id == orbit_id)
    corrections = (await db.execute(q)).scalars().all()
    if not corrections:
        return 0
    claims = (await db.execute(select(OmegaClaim).where(
        OmegaClaim.owner_user_id == owner_user_id,
        OmegaClaim.truth_status.in_(["OBSERVED", "INFERRED", "HYPOTHESIS"]),
    ).limit(25))).scalars().all()
    updated = 0
    touched: set[uuid.UUID] = set()
    for correction in corrections:
        correction_terms = set(correction.correction_text.lower().split())
        for claim in claims:
            if claim.id in touched:
                continue
            claim_terms = set(claim.claim_text.lower().split())
            if len(correction_terms & claim_terms) >= 2:
                await weaken_claim_for_correction(
                    db,
                    owner_user_id=owner_user_id,
                    claim_id=claim.id,
                    correction_event_id=correction.id,
                    note="Owner correction conflicts with stored claim.",
                )
                touched.add(claim.id)
                updated += 1
    return updated
