import datetime as dt
import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import exists, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AMProject,
    AMProjectEvidence,
    AMProjectTask,
    CognitiveEvent,
    CommunityComment,
    CommunityMessage,
    CommunityPost,
    Consultation,
    CouncilDecision,
    CouncilPosition,
    FeasibilityAssessment,
    GlowAchievement,
    GlowAchievementDefinition,
    GlowAchievementEvent,
    GlowBalance,
    GlowFraudFlag,
    GlowLevelDefinition,
    GlowLevelEvent,
    GlowQuest,
    GlowQuestDefinition,
    GlowReversal,
    GlowRewardDefinition,
    GlowRewardEvent,
    GlowRewardRedemption,
    GlowRule,
    GlowSourceClaim,
    GlowStreak,
    GlowStreakDefinition,
    GlowStreakEvent,
    GlowStreakRepair,
    GlowTransaction,
    GlowUserLevel,
    Goal,
    JournalEntry,
    Objective,
    Outcome,
    Plan,
    PlanStep,
    Profile,
    ScheduledAction,
    SystemAction,
    SystemDiagnostic,
    TodayCheckIn,
)
from app.models._mixins import now_utc
from app.services.domain_event_service import emit_domain_event


SOURCE_EVENT_TYPES = {
    "daily_checkin": "today.checkin.completed.v1",
    "talk_meaningful": "talk.meaningful.completed.v1",
    "journal_saved": "journal.saved.v1",
    "plan_created": "plan.created.v1",
    "plan_step_completed": "plan.step.completed.v1",
    "task_made_smaller": "plan.step.made_smaller.v1",
    "outcome_returned": "return.recorded.v1",
    "goal.created": "goal.created.v1",
    "objective.created": "objective.created.v1",
    "schedule.created": "schedule.created.v1",
    "system.checklist_answered": "system.diagnostic.completed.v1",
    "system.action_marked": "system.action.completed.v1",
    "missed_step_returned": "system.action.returned.v1",
    "feasibility.created": "feasibility.completed.v1",
    "project.created": "project.created.v1",
    "project.task_completed": "project.task.completed.v1",
    "project.evidence_verified": "project.evidence.verified.v1",
    "community.message_posted": "community.message.created.v1",
    "community.post_created": "community.post.created.v1",
    "community.comment_created": "community.comment.created.v1",
    "council.position_added": "council.position.created.v1",
    "council.decision_recorded": "council.decision.recorded.v1",
    "consultation_return": "consultation.return.completed.v1",
    "quest.daily_claimed": "quest.daily.claimed.v1",
    "quest.weekly_claimed": "quest.weekly.claimed.v1",
}


@dataclass(frozen=True)
class CalendarWindow:
    timezone: str
    local_key: str
    local_date: dt.date
    start: dt.datetime
    end: dt.datetime


@dataclass
class AwardResult:
    transaction: GlowTransaction
    balance: GlowBalance
    streak: GlowStreak | None
    idempotent_replay: bool
    achievements: list[GlowAchievement]


@dataclass
class ReversalResult:
    reversal: GlowReversal
    balance: GlowBalance
    idempotent_replay: bool


@dataclass
class RepairResult:
    repair: GlowStreakRepair
    streak: GlowStreak
    balance: GlowBalance
    idempotent_replay: bool


@dataclass
class RedemptionResult:
    redemption: GlowRewardRedemption
    balance: GlowBalance
    idempotent_replay: bool


def _aware(value: dt.datetime | None = None) -> dt.datetime:
    result = value or now_utc()
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Glow event timestamps must include a timezone.")
    return result.astimezone(dt.UTC)


def _zone(timezone_name: str | None) -> tuple[str, ZoneInfo]:
    name = timezone_name or "UTC"
    try:
        return name, ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return "UTC", ZoneInfo("UTC")


def calendar_window(
    instant: dt.datetime,
    timezone_name: str | None,
    cadence: str,
) -> CalendarWindow:
    instant = _aware(instant)
    name, zone = _zone(timezone_name)
    local = instant.astimezone(zone)
    if cadence == "DAILY":
        start_date = local.date()
        end_date = start_date + dt.timedelta(days=1)
        local_key = start_date.isoformat()
    elif cadence == "WEEKLY":
        start_date = local.date() - dt.timedelta(days=local.weekday())
        end_date = start_date + dt.timedelta(days=7)
        local_key = f"{start_date.isoformat()}/W"
    else:
        raise ValueError("cadence must be DAILY or WEEKLY")
    local_start = dt.datetime.combine(start_date, dt.time.min, tzinfo=zone)
    local_end = dt.datetime.combine(end_date, dt.time.min, tzinfo=zone)
    return CalendarWindow(
        timezone=name,
        local_key=local_key,
        local_date=local.date(),
        start=local_start.astimezone(dt.UTC),
        end=local_end.astimezone(dt.UTC),
    )


async def _owner_timezone(db: AsyncSession, owner_user_id: uuid.UUID) -> str:
    timezone_name = (
        await db.execute(select(Profile.timezone).where(Profile.user_id == owner_user_id))
    ).scalar_one_or_none()
    return _zone(timezone_name)[0]


async def _lock_owner(db: AsyncSession, owner_user_id: uuid.UUID) -> None:
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
        {"lock_key": f"glow:{owner_user_id}"},
    )


def _not_reversed(transaction_id) -> object:
    return ~exists(select(GlowReversal.id).where(GlowReversal.transaction_id == transaction_id))


async def _owned_source(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    source_kind: str,
    source_id: uuid.UUID,
):
    models = {
        "COGNITIVE_EVENT": CognitiveEvent,
        "JOURNAL_ENTRY": JournalEntry,
        "PLAN": Plan,
        "PLAN_STEP": PlanStep,
        "OUTCOME": Outcome,
        "GOAL": Goal,
        "OBJECTIVE": Objective,
        "SCHEDULED_ACTION": ScheduledAction,
        "SYSTEM_DIAGNOSTIC": SystemDiagnostic,
        "SYSTEM_ACTION": SystemAction,
        "FEASIBILITY": FeasibilityAssessment,
        "AM_PROJECT": AMProject,
        "AM_PROJECT_TASK": AMProjectTask,
        "AM_PROJECT_EVIDENCE": AMProjectEvidence,
        "COMMUNITY_MESSAGE": CommunityMessage,
        "COMMUNITY_POST": CommunityPost,
        "COMMUNITY_COMMENT": CommunityComment,
        "COUNCIL_POSITION": CouncilPosition,
        "COUNCIL_DECISION": CouncilDecision,
        "CONSULTATION": Consultation,
        "GLOW_QUEST": GlowQuest,
    }
    model = models.get(source_kind)
    if model is None:
        raise HTTPException(422, "Unsupported Glow source kind.")
    row = (
        await db.execute(
            select(model).where(
                model.id == source_id,
                model.owner_user_id == owner_user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Glow source not found.")
    return row


async def _validate_event_source(
    db: AsyncSession,
    *,
    event_type: str,
    source_kind: str,
    source,
) -> None:
    expected = {
        "daily_checkin": "COGNITIVE_EVENT",
        "talk_meaningful": "COGNITIVE_EVENT",
        "journal_saved": "JOURNAL_ENTRY",
        "plan_created": "PLAN",
        "plan_step_completed": "PLAN_STEP",
        "task_made_smaller": "PLAN_STEP",
        "outcome_returned": "OUTCOME",
        "goal.created": "GOAL",
        "objective.created": "OBJECTIVE",
        "schedule.created": "SCHEDULED_ACTION",
        "system.checklist_answered": "SYSTEM_DIAGNOSTIC",
        "system.action_marked": "SYSTEM_ACTION",
        "missed_step_returned": "SYSTEM_ACTION",
        "feasibility.created": "FEASIBILITY",
        "project.created": "AM_PROJECT",
        "project.task_completed": "AM_PROJECT_TASK",
        "project.evidence_verified": "AM_PROJECT_EVIDENCE",
        "community.message_posted": "COMMUNITY_MESSAGE",
        "community.post_created": "COMMUNITY_POST",
        "community.comment_created": "COMMUNITY_COMMENT",
        "council.position_added": "COUNCIL_POSITION",
        "council.decision_recorded": "COUNCIL_DECISION",
        "consultation_return": "CONSULTATION",
        "quest.daily_claimed": "GLOW_QUEST",
        "quest.weekly_claimed": "GLOW_QUEST",
    }
    if expected.get(event_type) != source_kind:
        raise HTTPException(422, "Glow event does not match its source kind.")
    if source_kind.startswith(("COMMUNITY_", "COUNCIL_")) and getattr(source, "is_demo", False):
        raise HTTPException(409, "DEMO-marked community content never earns Glow.")
    if event_type == "daily_checkin":
        payload = source.structured_payload or {}
        if source.event_kind != "SYSTEM_EVENT" or payload.get("type") != "today_checkin":
            raise HTTPException(409, "Daily check-in Glow requires a persisted check-in event.")
    if event_type == "talk_meaningful" and source.event_kind != "TALK_TURN":
        raise HTTPException(409, "Talk Glow requires a persisted Talk turn.")
    if event_type == "plan_step_completed" and not source.done:
        raise HTTPException(409, "Plan step Glow requires a completed step.")
    if event_type == "task_made_smaller" and not (source.body or "").strip():
        raise HTTPException(409, "A smaller task requires a persisted replacement description.")
    if event_type == "system.action_marked" and source.status != "COMPLETED":
        raise HTTPException(409, "System action Glow requires a completed action.")
    if event_type == "missed_step_returned":
        returned = (source.action_metadata or {}).get("returned_from_missed")
        if source.status != "COMPLETED" or not returned:
            raise HTTPException(409, "Return Glow requires a completed action that was previously missed.")
    if event_type == "project.task_completed" and source.status != "DONE":
        raise HTTPException(409, "Project task Glow requires a completed task.")
    if event_type == "project.evidence_verified" and source.verification_status != "PASSED":
        raise HTTPException(409, "Project evidence Glow requires PASSED verification.")
    if event_type == "consultation_return":
        if source.status != "COMPLETED" or source.current_stage != "RETURN":
            raise HTTPException(409, "Consultation Glow requires a persisted RETURN stage.")
        if source.is_demo:
            raise HTTPException(409, "DEMO Consultations never earn Glow.")
    if source_kind == "GLOW_QUEST":
        if source.status not in {"COMPLETED", "CLAIMED"}:
            raise HTTPException(409, "Quest Glow requires completed persisted progress.")
        cadence = (
            await db.execute(
                select(GlowQuestDefinition.cadence).where(
                    GlowQuestDefinition.id == source.template_id
                )
            )
        ).scalar_one()
        expected_event = "quest.daily_claimed" if cadence == "DAILY" else "quest.weekly_claimed"
        if event_type != expected_event:
            raise HTTPException(409, "Quest cadence does not match its reward rule.")


async def _source_domain_event(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    event_type: str,
    source_kind: str,
    source_id: uuid.UUID,
    system_slug: str | None,
) -> object:
    domain_type = SOURCE_EVENT_TYPES.get(event_type)
    if domain_type is None:
        raise HTTPException(422, "Glow rule has no server event contract.")
    payload = {"glow_event_type": event_type, "source_kind": source_kind}
    if system_slug:
        payload["system_slug"] = system_slug
    return await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type=domain_type,
        aggregate_type=source_kind.lower(),
        aggregate_id=source_id,
        idempotency_key=f"glow-source:{event_type}:{source_id}",
        payload=payload,
    )


async def _balance_for_update(
    db: AsyncSession,
    owner_user_id: uuid.UUID,
) -> GlowBalance:
    row = (
        await db.execute(
            select(GlowBalance)
            .where(GlowBalance.owner_user_id == owner_user_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        row = GlowBalance(owner_user_id=owner_user_id)
        db.add(row)
        await db.flush()
    return row


async def _record_fraud_flag(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    source_kind: str,
    source_id: uuid.UUID,
    signal_type: str,
    idempotency_key: str,
    metadata: dict,
) -> None:
    existing = (
        await db.execute(
            select(GlowFraudFlag.id).where(
                GlowFraudFlag.owner_user_id == owner_user_id,
                GlowFraudFlag.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            GlowFraudFlag(
                owner_user_id=owner_user_id,
                source_kind=source_kind,
                source_id=source_id,
                signal_type=signal_type,
                severity="MEDIUM",
                idempotency_key=idempotency_key,
                signal_metadata=metadata,
            )
        )
        await db.flush()


def _derived_system_slug(
    source,
    structured: dict,
    rule: GlowRule,
) -> str | None:
    return getattr(source, "system_slug", None) or structured.get("system_slug") or rule.system_slug


async def _resolve_system_slug(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    source,
    rule: GlowRule,
) -> str | None:
    structured = getattr(source, "structured_payload", {}) or {}
    derived = _derived_system_slug(source, structured, rule)
    if isinstance(source, Objective):
        derived = (
            await db.execute(
                select(Goal.system_slug).where(
                    Goal.id == source.goal_id,
                    Goal.owner_user_id == owner_user_id,
                )
            )
        ).scalar_one_or_none()
    if isinstance(source, (AMProjectTask, AMProjectEvidence)):
        project = (
            await db.execute(
                select(AMProject).where(
                    AMProject.id == source.project_id,
                    AMProject.owner_user_id == owner_user_id,
                )
            )
        ).scalar_one_or_none()
        if project is not None:
            derived = project.system_slug
    return derived


async def _update_streak(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    streak_key: str | None,
    transaction: GlowTransaction,
    occurred_at: dt.datetime,
    timezone_name: str,
) -> GlowStreak | None:
    if not streak_key:
        return None
    definition = (
        await db.execute(
            select(GlowStreakDefinition).where(
                GlowStreakDefinition.streak_key == streak_key,
                GlowStreakDefinition.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if definition is None:
        raise HTTPException(500, "Active Glow rule has no streak definition.")
    name, zone = _zone(timezone_name)
    actual_date = occurred_at.astimezone(zone).date()
    row = (
        await db.execute(
            select(GlowStreak)
            .where(
                GlowStreak.owner_user_id == owner_user_id,
                GlowStreak.streak_key == streak_key,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    credited_date = actual_date
    state_reason = "VERIFIED_EVENT"
    if row is None:
        row = GlowStreak(
            owner_user_id=owner_user_id,
            streak_key=streak_key,
            current_count=1,
            best_count=1,
            last_event_date=actual_date,
            last_event_at=occurred_at,
            timezone=name,
            checkpoint_count=0,
            next_reward_at=definition.checkpoint_interval,
        )
        db.add(row)
        await db.flush()
    elif row.last_event_date is None:
        row.current_count = 1
        row.best_count = max(row.best_count, 1)
        row.last_event_date = actual_date
    elif actual_date <= row.last_event_date:
        credited_date = row.last_event_date
        state_reason = "SAME_LOCAL_DAY"
    else:
        delta = (actual_date - row.last_event_date).days
        grace_deadline = dt.datetime.combine(
            row.last_event_date + dt.timedelta(days=2),
            dt.time.min,
            tzinfo=zone,
        ) + dt.timedelta(hours=definition.grace_hours)
        if delta == 1:
            row.current_count += 1
        elif delta == 2 and occurred_at <= grace_deadline.astimezone(dt.UTC):
            credited_date = row.last_event_date + dt.timedelta(days=1)
            row.current_count += 1
            state_reason = "GRACE_WINDOW"
        else:
            row.current_count = 1
            state_reason = "GAP_RESET"
        row.best_count = max(row.best_count, row.current_count)
        row.last_event_date = credited_date
    row.last_event_at = max(row.last_event_at or occurred_at, occurred_at)
    row.timezone = name
    row.state_reason = state_reason
    row.checkpoint_count = row.current_count // definition.checkpoint_interval
    row.next_reward_at = (row.checkpoint_count + 1) * definition.checkpoint_interval
    row.grace_until = (
        dt.datetime.combine(
            (row.last_event_date or actual_date) + dt.timedelta(days=2),
            dt.time.min,
            tzinfo=zone,
        )
        + dt.timedelta(hours=definition.grace_hours)
    ).astimezone(dt.UTC)
    row.updated_at = now_utc()
    db.add(
        GlowStreakEvent(
            owner_user_id=owner_user_id,
            streak_id=row.id,
            transaction_id=transaction.id,
            event_kind="AWARDED",
            local_date=credited_date,
            timezone=name,
            idempotency_key=f"streak-award:{transaction.id}",
            event_metadata={"state_reason": state_reason, "actual_local_date": actual_date.isoformat()},
            occurred_at=occurred_at,
        )
    )
    await db.flush()
    return row


async def _sync_level(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    lifetime_points: int,
    source_transaction_id: uuid.UUID | None = None,
    source_reversal_id: uuid.UUID | None = None,
) -> tuple[GlowUserLevel, bool]:
    definition = (
        await db.execute(
            select(GlowLevelDefinition)
            .where(
                GlowLevelDefinition.active.is_(True),
                GlowLevelDefinition.threshold <= lifetime_points,
            )
            .order_by(GlowLevelDefinition.threshold.desc())
            .limit(1)
        )
    ).scalar_one()
    row = (
        await db.execute(
            select(GlowUserLevel)
            .where(GlowUserLevel.owner_user_id == owner_user_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    previous_level = row.level if row else None
    if row is None:
        row = GlowUserLevel(
            owner_user_id=owner_user_id,
            level=definition.level,
            lifetime_points=lifetime_points,
        )
        db.add(row)
        changed = definition.level > 1
    else:
        changed = row.level != definition.level
        row.level = definition.level
        row.lifetime_points = lifetime_points
        row.updated_at = now_utc()
        if changed and definition.level > (previous_level or 1):
            row.reached_at = now_utc()
    if changed:
        direction = "REACHED" if definition.level > (previous_level or 1) else "REVERSED"
        source_key = source_transaction_id or source_reversal_id
        db.add(
            GlowLevelEvent(
                owner_user_id=owner_user_id,
                level=definition.level,
                event_kind=direction,
                source_transaction_id=source_transaction_id,
                source_reversal_id=source_reversal_id,
                idempotency_key=f"level:{direction.lower()}:{definition.level}:{source_key}",
            )
        )
    await db.flush()
    return row, changed


async def _sync_achievements(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    lifetime_points: int,
    source_transaction_id: uuid.UUID | None = None,
    source_reversal_id: uuid.UUID | None = None,
) -> list[GlowAchievement]:
    definitions = (
        await db.execute(
            select(GlowAchievementDefinition)
            .where(GlowAchievementDefinition.active.is_(True))
            .order_by(GlowAchievementDefinition.threshold)
        )
    ).scalars().all()
    existing = {
        row.achievement_key: row
        for row in (
            await db.execute(
                select(GlowAchievement).where(
                    GlowAchievement.owner_user_id == owner_user_id
                )
            )
        ).scalars().all()
    }
    newly_active: list[GlowAchievement] = []
    for definition in definitions:
        row = existing.get(definition.achievement_key)
        eligible = lifetime_points >= definition.threshold
        if eligible and row is None:
            if source_transaction_id is None:
                continue
            row = GlowAchievement(
                owner_user_id=owner_user_id,
                achievement_key=definition.achievement_key,
                source_transaction_id=source_transaction_id,
                achievement_metadata={
                    "threshold": definition.threshold,
                    "label": definition.title,
                    "rule_version": definition.rule_version,
                },
            )
            db.add(row)
            db.add(
                GlowAchievementEvent(
                    owner_user_id=owner_user_id,
                    achievement_key=definition.achievement_key,
                    event_kind="UNLOCKED",
                    source_transaction_id=source_transaction_id,
                    idempotency_key=(
                        f"achievement:unlocked:{definition.achievement_key}:"
                        f"{source_transaction_id}"
                    ),
                )
            )
            newly_active.append(row)
        elif eligible and row is not None and row.revoked_at is not None:
            row.revoked_at = None
            row.revocation_reason = None
            if source_transaction_id is not None:
                row.source_transaction_id = source_transaction_id
                db.add(
                    GlowAchievementEvent(
                        owner_user_id=owner_user_id,
                        achievement_key=definition.achievement_key,
                        event_kind="RESTORED",
                        source_transaction_id=source_transaction_id,
                        idempotency_key=(
                            f"achievement:restored:{definition.achievement_key}:"
                            f"{source_transaction_id}"
                        ),
                    )
                )
                newly_active.append(row)
        elif (
            not eligible
            and row is not None
            and row.revoked_at is None
            and definition.reversible
            and source_reversal_id is not None
        ):
            row.revoked_at = now_utc()
            row.revocation_reason = "Underlying verified Glow was reversed."
            db.add(
                GlowAchievementEvent(
                    owner_user_id=owner_user_id,
                    achievement_key=definition.achievement_key,
                    event_kind="REVOKED",
                    source_reversal_id=source_reversal_id,
                    idempotency_key=(
                        f"achievement:revoked:{definition.achievement_key}:"
                        f"{source_reversal_id}"
                    ),
                )
            )
    if newly_active or source_reversal_id:
        await db.flush()
    return newly_active


async def award_glow(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    event_type: str,
    source_kind: str,
    source_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    idempotency_key: str,
    occurred_at: dt.datetime | None = None,
    system_slug_override: str | None = None,
) -> AwardResult:
    event_time = _aware(occurred_at)
    await _lock_owner(db, owner_user_id)
    replay = (
        await db.execute(
            select(GlowTransaction).where(
                GlowTransaction.owner_user_id == owner_user_id,
                GlowTransaction.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if replay is None:
        claim = (
            await db.execute(
                select(GlowSourceClaim).where(
                    GlowSourceClaim.owner_user_id == owner_user_id,
                    GlowSourceClaim.event_type == event_type,
                    GlowSourceClaim.source_kind == source_kind,
                    GlowSourceClaim.source_id == source_id,
                )
            )
        ).scalar_one_or_none()
        if claim is not None:
            replay = (
                await db.execute(
                    select(GlowTransaction).where(
                        GlowTransaction.id == claim.transaction_id,
                        GlowTransaction.owner_user_id == owner_user_id,
                    )
                )
            ).scalar_one()
            await _record_fraud_flag(
                db,
                owner_user_id=owner_user_id,
                source_kind=source_kind,
                source_id=source_id,
                signal_type="SOURCE_REPLAY_DIFFERENT_KEY",
                idempotency_key=f"source-replay:{event_type}:{source_id}:{idempotency_key}",
                metadata={"event_type": event_type},
            )
    if replay is not None:
        balance = await _balance_for_update(db, owner_user_id)
        rule = (
            await db.execute(
                select(GlowRule).where(GlowRule.event_type == replay.event_type)
            )
        ).scalar_one()
        streak = None
        if rule.streak_key:
            streak = (
                await db.execute(
                    select(GlowStreak).where(
                        GlowStreak.owner_user_id == owner_user_id,
                        GlowStreak.streak_key == rule.streak_key,
                    )
                )
            ).scalar_one_or_none()
        return AwardResult(replay, balance, streak, True, [])

    rule = (
        await db.execute(
            select(GlowRule).where(
                GlowRule.event_type == event_type,
                GlowRule.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if rule is None:
        raise HTTPException(422, "Unknown or inactive Glow event.")
    source = await _owned_source(
        db,
        owner_user_id=owner_user_id,
        source_kind=source_kind,
        source_id=source_id,
    )
    await _validate_event_source(
        db,
        event_type=event_type,
        source_kind=source_kind,
        source=source,
    )
    if orbit_id is not None:
        source_orbit = getattr(source, "orbit_id", None)
        if source_orbit is not None and source_orbit != orbit_id:
            raise HTTPException(409, "Glow Orbit does not match its source.")

    timezone_name = await _owner_timezone(db, owner_user_id)
    day = calendar_window(event_time, timezone_name, "DAILY")
    week = calendar_window(event_time, timezone_name, "WEEKLY")
    if rule.spam_window_seconds:
        spam_start = event_time - dt.timedelta(seconds=rule.spam_window_seconds)
        recent = (
            await db.execute(
                select(GlowTransaction.id)
                .where(
                    GlowTransaction.owner_user_id == owner_user_id,
                    GlowTransaction.event_type == event_type,
                    GlowTransaction.created_at >= spam_start,
                    GlowTransaction.created_at <= event_time,
                    _not_reversed(GlowTransaction.id),
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if recent is not None:
            await _record_fraud_flag(
                db,
                owner_user_id=owner_user_id,
                source_kind=source_kind,
                source_id=source_id,
                signal_type="RAPID_REPEAT",
                idempotency_key=f"rapid-repeat:{event_type}:{source_id}",
                metadata={"spam_window_seconds": rule.spam_window_seconds},
            )
            raise HTTPException(409, "Glow action is inside its anti-spam window.")

    multiplier = Decimal(rule.default_multiplier)
    final_points = int(
        (Decimal(rule.base_points) * multiplier).quantize(Decimal("1"), rounding=ROUND_DOWN)
    )
    if rule.daily_cap is not None:
        awarded_today = int(
            (
                await db.execute(
                    select(func.coalesce(func.sum(GlowTransaction.final_points), 0)).where(
                        GlowTransaction.owner_user_id == owner_user_id,
                        GlowTransaction.event_type == event_type,
                        GlowTransaction.created_at >= day.start,
                        GlowTransaction.created_at < day.end,
                        _not_reversed(GlowTransaction.id),
                    )
                )
            ).scalar_one()
        )
        if awarded_today + final_points > rule.daily_cap:
            raise HTTPException(409, "Daily Glow cap reached for this action.")
    if rule.weekly_cap is not None:
        awarded_week = int(
            (
                await db.execute(
                    select(func.coalesce(func.sum(GlowTransaction.final_points), 0)).where(
                        GlowTransaction.owner_user_id == owner_user_id,
                        GlowTransaction.event_type == event_type,
                        GlowTransaction.created_at >= week.start,
                        GlowTransaction.created_at < week.end,
                        _not_reversed(GlowTransaction.id),
                    )
                )
            ).scalar_one()
        )
        if awarded_week + final_points > rule.weekly_cap:
            raise HTTPException(409, "Weekly Glow cap reached for this action.")

    # G10: an explicit System context (e.g. an outcome Return completed from a
    # System surface) takes precedence; otherwise derive from the source. This
    # sets system_slug at INSERT, honoring G09's append-only glow_transactions
    # (UPDATE is revoked) instead of patching the row after the fact.
    system_slug = (
        system_slug_override
        if system_slug_override is not None
        else await _resolve_system_slug(
            db,
            owner_user_id=owner_user_id,
            source=source,
            rule=rule,
        )
    )
    source_event = await _source_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type=event_type,
        source_kind=source_kind,
        source_id=source_id,
        system_slug=system_slug,
    )
    balance = await _balance_for_update(db, owner_user_id)
    debt_settled = min(balance.reversal_debt, final_points)
    balance.reversal_debt -= debt_settled
    balance.balance += final_points - debt_settled
    balance.lifetime_points += final_points
    balance.updated_at = now_utc()
    transaction = GlowTransaction(
        owner_user_id=owner_user_id,
        event_type=event_type,
        source_kind=source_kind,
        source_id=source_id,
        source_event_id=source_event.id,
        orbit_id=orbit_id,
        system_slug=system_slug,
        base_points=rule.base_points,
        multiplier=multiplier,
        multiplier_reason=rule.multiplier_reason,
        rule_version=rule.rule_version,
        final_points=final_points,
        reason=rule.description,
        idempotency_key=idempotency_key,
        anti_abuse_state="CLEAR",
        anti_abuse_metadata={
            "source_verified": True,
            "server_event_id": str(source_event.id),
            "daily_cap": rule.daily_cap,
            "weekly_cap": rule.weekly_cap,
            "spam_window_seconds": rule.spam_window_seconds,
            "reversal_debt_settled": debt_settled,
        },
        timezone=day.timezone,
        local_date=day.local_date,
        created_at=event_time,
    )
    db.add(transaction)
    await db.flush()
    db.add(
        GlowSourceClaim(
            owner_user_id=owner_user_id,
            event_type=event_type,
            source_kind=source_kind,
            source_id=source_id,
            source_event_id=source_event.id,
            transaction_id=transaction.id,
            claimed_at=event_time,
        )
    )
    db.add(
        GlowRewardEvent(
            owner_user_id=owner_user_id,
            event_type=event_type,
            source_kind=source_kind,
            source_id=source_id,
            idempotency_key=idempotency_key,
            transaction_id=transaction.id,
            status="AWARDED",
            event_metadata={
                "final_points": final_points,
                "streak_key": rule.streak_key,
                "source_event_id": str(source_event.id),
            },
            created_at=event_time,
        )
    )
    streak = await _update_streak(
        db,
        owner_user_id=owner_user_id,
        streak_key=rule.streak_key,
        transaction=transaction,
        occurred_at=event_time,
        timezone_name=timezone_name,
    )
    achievements = await _sync_achievements(
        db,
        owner_user_id=owner_user_id,
        lifetime_points=balance.lifetime_points,
        source_transaction_id=transaction.id,
    )
    level, level_changed = await _sync_level(
        db,
        owner_user_id=owner_user_id,
        lifetime_points=balance.lifetime_points,
        source_transaction_id=transaction.id,
    )
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="glow.posted.v1",
        aggregate_type="glow_transaction",
        aggregate_id=transaction.id,
        idempotency_key=f"glow-posted:{transaction.id}",
        payload={
            "transaction_id": str(transaction.id),
            "source_event_id": str(source_event.id),
            "event_type": event_type,
            "points": final_points,
            "level": level.level,
            "level_changed": level_changed,
            "achievement_keys": [row.achievement_key for row in achievements],
        },
    )
    if achievements or level_changed:
        from app.services.engagement_policy import create_policy_notification

        milestone = achievements[-1].achievement_metadata.get("label") if achievements else None
        await create_policy_notification(
            db,
            owner_user_id=owner_user_id,
            category="PROGRESS",
            title="Your constellation changed",
            body=(
                f"Milestone confirmed: {milestone}."
                if milestone
                else f"Level {level.level} is now confirmed from verified Glow."
            ),
            route="/today",
            source_type="GLOW_MILESTONE",
            source_id=transaction.id,
            idempotency_key=f"glow-milestone:{transaction.id}",
            occurred_at=event_time,
        )
    return AwardResult(transaction, balance, streak, False, achievements)


async def award_glow_if_eligible(
    db: AsyncSession,
    **kwargs,
) -> tuple[AwardResult | None, str | None]:
    try:
        return await award_glow(db, **kwargs), None
    except HTTPException as exc:
        detail = str(exc.detail)
        if exc.status_code == 409 and any(
            marker in detail.lower() for marker in ("cap", "anti-spam")
        ):
            return None, detail
        raise


async def _rebuild_streak(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    streak: GlowStreak,
) -> None:
    active_award = or_(
        GlowStreakEvent.event_kind == "REPAIRED",
        (
            (GlowStreakEvent.event_kind == "AWARDED")
            & _not_reversed(GlowStreakEvent.transaction_id)
        ),
    )
    events = (
        await db.execute(
            select(
                GlowStreakEvent.local_date,
                GlowStreakEvent.timezone,
                GlowStreakEvent.occurred_at,
            )
            .where(
                GlowStreakEvent.owner_user_id == owner_user_id,
                GlowStreakEvent.streak_id == streak.id,
                active_award,
            )
            .order_by(GlowStreakEvent.local_date, GlowStreakEvent.occurred_at)
        )
    ).all()
    dates = sorted({row.local_date for row in events})
    best = 0
    run = 0
    previous = None
    for local_date in dates:
        run = run + 1 if previous and local_date == previous + dt.timedelta(days=1) else 1
        best = max(best, run)
        previous = local_date
    current = 0
    for local_date in reversed(dates):
        if current == 0:
            current = 1
            previous = local_date
        elif local_date == previous - dt.timedelta(days=1):
            current += 1
            previous = local_date
        else:
            break
    definition = (
        await db.execute(
            select(GlowStreakDefinition).where(
                GlowStreakDefinition.streak_key == streak.streak_key
            )
        )
    ).scalar_one()
    streak.current_count = current if dates else 0
    streak.best_count = best
    streak.last_event_date = dates[-1] if dates else None
    streak.last_event_at = max((row.occurred_at for row in events), default=None)
    if events:
        streak.timezone = events[-1].timezone
    streak.checkpoint_count = streak.current_count // definition.checkpoint_interval
    streak.next_reward_at = (streak.checkpoint_count + 1) * definition.checkpoint_interval
    streak.state_reason = "REBUILT_AFTER_REVERSAL"
    streak.updated_at = now_utc()


async def reverse_glow(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    reason: str,
    idempotency_key: str,
    actor_type: str = "SYSTEM",
    actor_user_id: uuid.UUID | None = None,
) -> ReversalResult:
    if actor_type not in {"SYSTEM", "OWNER", "REVIEWER"}:
        raise ValueError("Unsupported Glow reversal actor type.")
    await _lock_owner(db, owner_user_id)
    existing = (
        await db.execute(
            select(GlowReversal).where(
                GlowReversal.owner_user_id == owner_user_id,
                or_(
                    GlowReversal.idempotency_key == idempotency_key,
                    GlowReversal.transaction_id == transaction_id,
                ),
            )
        )
    ).scalar_one_or_none()
    balance = await _balance_for_update(db, owner_user_id)
    if existing is not None:
        return ReversalResult(existing, balance, True)
    transaction = (
        await db.execute(
            select(GlowTransaction).where(
                GlowTransaction.id == transaction_id,
                GlowTransaction.owner_user_id == owner_user_id,
            )
        )
    ).scalar_one_or_none()
    if transaction is None:
        raise HTTPException(404, "Glow transaction not found.")
    reversal_event = await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="glow.reversed.v1",
        aggregate_type="glow_transaction",
        aggregate_id=transaction.id,
        idempotency_key=f"glow-reversal-source:{idempotency_key}",
        payload={"transaction_id": str(transaction.id), "reason_code": "SOURCE_INVALIDATED"},
    )
    balance_effect = min(balance.balance, transaction.final_points)
    debt_effect = transaction.final_points - balance_effect
    balance.balance -= balance_effect
    balance.reversal_debt += debt_effect
    balance.lifetime_points = max(0, balance.lifetime_points - transaction.final_points)
    balance.updated_at = now_utc()
    reversal = GlowReversal(
        owner_user_id=owner_user_id,
        transaction_id=transaction.id,
        source_event_id=reversal_event.id,
        points=transaction.final_points,
        balance_effect=balance_effect,
        debt_effect=debt_effect,
        reason=reason,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        idempotency_key=idempotency_key,
    )
    db.add(reversal)
    await db.flush()
    db.add(
        GlowRewardEvent(
            owner_user_id=owner_user_id,
            event_type=transaction.event_type,
            source_kind=transaction.source_kind,
            source_id=transaction.source_id,
            idempotency_key=f"reward-reversal:{idempotency_key}",
            transaction_id=transaction.id,
            status="REVERSED",
            event_metadata={"reversal_id": str(reversal.id), "reason": reason},
        )
    )
    rule = (
        await db.execute(
            select(GlowRule).where(GlowRule.event_type == transaction.event_type)
        )
    ).scalar_one()
    if rule.streak_key:
        streak = (
            await db.execute(
                select(GlowStreak)
                .where(
                    GlowStreak.owner_user_id == owner_user_id,
                    GlowStreak.streak_key == rule.streak_key,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if streak:
            db.add(
                GlowStreakEvent(
                    owner_user_id=owner_user_id,
                    streak_id=streak.id,
                    transaction_id=transaction.id,
                    event_kind="REVERSED",
                    local_date=transaction.local_date,
                    timezone=transaction.timezone,
                    idempotency_key=f"streak-reversal:{reversal.id}",
                    event_metadata={"reversal_id": str(reversal.id)},
                )
            )
            await _rebuild_streak(db, owner_user_id=owner_user_id, streak=streak)
    await _sync_achievements(
        db,
        owner_user_id=owner_user_id,
        lifetime_points=balance.lifetime_points,
        source_reversal_id=reversal.id,
    )
    await _sync_level(
        db,
        owner_user_id=owner_user_id,
        lifetime_points=balance.lifetime_points,
        source_reversal_id=reversal.id,
    )
    return ReversalResult(reversal, balance, False)


async def reverse_source_glow(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    event_type: str,
    source_kind: str,
    source_id: uuid.UUID,
    reason: str,
) -> ReversalResult | None:
    transaction = (
        await db.execute(
            select(GlowTransaction).where(
                GlowTransaction.owner_user_id == owner_user_id,
                GlowTransaction.event_type == event_type,
                GlowTransaction.source_kind == source_kind,
                GlowTransaction.source_id == source_id,
            )
        )
    ).scalar_one_or_none()
    if transaction is None:
        return None
    return await reverse_glow(
        db,
        owner_user_id=owner_user_id,
        transaction_id=transaction.id,
        reason=reason,
        idempotency_key=f"source-reversed:{event_type}:{source_id}",
    )


async def repair_streak(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    streak_id: uuid.UUID,
    idempotency_key: str,
    occurred_at: dt.datetime | None = None,
) -> RepairResult:
    instant = _aware(occurred_at)
    await _lock_owner(db, owner_user_id)
    existing = (
        await db.execute(
            select(GlowStreakRepair).where(
                GlowStreakRepair.owner_user_id == owner_user_id,
                GlowStreakRepair.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    streak = (
        await db.execute(
            select(GlowStreak)
            .where(
                GlowStreak.id == streak_id,
                GlowStreak.owner_user_id == owner_user_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if streak is None:
        raise HTTPException(404, "Glow streak not found.")
    balance = await _balance_for_update(db, owner_user_id)
    if existing is not None:
        return RepairResult(existing, streak, balance, True)
    definition = (
        await db.execute(
            select(GlowStreakDefinition).where(
                GlowStreakDefinition.streak_key == streak.streak_key,
                GlowStreakDefinition.active.is_(True),
            )
        )
    ).scalar_one()
    timezone_name = await _owner_timezone(db, owner_user_id)
    today = calendar_window(instant, timezone_name, "DAILY").local_date
    if streak.last_event_date != today - dt.timedelta(days=2):
        raise HTTPException(409, "This streak has no single repairable local-calendar gap.")
    repair_date = today - dt.timedelta(days=1)
    if balance.reversal_debt:
        raise HTTPException(409, "Resolve reversed Glow before using a Glow sink.")
    if balance.balance < definition.repair_cost:
        raise HTTPException(409, "Not enough available Glow for this repair.")
    balance.balance -= definition.repair_cost
    balance.spent_points += definition.repair_cost
    balance.updated_at = now_utc()
    repair = GlowStreakRepair(
        owner_user_id=owner_user_id,
        streak_id=streak.id,
        repaired_local_date=repair_date,
        cost_points=definition.repair_cost,
        idempotency_key=idempotency_key,
        status="APPLIED",
        created_at=instant,
    )
    db.add(repair)
    await db.flush()
    streak.current_count += 1
    streak.best_count = max(streak.best_count, streak.current_count)
    streak.last_event_date = repair_date
    streak.state_reason = "OWNER_REPAIR"
    streak.updated_at = now_utc()
    db.add(
        GlowStreakEvent(
            owner_user_id=owner_user_id,
            streak_id=streak.id,
            event_kind="REPAIRED",
            local_date=repair_date,
            timezone=timezone_name,
            idempotency_key=f"streak-repair-event:{repair.id}",
            event_metadata={"cost_points": definition.repair_cost},
            occurred_at=instant,
        )
    )
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="streak.repaired.v1",
        aggregate_type="glow_streak",
        aggregate_id=streak.id,
        idempotency_key=f"streak-repaired:{repair.id}",
        payload={"repair_id": str(repair.id), "streak_key": streak.streak_key},
    )
    return RepairResult(repair, streak, balance, False)


async def sync_quests(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    occurred_at: dt.datetime | None = None,
) -> list[tuple[GlowQuest, GlowQuestDefinition]]:
    instant = _aware(occurred_at)
    timezone_name = await _owner_timezone(db, owner_user_id)
    daily = calendar_window(instant, timezone_name, "DAILY")
    checkin = (
        await db.execute(
            select(TodayCheckIn)
            .where(
                TodayCheckIn.owner_user_id == owner_user_id,
                TodayCheckIn.checkin_date == daily.local_date,
            )
            .order_by(TodayCheckIn.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    low_capacity = bool(
        checkin
        and (
            checkin.energy <= 3
            or checkin.pain >= 7
            or checkin.sleep_quality <= 3
            or checkin.emotional_load >= 8
        )
    )
    definitions = (
        await db.execute(
            select(GlowQuestDefinition)
            .where(GlowQuestDefinition.active.is_(True))
            .order_by(GlowQuestDefinition.cadence, GlowQuestDefinition.quest_key)
        )
    ).scalars().all()
    result: list[tuple[GlowQuest, GlowQuestDefinition]] = []
    for definition in definitions:
        window = calendar_window(instant, timezone_name, definition.cadence)
        quest = (
            await db.execute(
                select(GlowQuest).where(
                    GlowQuest.owner_user_id == owner_user_id,
                    GlowQuest.template_id == definition.id,
                    GlowQuest.local_period_key == window.local_key,
                )
            )
        ).scalar_one_or_none()
        if quest is None:
            quest = GlowQuest(
                owner_user_id=owner_user_id,
                template_id=definition.id,
                local_period_key=window.local_key,
                timezone=window.timezone,
                period_start=window.start,
                period_end=window.end,
                target_count=(
                    definition.low_capacity_target if low_capacity else definition.base_target
                ),
            )
            db.add(quest)
            await db.flush()
        target_events = [str(item) for item in definition.target_event_types]
        progress = int(
            (
                await db.execute(
                    select(func.count(GlowTransaction.id)).where(
                        GlowTransaction.owner_user_id == owner_user_id,
                        GlowTransaction.event_type.in_(target_events),
                        GlowTransaction.created_at >= quest.period_start,
                        GlowTransaction.created_at < quest.period_end,
                        _not_reversed(GlowTransaction.id),
                    )
                )
            ).scalar_one()
        )
        quest.progress_count = progress
        if quest.status not in {"CLAIMED", "EXPIRED"} and progress >= quest.target_count:
            quest.status = "COMPLETED"
            quest.completed_at = quest.completed_at or instant
        elif quest.status == "COMPLETED" and progress < quest.target_count:
            quest.status = "ACTIVE"
            quest.completed_at = None
        quest.updated_at = now_utc()
        result.append((quest, definition))
    await db.flush()
    return result


async def claim_quest(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    quest_id: uuid.UUID,
    idempotency_key: str,
    occurred_at: dt.datetime | None = None,
) -> AwardResult:
    instant = _aware(occurred_at)
    await _lock_owner(db, owner_user_id)
    synced = await sync_quests(db, owner_user_id=owner_user_id, occurred_at=instant)
    pair = next((item for item in synced if item[0].id == quest_id), None)
    if pair is None:
        raise HTTPException(404, "Glow quest not found in the current period.")
    quest, definition = pair
    if quest.status == "CLAIMED" and quest.claim_transaction_id:
        transaction = (
            await db.execute(
                select(GlowTransaction).where(
                    GlowTransaction.id == quest.claim_transaction_id,
                    GlowTransaction.owner_user_id == owner_user_id,
                )
            )
        ).scalar_one()
        balance = await _balance_for_update(db, owner_user_id)
        return AwardResult(transaction, balance, None, True, [])
    if quest.status != "COMPLETED":
        raise HTTPException(409, "Quest progress is not complete and cannot be claimed.")
    event_type = (
        "quest.daily_claimed" if definition.cadence == "DAILY" else "quest.weekly_claimed"
    )
    result = await award_glow(
        db,
        owner_user_id=owner_user_id,
        event_type=event_type,
        source_kind="GLOW_QUEST",
        source_id=quest.id,
        orbit_id=None,
        idempotency_key=idempotency_key,
        occurred_at=instant,
    )
    quest.status = "CLAIMED"
    quest.claimed_at = instant
    quest.claim_transaction_id = result.transaction.id
    quest.updated_at = now_utc()
    return result


async def redeem_reward(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    reward_key: str,
    idempotency_key: str,
) -> RedemptionResult:
    await _lock_owner(db, owner_user_id)
    existing = (
        await db.execute(
            select(GlowRewardRedemption).where(
                GlowRewardRedemption.owner_user_id == owner_user_id,
                or_(
                    GlowRewardRedemption.idempotency_key == idempotency_key,
                    GlowRewardRedemption.reward_key == reward_key,
                ),
            )
        )
    ).scalar_one_or_none()
    balance = await _balance_for_update(db, owner_user_id)
    if existing is not None:
        return RedemptionResult(existing, balance, True)
    definition = (
        await db.execute(
            select(GlowRewardDefinition).where(
                GlowRewardDefinition.reward_key == reward_key,
                GlowRewardDefinition.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if definition is None:
        raise HTTPException(404, "Glow reward not found.")
    level = (
        await db.execute(
            select(GlowUserLevel).where(GlowUserLevel.owner_user_id == owner_user_id)
        )
    ).scalar_one_or_none()
    current_level = level.level if level else 1
    if current_level < definition.minimum_level:
        raise HTTPException(409, "This cosmetic reward has not unlocked yet.")
    if balance.reversal_debt:
        raise HTTPException(409, "Resolve reversed Glow before using a Glow sink.")
    if balance.balance < definition.cost_points:
        raise HTTPException(409, "Not enough available Glow for this reward.")
    balance.balance -= definition.cost_points
    balance.spent_points += definition.cost_points
    balance.updated_at = now_utc()
    redemption = GlowRewardRedemption(
        owner_user_id=owner_user_id,
        reward_key=reward_key,
        cost_points=definition.cost_points,
        idempotency_key=idempotency_key,
        status="REDEEMED",
    )
    db.add(redemption)
    await db.flush()
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="glow.reward.redeemed.v1",
        aggregate_type="glow_reward",
        aggregate_id=redemption.id,
        idempotency_key=f"glow-reward-redeemed:{redemption.id}",
        payload={"reward_key": reward_key, "cost_points": definition.cost_points},
    )
    return RedemptionResult(redemption, balance, False)
