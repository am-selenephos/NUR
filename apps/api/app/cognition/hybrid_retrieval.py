import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.redaction import redact_for_model
from app.ai.schemas import EvidenceRef
from app.cognition.memory_service import retrieve_relevant


async def retrieve_hybrid(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    query: str,
    orbit_id: uuid.UUID | None,
    limit: int = 6,
) -> list[EvidenceRef]:
    # Lexical retrieval is live today. Embedding/vector search is not queried
    # until embedding writes exist; this keeps the "hybrid" seam honest.
    refs = await retrieve_relevant(
        db,
        owner_user_id=owner_user_id,
        query=query,
        orbit_id=orbit_id,
        limit=min(limit, 6),
    )
    return [EvidenceRef(kind=r.kind, id=r.id, excerpt=redact_for_model(r.excerpt), rank=r.rank) for r in refs]
