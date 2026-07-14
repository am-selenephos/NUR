"""run_cognitive_cycle (mandate E3) — bounded, honest, durable.

One cycle: load the owned trigger event -> real scoped retrieval -> ask the
model gateway for hypothesis proposals. The gateway is Disabled in this phase,
so the cycle records exactly that: an EVALUATION_EVENT carrying full
provenance (retrieved refs + gateway status) is persisted, and the structured
result says the gateway was unavailable. No invented intelligence, ever
(constitution §17 / mandate E4)."""
import uuid
from dataclasses import asdict, dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognition.memory_service import RetrievedRef, retrieve_relevant
from app.cognition.model_gateway import get_gateway
from app.models import CognitiveEvent


@dataclass
class CycleResult:
    trigger_event_id: str
    retrieved: list[dict]
    gateway: str
    gateway_available: bool
    gateway_reason: str
    evaluation_event_id: str | None
    proposals: list[dict] = field(default_factory=list)


async def run_cognitive_cycle(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    trigger_event_id: uuid.UUID,
    action_mode: str = "observe",
) -> CycleResult:
    trigger = (
        await db.execute(
            select(CognitiveEvent).where(
                CognitiveEvent.id == trigger_event_id,
                CognitiveEvent.owner_user_id == owner_user_id,
            )
        )
    ).scalar_one()

    refs: list[RetrievedRef] = await retrieve_relevant(
        db,
        owner_user_id=owner_user_id,
        query=trigger.content_text or "",
        orbit_id=trigger.orbit_id,
        limit=6,
    )
    refs = [r for r in refs if r.id != str(trigger.id)]

    gw = get_gateway()
    result = await gw.generate_hypotheses(
        question=trigger.content_text or "",
        context_snippets=[asdict(r) for r in refs],
    )

    evaluation = CognitiveEvent(
        owner_user_id=owner_user_id,
        orbit_id=trigger.orbit_id,
        event_kind="EVALUATION_EVENT",
        content_text=f"cycle:{action_mode} over trigger {trigger.id}",
        structured_payload={
            "trigger_event_id": str(trigger.id),
            "retrieved": [asdict(r) for r in refs],
            "gateway": gw.name,
            "gateway_available": result.available,
            "gateway_reason": result.reason,
            "action_mode": action_mode,
        },
        source_ref=f"cognitive_event:{trigger.id}",
        scope=trigger.scope,
        parent_event_id=trigger.id,
    )
    db.add(evaluation)
    await db.flush()

    return CycleResult(
        trigger_event_id=str(trigger.id),
        retrieved=[asdict(r) for r in refs],
        gateway=gw.name,
        gateway_available=result.available,
        gateway_reason=result.reason,
        evaluation_event_id=str(evaluation.id),
        proposals=result.proposals,
    )
