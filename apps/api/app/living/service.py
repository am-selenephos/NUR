"""Calculations and owner-bound helpers for Today and Star Systems."""

import datetime as dt
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.living.catalog import BY_SLUG, SYSTEMS, SystemDefinition, require_system
from app.models import (
    AuditEvent,
    CognitiveEvent,
    GlowTransaction,
    Goal,
    OmegaClaim,
    Orbit,
    Outcome,
    Plan,
    Profile,
    ScheduledAction,
    SystemAction,
    SystemDiagnostic,
    TodayCheckIn,
)


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def _daypart(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "night"


async def owner_now(
    db: AsyncSession, owner_user_id: uuid.UUID
) -> tuple[dt.datetime, str]:
    timezone = (await db.execute(
        select(Profile.timezone).where(Profile.user_id == owner_user_id)
    )).scalar_one_or_none()
    timezone = timezone or "UTC"
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo("UTC")
        timezone = "UTC"
    return dt.datetime.now(zone), timezone


async def owned_system_orbit(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    system: SystemDefinition | str,
) -> Orbit:
    definition = require_system(system) if isinstance(system, str) else system
    orbit = (await db.execute(select(Orbit).where(
        Orbit.owner_user_id == owner_user_id,
        Orbit.title == definition.title,
        Orbit.status == "ACTIVE",
    ))).scalar_one_or_none()
    if orbit is None:
        raise HTTPException(404, f"{definition.title} System not found.")
    return orbit


def add_living_event(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    timeline_kind: str,
    content: str,
    object_type: str,
    object_id: uuid.UUID,
    metadata: dict | None = None,
) -> CognitiveEvent:
    payload = {
        "type": timeline_kind.lower(),
        "timeline_kind": timeline_kind,
        "object_type": object_type,
        "object_id": str(object_id),
        "provenance_label": "OWNER_WRITTEN",
        **(metadata or {}),
    }
    event = CognitiveEvent(
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        event_kind="SYSTEM_EVENT",
        content_text=content,
        structured_payload=payload,
        source_ref=f"{object_type}:{object_id}",
    )
    db.add(event)
    db.add(AuditEvent(
        actor_user_id=owner_user_id,
        event_type=timeline_kind.lower(),
        object_type=object_type,
        object_id=object_id,
        event_metadata={
            "orbit_id": str(orbit_id) if orbit_id else None,
            "provenance_label": "OWNER_WRITTEN",
            **(metadata or {}),
        },
    ))
    return event


async def system_snapshot(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    slug: str,
) -> dict:
    definition = require_system(slug)
    orbit = await owned_system_orbit(
        db, owner_user_id=owner_user_id, system=definition
    )
    actions = (await db.execute(select(SystemAction).where(
        SystemAction.owner_user_id == owner_user_id,
        SystemAction.system_slug == slug,
    ).order_by(SystemAction.created_at.desc()).limit(100))).scalars().all()
    goals = (await db.execute(select(Goal).where(
        Goal.owner_user_id == owner_user_id,
        Goal.system_slug == slug,
    ).order_by(Goal.created_at.desc()).limit(50))).scalars().all()
    latest_diagnostic = (await db.execute(select(SystemDiagnostic).where(
        SystemDiagnostic.owner_user_id == owner_user_id,
        SystemDiagnostic.system_slug == slug,
    ).order_by(SystemDiagnostic.created_at.desc()).limit(1))).scalar_one_or_none()
    glow_points = int((await db.execute(select(func.coalesce(
        func.sum(GlowTransaction.final_points), 0
    )).where(
        GlowTransaction.owner_user_id == owner_user_id,
        GlowTransaction.system_slug == slug,
        GlowTransaction.reversed.is_(False),
    ))).scalar_one())

    total_actions = len(actions)
    completed_actions = sum(row.status == "COMPLETED" for row in actions)
    missed_actions = [row for row in actions if row.status == "MISSED"]
    action_score = 100 * completed_actions / total_actions if total_actions else 0
    goal_score = (
        sum(row.progress_percent for row in goals) / len(goals) if goals else 0
    )
    diagnostic_score = latest_diagnostic.score if latest_diagnostic else 0
    glow_score = min(100, glow_points * 2)
    progress = _clamp(
        action_score * 0.45
        + goal_score * 0.25
        + diagnostic_score * 0.20
        + glow_score * 0.10
    )
    open_actions = [row for row in reversed(actions) if row.status == "OPEN"]
    next_move = (
        {
            "kind": "SYSTEM_ACTION",
            "id": str(open_actions[0].id),
            "title": open_actions[0].title,
        }
        if open_actions
        else {
            "kind": "CHECKLIST_SUGGESTION",
            "id": None,
            "title": definition.checklist[min(completed_actions, len(definition.checklist) - 1)],
        }
    )
    blockers = list(latest_diagnostic.blockers if latest_diagnostic else [])
    blockers.extend(row.title for row in missed_actions[:3])
    return {
        "slug": slug,
        "title": definition.title,
        "definition": definition.definition,
        "orbit_id": str(orbit.id),
        "questions": list(definition.questions),
        "checklist": list(definition.checklist),
        "progress_percent": progress,
        "progress_sources": {
            "completed_actions": completed_actions,
            "total_actions": total_actions,
            "action_completion_percent": round(action_score),
            "goal_progress_percent": round(goal_score),
            "latest_diagnostic_score": diagnostic_score,
            "glow_points": glow_points,
            "formula": "45% actions + 25% goals + 20% diagnostic + 10% Glow activity",
        },
        "active_goal_count": sum(row.status == "ACTIVE" for row in goals),
        "goals": [
            {
                "id": str(row.id),
                "title": row.title,
                "status": row.status,
                "progress_percent": row.progress_percent,
                "target_date": row.target_date,
            }
            for row in goals[:10]
        ],
        "actions": [
            {
                "id": str(row.id),
                "title": row.title,
                "status": row.status,
                "due_at": row.due_at,
                "effort_minutes": row.effort_minutes,
                "completed_at": row.completed_at,
                "missed_at": row.missed_at,
            }
            for row in actions[:20]
        ],
        "blockers": blockers[:8],
        "next_move": next_move,
        "prediction": {
            "if_ignored": definition.ignored_prediction,
            "if_followed": definition.followed_prediction,
            "basis": {
                "progress_percent": progress,
                "missed_actions": len(missed_actions),
                "open_actions": len(open_actions),
            },
            "provenance_label": "DETERMINISTIC_INFERENCE",
        },
    }


async def all_system_snapshots(
    db: AsyncSession, *, owner_user_id: uuid.UUID
) -> list[dict]:
    return [
        await system_snapshot(db, owner_user_id=owner_user_id, slug=system.slug)
        for system in SYSTEMS
    ]


def _checkin_body(checkin: TodayCheckIn) -> int:
    return _clamp(
        checkin.energy * 10 * 0.30
        + (10 - checkin.pain) * 10 * 0.25
        + checkin.sleep_quality * 10 * 0.20
        + checkin.nourishment * 10 * 0.15
        + checkin.movement * 10 * 0.10
    )


def _checkin_mind(checkin: TodayCheckIn) -> int:
    return _clamp(
        checkin.clarity * 10 * 0.55
        + (10 - checkin.emotional_load) * 10 * 0.45
    )


def _blend(evidence_score: int | None, system_score: float) -> int:
    if evidence_score is None:
        return _clamp(system_score)
    return _clamp(evidence_score * 0.65 + system_score * 0.35)


async def today_snapshot(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    systems: list[dict] | None = None,
) -> dict:
    now, timezone = await owner_now(db, owner_user_id)
    today = now.date()
    start_utc = dt.datetime.combine(today, dt.time.min, tzinfo=now.tzinfo).astimezone(dt.UTC)
    end_utc = start_utc + dt.timedelta(days=1)
    systems = systems or await all_system_snapshots(
        db, owner_user_id=owner_user_id
    )
    by_slug = {row["slug"]: row for row in systems}
    checkin = (await db.execute(select(TodayCheckIn).where(
        TodayCheckIn.owner_user_id == owner_user_id,
        TodayCheckIn.checkin_date == today,
    ))).scalar_one_or_none()

    mind_system = sum(
        by_slug[slug]["progress_percent"]
        for slug in ("quiet-ambition", "study", "rebuild")
    ) / 3
    life_system = sum(
        by_slug[slug]["progress_percent"]
        for slug in ("money", "connection", "creation", "rebuild")
    ) / 4
    body_evidence = _checkin_body(checkin) if checkin else None
    mind_evidence = _checkin_mind(checkin) if checkin else None
    body_score = _blend(body_evidence, by_slug["body"]["progress_percent"])
    mind_score = _blend(mind_evidence, mind_system)
    life_score = _clamp(life_system)

    goals = (await db.execute(select(Goal).where(
        Goal.owner_user_id == owner_user_id,
        Goal.status == "ACTIVE",
    ).order_by(Goal.created_at.desc()).limit(20))).scalars().all()
    plans = (await db.execute(select(Plan).where(
        Plan.owner_user_id == owner_user_id,
        Plan.status == "ACTIVE",
    ).order_by(Plan.created_at.desc()).limit(20))).scalars().all()
    actions = (await db.execute(select(SystemAction).where(
        SystemAction.owner_user_id == owner_user_id,
    ).order_by(SystemAction.created_at.desc()).limit(200))).scalars().all()
    scheduled = (await db.execute(select(ScheduledAction).where(
        ScheduledAction.owner_user_id == owner_user_id,
        ScheduledAction.scheduled_for >= start_utc,
        ScheduledAction.scheduled_for < end_utc,
    ).order_by(ScheduledAction.scheduled_for.asc()))).scalars().all()
    glow_today = int((await db.execute(select(func.coalesce(
        func.sum(GlowTransaction.final_points), 0
    )).where(
        GlowTransaction.owner_user_id == owner_user_id,
        GlowTransaction.reversed.is_(False),
        GlowTransaction.created_at >= start_utc,
        GlowTransaction.created_at < end_utc,
    ))).scalar_one())
    latest_insight = (await db.execute(select(OmegaClaim).where(
        OmegaClaim.owner_user_id == owner_user_id,
    ).order_by(OmegaClaim.updated_at.desc()).limit(1))).scalar_one_or_none()
    latest_event = (await db.execute(select(CognitiveEvent).where(
        CognitiveEvent.owner_user_id == owner_user_id,
    ).order_by(CognitiveEvent.created_at.desc()).limit(1))).scalar_one_or_none()
    latest_outcome = (await db.execute(select(Outcome).where(
        Outcome.owner_user_id == owner_user_id,
    ).order_by(Outcome.created_at.desc()).limit(1))).scalar_one_or_none()

    completed_today = [
        row for row in actions
        if row.completed_at and start_utc <= row.completed_at < end_utc
    ]
    missed_today = [
        row for row in actions
        if row.status == "MISSED"
        and row.missed_at
        and start_utc <= row.missed_at < end_utc
    ]
    open_today = [row for row in scheduled if row.status == "SCHEDULED"]
    open_actions = [row for row in reversed(actions) if row.status == "OPEN"]
    return_actions = [row for row in reversed(actions) if row.status == "MISSED"]
    next_move = None
    if open_today:
        next_move = {
            "kind": "SYSTEM_ACTION" if open_today[0].system_action_id else "SCHEDULED_ACTION",
            "id": str(open_today[0].system_action_id or open_today[0].id),
            "title": open_today[0].title,
            "scheduled_for": open_today[0].scheduled_for,
            "schedule_id": str(open_today[0].id),
        }
    elif open_actions:
        next_move = {
            "kind": "SYSTEM_ACTION",
            "id": str(open_actions[0].id),
            "title": open_actions[0].title,
            "scheduled_for": open_actions[0].due_at,
        }
    elif return_actions:
        next_move = {
            "kind": "SYSTEM_ACTION",
            "id": str(return_actions[0].id),
            "title": f"Return to: {return_actions[0].title}",
            "scheduled_for": return_actions[0].due_at,
            "returning_from_missed": True,
        }

    return {
        "date": today,
        "day_label": now.strftime("%A"),
        "local_time": now.isoformat(),
        "timezone": timezone,
        "daypart": _daypart(now.hour),
        "body": {
            "score": body_score,
            "sources": {
                "today_checkin": body_evidence,
                "body_system": by_slug["body"]["progress_percent"],
            },
            "calculation": "65% today's body check-in + 35% persisted Body System progress when a check-in exists",
        },
        "mind": {
            "score": mind_score,
            "sources": {
                "today_checkin": mind_evidence,
                "quiet_ambition": by_slug["quiet-ambition"]["progress_percent"],
                "study": by_slug["study"]["progress_percent"],
                "rebuild": by_slug["rebuild"]["progress_percent"],
            },
            "calculation": "check-in clarity/load blended with Quiet Ambition, Study, and Rebuild",
        },
        "life": {
            "score": life_score,
            "sources": {
                slug: by_slug[slug]["progress_percent"]
                for slug in ("money", "connection", "creation", "rebuild")
            },
            "calculation": "mean persisted progress of Money, Connection, Creation, and Rebuild",
        },
        "glow_today": glow_today,
        "active_systems": [
            {
                "slug": row["slug"],
                "title": row["title"],
                "progress_percent": row["progress_percent"],
                "next_move": row["next_move"],
            }
            for row in systems
            if row["progress_sources"]["total_actions"]
            or row["active_goal_count"]
            or row["progress_sources"]["latest_diagnostic_score"]
        ],
        "active_goals": [
            {
                "id": str(row.id),
                "title": row.title,
                "system_slug": row.system_slug,
                "progress_percent": row.progress_percent,
                "target_date": row.target_date,
            }
            for row in goals
        ],
        "active_plans": [
            {"id": str(row.id), "title": row.title, "orbit_id": str(row.orbit_id) if row.orbit_id else None}
            for row in plans
        ],
        "scheduled_today": [
            {
                "id": str(row.id),
                "title": row.title,
                "system_slug": row.system_slug,
                "status": row.status,
                "scheduled_for": row.scheduled_for,
            }
            for row in scheduled
        ],
        "completed_today": [
            {"id": str(row.id), "title": row.title, "system_slug": row.system_slug}
            for row in completed_today
        ],
        "missed_today": [
            {"id": str(row.id), "title": row.title, "system_slug": row.system_slug}
            for row in missed_today
        ],
        "daily_quest": {
            "key": "return_one_real_move",
            "title": "Complete one persisted System action.",
            "completed": bool(completed_today),
            "progress": 1 if completed_today else 0,
            "target": 1,
        },
        "next_move": next_move,
        "latest_insight": (
            {
                "id": str(latest_insight.id),
                "text": latest_insight.claim_text,
                "truth_status": latest_insight.truth_status,
                "provenance_label": f"OMEGA_{latest_insight.truth_status}",
            }
            if latest_insight else None
        ),
        "latest_timeline_event": (
            {
                "id": str(latest_event.id),
                "kind": latest_event.structured_payload.get("timeline_kind", latest_event.event_kind),
                "text": latest_event.content_text,
                "created_at": latest_event.created_at,
            }
            if latest_event else None
        ),
        "return_check": (
            {
                "outcome_id": str(latest_outcome.id),
                "observed_result": latest_outcome.observed_result,
                "created_at": latest_outcome.created_at,
            }
            if latest_outcome else None
        ),
        "provenance_label": "OWNER_LEDGER_CALCULATION",
    }


def system_exists(slug: str) -> bool:
    return slug in BY_SLUG
