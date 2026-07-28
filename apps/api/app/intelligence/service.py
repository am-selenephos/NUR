import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.intelligence.evaluation import run_intelligence_evaluation
from app.intelligence.schemas import IntelligenceProviderStatus, ProviderLastRun
from app.models import ModelEvaluation, ModelRun
from app.services import audit_service
from app.services.domain_event_service import emit_domain_event


async def provider_status(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
) -> IntelligenceProviderStatus:
    settings = get_settings()
    last_run = (
        await db.execute(
            select(ModelRun)
            .where(ModelRun.owner_user_id == owner_user_id)
            .order_by(ModelRun.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    last_run_out = None
    if last_run:
        error = last_run.error or {}
        last_run_out = ProviderLastRun(
            id=last_run.id,
            provider=last_run.provider,
            model=last_run.model,
            status=last_run.status,
            error_code=str(error.get("code") or error.get("kind")) if error else None,
            created_at=last_run.created_at,
        )
    configured = settings.ai_provider == "openai"
    return IntelligenceProviderStatus(
        provider=settings.ai_provider,
        configuration_status="CONFIGURED" if configured else "DISABLED",
        configured=configured,
        model=settings.openai_model or None,
        credential_state=(
            "PRESENT_SERVER_SIDE" if configured else "NOT_CONFIGURED"
        ),
        semantic_streaming=configured,
        external_web_research=settings.ai_allow_external_web_research,
        live_probe_status="OWNER_RUN_RECORDED" if last_run else "NOT_RUN",
        release_proof=(
            "EXTERNAL_GATE_REQUIRED" if configured else "FOUNDER_KEY_REQUIRED"
        ),
        last_owner_run=last_run_out,
    )


async def evaluate_intelligence(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    suites: list[str],
) -> tuple[ModelEvaluation, dict]:
    result = run_intelligence_evaluation(suites)
    row = ModelEvaluation(
        owner_user_id=owner_user_id,
        model_run_id=None,
        verdict=result["verdict"],
        checks={
            "evaluation_kind": "INTELLIGENCE_SPINE",
            **result,
        },
    )
    db.add(row)
    await db.flush()
    await audit_service.record(
        db,
        event_type="INTELLIGENCE_EVALUATED",
        object_type="model_evaluation",
        actor_user_id=owner_user_id,
        object_id=row.id,
        metadata={
            "verdict": result["verdict"],
            "suite_version": result["suite_version"],
            "case_count": result["case_count"],
            "critical_failure_count": len(result["critical_failures"]),
        },
    )
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="intelligence.evaluation.completed",
        aggregate_type="model_evaluation",
        aggregate_id=row.id,
        idempotency_key=f"intelligence-evaluation:{row.id}",
        payload={
            "verdict": result["verdict"],
            "suite_version": result["suite_version"],
            "case_count": result["case_count"],
            "critical_failure_count": len(result["critical_failures"]),
        },
    )
    return row, result
