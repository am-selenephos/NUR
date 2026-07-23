import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DomainEvent

_RAW_PRIVATE_KEYS = {"text", "body", "content", "message", "journal", "chat", "prompt"}


def _contains_raw_private_field(value) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in _RAW_PRIVATE_KEYS or _contains_raw_private_field(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_raw_private_field(item) for item in value)
    return False


async def emit_domain_event(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    idempotency_key: str,
    payload: dict | None = None,
) -> DomainEvent:
    safe_payload = payload or {}
    if _contains_raw_private_field(safe_payload):
        raise ValueError("Domain event payloads may contain IDs and derived state, not raw private text.")
    existing = (
        await db.execute(
            select(DomainEvent).where(
                DomainEvent.owner_user_id == owner_user_id,
                DomainEvent.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    row = DomainEvent(
        owner_user_id=owner_user_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_payload=safe_payload,
        idempotency_key=idempotency_key,
    )
    db.add(row)
    await db.flush()
    return row
