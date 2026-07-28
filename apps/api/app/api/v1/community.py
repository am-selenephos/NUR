"""Bounded Community, Group NUR, and Council collaboration routes.

Room rows are intentionally separate from each member's private cognition.
Shared content is readable only through room membership; actor audit/timeline
events stay in the actor's own ledger and never import another member's Talk,
Journal, Timeline, or Omega memory.
"""

import datetime as dt
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text as sa_text

from app.api.deps import Identity, Scoped, require_csrf
from app.services.glow_service import award_glow
from app.models import (
    AuditEvent,
    CognitiveEvent,
    CommunityComment,
    CommunityMembership,
    CommunityMessage,
    CommunityPost,
    CommunityReaction,
    CommunityRoom,
    CommunityRoomSanction,
    CouncilDecision,
    CouncilPosition,
    Orbit,
    TimelineEvent,
)

router = APIRouter(prefix="/community", tags=["community"])


class RoomIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    room_kind: str = "GROUP"
    orbit_id: uuid.UUID | None = None
    system_slug: str | None = Field(default=None, max_length=48)
    language_tag: str = Field(default="en", min_length=2, max_length=20)
    is_demo: bool = False


class MemberIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: str = "MEMBER"


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=12000)
    language_tag: str = Field(default="en", min_length=2, max_length=20)
    is_demo: bool = False


class PostIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=30000)
    language_tag: str = Field(default="en", min_length=2, max_length=20)
    is_demo: bool = False


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=12000)
    parent_comment_id: uuid.UUID | None = None
    language_tag: str = Field(default="en", min_length=2, max_length=20)
    is_demo: bool = False


class ReactionIn(BaseModel):
    target_kind: str
    target_id: uuid.UUID
    reaction: str = Field(min_length=1, max_length=32)


class PositionIn(BaseModel):
    position: str = Field(min_length=1, max_length=12000)
    evidence: list[dict | str] = Field(default_factory=list, max_length=50)
    is_minority: bool = False
    is_demo: bool = False


class DecisionIn(BaseModel):
    decision: str = Field(min_length=1, max_length=12000)
    rationale: str | None = Field(default=None, max_length=12000)
    minority_opinion: str | None = Field(default=None, max_length=12000)
    return_check_at: dt.datetime | None = None
    is_demo: bool = False


def _room_json(room: CommunityRoom, role: str) -> dict:
    return {
        "id": room.id,
        "owner_user_id": room.owner_user_id,
        "orbit_id": room.orbit_id,
        "title": room.title,
        "description": room.description,
        "room_kind": room.room_kind,
        "system_slug": room.system_slug,
        "language_tag": room.language_tag,
        "status": room.status,
        "is_demo": room.is_demo,
        "metadata": room.room_metadata,
        "current_user_role": role,
        "privacy": "Room content only. Private Talk, Journal, Timeline, and Omega stay unreachable.",
        "created_at": room.created_at,
        "updated_at": room.updated_at,
    }


async def _room(db: Scoped, room_id: uuid.UUID) -> CommunityRoom:
    row = (await db.execute(select(CommunityRoom).where(CommunityRoom.id == room_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Community room not found or unavailable.")
    return row


async def _membership(
    db: Scoped,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CommunityMembership:
    row = (await db.execute(select(CommunityMembership).where(
        CommunityMembership.room_id == room_id,
        CommunityMembership.user_id == user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Community room not found or unavailable.")
    return row


async def _active_member(
    db: Scoped,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[CommunityRoom, CommunityMembership]:
    room = await _room(db, room_id)
    member = await _membership(db, room_id, user_id)
    if room.status != "ACTIVE":
        raise HTTPException(409, "This room is not active.")
    return room, member


async def _contributing_member(
    db: Scoped,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[CommunityRoom, CommunityMembership]:
    room, member = await _active_member(db, room_id, user_id)
    sanction = (await db.execute(select(CommunityRoomSanction).where(
        CommunityRoomSanction.room_id == room_id,
        CommunityRoomSanction.target_user_id == user_id,
        CommunityRoomSanction.status == "ACTIVE",
        CommunityRoomSanction.sanction_kind.in_(["MUTE", "READ_ONLY", "BAN"]),
        (
            CommunityRoomSanction.expires_at.is_(None)
            | (CommunityRoomSanction.expires_at > dt.datetime.now(dt.UTC))
        ),
    ).order_by(CommunityRoomSanction.created_at.desc()).limit(1))).scalar_one_or_none()
    if sanction is not None:
        raise HTTPException(403, f"Room contribution blocked by active {sanction.sanction_kind.lower()}.")
    return room, member


async def _owned_room(db: Scoped, room_id: uuid.UUID, user_id: uuid.UUID) -> CommunityRoom:
    room = await _room(db, room_id)
    if room.owner_user_id != user_id:
        raise HTTPException(403, "Only the room owner can do that.")
    return room


def _record_actor_event(
    db: Scoped,
    *,
    actor_user_id: uuid.UUID,
    room: CommunityRoom,
    event_type: str,
    title: str,
    object_type: str,
    object_id: uuid.UUID,
    provenance_label: str,
) -> None:
    actor_owns_room = room.owner_user_id == actor_user_id
    actor_orbit_id = room.orbit_id if actor_owns_room else None
    payload = {
        "room_id": str(room.id),
        "room_kind": room.room_kind,
        "object_type": object_type,
        "object_id": str(object_id),
        "provenance_label": provenance_label,
        "privacy_boundary": "BOUNDED_COMMUNITY_ROOM",
    }
    db.add(CognitiveEvent(
        owner_user_id=actor_user_id,
        orbit_id=actor_orbit_id,
        event_kind="COMMUNITY_NOTE_CREATED",
        content_text=title,
        source_ref=f"{object_type}:{object_id}",
        structured_payload=payload,
    ))
    db.add(TimelineEvent(
        owner_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        time_kind="PAST",
        occurred_at=dt.datetime.now(dt.UTC),
        source_type=object_type.upper(),
        source_id=object_id,
        group_id=actor_orbit_id,
        orbit_id=actor_orbit_id,
        status="COMPLETED",
        event_payload=payload,
    ))
    db.add(AuditEvent(
        actor_user_id=actor_user_id,
        event_type=event_type,
        object_type=object_type,
        object_id=object_id,
        event_metadata=payload,
    ))


async def _award_community_glow(
    db: Scoped,
    *,
    owner_user_id: uuid.UUID,
    event_type: str,
    source_kind: str,
    source_id: uuid.UUID,
) -> dict:
    """Server-side Glow for a persisted community action.

    A cap, anti-spam, or DEMO gate must never undo the underlying action, so
    every 409 collapses to a gated no-award. A 422 means the reward rules are
    stale (a deploy defect, not a user error) — the action still persists and
    the award is reported unavailable rather than failing the request.
    """
    try:
        result = await award_glow(
            db,
            owner_user_id=owner_user_id,
            event_type=event_type,
            source_kind=source_kind,
            source_id=source_id,
            orbit_id=None,
            idempotency_key=f"{event_type}:{source_id}",
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            return {"awarded_points": 0, "status": "GLOW_GATED", "note": str(exc.detail)}
        if exc.status_code == 422:
            return {"awarded_points": 0, "status": "GLOW_UNAVAILABLE", "note": str(exc.detail)}
        raise
    return {
        "awarded_points": result.transaction.final_points,
        "transaction_id": str(result.transaction.id),
        "idempotent_replay": result.idempotent_replay,
        "status": "AWARDED",
    }


@router.post("/rooms", status_code=201, dependencies=[Depends(require_csrf)])
async def create_room(payload: RoomIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room_kind = payload.room_kind.upper().strip()
    if room_kind not in {"GROUP", "COUNCIL", "SYSTEM", "PROJECT", "COMMUNITY"}:
        raise HTTPException(422, "Unsupported room kind.")
    if payload.orbit_id:
        orbit = (await db.execute(select(Orbit).where(
            Orbit.id == payload.orbit_id,
            Orbit.owner_user_id == user_id,
        ))).scalar_one_or_none()
        if orbit is None:
            raise HTTPException(404, "Orbit not found.")
    room = CommunityRoom(
        owner_user_id=user_id,
        orbit_id=payload.orbit_id,
        title=payload.title.strip(),
        description=payload.description,
        room_kind=room_kind,
        system_slug=payload.system_slug,
        language_tag=payload.language_tag,
        is_demo=payload.is_demo,
    )
    db.add(room)
    await db.flush()
    member = CommunityMembership(
        room_id=room.id,
        room_owner_user_id=user_id,
        user_id=user_id,
        role="OWNER",
    )
    db.add(member)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COMMUNITY_ROOM_CREATED",
        title=f"Created {room.room_kind.title()} room: {room.title}",
        object_type="community_room",
        object_id=room.id,
        provenance_label="OWNER_WRITTEN",
    )
    await db.commit()
    return _room_json(room, "OWNER")


@router.get("/rooms")
async def list_rooms(db: Scoped, identity: Identity) -> list[dict]:
    user_id, _ = identity
    rows = (await db.execute(
        select(CommunityRoom, CommunityMembership.role)
        .join(CommunityMembership, CommunityMembership.room_id == CommunityRoom.id)
        .where(CommunityMembership.user_id == user_id)
        .order_by(CommunityRoom.updated_at.desc())
    )).all()
    return [_room_json(room, role) for room, role in rows]


@router.get("/rooms/{room_id}")
async def get_room(room_id: uuid.UUID, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room = await _room(db, room_id)
    member = await _membership(db, room_id, user_id)
    return _room_json(room, member.role)


@router.post("/rooms/{room_id}/members", status_code=201, dependencies=[Depends(require_csrf)])
async def add_member(room_id: uuid.UUID, payload: MemberIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room = await _owned_room(db, room_id, user_id)
    role = payload.role.upper().strip()
    if role not in {"MODERATOR", "MEMBER", "WITNESS"}:
        raise HTTPException(422, "Role must be MODERATOR, MEMBER, or WITNESS.")
    # RLS shows a user only their own users row, so the invitee is resolved
    # through the capsule-style SECURITY DEFINER lookup, never a table read.
    target_id = (await db.execute(
        sa_text("SELECT fn_active_user_id_by_email(:em)"),
        {"em": payload.email},
    )).scalar()
    if target_id is None:
        raise HTTPException(404, "No active NUR account exists for that exact email.")
    blocked = bool((await db.execute(
        sa_text("SELECT fn_community_users_blocked(:a, :b)"),
        {"a": user_id, "b": target_id},
    )).scalar_one())
    if blocked:
        raise HTTPException(409, "Room membership cannot be added across an active block.")
    exists = (await db.execute(select(CommunityMembership).where(
        CommunityMembership.room_id == room.id,
        CommunityMembership.user_id == target_id,
    ))).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "That account is already a room member.")
    member = CommunityMembership(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        user_id=target_id,
        role=role,
    )
    db.add(member)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COMMUNITY_MEMBER_ADDED",
        title=f"Added a {role.lower()} to {room.title}.",
        object_type="community_membership",
        object_id=member.id,
        provenance_label="OWNER_ACTION",
    )
    await db.commit()
    return {"id": member.id, "room_id": room.id, "user_id": target_id, "role": role}


@router.get("/rooms/{room_id}/members")
async def list_members(room_id: uuid.UUID, db: Scoped, identity: Identity) -> list[dict]:
    user_id, _ = identity
    await _membership(db, room_id, user_id)
    rows = (await db.execute(select(CommunityMembership).where(
        CommunityMembership.room_id == room_id,
    ).order_by(CommunityMembership.joined_at))).scalars().all()
    return [{
        "id": row.id,
        "user_id": row.user_id,
        "role": row.role,
        "joined_at": row.joined_at,
    } for row in rows]


@router.post("/rooms/{room_id}/messages", status_code=201, dependencies=[Depends(require_csrf)])
async def create_message(
    room_id: uuid.UUID,
    payload: MessageIn,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    room, member = await _contributing_member(db, room_id, user_id)
    sequence = (await db.execute(
        sa_text("SELECT fn_next_community_message_sequence(:room_id)"),
        {"room_id": room.id},
    )).scalar_one()
    row = CommunityMessage(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        owner_user_id=user_id,
        body=payload.body.strip(),
        language_tag=payload.language_tag,
        provenance_label="OWNER_WRITTEN" if member.role == "OWNER" else "MEMBER_WRITTEN",
        sequence=sequence,
        is_demo=payload.is_demo,
    )
    db.add(row)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COMMUNITY_MESSAGE_CREATED",
        title=f"Message added in {room.title}.",
        object_type="community_message",
        object_id=row.id,
        provenance_label=row.provenance_label,
    )
    glow = await _award_community_glow(
        db,
        owner_user_id=user_id,
        event_type="community.message_posted",
        source_kind="COMMUNITY_MESSAGE",
        source_id=row.id,
    )
    await db.commit()
    realtime_signal = "PUBLISHED"
    try:
        await request.app.state.redis.publish(
            f"nur:community:room:{room.id}",
            json.dumps({"room_id": str(room.id), "sequence": row.sequence}),
        )
    except Exception:
        realtime_signal = "UNAVAILABLE_RECONNECT_WITH_SEQUENCE"
    return {
        "id": row.id, "room_id": row.room_id, "owner_user_id": row.owner_user_id,
        "body": row.body, "language_tag": row.language_tag,
        "provenance_label": row.provenance_label, "is_demo": row.is_demo,
        "sequence": row.sequence, "revision_number": row.revision_number,
        "status": row.status, "created_at": row.created_at, "glow": glow,
        "realtime_signal": realtime_signal,
    }


@router.get("/rooms/{room_id}/messages")
async def list_messages(room_id: uuid.UUID, db: Scoped, identity: Identity, limit: int = 100) -> list[dict]:
    user_id, _ = identity
    await _membership(db, room_id, user_id)
    rows = (await db.execute(select(CommunityMessage).where(
        CommunityMessage.room_id == room_id,
        CommunityMessage.status.in_(["ACTIVE", "EDITED"]),
    ).order_by(CommunityMessage.sequence.asc()).limit(min(limit, 250)))).scalars().all()
    return [{
        "id": row.id, "room_id": row.room_id, "owner_user_id": row.owner_user_id,
        "body": row.body, "language_tag": row.language_tag,
        "provenance_label": row.provenance_label, "is_demo": row.is_demo,
        "sequence": row.sequence, "revision_number": row.revision_number,
        "status": row.status, "created_at": row.created_at,
    } for row in rows]


@router.post("/rooms/{room_id}/posts", status_code=201, dependencies=[Depends(require_csrf)])
async def create_post(room_id: uuid.UUID, payload: PostIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room, member = await _contributing_member(db, room_id, user_id)
    row = CommunityPost(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        owner_user_id=user_id,
        title=payload.title.strip(),
        body=payload.body.strip(),
        language_tag=payload.language_tag,
        provenance_label="OWNER_WRITTEN" if member.role == "OWNER" else "MEMBER_WRITTEN",
        is_demo=payload.is_demo,
    )
    db.add(row)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COMMUNITY_POST_CREATED",
        title=f"Post created in {room.title}: {row.title}",
        object_type="community_post",
        object_id=row.id,
        provenance_label=row.provenance_label,
    )
    glow = await _award_community_glow(
        db,
        owner_user_id=user_id,
        event_type="community.post_created",
        source_kind="COMMUNITY_POST",
        source_id=row.id,
    )
    await db.commit()
    return {
        "id": row.id, "room_id": row.room_id, "owner_user_id": row.owner_user_id,
        "title": row.title, "body": row.body, "language_tag": row.language_tag,
        "provenance_label": row.provenance_label, "is_demo": row.is_demo,
        "revision_number": row.revision_number, "status": row.status,
        "created_at": row.created_at, "glow": glow,
    }


@router.get("/rooms/{room_id}/posts")
async def list_posts(room_id: uuid.UUID, db: Scoped, identity: Identity, limit: int = 100) -> list[dict]:
    user_id, _ = identity
    await _membership(db, room_id, user_id)
    rows = (await db.execute(select(CommunityPost).where(
        CommunityPost.room_id == room_id,
        CommunityPost.status.in_(["ACTIVE", "EDITED"]),
    ).order_by(CommunityPost.created_at.desc()).limit(min(limit, 250)))).scalars().all()
    return [{
        "id": row.id, "room_id": row.room_id, "owner_user_id": row.owner_user_id,
        "title": row.title, "body": row.body, "language_tag": row.language_tag,
        "provenance_label": row.provenance_label, "is_demo": row.is_demo,
        "revision_number": row.revision_number, "status": row.status,
        "created_at": row.created_at,
    } for row in rows]


@router.post("/rooms/{room_id}/posts/{post_id}/comments", status_code=201, dependencies=[Depends(require_csrf)])
async def create_comment(
    room_id: uuid.UUID,
    post_id: uuid.UUID,
    payload: CommentIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    user_id, _ = identity
    room, _ = await _contributing_member(db, room_id, user_id)
    post = (await db.execute(select(CommunityPost).where(
        CommunityPost.id == post_id,
        CommunityPost.room_id == room.id,
    ))).scalar_one_or_none()
    if post is None:
        raise HTTPException(404, "Post not found in this room.")
    if payload.parent_comment_id:
        parent = (await db.execute(select(CommunityComment).where(
            CommunityComment.id == payload.parent_comment_id,
            CommunityComment.room_id == room.id,
            CommunityComment.post_id == post.id,
        ))).scalar_one_or_none()
        if parent is None:
            raise HTTPException(404, "Parent comment not found in this post.")
    row = CommunityComment(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        post_id=post.id,
        parent_comment_id=payload.parent_comment_id,
        owner_user_id=user_id,
        body=payload.body.strip(),
        language_tag=payload.language_tag,
        is_demo=payload.is_demo,
    )
    db.add(row)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COMMUNITY_COMMENT_CREATED",
        title=f"Comment added to {post.title}.",
        object_type="community_comment",
        object_id=row.id,
        provenance_label="MEMBER_WRITTEN",
    )
    glow = await _award_community_glow(
        db,
        owner_user_id=user_id,
        event_type="community.comment_created",
        source_kind="COMMUNITY_COMMENT",
        source_id=row.id,
    )
    await db.commit()
    return {
        "id": row.id, "room_id": row.room_id, "post_id": row.post_id,
        "parent_comment_id": row.parent_comment_id, "owner_user_id": row.owner_user_id,
        "body": row.body, "language_tag": row.language_tag,
        "revision_number": row.revision_number, "status": row.status,
        "is_demo": row.is_demo, "created_at": row.created_at, "glow": glow,
    }


@router.get("/rooms/{room_id}/posts/{post_id}/comments")
async def list_comments(
    room_id: uuid.UUID,
    post_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
    limit: int = 200,
) -> list[dict]:
    user_id, _ = identity
    await _membership(db, room_id, user_id)
    post = (await db.execute(select(CommunityPost).where(
        CommunityPost.id == post_id,
        CommunityPost.room_id == room_id,
    ))).scalar_one_or_none()
    if post is None:
        raise HTTPException(404, "Post not found in this room.")
    rows = (await db.execute(select(CommunityComment).where(
        CommunityComment.room_id == room_id,
        CommunityComment.post_id == post_id,
        CommunityComment.status.in_(["ACTIVE", "EDITED"]),
    ).order_by(CommunityComment.created_at.asc()).limit(min(limit, 500)))).scalars().all()
    return [{
        "id": row.id, "room_id": row.room_id, "post_id": row.post_id,
        "parent_comment_id": row.parent_comment_id, "owner_user_id": row.owner_user_id,
        "body": row.body, "language_tag": row.language_tag,
        "revision_number": row.revision_number, "status": row.status,
        "is_demo": row.is_demo, "created_at": row.created_at,
    } for row in rows]


@router.post("/rooms/{room_id}/reactions", status_code=201, dependencies=[Depends(require_csrf)])
async def create_reaction(room_id: uuid.UUID, payload: ReactionIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room, _ = await _contributing_member(db, room_id, user_id)
    kind = payload.target_kind.upper().strip()
    model = {"POST": CommunityPost, "COMMENT": CommunityComment, "MESSAGE": CommunityMessage}.get(kind)
    if model is None:
        raise HTTPException(422, "target_kind must be POST, COMMENT, or MESSAGE.")
    target = (await db.execute(select(model).where(
        model.id == payload.target_id,
        model.room_id == room.id,
    ))).scalar_one_or_none()
    if target is None:
        raise HTTPException(404, "Reaction target not found in this room.")
    if target.status not in {"ACTIVE", "EDITED"}:
        raise HTTPException(409, "Moderated content cannot receive reactions.")
    duplicate = (await db.execute(select(CommunityReaction).where(
        CommunityReaction.owner_user_id == user_id,
        CommunityReaction.target_kind == kind,
        CommunityReaction.target_id == payload.target_id,
        CommunityReaction.reaction == payload.reaction.strip().upper(),
    ))).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(409, "You already added that reaction.")
    row = CommunityReaction(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        owner_user_id=user_id,
        target_kind=kind,
        target_id=payload.target_id,
        reaction=payload.reaction.strip().upper(),
    )
    db.add(row)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COMMUNITY_REACTION_CREATED",
        title=f"Reaction added in {room.title}.",
        object_type="community_reaction",
        object_id=row.id,
        provenance_label="MEMBER_ACTION",
    )
    await db.commit()
    return {"id": row.id, "target_kind": kind, "target_id": row.target_id, "reaction": row.reaction}


@router.post("/rooms/{room_id}/positions", status_code=201, dependencies=[Depends(require_csrf)])
async def create_position(room_id: uuid.UUID, payload: PositionIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room, _ = await _contributing_member(db, room_id, user_id)
    if room.room_kind != "COUNCIL":
        raise HTTPException(409, "Positions can be added only inside a Council room.")
    row = CouncilPosition(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        owner_user_id=user_id,
        position=payload.position.strip(),
        evidence=payload.evidence,
        is_minority=payload.is_minority,
        is_demo=payload.is_demo,
    )
    db.add(row)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COUNCIL_POSITION_ADDED",
        title=f"Council position added in {room.title}.",
        object_type="council_position",
        object_id=row.id,
        provenance_label="MEMBER_WRITTEN",
    )
    glow = await _award_community_glow(
        db,
        owner_user_id=user_id,
        event_type="council.position_added",
        source_kind="COUNCIL_POSITION",
        source_id=row.id,
    )
    await db.commit()
    return {
        "id": row.id, "owner_user_id": row.owner_user_id,
        "position": row.position, "evidence": row.evidence,
        "is_minority": row.is_minority, "is_demo": row.is_demo,
        "created_at": row.created_at, "glow": glow,
    }


@router.get("/rooms/{room_id}/positions")
async def list_positions(room_id: uuid.UUID, db: Scoped, identity: Identity) -> list[dict]:
    user_id, _ = identity
    await _membership(db, room_id, user_id)
    rows = (await db.execute(select(CouncilPosition).where(
        CouncilPosition.room_id == room_id,
    ).order_by(CouncilPosition.created_at))).scalars().all()
    return [{
        "id": row.id, "owner_user_id": row.owner_user_id,
        "position": row.position, "evidence": row.evidence,
        "is_minority": row.is_minority, "is_demo": row.is_demo,
        "created_at": row.created_at,
    } for row in rows]


@router.post("/rooms/{room_id}/decision", status_code=201, dependencies=[Depends(require_csrf)])
async def create_decision(room_id: uuid.UUID, payload: DecisionIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room = await _owned_room(db, room_id, user_id)
    if room.room_kind != "COUNCIL":
        raise HTTPException(409, "A Council decision requires a Council room.")
    row = CouncilDecision(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        owner_user_id=user_id,
        decision=payload.decision.strip(),
        rationale=payload.rationale,
        minority_opinion=payload.minority_opinion,
        return_check_at=payload.return_check_at,
        is_demo=payload.is_demo,
    )
    db.add(row)
    await db.flush()
    _record_actor_event(
        db,
        actor_user_id=user_id,
        room=room,
        event_type="COUNCIL_DECISION_RECORDED",
        title=f"Council decision recorded: {row.decision[:240]}",
        object_type="council_decision",
        object_id=row.id,
        provenance_label="OWNER_DECISION",
    )
    glow = await _award_community_glow(
        db,
        owner_user_id=user_id,
        event_type="council.decision_recorded",
        source_kind="COUNCIL_DECISION",
        source_id=row.id,
    )
    await db.commit()
    return {
        "id": row.id, "decision": row.decision, "rationale": row.rationale,
        "minority_opinion": row.minority_opinion,
        "return_check_at": row.return_check_at, "is_demo": row.is_demo,
        "created_at": row.created_at,
        "glow": glow,
    }


@router.get("/rooms/{room_id}/summary")
async def room_summary(room_id: uuid.UUID, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    room = await _room(db, room_id)
    member = await _membership(db, room_id, user_id)
    counts = {}
    for name, model in {
        "messages": CommunityMessage,
        "posts": CommunityPost,
        "comments": CommunityComment,
        "positions": CouncilPosition,
        "decisions": CouncilDecision,
    }.items():
        counts[name] = int((await db.execute(select(func.count(model.id)).where(
            model.room_id == room.id,
        ))).scalar_one())
    if room.owner_user_id == user_id:
        counts["members"] = int((await db.execute(select(func.count(CommunityMembership.id)).where(
            CommunityMembership.room_id == room.id,
        ))).scalar_one())
    else:
        counts["members"] = None
    return {
        "room": _room_json(room, member.role),
        "counts": counts,
        "truth_state": "persisted_local_room_data",
        "external_public_feed": "not_connected",
    }
