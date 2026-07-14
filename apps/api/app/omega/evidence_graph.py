import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OmegaClaim, OmegaEvidenceEdge


async def link_evidence(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    claim_id: uuid.UUID,
    evidence_kind: str,
    evidence_id: uuid.UUID,
    relation: str,
    strength: float = 1.0,
    note: str | None = None,
) -> OmegaEvidenceEdge:
    claim = (await db.execute(select(OmegaClaim).where(
        OmegaClaim.id == claim_id,
        OmegaClaim.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if not claim:
        raise PermissionError("Claim not found.")
    row = OmegaEvidenceEdge(
        owner_user_id=owner_user_id,
        claim_id=claim_id,
        evidence_kind=evidence_kind,
        evidence_id=evidence_id,
        relation=relation,
        strength=strength,
        note=note,
    )
    db.add(row)
    now = dt.datetime.now(dt.timezone.utc)
    if relation == "SUPPORTS":
        claim.support_count += 1
        claim.last_supported_at = now
    elif relation == "CONTRADICTS":
        claim.contradiction_count += 1
        claim.last_contradicted_at = now
        if claim.truth_status in {"OBSERVED", "INFERRED", "HYPOTHESIS"}:
            claim.truth_status = "CONTRADICTED"
    claim.updated_at = now
    await db.flush()
    return row


async def claim_evidence(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    claim_id: uuid.UUID,
) -> list[OmegaEvidenceEdge]:
    q = (
        select(OmegaEvidenceEdge)
        .where(OmegaEvidenceEdge.owner_user_id == owner_user_id, OmegaEvidenceEdge.claim_id == claim_id)
        .order_by(OmegaEvidenceEdge.created_at.desc())
    )
    return list((await db.execute(q)).scalars())
