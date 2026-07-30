"""Authenticated operator diagnostics (G15).

A truthful, secret-free view of operational state for a signed-in operator. It is
separate from the public /healthz, /readyz and /metrics surfaces: those stay
dependency-light and public; this one requires a session and reports deeper
state. It never exposes secrets, credentials, private user content, or absolute
object-storage paths, and it never asserts provider authentication merely because
the provider mode is `openai`.
"""
import os
import time

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import Identity
from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.services.object_storage import bytes_stream, get_object_storage

router = APIRouter(prefix="/ops", tags=["ops"])
_BOOT = time.time()


def _provider_state(provider: str) -> str:
    # Configuration/mode only — authentication is proven only by a real provider
    # response, never by the configured mode.
    if provider == "openai":
        return "CONFIGURED_UNTESTED"
    return "DISABLED"


@router.get("/diagnostics")
async def diagnostics(identity: Identity) -> dict:
    settings = get_settings()
    checks: dict[str, str] = {}

    migration_revision = None
    try:
        async with get_sessionmaker()() as db:
            await db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        # Applied revision is best-effort: the runtime role may not be granted
        # SELECT on alembic_version. A restricted read leaves it null, not "error".
        try:
            async with get_sessionmaker()() as db:
                migration_revision = (
                    await db.execute(text("SELECT version_num FROM alembic_version"))
                ).scalar_one_or_none()
        except Exception:
            migration_revision = None
    except Exception:
        checks["database"] = "error"

    # Object store writability — a probe write proves the root is usable without
    # exposing the path. The probe is deleted immediately.
    object_store_writable = False
    try:
        storage = get_object_storage()
        probe = await storage.put(bytes_stream(b"ops-probe"), max_bytes=64)
        object_store_writable = storage.verify(probe.object_key, probe.checksum_sha256)
        storage.delete(probe.object_key)
        checks["object_store"] = "ok" if object_store_writable else "error"
    except Exception:
        checks["object_store"] = "error"

    return {
        "service": "nur-api",
        "version_sha": os.environ.get("NUR_GIT_SHA", "unknown"),
        "boot_epoch": int(_BOOT),
        "uptime_seconds": round(time.time() - _BOOT, 1),
        "app_env": settings.app_env,
        "migration_revision": migration_revision,
        "checks": checks,
        "provider_mode": settings.ai_provider,
        "provider_auth_state": _provider_state(settings.ai_provider),
        "object_store_writable": object_store_writable,
        "run_execution_inline": settings.project_run_inline,
        "budgets": {
            "ai_per_user_daily_limit": settings.ai_per_user_daily_limit,
            "ai_daily_budget_cents": settings.ai_daily_budget_cents,
            "project_upload_max_bytes": settings.project_upload_max_bytes,
            "project_run_timeout_seconds": settings.project_run_timeout_seconds,
        },
        "notes": [
            "provider_mode is configuration only; provider_auth_state is never PASS without a real provider response.",
            "no secrets, credentials, private content, or absolute paths are reported here.",
        ],
    }
