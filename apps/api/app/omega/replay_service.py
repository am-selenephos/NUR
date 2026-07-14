import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import OmegaConsolidationRun
from app.omega.consolidation_service import consolidate_owner


async def omega_consolidate_owner(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None = None,
    run_kind: str = "MANUAL",
) -> OmegaConsolidationRun:
    """ID-scoped replay/consolidation entrypoint.

    This function is safe for Celery payloads: the worker only needs owner_id
    and optional orbit_id. It never accepts raw private text.
    """
    return await consolidate_owner(
        db,
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        run_kind=run_kind,
        max_recent=get_settings().omega_max_experiences_per_run,
    )
