import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.cognition.schemas import VerificationResult
from app.models import ModelEvaluation


async def persist_model_evaluation(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    model_run_id: uuid.UUID,
    verification: VerificationResult,
) -> ModelEvaluation:
    row = ModelEvaluation(
        owner_user_id=owner_user_id,
        model_run_id=model_run_id,
        verdict=verification.verdict,
        checks=verification.checks,
    )
    db.add(row)
    return row
