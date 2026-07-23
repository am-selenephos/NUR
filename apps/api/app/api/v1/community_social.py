"""Real bounded Community revisions, social graph, feed, and reconnect routes."""

import datetime as dt
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import delete, func, select, update

from app.api.deps import Identity, Scoped, require_csrf
from app.community.access import (
    active_member,
    contributing_member,
    content_target,
    moderator,
    user_id_by_email,
    users_blocked,
    users_connected,
)
from app.models import (
    AuditEvent,
    CommunityComment,
    CommunityContentRevision,
    CommunityMembership,
    CommunityMessage,
    CommunityPost,
    CommunityReaction,
    CommunityRelationship,
    CommunitySave,
)
from app.models._mixins import now_utc


router = APIRouter(prefix="/community", tags=["community-social"])


class ContentEditIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = Field(default=None, min_length=1, max_length=30000)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _has_change(self) -> "ContentEditIn":
        if self.title is None and self.body is None:
            raise ValueError("A title or body change is required.")
        return self


class TargetIn(BaseModel):
    target_kind: str = Field(max_length=24)
    target_id: uuid.UUID


class RelationshipIn(BaseModel):
    target_email: str = Field(min_length=3, max_length=320)
    relationship_kind: str = Field(max_length=24)


class MemberRoleIn(BaseModel):
    role: str = Field(max_length=32)


def _message_json(row: CommunityMessage) -> dict:
    return {
        "id": row.id,
        "room_id": row.room_id,
        "owner_user_id": row.owner_user_id,
        "body": row.body,
        "language_tag": row.language_tag,
        "provenance_label": row.provenance_label,
        "sequence": row.sequence,
        "revision_number": row.revision_number,
        "status": row.status,
        "is_demo": row.is_demo,
        "created_at": row.created_at,
        "edited_at": row.edited_at,
    }


def _content_summary(kind: str, row) -> dict:
    return {
        "target_kind": kind,
        "target_id": row.id,
        "room_id": row.room_id,
        "owner_user_id": row.owner_user_id,
        "title": getattr(row, "title", None),
        "body": row.body,
        "revision_number": row.revision_number,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": getattr(row, "updated_at", None) or getattr(row, "edited_at", None),
    }


@router.get("/rooms/{room_id}/messages/sync")
async def sync_messages(
    room_id: uuid.UUID,
    request: Request,
    db: Scoped,
    identity: Identity,
    after_sequence: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=250),
    wait_seconds: int = Query(default=0, ge=0, le=20),
) -> dict:
    user_id, _ = identity
    current_room, _ = await active_member(db, room_id, user_id)
    channel = f"nur:community:room:{room_id}"

    async def _rows() -> list[CommunityMessage]:
        return list((await db.execute(select(CommunityMessage).where(
            CommunityMessage.room_id == room_id,
            CommunityMessage.sequence > after_sequence,
            CommunityMessage.status.in_(["ACTIVE", "EDITED"]),
        ).order_by(CommunityMessage.sequence).limit(limit + 1))).scalars().all())

    rows: list[CommunityMessage]
    wait_state = "NOT_REQUESTED"
    if wait_seconds:
        pubsub = request.app.state.redis.pubsub()
        try:
            await pubsub.subscribe(channel)
            subscribed = await pubsub.get_message(
                ignore_subscribe_messages=False,
                timeout=1,
            )
            if subscribed is None or subscribed.get("type") != "subscribe":
                raise RuntimeError("Community realtime subscription was not acknowledged.")
            rows = await _rows()
            if not rows:
                wait_state = "WAITING"
                signal = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=wait_seconds,
                )
                wait_state = "SIGNALED" if signal is not None else "TIMED_OUT"
                await active_member(db, room_id, user_id)
                rows = await _rows()
        except HTTPException:
            raise
        except Exception:
            wait_state = "REALTIME_UNAVAILABLE_SEQUENCE_CATCHUP_ONLY"
            rows = await _rows()
        finally:
            await pubsub.aclose()
    else:
        rows = await _rows()
    has_more = len(rows) > limit
    page = rows[:limit]
    return {
        "room_id": room_id,
        "messages": [_message_json(row) for row in page],
        "after_sequence": after_sequence,
        "next_sequence": page[-1].sequence if page else after_sequence,
        "latest_sequence": current_room.next_message_sequence - 1,
        "has_more": has_more,
        "wait_state": wait_state,
        "reconnect_contract": "Resume with the last persisted sequence; no message is synthesized.",
    }


@router.patch(
    "/rooms/{room_id}/content/{target_kind}/{target_id}",
    dependencies=[Depends(require_csrf)],
)
async def edit_content(
    room_id: uuid.UUID,
    target_kind: str,
    target_id: uuid.UUID,
    payload: ContentEditIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    current_room, _ = await contributing_member(db, room_id, user_id)
    kind, row = await content_target(
        db,
        room_id=room_id,
        target_kind=target_kind,
        target_id=target_id,
        include_moderated=True,
    )
    if row.owner_user_id != user_id:
        raise HTTPException(403, "Only the content author can revise it.")
    if row.status in {"HIDDEN", "REMOVED"}:
        raise HTTPException(409, "Moderated content cannot be revised while the action is active.")
    if kind != "POST" and payload.title is not None:
        raise HTTPException(422, "Only posts have editable titles.")

    previous_title = getattr(row, "title", None)
    previous_body = row.body
    current_title = (payload.title or "").strip() or previous_title
    current_body = (payload.body or "").strip() or previous_body
    if current_title == previous_title and current_body == previous_body:
        raise HTTPException(409, "The revision does not change persisted content.")

    row.revision_number += 1
    row.body = current_body
    row.status = "EDITED"
    edited_at = now_utc()
    if kind == "POST":
        row.title = current_title
        row.updated_at = edited_at
    else:
        row.edited_at = edited_at
    revision = CommunityContentRevision(
        room_id=room_id,
        room_owner_user_id=current_room.owner_user_id,
        owner_user_id=user_id,
        target_kind=kind,
        target_id=row.id,
        revision_number=row.revision_number,
        previous_title=previous_title,
        previous_body=previous_body,
        current_title=current_title,
        current_body=current_body,
        reason=(payload.reason or "").strip() or None,
    )
    db.add(revision)
    db.add(AuditEvent(
        actor_user_id=user_id,
        event_type="community.content_revised",
        object_type=kind.lower(),
        object_id=row.id,
        event_metadata={
            "room_id": str(room_id),
            "revision_number": row.revision_number,
            "reason_supplied": revision.reason is not None,
        },
    ))
    await db.commit()
    return _content_summary(kind, row)


@router.get("/rooms/{room_id}/content/{target_kind}/{target_id}/revisions")
async def list_revisions(
    room_id: uuid.UUID,
    target_kind: str,
    target_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> list[dict]:
    user_id, _ = identity
    await active_member(db, room_id, user_id)
    kind, _ = await content_target(
        db,
        room_id=room_id,
        target_kind=target_kind,
        target_id=target_id,
        include_moderated=True,
    )
    rows = (await db.execute(select(CommunityContentRevision).where(
        CommunityContentRevision.room_id == room_id,
        CommunityContentRevision.target_kind == kind,
        CommunityContentRevision.target_id == target_id,
    ).order_by(CommunityContentRevision.revision_number.desc()))).scalars().all()
    return [{
        "id": row.id,
        "revision_number": row.revision_number,
        "previous_title": row.previous_title,
        "previous_body": row.previous_body,
        "current_title": row.current_title,
        "current_body": row.current_body,
        "reason": row.reason,
        "created_at": row.created_at,
    } for row in rows]


@router.post("/rooms/{room_id}/saves", status_code=201, dependencies=[Depends(require_csrf)])
async def save_content(
    room_id: uuid.UUID,
    payload: TargetIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    await active_member(db, room_id, user_id)
    kind, row = await content_target(
        db, room_id=room_id, target_kind=payload.target_kind, target_id=payload.target_id
    )
    existing = (await db.execute(select(CommunitySave).where(
        CommunitySave.owner_user_id == user_id,
        CommunitySave.target_kind == kind,
        CommunitySave.target_id == row.id,
    ))).scalar_one_or_none()
    if existing is not None:
        return {
            "id": existing.id,
            "target_kind": kind,
            "target_id": row.id,
            "idempotent_replay": True,
        }
    saved = CommunitySave(
        owner_user_id=user_id,
        room_id=room_id,
        target_kind=kind,
        target_id=row.id,
    )
    db.add(saved)
    await db.commit()
    return {
        "id": saved.id,
        "target_kind": kind,
        "target_id": row.id,
        "idempotent_replay": False,
    }


@router.delete(
    "/saves/{target_kind}/{target_id}",
    status_code=204,
    dependencies=[Depends(require_csrf)],
)
async def unsave_content(
    target_kind: str,
    target_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> None:
    user_id, _ = identity
    kind = target_kind.upper().strip()
    if kind not in {"POST", "COMMENT", "MESSAGE"}:
        raise HTTPException(422, "target_kind must be POST, COMMENT, or MESSAGE.")
    await db.execute(delete(CommunitySave).where(
        CommunitySave.owner_user_id == user_id,
        CommunitySave.target_kind == kind,
        CommunitySave.target_id == target_id,
    ))
    await db.commit()


@router.get("/saves")
async def list_saves(db: Scoped, identity: Identity, limit: int = Query(100, ge=1, le=250)) -> list[dict]:
    user_id, _ = identity
    rows = (await db.execute(select(CommunitySave).where(
        CommunitySave.owner_user_id == user_id,
    ).order_by(CommunitySave.created_at.desc()).limit(limit))).scalars().all()
    result = []
    for saved in rows:
        try:
            kind, target = await content_target(
                db,
                room_id=saved.room_id,
                target_kind=saved.target_kind,
                target_id=saved.target_id,
            )
            content = _content_summary(kind, target)
        except HTTPException:
            content = None
        result.append({
            "id": saved.id,
            "target_kind": saved.target_kind,
            "target_id": saved.target_id,
            "room_id": saved.room_id,
            "created_at": saved.created_at,
            "content": content,
            "availability": "AVAILABLE" if content else "UNAVAILABLE",
        })
    return result


@router.post("/relationships", dependencies=[Depends(require_csrf)])
async def set_relationship(payload: RelationshipIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    kind = payload.relationship_kind.upper().strip()
    if kind not in {"FOLLOW", "BLOCK", "MUTE"}:
        raise HTTPException(422, "relationship_kind must be FOLLOW, BLOCK, or MUTE.")
    target_user_id = await user_id_by_email(db, payload.target_email)
    if target_user_id == user_id:
        raise HTTPException(422, "A Community relationship requires another account.")
    if kind == "FOLLOW" and await users_blocked(db, user_id, target_user_id):
        raise HTTPException(409, "Following is unavailable across an active block.")
    existing = (await db.execute(select(CommunityRelationship).where(
        CommunityRelationship.owner_user_id == user_id,
        CommunityRelationship.target_user_id == target_user_id,
        CommunityRelationship.relationship_kind == kind,
    ))).scalar_one_or_none()
    if existing is None:
        existing = CommunityRelationship(
            owner_user_id=user_id,
            target_user_id=target_user_id,
            relationship_kind=kind,
        )
        db.add(existing)
    else:
        existing.status = "ACTIVE"
        existing.updated_at = now_utc()
    if kind == "BLOCK":
        await db.execute(update(CommunityRelationship).where(
            CommunityRelationship.owner_user_id == user_id,
            CommunityRelationship.target_user_id == target_user_id,
            CommunityRelationship.relationship_kind.in_(["FOLLOW", "MUTE"]),
        ).values(status="REVOKED", updated_at=now_utc()))
    await db.commit()
    return {
        "id": existing.id,
        "target_user_id": target_user_id,
        "relationship_kind": kind,
        "status": existing.status,
        "connected": await users_connected(db, user_id, target_user_id),
    }


@router.delete(
    "/relationships/{relationship_kind}/{target_user_id}",
    dependencies=[Depends(require_csrf)],
)
async def revoke_relationship(
    relationship_kind: str,
    target_user_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    kind = relationship_kind.upper().strip()
    if kind not in {"FOLLOW", "BLOCK", "MUTE"}:
        raise HTTPException(422, "relationship_kind must be FOLLOW, BLOCK, or MUTE.")
    row = (await db.execute(select(CommunityRelationship).where(
        CommunityRelationship.owner_user_id == user_id,
        CommunityRelationship.target_user_id == target_user_id,
        CommunityRelationship.relationship_kind == kind,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Community relationship not found.")
    row.status = "REVOKED"
    row.updated_at = now_utc()
    await db.commit()
    return {
        "id": row.id,
        "target_user_id": target_user_id,
        "relationship_kind": kind,
        "status": row.status,
        "connected": await users_connected(db, user_id, target_user_id),
    }


@router.get("/relationships")
async def list_relationships(db: Scoped, identity: Identity) -> list[dict]:
    user_id, _ = identity
    rows = (await db.execute(select(CommunityRelationship).where(
        CommunityRelationship.owner_user_id == user_id,
        CommunityRelationship.status == "ACTIVE",
    ).order_by(CommunityRelationship.updated_at.desc()))).scalars().all()
    return [{
        "id": row.id,
        "target_user_id": row.target_user_id,
        "relationship_kind": row.relationship_kind,
        "status": row.status,
        "connected": await users_connected(db, user_id, row.target_user_id),
        "updated_at": row.updated_at,
    } for row in rows]


@router.patch(
    "/rooms/{room_id}/members/{target_user_id}",
    dependencies=[Depends(require_csrf)],
)
async def change_member_role(
    room_id: uuid.UUID,
    target_user_id: uuid.UUID,
    payload: MemberRoleIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    current_room, actor = await moderator(db, room_id, user_id)
    if actor.role != "OWNER":
        raise HTTPException(403, "Only the room owner can change member roles.")
    target = (await db.execute(select(CommunityMembership).where(
        CommunityMembership.room_id == room_id,
        CommunityMembership.user_id == target_user_id,
    ))).scalar_one_or_none()
    if target is None:
        raise HTTPException(404, "Room member not found.")
    if target.user_id == current_room.owner_user_id:
        raise HTTPException(409, "The room owner role cannot be changed here.")
    role = payload.role.upper().strip()
    if role not in {"MODERATOR", "MEMBER", "WITNESS"}:
        raise HTTPException(422, "Role must be MODERATOR, MEMBER, or WITNESS.")
    target.role = role
    await db.commit()
    return {"room_id": room_id, "user_id": target_user_id, "role": role}


@router.delete(
    "/rooms/{room_id}/members/{target_user_id}",
    status_code=204,
    dependencies=[Depends(require_csrf)],
)
async def remove_or_leave_room(
    room_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> None:
    user_id, _ = identity
    current_room, actor = await active_member(db, room_id, user_id)
    target = (await db.execute(select(CommunityMembership).where(
        CommunityMembership.room_id == room_id,
        CommunityMembership.user_id == target_user_id,
    ))).scalar_one_or_none()
    if target is None:
        raise HTTPException(404, "Room member not found.")
    if target.user_id == current_room.owner_user_id:
        raise HTTPException(409, "The room owner cannot leave without transferring or closing the room.")
    is_self_leave = target.user_id == user_id
    if not is_self_leave and actor.role not in {"OWNER", "MODERATOR"}:
        raise HTTPException(403, "Removing another member requires moderation permission.")
    if actor.role == "MODERATOR" and target.role == "MODERATOR":
        raise HTTPException(403, "Only the owner can remove another moderator.")
    await db.delete(target)
    await db.commit()


@router.get("/feed")
async def signal_feed(
    db: Scoped,
    identity: Identity,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=200),
    before: dt.datetime | None = Query(default=None),
) -> dict:
    user_id, _ = identity
    room_ids = list((await db.execute(select(CommunityMembership.room_id).where(
        CommunityMembership.user_id == user_id,
    ))).scalars().all())
    if not room_ids:
        return {
            "items": [],
            "has_more": False,
            "next_before": None,
            "next_offset": None,
            "stop_point": "END_OF_BOUNDED_FEED",
            "release_state": "COHORT_ONLY",
            "public_discovery": False,
        }
    muted = set((await db.execute(select(CommunityRelationship.target_user_id).where(
        CommunityRelationship.owner_user_id == user_id,
        CommunityRelationship.relationship_kind == "MUTE",
        CommunityRelationship.status == "ACTIVE",
    ))).scalars().all())
    followed = set((await db.execute(select(CommunityRelationship.target_user_id).where(
        CommunityRelationship.owner_user_id == user_id,
        CommunityRelationship.relationship_kind == "FOLLOW",
        CommunityRelationship.status == "ACTIVE",
    ))).scalars().all())
    query = select(CommunityPost).where(
        CommunityPost.room_id.in_(room_ids),
        CommunityPost.status.in_(["ACTIVE", "EDITED"]),
        CommunityPost.is_demo.is_(False),
        func.fn_community_users_blocked(user_id, CommunityPost.owner_user_id).is_(False),
    )
    if muted:
        query = query.where(CommunityPost.owner_user_id.not_in(muted))
    if before is not None:
        query = query.where(CommunityPost.created_at < before)
    candidate_limit = 201
    posts = list((await db.execute(
        query.order_by(CommunityPost.created_at.desc()).limit(candidate_limit)
    )).scalars().all())
    post_ids = [post.id for post in posts]
    reaction_counts: dict[uuid.UUID, int] = {}
    comment_counts: dict[uuid.UUID, int] = {}
    saved_ids: set[uuid.UUID] = set()
    if post_ids:
        reaction_counts = dict((await db.execute(select(
            CommunityReaction.target_id, func.count(CommunityReaction.id)
        ).where(
            CommunityReaction.target_kind == "POST",
            CommunityReaction.target_id.in_(post_ids),
        ).group_by(CommunityReaction.target_id))).all())
        comment_counts = dict((await db.execute(select(
            CommunityComment.post_id, func.count(CommunityComment.id)
        ).where(
            CommunityComment.post_id.in_(post_ids),
            CommunityComment.status.in_(["ACTIVE", "EDITED"]),
            CommunityComment.is_demo.is_(False),
        ).group_by(CommunityComment.post_id))).all())
        saved_ids = set((await db.execute(select(CommunitySave.target_id).where(
            CommunitySave.owner_user_id == user_id,
            CommunitySave.target_kind == "POST",
            CommunitySave.target_id.in_(post_ids),
        ))).scalars().all())

    now = dt.datetime.now(dt.UTC)
    ranked = []
    for post in posts:
        reactions = int(reaction_counts.get(post.id, 0))
        comments = int(comment_counts.get(post.id, 0))
        age_hours = max(0.0, (now - post.created_at).total_seconds() / 3600)
        recency = max(0, 24 - min(24, int(age_hours)))
        follow_bonus = 5 if post.owner_user_id in followed else 0
        score = recency + reactions * 2 + comments * 3 + follow_bonus
        ranked.append((score, post, reactions, comments, recency, follow_bonus))
    ranked.sort(key=lambda item: (item[0], item[1].created_at, item[1].id), reverse=True)
    page = ranked[offset:offset + limit]
    has_more = offset + limit < len(ranked)
    window_truncated = len(posts) == candidate_limit
    items = [{
        **_content_summary("POST", post),
        "reaction_count": reactions,
        "comment_count": comments,
        "saved": post.id in saved_ids,
        "rank_score": score,
        "rank_explanation": {
            "recency_points": recency,
            "reaction_points": reactions * 2,
            "comment_points": comments * 3,
            "follow_points": follow_bonus,
            "candidate_source": "PERSISTED_SHARED_ROOM_MEMBERSHIP",
        },
    } for score, post, reactions, comments, recency, follow_bonus in page]
    return {
        "items": items,
        "has_more": has_more,
        "next_before": before,
        "next_offset": offset + limit if has_more else None,
        "stop_point": (
            "REQUEST_NEXT_PAGE_EXPLICITLY"
            if has_more
            else "CANDIDATE_WINDOW_LIMIT"
            if window_truncated
            else "END_OF_BOUNDED_FEED"
        ),
        "candidate_window": 200,
        "release_state": "COHORT_ONLY",
        "public_discovery": False,
        "ranking_contract": "Persisted room activity only; no invented popularity or infinite-scroll claim.",
    }


@router.get("/rooms/{room_id}/leaderboard")
async def room_leaderboard(
    room_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
    limit: int = Query(default=25, ge=1, le=100),
) -> dict:
    user_id, _ = identity
    await active_member(db, room_id, user_id)
    metrics: dict[uuid.UUID, dict[str, int]] = defaultdict(lambda: {
        "messages": 0,
        "posts": 0,
        "comments": 0,
        "reactions": 0,
    })
    specs = (
        (CommunityMessage, "messages", 1),
        (CommunityPost, "posts", 4),
        (CommunityComment, "comments", 2),
        (CommunityReaction, "reactions", 1),
    )
    points: defaultdict[uuid.UUID, int] = defaultdict(int)
    for model, label, weight in specs:
        conditions = [model.room_id == room_id]
        if hasattr(model, "status"):
            conditions.append(model.status.in_(["ACTIVE", "EDITED"]))
        if hasattr(model, "is_demo"):
            conditions.append(model.is_demo.is_(False))
        rows = (await db.execute(select(
            model.owner_user_id, func.count(model.id)
        ).where(*conditions).group_by(model.owner_user_id))).all()
        for owner_user_id, count in rows:
            value = int(count)
            metrics[owner_user_id][label] = value
            points[owner_user_id] += value * weight
    ordered = sorted(points, key=lambda uid: (points[uid], str(uid)), reverse=True)[:limit]
    return {
        "room_id": room_id,
        "entries": [{
            "rank": index,
            "user_id": participant,
            "reputation_points": points[participant],
            "persisted_contributions": metrics[participant],
        } for index, participant in enumerate(ordered, start=1)],
        "scope": "ROOM_ONLY",
        "truth_contract": "Counts include persisted non-demo contributions only.",
    }
