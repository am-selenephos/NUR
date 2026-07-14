import datetime as dt
import uuid
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import func, select
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
    GlowBalance,
    GlowRewardEvent,
    GlowRule,
    GlowStreak,
    GlowTransaction,
    JournalEntry,
    Goal,
    Objective,
    Outcome,
    Plan,
    PlanStep,
    ScheduledAction,
    SystemAction,
    SystemDiagnostic,
)
from app.models._mixins import now_utc


@dataclass
class AwardResult:
    transaction: GlowTransaction
    balance: GlowBalance
    streak: GlowStreak | None
    idempotent_replay: bool
    achievements: list[GlowAchievement]


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
    }
    model = models.get(source_kind)
    if model is None:
        raise HTTPException(422, "Unsupported Glow source kind.")
    row = (await db.execute(select(model).where(
        model.id == source_id,
        model.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Glow source not found.")
    return row


def _validate_event_source(event_type: str, source_kind: str, source) -> None:
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


async def _unlock_achievements(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    lifetime_points: int,
    source_transaction_id: uuid.UUID,
) -> list[GlowAchievement]:
    thresholds = (
        ("first_glow", 1, "First verified Glow"),
        ("ember_50", 50, "Fifty source-linked Glow"),
        ("star_builder_150", 150, "One hundred fifty source-linked Glow"),
        ("orbit_keeper_350", 350, "Three hundred fifty source-linked Glow"),
        ("constellation_700", 700, "Seven hundred source-linked Glow"),
    )
    eligible = [row for row in thresholds if lifetime_points >= row[1]]
    if not eligible:
        return []
    existing = set((await db.execute(select(GlowAchievement.achievement_key).where(
        GlowAchievement.owner_user_id == owner_user_id,
        GlowAchievement.achievement_key.in_([row[0] for row in eligible]),
    ))).scalars().all())
    unlocked: list[GlowAchievement] = []
    for key, threshold, label in eligible:
        if key in existing:
            continue
        achievement = GlowAchievement(
            owner_user_id=owner_user_id,
            achievement_key=key,
            source_transaction_id=source_transaction_id,
            achievement_metadata={"threshold": threshold, "label": label},
        )
        db.add(achievement)
        unlocked.append(achievement)
    if unlocked:
        await db.flush()
    return unlocked


async def _update_streak(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    streak_key: str | None,
) -> GlowStreak | None:
    if not streak_key:
        return None
    today = dt.datetime.now(dt.timezone.utc).date()
    row = (await db.execute(
        select(GlowStreak)
        .where(GlowStreak.owner_user_id == owner_user_id, GlowStreak.streak_key == streak_key)
        .with_for_update()
    )).scalar_one_or_none()
    if row is None:
        row = GlowStreak(
            owner_user_id=owner_user_id,
            streak_key=streak_key,
            current_count=1,
            best_count=1,
            last_event_date=today,
        )
        db.add(row)
        await db.flush()
        return row
    if row.last_event_date == today:
        return row
    yesterday = today - dt.timedelta(days=1)
    row.current_count = row.current_count + 1 if row.last_event_date == yesterday else 1
    row.best_count = max(row.best_count, row.current_count)
    row.last_event_date = today
    row.updated_at = now_utc()
    return row


async def award_glow(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    event_type: str,
    source_kind: str,
    source_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    idempotency_key: str,
) -> AwardResult:
    replay = (await db.execute(select(GlowTransaction).where(
        GlowTransaction.owner_user_id == owner_user_id,
        GlowTransaction.idempotency_key == idempotency_key,
    ))).scalar_one_or_none()
    if replay is not None:
        balance = (await db.execute(select(GlowBalance).where(
            GlowBalance.owner_user_id == owner_user_id,
        ))).scalar_one()
        rule = (await db.execute(select(GlowRule).where(GlowRule.event_type == replay.event_type))).scalar_one()
        streak = None
        if rule.streak_key:
            streak = (await db.execute(select(GlowStreak).where(
                GlowStreak.owner_user_id == owner_user_id,
                GlowStreak.streak_key == rule.streak_key,
            ))).scalar_one_or_none()
        return AwardResult(replay, balance, streak, True, [])

    rule = (await db.execute(select(GlowRule).where(
        GlowRule.event_type == event_type,
        GlowRule.active.is_(True),
    ))).scalar_one_or_none()
    if rule is None:
        raise HTTPException(422, "Unknown or inactive Glow event.")

    source = await _owned_source(
        db,
        owner_user_id=owner_user_id,
        source_kind=source_kind,
        source_id=source_id,
    )
    _validate_event_source(event_type, source_kind, source)

    if rule.spam_window_seconds:
        spam_start = now_utc() - dt.timedelta(seconds=rule.spam_window_seconds)
        recent = (await db.execute(select(GlowTransaction.id).where(
            GlowTransaction.owner_user_id == owner_user_id,
            GlowTransaction.event_type == event_type,
            GlowTransaction.reversed.is_(False),
            GlowTransaction.created_at >= spam_start,
        ).limit(1))).scalar_one_or_none()
        if recent is not None:
            raise HTTPException(409, "Glow action is inside its anti-spam window.")

    if orbit_id is not None:
        source_orbit = getattr(source, "orbit_id", None)
        if source_orbit is not None and source_orbit != orbit_id:
            raise HTTPException(409, "Glow Orbit does not match its source.")

    if rule.daily_cap is not None:
        start = dt.datetime.combine(dt.datetime.now(dt.timezone.utc).date(), dt.time.min, tzinfo=dt.timezone.utc)
        awarded_today = int((await db.execute(select(func.coalesce(func.sum(GlowTransaction.final_points), 0)).where(
            GlowTransaction.owner_user_id == owner_user_id,
            GlowTransaction.event_type == event_type,
            GlowTransaction.reversed.is_(False),
            GlowTransaction.created_at >= start,
        ))).scalar_one())
        if awarded_today + rule.base_points > rule.daily_cap:
            raise HTTPException(409, "Daily Glow cap reached for this action.")

    if rule.weekly_cap is not None:
        now = dt.datetime.now(dt.timezone.utc)
        week_start = dt.datetime.combine(
            now.date() - dt.timedelta(days=now.weekday()),
            dt.time.min,
            tzinfo=dt.timezone.utc,
        )
        awarded_week = int((await db.execute(select(func.coalesce(func.sum(GlowTransaction.final_points), 0)).where(
            GlowTransaction.owner_user_id == owner_user_id,
            GlowTransaction.event_type == event_type,
            GlowTransaction.reversed.is_(False),
            GlowTransaction.created_at >= week_start,
        ))).scalar_one())
        if awarded_week + rule.base_points > rule.weekly_cap:
            raise HTTPException(409, "Weekly Glow cap reached for this action.")

    balance = (await db.execute(
        select(GlowBalance).where(GlowBalance.owner_user_id == owner_user_id).with_for_update()
    )).scalar_one_or_none()
    if balance is None:
        balance = GlowBalance(owner_user_id=owner_user_id)
        db.add(balance)
        await db.flush()

    structured = getattr(source, "structured_payload", {}) or {}
    derived_system_slug = getattr(source, "system_slug", None)
    if isinstance(source, Objective):
        derived_system_slug = (await db.execute(select(Goal.system_slug).where(
            Goal.id == source.goal_id,
            Goal.owner_user_id == owner_user_id,
        ))).scalar_one_or_none()
    if isinstance(source, (AMProjectTask, AMProjectEvidence)):
        project = (await db.execute(select(AMProject).where(
            AMProject.id == source.project_id,
            AMProject.owner_user_id == owner_user_id,
        ))).scalar_one_or_none()
        if project is not None:
            derived_system_slug = project.system_slug
    transaction = GlowTransaction(
        owner_user_id=owner_user_id,
        event_type=event_type,
        source_kind=source_kind,
        source_id=source_id,
        orbit_id=orbit_id,
        system_slug=(
            derived_system_slug
            or structured.get("system_slug")
            or rule.system_slug
        ),
        base_points=rule.base_points,
        multiplier=1,
        final_points=rule.base_points,
        reason=rule.description,
        idempotency_key=idempotency_key,
        anti_abuse_metadata={
            "source_verified": True,
            "daily_cap": rule.daily_cap,
            "weekly_cap": rule.weekly_cap,
            "spam_window_seconds": rule.spam_window_seconds,
        },
    )
    db.add(transaction)
    await db.flush()
    balance.balance += transaction.final_points
    balance.lifetime_points += transaction.final_points
    balance.updated_at = now_utc()
    streak = await _update_streak(
        db,
        owner_user_id=owner_user_id,
        streak_key=rule.streak_key,
    )
    db.add(GlowRewardEvent(
        owner_user_id=owner_user_id,
        event_type=event_type,
        source_kind=source_kind,
        source_id=source_id,
        idempotency_key=idempotency_key,
        transaction_id=transaction.id,
        event_metadata={"final_points": transaction.final_points, "streak_key": rule.streak_key},
    ))
    achievements = await _unlock_achievements(
        db,
        owner_user_id=owner_user_id,
        lifetime_points=balance.lifetime_points,
        source_transaction_id=transaction.id,
    )
    return AwardResult(transaction, balance, streak, False, achievements)
