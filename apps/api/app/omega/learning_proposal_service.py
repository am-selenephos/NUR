import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OmegaLearningProposal
from app.omega.safety_law import ensure_proposal_allowed, proposal_risk, redact_secrets
from app.omega.schemas import OmegaLearningProposalIn


async def create_learning_proposal(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    payload: OmegaLearningProposalIn,
) -> OmegaLearningProposal:
    ensure_proposal_allowed(payload.description, payload.proposal_kind)
    description, _ = redact_secrets(payload.description, max_len=1600)
    evidence_summary, _ = redact_secrets(payload.evidence_summary, max_len=1600)
    row = OmegaLearningProposal(
        owner_user_id=owner_user_id,
        proposal_kind=payload.proposal_kind,
        description=description,
        evidence_summary=evidence_summary,
        supporting_evaluation_ids=payload.supporting_evaluation_ids,
        risk_level=proposal_risk(description, payload.proposal_kind),
        status="PROPOSED",
    )
    db.add(row)
    await db.flush()
    return row


async def list_learning_proposals(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    limit: int = 50,
) -> list[OmegaLearningProposal]:
    q = (
        select(OmegaLearningProposal)
        .where(OmegaLearningProposal.owner_user_id == owner_user_id)
        .order_by(OmegaLearningProposal.created_at.desc())
        .limit(min(limit, 200))
    )
    return list((await db.execute(q)).scalars())


async def transition_learning_proposal(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    proposal_id: uuid.UUID,
    action: str,
) -> OmegaLearningProposal:
    row = (await db.execute(select(OmegaLearningProposal).where(
        OmegaLearningProposal.id == proposal_id,
        OmegaLearningProposal.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if not row:
        raise PermissionError("Learning proposal not found.")
    if row.risk_level == "FORBIDDEN":
        raise PermissionError("Forbidden learning proposals cannot be promoted.")
    if action == "approve":
        row.status = "APPROVED"
        row.approved_by_owner = True
    elif action == "reject":
        row.status = "REJECTED"
        row.approved_by_owner = False
    elif action == "rollback":
        row.status = "ROLLED_BACK"
        row.approved_by_owner = False
    else:
        raise ValueError("Unknown learning proposal action.")
    row.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.flush()
    return row
