import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OmegaClaim, OmegaReviewQueue
from app.omega.claim_service import create_claim
from app.omega.schemas import OmegaClaimIn, OmegaClaimCandidate


async def queue_claim_candidate(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    candidate: OmegaClaimCandidate,
    orbit_id: uuid.UUID | None,
    reason: str,
) -> OmegaReviewQueue:
    existing = (await db.execute(select(OmegaReviewQueue).where(
        OmegaReviewQueue.owner_user_id == owner_user_id,
        OmegaReviewQueue.status == "PENDING_REVIEW",
        OmegaReviewQueue.candidate_claim_text == candidate.claim_text,
    ))).scalar_one_or_none()
    if existing:
        return existing
    row = OmegaReviewQueue(
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        experience_id=candidate.source_experience_id,
        candidate_claim_text=candidate.claim_text,
        candidate_claim_type=candidate.claim_type,
        candidate_truth_status=candidate.truth_status if candidate.truth_status in {"INFERRED", "HYPOTHESIS"} else "HYPOTHESIS",
        sensitivity=candidate.sensitivity,
        reason=reason,
        model_candidate=candidate.model_dump(mode="json"),
    )
    db.add(row)
    await db.flush()
    return row


async def list_review_items(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    status: str | None = None,
    limit: int = 50,
) -> list[OmegaReviewQueue]:
    q = (
        select(OmegaReviewQueue)
        .where(OmegaReviewQueue.owner_user_id == owner_user_id)
        .order_by(OmegaReviewQueue.created_at.desc())
        .limit(min(limit, 100))
    )
    if status:
        q = q.where(OmegaReviewQueue.status == status)
    return list((await db.execute(q)).scalars())


async def approve_review_item(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    review_id: uuid.UUID,
) -> tuple[OmegaReviewQueue, OmegaClaim]:
    row = await _review_item(db, owner_user_id=owner_user_id, review_id=review_id)
    if row.status not in {"PENDING_REVIEW", "EDITED"}:
        raise ValueError("Review item has already been closed.")
    claim = await create_claim(
        db,
        owner_user_id=owner_user_id,
        payload=OmegaClaimIn(
            claim_text=row.candidate_claim_text,
            claim_type=row.candidate_claim_type,
            truth_status=row.candidate_truth_status,
            provenance_label="MODEL_GENERATED",
            orbit_id=row.orbit_id,
            confidence=float((row.model_candidate or {}).get("confidence") or 0.55),
            evidence_id=row.experience_id,
            evidence_kind="EXPERIENCE",
        ),
    )
    now = dt.datetime.now(dt.timezone.utc)
    row.status = "APPROVED"
    row.reviewed_at = now
    row.updated_at = now
    row.created_claim_id = claim.id
    await db.flush()
    return row, claim


async def reject_review_item(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    review_id: uuid.UUID,
) -> OmegaReviewQueue:
    row = await _review_item(db, owner_user_id=owner_user_id, review_id=review_id)
    if row.status not in {"PENDING_REVIEW", "EDITED"}:
        raise ValueError("Review item has already been closed.")
    now = dt.datetime.now(dt.timezone.utc)
    row.status = "REJECTED"
    row.reviewed_at = now
    row.updated_at = now
    await db.flush()
    return row


async def edit_review_item(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    review_id: uuid.UUID,
    claim_text: str,
    claim_type: str,
) -> OmegaReviewQueue:
    row = await _review_item(db, owner_user_id=owner_user_id, review_id=review_id)
    if row.status not in {"PENDING_REVIEW", "EDITED"}:
        raise ValueError("Review item has already been closed.")
    now = dt.datetime.now(dt.timezone.utc)
    row.candidate_claim_text = claim_text
    row.candidate_claim_type = claim_type
    row.status = "EDITED"
    row.updated_at = now
    await db.flush()
    return row


async def _review_item(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    review_id: uuid.UUID,
) -> OmegaReviewQueue:
    row = (await db.execute(select(OmegaReviewQueue).where(
        OmegaReviewQueue.id == review_id,
        OmegaReviewQueue.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if not row:
        raise PermissionError("Omega review item not found.")
    return row
