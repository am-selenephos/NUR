import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.cognition import ModelRun


async def assert_daily_ai_budget(db: AsyncSession, *, owner_user_id: uuid.UUID) -> None:
    s = get_settings()
    if s.ai_provider != "openai":
        return
    start = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = (
        await db.execute(
            select(func.count(ModelRun.id)).where(
                ModelRun.owner_user_id == owner_user_id,
                ModelRun.created_at >= start,
                ModelRun.provider == "openai",
            )
        )
    ).scalar_one()
    if count >= s.ai_per_user_daily_limit:
        raise PermissionError("Daily AI request limit reached.")
