"""Provenance & revision (mandate F4): outcomes revise hypothesis confidence
and land as claim evidence with explicit rationale. Deterministic, inspectable
arithmetic — no model, no magic."""
import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClaimEvidence, Hypothesis, Outcome, SemanticClaim


def prediction_error(prediction: dict, measurements: dict) -> dict:
    """Field-wise numeric deltas where both sides speak numbers; the rest is
    listed as uncompared. Honest and shallow by design."""
    diff: dict = {"compared": {}, "uncompared": []}
    for key, pred in (prediction or {}).items():
        got = (measurements or {}).get(key)
        if isinstance(pred, (int, float)) and isinstance(got, (int, float)):
            diff["compared"][key] = {"predicted": pred, "observed": got, "delta": got - pred}
        else:
            diff["uncompared"].append(key)
    return diff


async def revise_hypothesis_from_outcome(
    db: AsyncSession, *, owner_user_id: uuid.UUID, hypothesis: Hypothesis, outcome: Outcome, supports: bool, rationale: str
) -> SemanticClaim:
    """Nudge confidence, mint/update the mirroring claim, attach evidence."""
    step = 0.1 if supports else -0.15
    hypothesis.confidence = max(0.0, min(1.0, (hypothesis.confidence or 0.5) + step))
    if hypothesis.status in ("PROPOSED", "TESTING"):
        hypothesis.status = "TESTING"

    claim = (
        await db.execute(
            select(SemanticClaim).where(
                SemanticClaim.owner_user_id == owner_user_id,
                SemanticClaim.subject_ref == f"hypothesis:{hypothesis.id}",
            )
        )
    ).scalar_one_or_none()
    if claim is None:
        claim = SemanticClaim(
            owner_user_id=owner_user_id,
            claim_text=hypothesis.hypothesis_text,
            subject_ref=f"hypothesis:{hypothesis.id}",
            predicate="supported_by_outcomes",
            confidence=hypothesis.confidence,
        )
        db.add(claim)
        await db.flush()
    if supports:
        claim.evidence_count += 1
    else:
        claim.counterevidence_count += 1
    claim.confidence = hypothesis.confidence
    claim.status = (
        "SUPPORTED" if claim.evidence_count >= 2 and claim.counterevidence_count == 0
        else "DISPUTED" if claim.counterevidence_count > claim.evidence_count
        else "MIXED" if claim.counterevidence_count and claim.evidence_count
        else "EMERGING"
    )
    claim.last_evaluated_at = dt.datetime.now(dt.timezone.utc)

    db.add(ClaimEvidence(
        owner_user_id=owner_user_id, claim_id=claim.id, outcome_id=outcome.id,
        supports=supports, weight=1.0, rationale=rationale,
    ))
    return claim
