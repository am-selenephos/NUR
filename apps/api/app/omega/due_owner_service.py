import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.rls import set_auth_context
from app.models import User


async def omega_consolidation_due_owner_ids(db: AsyncSession, *, limit: int = 50) -> list[uuid.UUID]:
    """Return owner IDs only for the scheduled worker.

    The scheduler never receives raw private text. It uses the existing auth
    context read policy to enumerate active user IDs, then each owner run sets
    app.current_user_id before touching owner-scoped Omega tables.
    """
    await set_auth_context(db)
    rows = (await db.execute(
        select(User.id)
        .where(User.status == "active")
        .order_by(User.created_at.asc())
        .limit(min(limit, 100))
    )).scalars()
    return list(rows)
