"""Reviewable room moderation with reports, actions, sanctions, and appeals."""

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, text as sa_text, update

from app.api.deps import Identity, Scoped, require_csrf
from app.community.access import active_member, content_target, moderator
from app.models import (
    AuditEvent,
    CommunityAppeal,
    CommunityMembership,
    CommunityModerationAction,
    CommunityModerationEvent,
    CommunityReport,
    CommunityRoomSanction,
)
from app.models._mixins import now_utc


router = APIRouter(prefix="/community", tags=["community-moderation"])

REPORT_CATEGORIES = {
    "HARASSMENT",
    "HATE",
    "THREAT",
    "SPAM",
    "MISINFORMATION",
    "PRIVACY",
    "SELF_HARM",
    "OTHER",
}
ACTION_KINDS = {
    "NO_ACTION",
    "WARN",
    "HIDE_CONTENT",
    "REMOVE_CONTENT",
    "MUTE_MEMBER",
    "REMOVE_MEMBER",
}
APPEAL_OUTCOMES = {"UPHELD", "OVERTURNED", "DENIED"}


class ReportIn(BaseModel):
    target_kind: str = Field(max_length=24)
    target_id: uuid.UUID
    category: str = Field(max_length=48)
    details: str | None = Field(default=None, max_length=4000)


class ModerationActionIn(BaseModel):
    action_kind: str = Field(max_length=32)
    rationale: str = Field(min_length=3, max_length=12000)
    duration_hours: int | None = Field(default=None, ge=1, le=720)


class AppealIn(BaseModel):
    body: str = Field(min_length=3, max_length=12000)


class AppealReviewIn(BaseModel):
    outcome: str = Field(max_length=24)
    rationale: str = Field(min_length=3, max_length=12000)


def _report_json(row: CommunityReport) -> dict:
    now = dt.datetime.now(dt.UTC)
    return {
        "id": row.id,
        "room_id": row.room_id,
        "reporter_user_id": row.owner_user_id,
        "target_kind": row.target_kind,
        "target_id": row.target_id,
        "target_owner_user_id": row.target_owner_user_id,
        "category": row.category,
        "details": row.details,
        "status": row.status,
        "response_due_at": row.response_due_at,
        "response_overdue": row.resolved_at is None and row.response_due_at < now,
        "resolved_at": row.resolved_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _action_json(row: CommunityModerationAction) -> dict:
    return {
        "id": row.id,
        "report_id": row.report_id,
        "room_id": row.room_id,
        "actor_user_id": row.actor_user_id,
        "target_user_id": row.target_user_id,
        "action_kind": row.action_kind,
        "rationale": row.rationale,
        "status": row.status,
        "reversible_until": row.reversible_until,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _appeal_json(row: CommunityAppeal) -> dict:
    now = dt.datetime.now(dt.UTC)
    return {
        "id": row.id,
        "report_id": row.report_id,
        "action_id": row.action_id,
        "room_id": row.room_id,
        "owner_user_id": row.owner_user_id,
        "body": row.body,
        "status": row.status,
        "reviewer_user_id": row.reviewer_user_id,
        "review_rationale": row.review_rationale,
        "response_due_at": row.response_due_at,
        "response_overdue": row.resolved_at is None and row.response_due_at < now,
        "resolved_at": row.resolved_at,
        "created_at": row.created_at,
    }


def _record_event(
    db: Scoped,
    *,
    room_id: uuid.UUID,
    room_owner_user_id: uuid.UUID,
    report_id: uuid.UUID | None,
    actor_user_id: uuid.UUID,
    target_user_id: uuid.UUID | None,
    event_type: str,
    metadata: dict,
    visible_to_subject: bool = True,
) -> None:
    db.add(CommunityModerationEvent(
        room_id=room_id,
        room_owner_user_id=room_owner_user_id,
        report_id=report_id,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        event_type=event_type,
        event_metadata=metadata,
        visible_to_subject=visible_to_subject,
    ))
    db.add(AuditEvent(
        actor_user_id=actor_user_id,
        event_type=f"community.moderation.{event_type.lower()}",
        object_type="community_report" if report_id else "community_room",
        object_id=report_id or room_id,
        event_metadata={"room_id": str(room_id), **metadata},
    ))


async def _set_content_status(
    db: Scoped,
    *,
    target_kind: str,
    target_id: uuid.UUID,
    room_id: uuid.UUID,
    status: str,
) -> None:
    changed = bool((await db.execute(sa_text("""
        SELECT fn_set_community_content_status(
            :target_kind, :target_id, :room_id, :status
        )
    """), {
        "target_kind": target_kind,
        "target_id": target_id,
        "room_id": room_id,
        "status": status,
    })).scalar_one())
    if not changed:
        raise HTTPException(409, "Moderation target could not be updated.")


@router.post("/rooms/{room_id}/reports", status_code=201, dependencies=[Depends(require_csrf)])
async def create_report(
    room_id: uuid.UUID,
    payload: ReportIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    current_room, _ = await active_member(db, room_id, user_id)
    category = payload.category.upper().strip()
    if category not in REPORT_CATEGORIES:
        raise HTTPException(422, "Unsupported moderation report category.")
    kind, target = await content_target(
        db,
        room_id=room_id,
        target_kind=payload.target_kind,
        target_id=payload.target_id,
        include_moderated=True,
    )
    if target.owner_user_id == user_id:
        raise HTTPException(422, "Use content revision instead of reporting your own content.")
    existing = (await db.execute(select(CommunityReport).where(
        CommunityReport.owner_user_id == user_id,
        CommunityReport.target_kind == kind,
        CommunityReport.target_id == target.id,
        CommunityReport.category == category,
    ))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, "This report is already persisted.")
    now = now_utc()
    report = CommunityReport(
        room_id=room_id,
        room_owner_user_id=current_room.owner_user_id,
        owner_user_id=user_id,
        target_kind=kind,
        target_id=target.id,
        target_owner_user_id=target.owner_user_id,
        category=category,
        details=(payload.details or "").strip() or None,
        response_due_at=now + dt.timedelta(hours=48),
    )
    db.add(report)
    await db.flush()
    _record_event(
        db,
        room_id=room_id,
        room_owner_user_id=current_room.owner_user_id,
        report_id=report.id,
        actor_user_id=user_id,
        target_user_id=target.owner_user_id,
        event_type="REPORT_CREATED",
        metadata={"category": category, "target_kind": kind, "target_id": str(target.id)},
    )
    await db.commit()
    return _report_json(report)


@router.get("/moderation/reports")
async def visible_reports(
    db: Scoped,
    identity: Identity,
    limit: int = Query(default=100, ge=1, le=250),
) -> list[dict]:
    _user_id, _ = identity
    rows = (await db.execute(select(CommunityReport).order_by(
        CommunityReport.created_at.desc()
    ).limit(limit))).scalars().all()
    return [_report_json(row) for row in rows]


@router.get("/rooms/{room_id}/moderation/queue")
async def moderation_queue(
    room_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
    status: str | None = Query(default=None, max_length=24),
) -> dict:
    user_id, _ = identity
    await moderator(db, room_id, user_id)
    query = select(CommunityReport).where(CommunityReport.room_id == room_id)
    if status:
        query = query.where(CommunityReport.status == status.upper().strip())
    rows = (await db.execute(query.order_by(
        CommunityReport.response_due_at,
        CommunityReport.created_at,
    ))).scalars().all()
    return {
        "room_id": room_id,
        "reports": [_report_json(row) for row in rows],
        "response_slo_hours": 48,
        "release_state": "COHORT_ONLY",
    }


@router.post(
    "/rooms/{room_id}/moderation/reports/{report_id}/actions",
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def take_moderation_action(
    room_id: uuid.UUID,
    report_id: uuid.UUID,
    payload: ModerationActionIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    current_room, actor = await moderator(db, room_id, user_id)
    action_kind = payload.action_kind.upper().strip()
    if action_kind not in ACTION_KINDS:
        raise HTTPException(422, "Unsupported moderation action.")
    report = (await db.execute(select(CommunityReport).where(
        CommunityReport.id == report_id,
        CommunityReport.room_id == room_id,
    ))).scalar_one_or_none()
    if report is None:
        raise HTTPException(404, "Moderation report not found.")
    if report.status not in {"OPEN", "UNDER_REVIEW"}:
        raise HTTPException(409, "This report already has a terminal action or appeal.")
    kind, target = await content_target(
        db,
        room_id=room_id,
        target_kind=report.target_kind,
        target_id=report.target_id,
        include_moderated=True,
    )
    if action_kind in {"MUTE_MEMBER", "REMOVE_MEMBER"}:
        if report.target_owner_user_id == current_room.owner_user_id:
            raise HTTPException(409, "The room owner cannot be sanctioned as a member.")
        if actor.role == "MODERATOR":
            target_membership = (await db.execute(select(CommunityMembership).where(
                CommunityMembership.room_id == room_id,
                CommunityMembership.user_id == report.target_owner_user_id,
            ))).scalar_one_or_none()
            if target_membership is not None and target_membership.role == "MODERATOR":
                raise HTTPException(403, "Only the room owner can sanction another moderator.")

    now = now_utc()
    action = CommunityModerationAction(
        report_id=report.id,
        room_id=room_id,
        room_owner_user_id=current_room.owner_user_id,
        actor_user_id=user_id,
        target_user_id=report.target_owner_user_id,
        action_kind=action_kind,
        rationale=payload.rationale.strip(),
        reversible_until=(
            now + dt.timedelta(days=7) if action_kind != "NO_ACTION" else None
        ),
    )
    db.add(action)
    await db.flush()

    if action_kind == "HIDE_CONTENT":
        await _set_content_status(
            db, target_kind=kind, target_id=target.id, room_id=room_id, status="HIDDEN"
        )
    elif action_kind == "REMOVE_CONTENT":
        await _set_content_status(
            db, target_kind=kind, target_id=target.id, room_id=room_id, status="REMOVED"
        )
    elif action_kind == "MUTE_MEMBER":
        duration = payload.duration_hours or 168
        db.add(CommunityRoomSanction(
            room_id=room_id,
            room_owner_user_id=current_room.owner_user_id,
            target_user_id=report.target_owner_user_id,
            actor_user_id=user_id,
            action_id=action.id,
            sanction_kind="MUTE",
            reason=payload.rationale.strip(),
            expires_at=now + dt.timedelta(hours=duration),
        ))
    elif action_kind == "REMOVE_MEMBER":
        if actor.role != "OWNER":
            raise HTTPException(403, "Only the room owner can remove a member by moderation action.")
        membership = (await db.execute(select(CommunityMembership).where(
            CommunityMembership.room_id == room_id,
            CommunityMembership.user_id == report.target_owner_user_id,
        ))).scalar_one_or_none()
        if membership is None:
            raise HTTPException(409, "The reported author is no longer a room member.")
        await db.delete(membership)

    report.status = "DISMISSED" if action_kind == "NO_ACTION" else "ACTIONED"
    report.resolved_at = now
    report.updated_at = now
    _record_event(
        db,
        room_id=room_id,
        room_owner_user_id=current_room.owner_user_id,
        report_id=report.id,
        actor_user_id=user_id,
        target_user_id=report.target_owner_user_id,
        event_type="ACTION_TAKEN",
        metadata={
            "action_id": str(action.id),
            "action_kind": action_kind,
            "target_kind": kind,
            "target_id": str(target.id),
        },
    )
    await db.commit()
    return {"report": _report_json(report), "action": _action_json(action)}


@router.get("/moderation/actions/{action_id}")
async def get_moderation_action(
    action_id: uuid.UUID, db: Scoped, identity: Identity
) -> dict:
    _user_id, _ = identity
    row = (await db.execute(select(CommunityModerationAction).where(
        CommunityModerationAction.id == action_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Moderation action not found.")
    return _action_json(row)


@router.post(
    "/moderation/actions/{action_id}/appeals",
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_appeal(
    action_id: uuid.UUID,
    payload: AppealIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    action = (await db.execute(select(CommunityModerationAction).where(
        CommunityModerationAction.id == action_id,
    ))).scalar_one_or_none()
    if action is None or action.target_user_id != user_id:
        raise HTTPException(404, "Moderation action not found.")
    if action.status != "ACTIVE" or action.action_kind == "NO_ACTION":
        raise HTTPException(409, "This moderation action is not appealable.")
    existing = (await db.execute(select(CommunityAppeal).where(
        CommunityAppeal.action_id == action.id,
        CommunityAppeal.owner_user_id == user_id,
    ))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, "An appeal already exists for this action.")
    now = now_utc()
    appeal = CommunityAppeal(
        report_id=action.report_id,
        action_id=action.id,
        room_id=action.room_id,
        room_owner_user_id=action.room_owner_user_id,
        owner_user_id=user_id,
        body=payload.body.strip(),
        response_due_at=now + dt.timedelta(hours=72),
    )
    db.add(appeal)
    await db.flush()
    _record_event(
        db,
        room_id=action.room_id,
        room_owner_user_id=action.room_owner_user_id,
        report_id=action.report_id,
        actor_user_id=user_id,
        target_user_id=user_id,
        event_type="APPEAL_CREATED",
        metadata={"appeal_id": str(appeal.id), "action_id": str(action.id)},
    )
    await db.commit()
    return _appeal_json(appeal)


@router.get("/moderation/appeals")
async def visible_appeals(
    db: Scoped,
    identity: Identity,
    limit: int = Query(default=100, ge=1, le=250),
) -> list[dict]:
    _user_id, _ = identity
    rows = (await db.execute(select(CommunityAppeal).order_by(
        CommunityAppeal.created_at.desc()
    ).limit(limit))).scalars().all()
    return [_appeal_json(row) for row in rows]


@router.get("/rooms/{room_id}/moderation/appeals")
async def appeal_queue(room_id: uuid.UUID, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    await moderator(db, room_id, user_id)
    rows = (await db.execute(select(CommunityAppeal).where(
        CommunityAppeal.room_id == room_id,
    ).order_by(CommunityAppeal.response_due_at, CommunityAppeal.created_at))).scalars().all()
    return {
        "room_id": room_id,
        "appeals": [_appeal_json(row) for row in rows],
        "response_slo_hours": 72,
    }


@router.post(
    "/rooms/{room_id}/moderation/appeals/{appeal_id}/review",
    dependencies=[Depends(require_csrf)],
)
async def review_appeal(
    room_id: uuid.UUID,
    appeal_id: uuid.UUID,
    payload: AppealReviewIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    current_room, reviewer = await moderator(db, room_id, user_id)
    outcome = payload.outcome.upper().strip()
    if outcome not in APPEAL_OUTCOMES:
        raise HTTPException(422, "Appeal outcome must be UPHELD, OVERTURNED, or DENIED.")
    appeal = (await db.execute(select(CommunityAppeal).where(
        CommunityAppeal.id == appeal_id,
        CommunityAppeal.room_id == room_id,
    ))).scalar_one_or_none()
    if appeal is None:
        raise HTTPException(404, "Community appeal not found.")
    if appeal.status != "OPEN":
        raise HTTPException(409, "This appeal has already been reviewed.")
    action = (await db.execute(select(CommunityModerationAction).where(
        CommunityModerationAction.id == appeal.action_id,
    ))).scalar_one()
    report = (await db.execute(select(CommunityReport).where(
        CommunityReport.id == appeal.report_id,
    ))).scalar_one()
    now = now_utc()
    if outcome == "OVERTURNED":
        action.status = "REVERSED"
        action.updated_at = now
        if action.action_kind in {"HIDE_CONTENT", "REMOVE_CONTENT"}:
            _kind, target = await content_target(
                db,
                room_id=room_id,
                target_kind=report.target_kind,
                target_id=report.target_id,
                include_moderated=True,
            )
            await _set_content_status(
                db,
                target_kind=report.target_kind,
                target_id=report.target_id,
                room_id=room_id,
                status="EDITED" if target.revision_number > 1 else "ACTIVE",
            )
        elif action.action_kind == "MUTE_MEMBER":
            await db.execute(update(CommunityRoomSanction).where(
                CommunityRoomSanction.action_id == action.id,
                CommunityRoomSanction.status == "ACTIVE",
            ).values(status="REVERSED", updated_at=now))
        elif action.action_kind == "REMOVE_MEMBER":
            if reviewer.role != "OWNER":
                raise HTTPException(403, "Only the room owner can restore removed membership.")
            existing = (await db.execute(select(CommunityMembership).where(
                CommunityMembership.room_id == room_id,
                CommunityMembership.user_id == action.target_user_id,
            ))).scalar_one_or_none()
            if existing is None:
                db.add(CommunityMembership(
                    room_id=room_id,
                    room_owner_user_id=current_room.owner_user_id,
                    user_id=action.target_user_id,
                    role="MEMBER",
                ))
    appeal.status = outcome
    appeal.reviewer_user_id = user_id
    appeal.review_rationale = payload.rationale.strip()
    appeal.resolved_at = now
    appeal.updated_at = now
    report.status = "CLOSED"
    report.updated_at = now
    _record_event(
        db,
        room_id=room_id,
        room_owner_user_id=current_room.owner_user_id,
        report_id=report.id,
        actor_user_id=user_id,
        target_user_id=appeal.owner_user_id,
        event_type="APPEAL_REVIEWED",
        metadata={
            "appeal_id": str(appeal.id),
            "action_id": str(action.id),
            "outcome": outcome,
            "independent_reviewer": user_id != action.actor_user_id,
        },
    )
    await db.commit()
    return {
        "appeal": _appeal_json(appeal),
        "action": _action_json(action),
        "report": _report_json(report),
        "independent_reviewer": user_id != action.actor_user_id,
    }


@router.get("/rooms/{room_id}/moderation/events")
async def moderation_events(
    room_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
    limit: int = Query(default=100, ge=1, le=250),
) -> list[dict]:
    _user_id, _ = identity
    rows = (await db.execute(select(CommunityModerationEvent).where(
        CommunityModerationEvent.room_id == room_id,
    ).order_by(CommunityModerationEvent.created_at.desc()).limit(limit))).scalars().all()
    if not rows:
        raise HTTPException(404, "No visible moderation events found for this room.")
    return [{
        "id": row.id,
        "room_id": row.room_id,
        "report_id": row.report_id,
        "actor_user_id": row.actor_user_id,
        "target_user_id": row.target_user_id,
        "event_type": row.event_type,
        "event_metadata": row.event_metadata,
        "visible_to_subject": row.visible_to_subject,
        "created_at": row.created_at,
    } for row in rows]
