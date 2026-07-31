import time

from fastapi import APIRouter, Request, Response
from sqlalchemy import text

from app.db.session import get_sessionmaker
from app.core.config import get_settings
from app.observability.metrics import format_labelset

router = APIRouter(tags=["ops"])
_START = time.time()


@router.get("/healthz")
async def healthz():
    s = get_settings()
    return {"status": "healthy", "ai_provider": s.ai_provider}


@router.get("/readyz")
async def readyz(request: Request, response: Response):
    # During graceful shutdown the lifespan flips readiness off before releasing
    # resources; report draining (503) so drainers stop routing new traffic here
    # even while the database and Redis are still momentarily healthy.
    if not getattr(request.app.state, "ready", True):
        response.status_code = 503
        return {"status": "draining", "checks": {"lifecycle": "draining"}}
    checks: dict[str, str] = {}
    try:
        async with get_sessionmaker()() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    try:
        pong = await request.app.state.redis.ping()
        checks["redis"] = "ok" if pong else "error"
    except Exception:
        checks["redis"] = "error"
    ready = all(v == "ok" for v in checks.values())
    response.status_code = 200 if ready else 503
    return {"status": "ready" if ready else "not_ready", "checks": checks}


@router.get("/metrics")
async def metrics(request: Request):
    """Minimal Prometheus text exposition — honest, hand-rolled, no fake gauges."""
    counters: dict = request.app.state.request_counters
    s = get_settings()
    lines = [
        "# HELP nur_uptime_seconds Seconds since process start.",
        "# TYPE nur_uptime_seconds gauge",
        f"nur_uptime_seconds {time.time() - _START:.1f}",
        "# HELP nur_ai_provider_configured Configured server AI provider, without secrets.",
        "# TYPE nur_ai_provider_configured gauge",
        f'nur_ai_provider_configured{{provider="{s.ai_provider}"}} 1',
        "# HELP nur_http_requests_total HTTP requests by method, route, status.",
        "# TYPE nur_http_requests_total counter",
    ]
    for (method, route, status), n in sorted(counters.items()):
        lines.append(f'nur_http_requests_total{{method="{method}",route="{route}",status="{status}"}} {n}')
    domain_counters = getattr(request.app.state, "domain_counters", {})
    if domain_counters:
        lines.extend([
            "# HELP nur_domain_events_total Domain events observed by the API process.",
            "# TYPE nur_domain_events_total counter",
        ])
    for (name, labels), n in sorted(domain_counters.items()):
        lines.append(f"{name}{format_labelset(labels)} {n}")
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
