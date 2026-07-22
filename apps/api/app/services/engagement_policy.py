import datetime as dt
import hashlib
import uuid
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    EngagementExperimentAssignment,
    EngagementExperimentDefinition,
    EngagementExperimentExposure,
    GlowQuest,
    GlowQuestDefinition,
    GlowStreak,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    Profile,
)
from app.models._mixins import now_utc


@dataclass(frozen=True)
class NotificationDecision:
    allowed: bool
    reason: str
    deliver_after: dt.datetime


def _aware(value: dt.datetime | None = None) -> dt.datetime:
    result = value or now_utc()
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Engagement policy timestamps must include a timezone.")
    return result.astimezone(dt.UTC)


def _zone(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(name or "UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def quiet_hours_end(
    instant: dt.datetime,
    timezone_name: str | None,
    start: str | None,
    end: str | None,
) -> dt.datetime | None:
    if not start or not end or start == end:
        return None
    instant = _aware(instant)
    zone = _zone(timezone_name)
    local = instant.astimezone(zone)
    start_time = dt.time.fromisoformat(start)
    end_time = dt.time.fromisoformat(end)
    local_time = local.timetz().replace(tzinfo=None)
    overnight = start_time > end_time
    inside = (
        local_time >= start_time or local_time < end_time
        if overnight
        else start_time <= local_time < end_time
    )
    if not inside:
        return None
    end_date = local.date()
    if overnight and local_time >= start_time:
        end_date += dt.timedelta(days=1)
    local_end = dt.datetime.combine(end_date, end_time, tzinfo=zone)
    return local_end.astimezone(dt.UTC)


async def notification_decision(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    category: str,
    occurred_at: dt.datetime | None = None,
) -> NotificationDecision:
    instant = _aware(occurred_at)
    preference = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.owner_user_id == owner_user_id
            )
        )
    ).scalar_one_or_none()
    if preference is None:
        return NotificationDecision(False, "NO_EXPLICIT_PREFERENCE", instant)
    if not preference.in_app_enabled:
        return NotificationDecision(False, "IN_APP_DISABLED", instant)
    if not bool((preference.category_settings or {}).get(category)):
        return NotificationDecision(False, "CATEGORY_NOT_OPTED_IN", instant)
    if preference.paused_until and preference.paused_until > instant:
        return NotificationDecision(False, "PAUSED", preference.paused_until)
    timezone_name = (
        await db.execute(select(Profile.timezone).where(Profile.user_id == owner_user_id))
    ).scalar_one_or_none()
    zone = _zone(timezone_name)
    local = instant.astimezone(zone)
    local_start = dt.datetime.combine(local.date(), dt.time.min, tzinfo=zone).astimezone(dt.UTC)
    local_end = (
        dt.datetime.combine(
            local.date() + dt.timedelta(days=1), dt.time.min, tzinfo=zone
        )
    ).astimezone(dt.UTC)
    delivered_today = int(
        (
            await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.owner_user_id == owner_user_id,
                    Notification.source_type != "OWNER_REMINDER",
                    Notification.created_at >= local_start,
                    Notification.created_at < local_end,
                )
            )
        ).scalar_one()
    )
    frequency_cap = {"QUIET": 1, "BALANCED": 2, "ACTIVE": 3}.get(
        preference.frequency, 2
    )
    cap = min(preference.max_daily, frequency_cap)
    if delivered_today >= cap:
        return NotificationDecision(False, "DAILY_FREQUENCY_CAP", instant)
    quiet_end = quiet_hours_end(
        instant,
        timezone_name,
        preference.quiet_hours_start,
        preference.quiet_hours_end,
    )
    if quiet_end:
        return NotificationDecision(True, "DEFERRED_QUIET_HOURS", quiet_end)
    return NotificationDecision(True, "ALLOWED", instant)


async def create_policy_notification(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    category: str,
    title: str,
    body: str,
    route: str,
    source_type: str,
    source_id: uuid.UUID,
    idempotency_key: str,
    occurred_at: dt.datetime | None = None,
) -> Notification | None:
    instant = _aware(occurred_at)
    existing = (
        await db.execute(
            select(Notification).where(
                Notification.owner_user_id == owner_user_id,
                Notification.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    decision = await notification_decision(
        db,
        owner_user_id=owner_user_id,
        category=category,
        occurred_at=instant,
    )
    if not decision.allowed:
        return None
    notification = Notification(
        owner_user_id=owner_user_id,
        category=category,
        title=title,
        body=body,
        route=route,
        source_type=source_type,
        source_id=source_id,
        idempotency_key=idempotency_key,
        provenance_label="SERVER_DERIVED",
        delivery_state=(
            "SCHEDULED" if decision.deliver_after > instant else "IN_APP"
        ),
        scheduled_at=decision.deliver_after,
        created_at=instant,
    )
    db.add(notification)
    await db.flush()
    db.add(
        NotificationDelivery(
            owner_user_id=owner_user_id,
            notification_id=notification.id,
            channel="IN_APP",
            status="PENDING" if decision.deliver_after > instant else "DELIVERED",
            idempotency_key=f"{idempotency_key}:in-app",
            attempt_count=1,
            deliver_after=decision.deliver_after,
            delivered_at=None if decision.deliver_after > instant else instant,
        )
    )
    return notification


async def engagement_cue(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    occurred_at: dt.datetime | None = None,
) -> dict:
    instant = _aware(occurred_at)
    preference = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.owner_user_id == owner_user_id
            )
        )
    ).scalar_one_or_none()
    if preference and preference.paused_until and preference.paused_until > instant:
        return {"kind": "NO_INTERVENTION", "reason": "PAUSED"}
    quest = (
        await db.execute(
            select(GlowQuest, GlowQuestDefinition)
            .join(GlowQuestDefinition, GlowQuestDefinition.id == GlowQuest.template_id)
            .where(
                GlowQuest.owner_user_id == owner_user_id,
                GlowQuest.status == "COMPLETED",
                GlowQuest.period_end > instant,
            )
            .order_by(GlowQuest.period_end)
            .limit(1)
        )
    ).first()
    if quest:
        row, definition = quest
        return {
            "kind": "CLAIM_QUEST",
            "quest_id": str(row.id),
            "title": definition.title,
            "route": "/today",
            "provenance_label": "PERSISTED_QUEST_PROGRESS",
        }
    streak = (
        await db.execute(
            select(GlowStreak)
            .where(
                GlowStreak.owner_user_id == owner_user_id,
                GlowStreak.grace_until.is_not(None),
                GlowStreak.grace_until > instant,
            )
            .order_by(GlowStreak.grace_until)
            .limit(1)
        )
    ).scalar_one_or_none()
    if streak and streak.grace_until - instant <= dt.timedelta(hours=6):
        return {
            "kind": "STREAK_RESCUE",
            "streak_id": str(streak.id),
            "title": "Return gently before this continuity window closes.",
            "route": "/today",
            "provenance_label": "PERSISTED_STREAK_STATE",
        }
    active = (
        await db.execute(
            select(GlowQuest, GlowQuestDefinition)
            .join(GlowQuestDefinition, GlowQuestDefinition.id == GlowQuest.template_id)
            .where(
                GlowQuest.owner_user_id == owner_user_id,
                GlowQuest.status == "ACTIVE",
                GlowQuest.period_end > instant,
            )
            .order_by(GlowQuest.period_end)
            .limit(1)
        )
    ).first()
    if active:
        row, definition = active
        return {
            "kind": "NEXT_MOVEMENT",
            "quest_id": str(row.id),
            "title": definition.title,
            "route": "/today",
            "provenance_label": "PERSISTED_QUEST_ASSIGNMENT",
        }
    return {"kind": "NO_INTERVENTION", "reason": "NO_VERIFIED_CUE"}


async def assign_experiment(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    experiment_key: str,
    eligible: bool,
) -> EngagementExperimentAssignment | None:
    if not eligible:
        return None
    definition = (
        await db.execute(
            select(EngagementExperimentDefinition).where(
                EngagementExperimentDefinition.experiment_key == experiment_key,
                EngagementExperimentDefinition.status == "ACTIVE",
            )
        )
    ).scalar_one_or_none()
    if definition is None:
        return None
    existing = (
        await db.execute(
            select(EngagementExperimentAssignment).where(
                EngagementExperimentAssignment.owner_user_id == owner_user_id,
                EngagementExperimentAssignment.experiment_key == experiment_key,
                EngagementExperimentAssignment.experiment_version == definition.version,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    digest = hashlib.sha256(
        f"{owner_user_id}:{experiment_key}:{definition.version}".encode("ascii")
    ).hexdigest()
    variants = [str(item) for item in definition.variants]
    variant = variants[int(digest[:8], 16) % len(variants)]
    row = EngagementExperimentAssignment(
        owner_user_id=owner_user_id,
        experiment_key=experiment_key,
        experiment_version=definition.version,
        variant=variant,
        assignment_digest=digest,
    )
    db.add(row)
    await db.flush()
    return row


async def record_exposure(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    assignment_id: uuid.UUID,
    surface: str,
    idempotency_key: str,
) -> EngagementExperimentExposure:
    existing = (
        await db.execute(
            select(EngagementExperimentExposure).where(
                EngagementExperimentExposure.owner_user_id == owner_user_id,
                EngagementExperimentExposure.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    assignment = (
        await db.execute(
            select(EngagementExperimentAssignment).where(
                EngagementExperimentAssignment.id == assignment_id,
                EngagementExperimentAssignment.owner_user_id == owner_user_id,
            )
        )
    ).scalar_one_or_none()
    if assignment is None:
        raise PermissionError("Experiment assignment is not owned by this user.")
    row = EngagementExperimentExposure(
        owner_user_id=owner_user_id,
        assignment_id=assignment.id,
        surface=surface,
        idempotency_key=idempotency_key,
        exposure_metadata={"contains_private_text": False},
    )
    db.add(row)
    await db.flush()
    return row
