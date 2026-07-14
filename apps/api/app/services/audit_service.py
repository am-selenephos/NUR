import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent


async def record(
    db: AsyncSession,
    *,
    event_type: str,
    object_type: str,
    actor_user_id: uuid.UUID | None = None,
    object_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            event_type=event_type,
            object_type=object_type,
            object_id=object_id,
            event_metadata=metadata or {},
        )
    )
