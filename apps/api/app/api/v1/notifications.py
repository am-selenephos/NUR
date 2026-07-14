import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import Identity, Scoped, require_csrf
from app.models import AuditEvent, Notification, NotificationPreference

router = APIRouter(prefix="/notifications", tags=["notifications"])
CATEGORIES = {"PROGRESS", "SOCIAL", "INTELLIGENCE", "PROJECT", "RECOVERY", "RESEARCH", "AGENT_RUN"}


class PreferenceIn(BaseModel):
    category_settings: dict = Field(default_factory=dict)
    frequency: str = "BALANCED"
    quiet_hours_start: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_hours_end: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    push_enabled: bool = False
    email_enabled: bool = False


class ReminderIn(BaseModel):
    category: str = "PROGRESS"
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=4000)
    route: str | None = Field(default=None, max_length=500)
    scheduled_at: dt.datetime | None = None
    is_demo: bool = False


def _preference(row: NotificationPreference) -> dict:
    return {
        "owner_user_id": row.owner_user_id, "category_settings": row.category_settings,
        "frequency": row.frequency, "quiet_hours_start": row.quiet_hours_start,
        "quiet_hours_end": row.quiet_hours_end, "push_enabled": row.push_enabled,
        "email_enabled": row.email_enabled, "updated_at": row.updated_at,
        "delivery_status": "IN_APP_ONLY" if not row.push_enabled else "PUSH_ARCHITECTURE_ONLY",
    }


def _notification(row: Notification) -> dict:
    return {
        "id": row.id, "category": row.category, "title": row.title, "body": row.body,
        "route": row.route, "source_type": row.source_type, "source_id": row.source_id,
        "provenance_label": row.provenance_label, "delivery_state": row.delivery_state,
        "is_demo": row.is_demo, "scheduled_at": row.scheduled_at, "read_at": row.read_at,
        "created_at": row.created_at,
    }


@router.get("/preferences")
async def preferences(db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    row = (await db.execute(select(NotificationPreference).where(NotificationPreference.owner_user_id == user_id))).scalar_one_or_none()
    if row is None:
        row = NotificationPreference(owner_user_id=user_id)
        db.add(row)
        await db.commit()
    return _preference(row)


@router.patch("/preferences", dependencies=[Depends(require_csrf)])
async def patch_preferences(payload: PreferenceIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    if payload.frequency not in {"QUIET", "BALANCED", "ACTIVE"}:
        raise HTTPException(422, "Unsupported notification frequency.")
    row = (await db.execute(select(NotificationPreference).where(NotificationPreference.owner_user_id == user_id))).scalar_one_or_none()
    if row is None:
        row = NotificationPreference(owner_user_id=user_id)
        db.add(row)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    row.updated_at = dt.datetime.now(dt.UTC)
    await db.commit()
    return _preference(row)


@router.get("")
async def list_notifications(db: Scoped, identity: Identity, unread_only: bool = False) -> list[dict]:
    user_id, _ = identity
    query = select(Notification).where(Notification.owner_user_id == user_id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    rows = (await db.execute(query.order_by(Notification.created_at.desc()).limit(100))).scalars().all()
    return [_notification(row) for row in rows]


@router.post("/reminders", status_code=201, dependencies=[Depends(require_csrf)])
async def create_reminder(payload: ReminderIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    category = payload.category.upper()
    if category not in CATEGORIES:
        raise HTTPException(422, "Unsupported notification category.")
    if payload.route and not payload.route.startswith("/"):
        raise HTTPException(422, "Reminder routes must stay inside NUR.")
    row = Notification(
        owner_user_id=user_id, category=category, title=payload.title, body=payload.body,
        route=payload.route, scheduled_at=payload.scheduled_at, is_demo=payload.is_demo,
    )
    db.add(row)
    await db.flush()
    db.add(AuditEvent(
        actor_user_id=user_id, event_type="NOTIFICATION_REMINDER_CREATED",
        object_type="notification", object_id=row.id,
        event_metadata={"category": category, "route": payload.route, "is_demo": payload.is_demo},
    ))
    await db.commit()
    return _notification(row)


@router.post("/{notification_id}/read", dependencies=[Depends(require_csrf)])
async def mark_read(notification_id: uuid.UUID, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    row = (await db.execute(select(Notification).where(
        Notification.id == notification_id, Notification.owner_user_id == user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Notification not found.")
    row.read_at = row.read_at or dt.datetime.now(dt.UTC)
    await db.commit()
    return _notification(row)
