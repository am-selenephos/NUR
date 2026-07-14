import datetime as dt
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.omega.claim_service import list_claims
from app.omega.consolidation_service import list_consolidation_runs
from app.omega.contradiction_service import list_contradictions
from app.omega.learning_proposal_service import list_learning_proposals
from app.omega.prediction_ledger import list_predictions
from app.omega.review_queue_service import list_review_items
from app.omega.schemas import (
    OmegaClaimOut,
    OmegaConsolidationOut,
    OmegaContradictionOut,
    OmegaExport,
    OmegaLearningProposalOut,
    OmegaPredictionOut,
    OmegaReviewQueueOut,
)


async def owner_omega_export(db: AsyncSession, *, owner_user_id: uuid.UUID) -> OmegaExport:
    claims = [OmegaClaimOut.model_validate(r) for r in await list_claims(db, owner_user_id=owner_user_id, limit=200)]
    contradictions = [OmegaContradictionOut.model_validate(r) for r in await list_contradictions(db, owner_user_id=owner_user_id, limit=200)]
    predictions = [OmegaPredictionOut.model_validate(r) for r in await list_predictions(db, owner_user_id=owner_user_id, limit=200)]
    runs = [OmegaConsolidationOut.model_validate(r) for r in await list_consolidation_runs(db, owner_user_id=owner_user_id, limit=100)]
    proposals = [OmegaLearningProposalOut.model_validate(r) for r in await list_learning_proposals(db, owner_user_id=owner_user_id, limit=100)]
    reviews = [OmegaReviewQueueOut.model_validate(r) for r in await list_review_items(db, owner_user_id=owner_user_id, limit=100)]
    return OmegaExport(
        exported_at=dt.datetime.now(dt.timezone.utc),
        owner_user_id=owner_user_id,
        safety={
            "owner_only": True,
            "capsule_recipient_context_excluded": True,
            "raw_private_dumps_excluded": True,
            "chain_of_thought_excluded": True,
        },
        counts={
            "claims": len(claims),
            "contradictions": len(contradictions),
            "predictions": len(predictions),
            "consolidation_runs": len(runs),
            "learning_proposals": len(proposals),
            "review_queue": len(reviews),
        },
        claims=claims,
        contradictions=contradictions,
        predictions=predictions,
        consolidation_runs=runs,
        learning_proposals=proposals,
        review_queue=reviews,
    )
