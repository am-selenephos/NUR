import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import Identity, Scoped, require_csrf
from app.core.config import get_settings
from app.models import CognitiveEvent
from app.observability.metrics import record_counter
from app.omega.claim_service import confirm_claim, create_claim, list_claims, retire_claim
from app.omega.consolidation_service import consolidate_owner, list_consolidation_runs
from app.omega.contradiction_service import list_contradictions, resolve_contradiction
from app.omega.evaluators import omega_status_labels
from app.omega.evidence_graph import claim_evidence
from app.omega.export_service import owner_omega_export
from app.omega.experience_service import ingest_experience, ingest_from_cognitive_event, list_experiences
from app.omega.learning_proposal_service import (
    create_learning_proposal,
    list_learning_proposals,
    transition_learning_proposal,
)
from app.omega.prediction_ledger import create_prediction, list_predictions
from app.omega.review_queue_service import approve_review_item, edit_review_item, list_review_items, reject_review_item
from app.omega.schemas import (
    OmegaClaimIn,
    OmegaClaimOut,
    OmegaContradictionOut,
    OmegaConsolidationOut,
    OmegaDashboard,
    OmegaEvidenceOut,
    OmegaExperienceIn,
    OmegaExperienceOut,
    OmegaExport,
    OmegaLearningProposalIn,
    OmegaLearningProposalOut,
    OmegaPredictionIn,
    OmegaPredictionOut,
    OmegaReviewEditIn,
    OmegaReviewQueueOut,
    OmegaWhyChanged,
)
from app.omega.why_changed_service import explain_why_claim_changed

router = APIRouter(prefix="/omega", tags=["omega"])


class FromEventIn(BaseModel):
    event_id: uuid.UUID | None = None
    event: OmegaExperienceIn | None = None


class ConsolidateIn(BaseModel):
    orbit_id: uuid.UUID | None = None
    run_kind: str = "MANUAL"


class ResolveIn(BaseModel):
    status: str = "RESOLVED"
    resolved_by_event_id: uuid.UUID | None = None


@router.get("/scheduler-status", response_model=dict)
async def scheduler_status(db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    settings = get_settings()
    runs = await list_consolidation_runs(db, owner_user_id=user_id, limit=1)
    latest = runs[0] if runs else None
    return {
        "enabled": settings.omega_enabled,
        "scheduled_consolidation": settings.omega_scheduled_consolidation,
        "interval_hours": settings.omega_consolidation_interval_hours,
        "worker_mode": "local_celery_beat",
        "last_consolidation_run_at": latest.created_at.isoformat() if latest else None,
        "last_consolidation_status": latest.status if latest else "none_yet",
        "provenance_label": "owner_ledger",
    }


@router.get("/dashboard", response_model=OmegaDashboard)
async def dashboard(db: Scoped, identity: Identity) -> OmegaDashboard:
    user_id, _ = identity
    return OmegaDashboard(
        statuses=omega_status_labels(),
        claims=[OmegaClaimOut.model_validate(r) for r in await list_claims(db, owner_user_id=user_id, limit=8)],
        contradictions=[OmegaContradictionOut.model_validate(r) for r in await list_contradictions(db, owner_user_id=user_id, status="OPEN", limit=8)],
        predictions=[OmegaPredictionOut.model_validate(r) for r in await list_predictions(db, owner_user_id=user_id, limit=8)],
        consolidation_runs=[OmegaConsolidationOut.model_validate(r) for r in await list_consolidation_runs(db, owner_user_id=user_id, limit=5)],
        learning_proposals=[OmegaLearningProposalOut.model_validate(r) for r in await list_learning_proposals(db, owner_user_id=user_id, limit=8)],
        recent_experiences=[OmegaExperienceOut.model_validate(r) for r in await list_experiences(db, owner_user_id=user_id, limit=8)],
        review_queue=[OmegaReviewQueueOut.model_validate(r) for r in await list_review_items(db, owner_user_id=user_id, status="PENDING_REVIEW", limit=8)],
    )


@router.post("/experiences/from-event", response_model=OmegaExperienceOut, status_code=201, dependencies=[Depends(require_csrf)])
async def from_event(payload: FromEventIn, request: Request, db: Scoped, identity: Identity) -> OmegaExperienceOut:
    user_id, _ = identity
    if payload.event_id:
        event = (await db.execute(select(CognitiveEvent).where(
            CognitiveEvent.id == payload.event_id,
            CognitiveEvent.owner_user_id == user_id,
        ))).scalar_one_or_none()
        if not event:
            raise HTTPException(404, "Event not found.")
        row = await ingest_from_cognitive_event(db, owner_user_id=user_id, event=event)
    elif payload.event:
        row = await ingest_experience(db, owner_user_id=user_id, payload=payload.event)
    else:
        raise HTTPException(422, "event_id or event payload required.")
    record_counter(request, "nur_omega_experiences_total")
    await db.commit()
    return OmegaExperienceOut.model_validate(row)


@router.get("/experiences", response_model=list[OmegaExperienceOut])
async def experiences(db: Scoped, identity: Identity, orbit_id: uuid.UUID | None = None, kind: str | None = None, limit: int = 50) -> list[OmegaExperienceOut]:
    user_id, _ = identity
    return [OmegaExperienceOut.model_validate(r) for r in await list_experiences(
        db, owner_user_id=user_id, orbit_id=orbit_id, kind=kind, limit=limit,
    )]


@router.post("/claims", response_model=OmegaClaimOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_claim(payload: OmegaClaimIn, request: Request, db: Scoped, identity: Identity) -> OmegaClaimOut:
    user_id, _ = identity
    row = await create_claim(db, owner_user_id=user_id, payload=payload)
    record_counter(request, "nur_omega_claims_total")
    await db.commit()
    return OmegaClaimOut.model_validate(row)


@router.get("/claims", response_model=list[OmegaClaimOut])
async def claims(db: Scoped, identity: Identity, orbit_id: uuid.UUID | None = None, status: str | None = None, type: str | None = None) -> list[OmegaClaimOut]:  # noqa: A002
    user_id, _ = identity
    return [OmegaClaimOut.model_validate(r) for r in await list_claims(
        db, owner_user_id=user_id, orbit_id=orbit_id, status=status, claim_type=type,
    )]


@router.post("/claims/{claim_id}/confirm", response_model=OmegaClaimOut, dependencies=[Depends(require_csrf)])
async def confirm(claim_id: uuid.UUID, db: Scoped, identity: Identity) -> OmegaClaimOut:
    user_id, _ = identity
    try:
        row = await confirm_claim(db, owner_user_id=user_id, claim_id=claim_id)
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
    await db.commit()
    return OmegaClaimOut.model_validate(row)


@router.post("/claims/{claim_id}/retire", response_model=OmegaClaimOut, dependencies=[Depends(require_csrf)])
async def retire(claim_id: uuid.UUID, db: Scoped, identity: Identity) -> OmegaClaimOut:
    user_id, _ = identity
    try:
        row = await retire_claim(db, owner_user_id=user_id, claim_id=claim_id)
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
    await db.commit()
    return OmegaClaimOut.model_validate(row)


@router.get("/claims/{claim_id}/evidence", response_model=list[OmegaEvidenceOut])
async def evidence(claim_id: uuid.UUID, db: Scoped, identity: Identity) -> list[OmegaEvidenceOut]:
    user_id, _ = identity
    return [OmegaEvidenceOut.model_validate(r) for r in await claim_evidence(db, owner_user_id=user_id, claim_id=claim_id)]


@router.get("/claims/{claim_id}/why-changed", response_model=OmegaWhyChanged)
async def why_changed(claim_id: uuid.UUID, db: Scoped, identity: Identity) -> OmegaWhyChanged:
    user_id, _ = identity
    try:
        return await explain_why_claim_changed(db, owner_user_id=user_id, claim_id=claim_id)
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/contradictions", response_model=list[OmegaContradictionOut])
async def contradictions(db: Scoped, identity: Identity, orbit_id: uuid.UUID | None = None, status: str | None = None) -> list[OmegaContradictionOut]:
    user_id, _ = identity
    return [OmegaContradictionOut.model_validate(r) for r in await list_contradictions(
        db, owner_user_id=user_id, orbit_id=orbit_id, status=status,
    )]


@router.post("/contradictions/{contradiction_id}/resolve", response_model=OmegaContradictionOut, dependencies=[Depends(require_csrf)])
async def resolve(contradiction_id: uuid.UUID, payload: ResolveIn, db: Scoped, identity: Identity) -> OmegaContradictionOut:
    user_id, _ = identity
    try:
        row = await resolve_contradiction(
            db,
            owner_user_id=user_id,
            contradiction_id=contradiction_id,
            status=payload.status,
            resolved_by_event_id=payload.resolved_by_event_id,
        )
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
    await db.commit()
    return OmegaContradictionOut.model_validate(row)


@router.post("/predictions", response_model=OmegaPredictionOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_prediction(payload: OmegaPredictionIn, request: Request, db: Scoped, identity: Identity) -> OmegaPredictionOut:
    user_id, _ = identity
    row = await create_prediction(db, owner_user_id=user_id, payload=payload)
    record_counter(request, "nur_omega_predictions_open_total")
    await db.commit()
    return OmegaPredictionOut.model_validate(row)


@router.get("/predictions", response_model=list[OmegaPredictionOut])
async def predictions(db: Scoped, identity: Identity, status: str | None = None) -> list[OmegaPredictionOut]:
    user_id, _ = identity
    return [OmegaPredictionOut.model_validate(r) for r in await list_predictions(db, owner_user_id=user_id, status=status)]


@router.post("/consolidate", response_model=OmegaConsolidationOut, dependencies=[Depends(require_csrf)])
async def consolidate(payload: ConsolidateIn, request: Request, db: Scoped, identity: Identity) -> OmegaConsolidationOut:
    user_id, _ = identity
    try:
        row = await consolidate_owner(
            db,
            owner_user_id=user_id,
            orbit_id=payload.orbit_id,
            run_kind=payload.run_kind,
            max_recent=get_settings().omega_max_experiences_per_run,
        )
    except RuntimeError as exc:
        record_counter(request, "nur_omega_consolidation_lock_total")
        raise HTTPException(409, str(exc)) from exc
    record_counter(request, "nur_omega_consolidation_runs_total", (("status", row.status),))
    record_counter(request, "nur_omega_contradictions_open_total", amount=row.contradictions_found)
    record_counter(request, "nur_omega_learning_proposals_total", amount=row.proposals_created)
    await db.commit()
    return OmegaConsolidationOut.model_validate(row)


@router.get("/consolidation-runs", response_model=list[OmegaConsolidationOut])
async def consolidation_runs(db: Scoped, identity: Identity) -> list[OmegaConsolidationOut]:
    user_id, _ = identity
    return [OmegaConsolidationOut.model_validate(r) for r in await list_consolidation_runs(db, owner_user_id=user_id)]


@router.post("/learning-proposals", response_model=OmegaLearningProposalOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_learning_proposal(payload: OmegaLearningProposalIn, request: Request, db: Scoped, identity: Identity) -> OmegaLearningProposalOut:
    user_id, _ = identity
    try:
        row = await create_learning_proposal(db, owner_user_id=user_id, payload=payload)
    except PermissionError as exc:
        record_counter(request, "nur_omega_forbidden_proposals_blocked_total")
        raise HTTPException(422, str(exc)) from exc
    record_counter(request, "nur_omega_learning_proposals_total", (("risk", row.risk_level),))
    await db.commit()
    return OmegaLearningProposalOut.model_validate(row)


@router.get("/learning-proposals", response_model=list[OmegaLearningProposalOut])
async def learning_proposals(db: Scoped, identity: Identity) -> list[OmegaLearningProposalOut]:
    user_id, _ = identity
    return [OmegaLearningProposalOut.model_validate(r) for r in await list_learning_proposals(db, owner_user_id=user_id)]


@router.post("/learning-proposals/{proposal_id}/{action}", response_model=OmegaLearningProposalOut, dependencies=[Depends(require_csrf)])
async def learning_action(proposal_id: uuid.UUID, action: str, db: Scoped, identity: Identity) -> OmegaLearningProposalOut:
    user_id, _ = identity
    try:
        row = await transition_learning_proposal(db, owner_user_id=user_id, proposal_id=proposal_id, action=action)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await db.commit()
    return OmegaLearningProposalOut.model_validate(row)


@router.get("/review-queue", response_model=list[OmegaReviewQueueOut])
async def review_queue(db: Scoped, identity: Identity, status: str | None = "PENDING_REVIEW") -> list[OmegaReviewQueueOut]:
    user_id, _ = identity
    return [OmegaReviewQueueOut.model_validate(r) for r in await list_review_items(db, owner_user_id=user_id, status=status)]


@router.post("/review-queue/{review_id}/approve", response_model=OmegaReviewQueueOut, dependencies=[Depends(require_csrf)])
async def approve_review(review_id: uuid.UUID, db: Scoped, identity: Identity) -> OmegaReviewQueueOut:
    user_id, _ = identity
    try:
        row, _claim = await approve_review_item(db, owner_user_id=user_id, review_id=review_id)
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await db.commit()
    return OmegaReviewQueueOut.model_validate(row)


@router.post("/review-queue/{review_id}/reject", response_model=OmegaReviewQueueOut, dependencies=[Depends(require_csrf)])
async def reject_review(review_id: uuid.UUID, db: Scoped, identity: Identity) -> OmegaReviewQueueOut:
    user_id, _ = identity
    try:
        row = await reject_review_item(db, owner_user_id=user_id, review_id=review_id)
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await db.commit()
    return OmegaReviewQueueOut.model_validate(row)


@router.post("/review-queue/{review_id}/edit", response_model=OmegaReviewQueueOut, dependencies=[Depends(require_csrf)])
async def edit_review(review_id: uuid.UUID, payload: OmegaReviewEditIn, db: Scoped, identity: Identity) -> OmegaReviewQueueOut:
    user_id, _ = identity
    try:
        row = await edit_review_item(
            db,
            owner_user_id=user_id,
            review_id=review_id,
            claim_text=payload.candidate_claim_text,
            claim_type=payload.candidate_claim_type,
        )
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await db.commit()
    return OmegaReviewQueueOut.model_validate(row)


@router.get("/export", response_model=OmegaExport)
async def export_omega(db: Scoped, identity: Identity) -> OmegaExport:
    user_id, _ = identity
    return await owner_omega_export(db, owner_user_id=user_id)
