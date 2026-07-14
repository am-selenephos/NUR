from celery import Celery

from app.core.config import get_settings

_s = get_settings()

celery = Celery(
    "nur",
    broker=_s.redis_url,
    backend=_s.redis_url,
    include=["app.workers.tasks"],
)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_hijack_root_logger=False,
    task_default_queue="nur_default",
    # Job payloads carry IDs only — never private raw text (constitution §17/§20).
)

if _s.omega_scheduled_consolidation:
    celery.conf.beat_schedule = {
        "nur-omega-consolidate-due-owners": {
            "task": "nur.omega_consolidate_due_owners",
            "schedule": max(3600, int(_s.omega_consolidation_interval_hours) * 3600),
            "args": (),
        }
    }
