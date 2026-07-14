import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Orbit


async def assert_owned_orbit(db: AsyncSession, *, owner_user_id: uuid.UUID, orbit_id: uuid.UUID | None) -> None:
    if orbit_id is None:
        return
    row = (
        await db.execute(select(Orbit.id).where(Orbit.id == orbit_id, Orbit.owner_user_id == owner_user_id))
    ).scalar_one_or_none()
    if row is None:
        raise PermissionError("Orbit is not owned by the current user.")
