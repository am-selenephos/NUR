import datetime as dt
import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OmegaClaim, OmegaContradiction


CONSTRAINT_MARKERS = ("must not", "never", "avoid", "cannot", "no ")
ACTION_MARKERS = ("will ", "should ", "must ", "use ", "do ", "ship ", "create ", "send ")


async def list_contradictions(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[OmegaContradiction]:
    q = (
        select(OmegaContradiction)
        .where(OmegaContradiction.owner_user_id == owner_user_id)
        .order_by(OmegaContradiction.created_at.desc())
        .limit(min(limit, 200))
    )
    if orbit_id:
        q = q.where(OmegaContradiction.orbit_id == orbit_id)
    if status:
        q = q.where(OmegaContradiction.status == status)
    return list((await db.execute(q)).scalars())


async def resolve_contradiction(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    contradiction_id: uuid.UUID,
    status: str = "RESOLVED",
    resolved_by_event_id: uuid.UUID | None = None,
) -> OmegaContradiction:
    row = (await db.execute(select(OmegaContradiction).where(
        OmegaContradiction.id == contradiction_id,
        OmegaContradiction.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if not row:
        raise PermissionError("Contradiction not found.")
    row.status = status
    row.resolved_by_event_id = resolved_by_event_id
    row.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.flush()
    return row


async def detect_claim_contradictions(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None = None,
) -> list[OmegaContradiction]:
    claims = await _active_claims(db, owner_user_id=owner_user_id, orbit_id=orbit_id)
    created: list[OmegaContradiction] = []
    for a in claims:
        for b in claims:
            if a.id == b.id:
                continue
            if not _conflicts(a, b):
                continue
            existing = (await db.execute(select(OmegaContradiction).where(
                OmegaContradiction.owner_user_id == owner_user_id,
                OmegaContradiction.status == "OPEN",
                or_(
                    (OmegaContradiction.claim_a_id == a.id) & (OmegaContradiction.claim_b_id == b.id),
                    (OmegaContradiction.claim_a_id == b.id) & (OmegaContradiction.claim_b_id == a.id),
                ),
            ))).scalar_one_or_none()
            if existing:
                continue
            severity = "HIGH" if "capsule" in f"{a.claim_text} {b.claim_text}".lower() else "MEDIUM"
            row = OmegaContradiction(
                owner_user_id=owner_user_id,
                orbit_id=a.orbit_id or b.orbit_id,
                claim_a_id=a.id,
                claim_b_id=b.id,
                severity=severity,
                description=f"Potential conflict: '{a.claim_text}' vs '{b.claim_text}'.",
                proposed_resolution="Review whether the action should be narrowed, retired, or held as an accepted paradox.",
            )
            db.add(row)
            created.append(row)
    await db.flush()
    return created


async def _active_claims(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
) -> list[OmegaClaim]:
    q = select(OmegaClaim).where(
        OmegaClaim.owner_user_id == owner_user_id,
        OmegaClaim.truth_status.in_(["OBSERVED", "INFERRED", "HYPOTHESIS"]),
    )
    if orbit_id:
        q = q.where(OmegaClaim.orbit_id == orbit_id)
    return list((await db.execute(q)).scalars())


def _conflicts(a: OmegaClaim, b: OmegaClaim) -> bool:
    at = a.claim_text.lower()
    bt = b.claim_text.lower()
    types = {a.claim_type, b.claim_type}
    if "CONSTRAINT" not in types or not (types & {"DECISION", "HYPOTHESIS", "PATTERN"}):
        return False
    constraint_text = at if a.claim_type == "CONSTRAINT" else bt
    action_text = bt if a.claim_type == "CONSTRAINT" else at
    if not any(marker in constraint_text for marker in CONSTRAINT_MARKERS):
        return False
    return any(marker in action_text for marker in ACTION_MARKERS)
