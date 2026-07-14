import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import NURTalkOutput
from app.models import MemoryCandidate


async def persist_memory_candidates(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    source_event_id: uuid.UUID,
    output: NURTalkOutput,
) -> list[MemoryCandidate]:
    rows: list[MemoryCandidate] = []
    for text in output.memory_candidates[:5]:
        candidate = text.strip()
        if not candidate:
            continue
        row = MemoryCandidate(
            owner_user_id=owner_user_id,
            orbit_id=orbit_id,
            source_event_id=source_event_id,
            candidate_text=candidate,
            scope="LEARNING_CANDIDATE",
        )
        db.add(row)
        rows.append(row)
    return rows
