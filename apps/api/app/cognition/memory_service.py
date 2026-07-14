"""Scoped retrieval (mandate E2/amendment NOW-organ): real Postgres full-text
search over the owner's own traces — events, journal, decisions, references,
research drafts. RLS already walls the rows; queries additionally scope by
owner and optional orbit. No embeddings are consulted until the gateway phase
(the vector columns stay NULL and unused)."""
import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class RetrievedRef:
    kind: str
    id: str
    excerpt: str
    rank: float


_SQL = """
WITH q AS (SELECT to_tsquery('english', :query) AS tsq)
SELECT * FROM (
  SELECT 'COGNITIVE_EVENT' AS kind, e.id::text AS id,
         left(coalesce(e.content_text,''), 240) AS excerpt,
         ts_rank(to_tsvector('english', coalesce(e.content_text,'')), q.tsq) AS rank
  FROM cognitive_events e, q
  WHERE e.owner_user_id = :owner
    AND (CAST(:orbit AS uuid) IS NULL OR e.orbit_id = CAST(:orbit AS uuid))
    AND to_tsvector('english', coalesce(e.content_text,'')) @@ q.tsq
  UNION ALL
  SELECT 'JOURNAL_ENTRY', j.id::text, left(j.body, 240),
         ts_rank(to_tsvector('english', j.body), q.tsq)
  FROM journal_entries j, q
  WHERE j.owner_user_id = :owner
    AND (CAST(:orbit AS uuid) IS NULL OR j.orbit_id = CAST(:orbit AS uuid))
    AND to_tsvector('english', j.body) @@ q.tsq
  UNION ALL
  SELECT 'DECISION', d.id::text, left(d.statement || ' — ' || coalesce(d.rationale,''), 240),
         ts_rank(to_tsvector('english', d.statement || ' ' || coalesce(d.rationale,'')), q.tsq)
  FROM decisions d, q
  WHERE d.owner_user_id = :owner
    AND (CAST(:orbit AS uuid) IS NULL OR d.orbit_id = CAST(:orbit AS uuid))
    AND to_tsvector('english', d.statement || ' ' || coalesce(d.rationale,'')) @@ q.tsq
  UNION ALL
  SELECT 'REFERENCE', r.id::text, left(r.title || ' — ' || coalesce(r.body,''), 240),
         ts_rank(to_tsvector('english', r.title || ' ' || coalesce(r.body,'')), q.tsq)
  FROM orbit_references r, q
  WHERE r.owner_user_id = :owner
    AND (CAST(:orbit AS uuid) IS NULL OR r.orbit_id = CAST(:orbit AS uuid))
    AND to_tsvector('english', r.title || ' ' || coalesce(r.body,'')) @@ q.tsq
  UNION ALL
  SELECT 'RESEARCH_DRAFT', rd.id::text, left(rd.question || ' ' || coalesce(rd.notes,''), 240),
         ts_rank(to_tsvector('english', rd.question || ' ' || coalesce(rd.notes,'')), q.tsq)
  FROM research_drafts rd, q
  WHERE rd.owner_user_id = :owner
    AND (CAST(:orbit AS uuid) IS NULL OR rd.orbit_id = CAST(:orbit AS uuid))
    AND to_tsvector('english', rd.question || ' ' || coalesce(rd.notes,'')) @@ q.tsq
) hits
ORDER BY rank DESC
LIMIT :limit
"""


_STOP = {"the","a","an","is","are","was","were","do","does","did","how","what","which","who",
         "why","when","where","of","to","in","on","for","and","or","we","our","you","your",
         "it","this","that","should","can","i","my","me","while","with"}


def _or_query(raw: str) -> str:
    """OR-of-lexemes: recall over precision for associative retrieval.
    websearch_to_tsquery ANDs terms, which makes any long sentence match
    nothing; ranking still orders by density of shared lexemes."""
    words = [w for w in "".join(c.lower() if c.isalnum() else " " for c in raw).split()
             if len(w) > 2 and w not in _STOP]
    return " | ".join(dict.fromkeys(words))


async def retrieve_relevant(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    query: str,
    orbit_id: uuid.UUID | None = None,
    limit: int = 8,
) -> list[RetrievedRef]:
    q = _or_query(query or "")
    if not q:
        return []
    rows = (
        await db.execute(
            text(_SQL),
            {"owner": str(owner_user_id), "query": q, "orbit": str(orbit_id) if orbit_id else None, "limit": limit},
        )
    ).all()
    return [RetrievedRef(kind=r.kind, id=r.id, excerpt=r.excerpt, rank=float(r.rank)) for r in rows]
