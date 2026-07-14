import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OmegaPrediction, Outcome
from app.omega.safety_law import redact_secrets
from app.omega.schemas import OmegaPredictionIn


async def create_prediction(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    payload: OmegaPredictionIn,
) -> OmegaPrediction:
    prediction_text, _ = redact_secrets(payload.prediction_text, max_len=1600)
    expected, _ = redact_secrets(payload.expected_observation, max_len=900)
    row = OmegaPrediction(
        owner_user_id=owner_user_id,
        orbit_id=payload.orbit_id,
        model_run_id=payload.model_run_id,
        claim_id=payload.claim_id,
        plan_step_id=payload.plan_step_id,
        prediction_text=prediction_text,
        expected_observation=expected,
        metric=payload.metric,
        time_window=payload.time_window,
        confidence=payload.confidence,
    )
    db.add(row)
    await db.flush()
    return row


async def list_predictions(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    status: str | None = None,
    limit: int = 50,
) -> list[OmegaPrediction]:
    q = (
        select(OmegaPrediction)
        .where(OmegaPrediction.owner_user_id == owner_user_id)
        .order_by(OmegaPrediction.created_at.desc())
        .limit(min(limit, 200))
    )
    if status:
        q = q.where(OmegaPrediction.status == status)
    return list((await db.execute(q)).scalars())


async def resolve_predictions_from_outcome(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    outcome: Outcome,
) -> int:
    rows = (await db.execute(select(OmegaPrediction).where(
        OmegaPrediction.owner_user_id == owner_user_id,
        OmegaPrediction.status == "OPEN",
    ))).scalars().all()
    count = 0
    observed = outcome.observed_result.lower()
    for row in rows:
        expected = row.expected_observation.lower()
        if not expected:
            continue
        if expected in observed:
            row.status = "CONFIRMED"
            row.prediction_error = 0.0
        elif outcome.plan_step_id and row.plan_step_id == outcome.plan_step_id:
            row.status = "DISCONFIRMED"
            row.prediction_error = 1.0
        else:
            continue
        row.outcome_id = outcome.id
        row.resolved_at = dt.datetime.now(dt.timezone.utc)
        count += 1
    await db.flush()
    return count
