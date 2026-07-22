import datetime as dt
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BillingEntitlement


class EntitlementRequired(RuntimeError):
    pass


@dataclass(frozen=True)
class EntitlementDecision:
    feature_key: str
    allowed: bool
    usage_limit: int | None
    usage_consumed: int
    reason: str


async def resolve_entitlement(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    feature_key: str,
) -> EntitlementDecision:
    row = (
        await db.execute(
            select(BillingEntitlement).where(
                BillingEntitlement.owner_user_id == owner_user_id,
                BillingEntitlement.feature_key == feature_key,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return EntitlementDecision(feature_key, False, None, 0, "NO_ENTITLEMENT")
    current = dt.datetime.now(dt.UTC)
    allowed = row.allowed and (row.valid_until is None or row.valid_until > current)
    reason = row.reason if allowed else "ENTITLEMENT_INACTIVE_OR_EXPIRED"
    return EntitlementDecision(
        feature_key=feature_key,
        allowed=allowed,
        usage_limit=row.usage_limit,
        usage_consumed=row.usage_consumed,
        reason=reason,
    )


async def require_entitlement(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    feature_key: str,
) -> EntitlementDecision:
    decision = await resolve_entitlement(
        db,
        owner_user_id=owner_user_id,
        feature_key=feature_key,
    )
    if not decision.allowed:
        raise EntitlementRequired(f"The '{feature_key}' entitlement is required.")
    return decision
