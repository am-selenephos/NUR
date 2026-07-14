import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.audit import model_run_metadata, safe_error_metadata
from app.ai.budget import assert_daily_ai_budget
from app.ai.provider import get_ai_provider
from app.ai.schemas import AIProviderResult, AIStreamSink, EvidenceRef, NURTalkOutput, TalkProviderRequest
from app.cognition.evaluation_service import persist_model_evaluation
from app.cognition.evidence_packet import build_evidence_packet
from app.cognition.hybrid_retrieval import retrieve_hybrid
from app.cognition.memory_candidate_service import persist_memory_candidates
from app.cognition.prediction_service import persist_predictions
from app.cognition.retrieval_policy import assert_owned_orbit
from app.cognition.schemas import EvidencePacket, TalkKernelResult, VerificationResult
from app.cognition.task_router import route_task
from app.cognition.verifier import verify_talk_output
from app.core.config import get_settings
from app.models import CognitiveEvent, ModelRun, ModelRunSource
from app.omega.schemas import OmegaTalkSummary
from app.omega.workspace_service import build_workspace_frame, mark_frame_used, talk_summary


async def run_talk_kernel(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    user_line: str,
    orbit_id: uuid.UUID | None,
    locale: str,
    writing_preference: str = "default",
    requested_mode: str | None = None,
    request_id: uuid.UUID | None = None,
    event_sink: AIStreamSink | None = None,
) -> TalkKernelResult:
    if request_id is not None:
        existing = (
            await db.execute(
                select(ModelRun).where(
                    ModelRun.owner_user_id == owner_user_id,
                    ModelRun.request_id == request_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.output_event_id is None:
                raise TalkRunConflict(f"Talk request {request_id} is already {existing.status.lower()}.")
            replay = await _replay_talk_result(db, existing)
            if event_sink is not None:
                await event_sink(
                    "talk.replayed",
                    {
                        "request_id": str(request_id),
                        "model_run_id": str(replay.model_run_id),
                        "response_event_id": str(replay.response_event_id),
                    },
                )
            return replay

    await assert_owned_orbit(db, owner_user_id=owner_user_id, orbit_id=orbit_id)
    task_mode = route_task(user_line, requested_mode)
    turn = CognitiveEvent(
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        event_kind="TALK_TURN",
        content_text=user_line,
        structured_payload={"mode": task_mode.value, "locale": locale, "writing_preference": writing_preference},
        source_ref="talk",
    )
    db.add(turn)
    await db.flush()
    frame = await build_workspace_frame(
        db,
        owner_user_id=owner_user_id,
        task_mode=task_mode.value,
        active_question=user_line,
        orbit_id=orbit_id,
        trigger_event_id=turn.id,
    )

    retrieval = await retrieve_hybrid(
        db,
        owner_user_id=owner_user_id,
        query=user_line,
        orbit_id=orbit_id,
        limit=6,
    )
    evidence = build_evidence_packet(orbit_id=orbit_id, retrieval=retrieval)
    await assert_daily_ai_budget(db, owner_user_id=owner_user_id)

    s = get_settings()
    run_metadata = model_run_metadata(
        provider=s.ai_provider,
        model=s.openai_model or None,
        mode=task_mode.value,
        locale=locale,
        prompt_logging=s.ai_log_prompts,
    )
    run_metadata["writing_preference"] = writing_preference
    run_metadata["omega_workspace_frame_id"] = str(frame.id)
    run_metadata["omega_scope_statement"] = frame.scope_statement
    model_run = ModelRun(
        owner_user_id=owner_user_id,
        request_id=request_id,
        orbit_id=orbit_id,
        provider=s.ai_provider,
        model=s.openai_model or None,
        mode=task_mode.value,
        status="RUNNING",
        input_event_id=turn.id,
        run_metadata=run_metadata,
        response_metadata={"available": False, "reason": "Provider response pending."},
        usage={},
        error={},
    )
    db.add(model_run)
    await db.flush()

    for ref in retrieval:
        db.add(
            ModelRunSource(
                owner_user_id=owner_user_id,
                model_run_id=model_run.id,
                source_kind=ref.kind,
                source_id=uuid.UUID(ref.id) if _is_uuid(ref.id) else None,
                excerpt=ref.excerpt,
                rank=ref.rank,
            )
        )

    if event_sink is not None:
        await event_sink(
            "talk.accepted",
            {
                "request_id": str(request_id) if request_id else None,
                "turn_event_id": str(turn.id),
                "model_run_id": str(model_run.id),
            },
        )

    result: AIProviderResult
    error: dict = {}
    provider_name = s.ai_provider
    try:
        provider = get_ai_provider()
        provider_name = provider.name
        result = await provider.complete_private_talk(
            TalkProviderRequest(
                user_line=user_line,
                orbit_id=str(orbit_id) if orbit_id else None,
                retrieval=retrieval,
                omega_context={
                    "workspace_frame_id": str(frame.id),
                    "scope_statement": frame.scope_statement,
                    "attention_items": frame.attention_items,
                    "risk_flags": frame.risk_flags,
                },
                locale=locale,
                writing_preference=writing_preference,
                mode=task_mode.value,
            ),
            event_sink=event_sink,
        )
    except asyncio.CancelledError:
        model_run.status = "CANCELLED"
        model_run.error = {"kind": "cancelled", "detail": "The owner cancelled this model run."}
        model_run.response_metadata = {"available": False, "reason": "Cancelled by owner."}
        await db.commit()
        if event_sink is not None:
            await event_sink(
                "talk.cancelled",
                {"request_id": str(request_id) if request_id else None, "model_run_id": str(model_run.id)},
            )
        raise
    except Exception as exc:
        error = safe_error_metadata(exc)
        result = AIProviderResult(
            provider=provider_name,
            model=s.openai_model or None,
            available=False,
            reason="AI provider failed closed; no model answer was trusted.",
            output=get_ai_provider_disabled_output(str(error["detail"])),
        )

    run_metadata = model_run_metadata(
        provider=result.provider,
        model=result.model,
        mode=task_mode.value,
        locale=locale,
        prompt_logging=s.ai_log_prompts,
    )
    run_metadata["writing_preference"] = writing_preference
    run_metadata["omega_workspace_frame_id"] = str(frame.id)
    run_metadata["omega_scope_statement"] = frame.scope_statement
    model_run.provider = result.provider
    model_run.model = result.model
    model_run.status = "COMPLETED" if not error else "ERROR"
    model_run.run_metadata = run_metadata
    model_run.response_metadata = {
        "available": result.available,
        "reason": result.reason,
        "raw_response_id": result.raw_response_id,
    }
    model_run.usage = result.usage
    model_run.error = error

    verification = verify_talk_output(result.output, evidence, provider_available=result.available)
    omega = await talk_summary(db, owner_user_id=owner_user_id, workspace_frame_id=frame.id)
    response_event = CognitiveEvent(
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        event_kind="MODEL_RESPONSE",
        content_text=result.output.direct_response,
        structured_payload={
            "talk_output": result.output.model_dump(),
            "provider": result.provider,
            "provider_available": result.available,
            "provider_reason": result.reason,
            "model_run_id": str(model_run.id),
            "verification": verification.model_dump(),
            "omega": omega.model_dump(mode="json"),
        },
        source_ref=f"model_run:{model_run.id}",
        parent_event_id=turn.id,
    )
    db.add(response_event)
    await db.flush()
    model_run.output_event_id = response_event.id
    await mark_frame_used(db, frame)

    await persist_model_evaluation(db, owner_user_id=owner_user_id, model_run_id=model_run.id, verification=verification)
    await persist_memory_candidates(
        db,
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        source_event_id=response_event.id,
        output=result.output,
    )
    await persist_predictions(
        db,
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        source_event_id=response_event.id,
        output=result.output,
    )

    if event_sink is not None:
        await event_sink(
            "talk.validated",
            {
                "request_id": str(request_id) if request_id else None,
                "model_run_id": str(model_run.id),
                "response_event_id": str(response_event.id),
                "schema_valid": True,
                "verification_verdict": verification.verdict,
            },
        )

    return TalkKernelResult(
        turn_event_id=turn.id,
        response_event_id=response_event.id,
        model_run_id=model_run.id,
        provider=result.provider,
        provider_available=result.available,
        provider_reason=result.reason,
        output=result.output,
        evidence=evidence,
        verification=verification,
        omega=omega,
        idempotent_replay=False,
    )


class TalkRunConflict(RuntimeError):
    pass


async def _replay_talk_result(db: AsyncSession, model_run: ModelRun) -> TalkKernelResult:
    if model_run.input_event_id is None or model_run.output_event_id is None:
        raise TalkRunConflict("The existing Talk request has no durable completed response.")
    response_event = (
        await db.execute(
            select(CognitiveEvent).where(
                CognitiveEvent.owner_user_id == model_run.owner_user_id,
                CognitiveEvent.id == model_run.output_event_id,
            )
        )
    ).scalar_one_or_none()
    if response_event is None:
        raise TalkRunConflict("The existing Talk response is no longer available.")
    sources = (
        await db.execute(
            select(ModelRunSource)
            .where(
                ModelRunSource.owner_user_id == model_run.owner_user_id,
                ModelRunSource.model_run_id == model_run.id,
            )
            .order_by(ModelRunSource.rank.desc(), ModelRunSource.created_at.asc())
        )
    ).scalars().all()
    payload = response_event.structured_payload or {}
    output = NURTalkOutput.model_validate(payload.get("talk_output") or {})
    verification = VerificationResult.model_validate(payload.get("verification") or {"verdict": "WARN", "checks": {}})
    omega_payload = payload.get("omega")
    omega = OmegaTalkSummary.model_validate(omega_payload) if omega_payload else None
    evidence = EvidencePacket(
        orbit_id=model_run.orbit_id,
        retrieval=[
            EvidenceRef(
                kind=row.source_kind,
                id=str(row.source_id or row.id),
                excerpt=row.excerpt or "",
                rank=row.rank,
            )
            for row in sources
        ],
    )
    return TalkKernelResult(
        turn_event_id=model_run.input_event_id,
        response_event_id=model_run.output_event_id,
        model_run_id=model_run.id,
        provider=str(payload.get("provider") or model_run.provider),
        provider_available=bool(payload.get("provider_available")),
        provider_reason=payload.get("provider_reason"),
        output=output,
        evidence=evidence,
        verification=verification,
        omega=omega,
        idempotent_replay=True,
    )


def get_ai_provider_disabled_output(reason: str):
    from app.cognition.response_composer import compose_disabled_output

    return compose_disabled_output(reason)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
