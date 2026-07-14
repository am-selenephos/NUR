import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import NURTalkOutput
from app.models import Prediction


async def persist_predictions(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    source_event_id: uuid.UUID,
    output: NURTalkOutput,
) -> list[Prediction]:
    rows: list[Prediction] = []
    for hypothesis in output.hypotheses[:3]:
        if "will " not in hypothesis.lower() and "if " not in hypothesis.lower():
            continue
        row = Prediction(
            owner_user_id=owner_user_id,
            orbit_id=orbit_id,
            source_event_id=source_event_id,
            statement=hypothesis,
            expected_observation={},
        )
        db.add(row)
        rows.append(row)
    return rows
