import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import Identity, Scoped, require_csrf
from app.intelligence import service
from app.intelligence.schemas import (
    IntelligenceEvaluationRequest,
    IntelligenceEvaluationResult,
    IntelligenceProviderStatus,
)
from app.observability.metrics import record_counter
from app.omega.schemas import OmegaWhyChanged
from app.omega.why_changed_service import explain_why_claim_changed

router = APIRouter(tags=["intelligence"])


@router.get(
    "/intelligence/provider-status",
    response_model=IntelligenceProviderStatus,
)
async def get_intelligence_provider_status(
    db: Scoped,
    identity: Identity,
) -> IntelligenceProviderStatus:
    owner_user_id, _ = identity
    return await service.provider_status(db, owner_user_id=owner_user_id)


@router.post(
    "/intelligence/evaluate",
    response_model=IntelligenceEvaluationResult,
    dependencies=[Depends(require_csrf)],
)
async def evaluate_intelligence_spine(
    payload: IntelligenceEvaluationRequest,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> IntelligenceEvaluationResult:
    owner_user_id, _ = identity
    row, result = await service.evaluate_intelligence(
        db,
        owner_user_id=owner_user_id,
        suites=payload.suites,
    )
    output = IntelligenceEvaluationResult(
        id=row.id,
        created_at=row.created_at,
        **result,
    )
    record_counter(
        request,
        "nur_intelligence_evaluations_total",
        (("verdict", result["verdict"].lower()),),
    )
    await db.commit()
    return output


@router.get("/claims/{claim_id}/why-changed", response_model=OmegaWhyChanged)
async def get_claim_why_changed(
    claim_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> OmegaWhyChanged:
    owner_user_id, _ = identity
    try:
        return await explain_why_claim_changed(
            db,
            owner_user_id=owner_user_id,
            claim_id=claim_id,
        )
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
