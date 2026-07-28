"""Explicit Community authorization and generic content lookup helpers."""

import datetime as dt
import uuid

from fastapi import HTTPException
from sqlalchemy import select, text as sa_text

from app.api.deps import Scoped
from app.models import (
    CommunityComment,
    CommunityMembership,
    CommunityMessage,
    CommunityPost,
    CommunityRoom,
    CommunityRoomSanction,
)


CONTENT_MODELS = {
    "POST": CommunityPost,
    "COMMENT": CommunityComment,
    "MESSAGE": CommunityMessage,
}


async def room(db: Scoped, room_id: uuid.UUID) -> CommunityRoom:
    row = (await db.execute(select(CommunityRoom).where(
        CommunityRoom.id == room_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Community room not found or unavailable.")
    return row


async def membership(
    db: Scoped, room_id: uuid.UUID, user_id: uuid.UUID
) -> CommunityMembership:
    row = (await db.execute(select(CommunityMembership).where(
        CommunityMembership.room_id == room_id,
        CommunityMembership.user_id == user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Community room not found or unavailable.")
    return row


async def active_member(
    db: Scoped, room_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[CommunityRoom, CommunityMembership]:
    current_room = await room(db, room_id)
    member = await membership(db, room_id, user_id)
    if current_room.status != "ACTIVE":
        raise HTTPException(409, "This room is not active.")
    return current_room, member


async def contributing_member(
    db: Scoped, room_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[CommunityRoom, CommunityMembership]:
    current_room, member = await active_member(db, room_id, user_id)
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
        raise HTTPException(
            403,
            f"Room contribution blocked by active {sanction.sanction_kind.lower()}.",
        )
    return current_room, member


async def moderator(
    db: Scoped, room_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[CommunityRoom, CommunityMembership]:
    current_room, member = await active_member(db, room_id, user_id)
    if member.role not in {"OWNER", "MODERATOR"}:
        raise HTTPException(403, "Room moderation requires OWNER or MODERATOR role.")
    return current_room, member


async def content_target(
    db: Scoped,
    *,
    room_id: uuid.UUID,
    target_kind: str,
    target_id: uuid.UUID,
    include_moderated: bool = False,
):
    kind = target_kind.upper().strip()
    model = CONTENT_MODELS.get(kind)
    if model is None:
        raise HTTPException(422, "target_kind must be POST, COMMENT, or MESSAGE.")
    row = (await db.execute(select(model).where(
        model.id == target_id,
        model.room_id == room_id,
    ))).scalar_one_or_none()
    if row is None or (
        not include_moderated and row.status not in {"ACTIVE", "EDITED"}
    ):
        raise HTTPException(404, "Community content not found in this room.")
    return kind, row


async def user_id_by_email(db: Scoped, email: str) -> uuid.UUID:
    target_id = (await db.execute(
        sa_text("SELECT fn_active_user_id_by_email(:email)"),
        {"email": email},
    )).scalar()
    if target_id is None:
        raise HTTPException(404, "No active NUR account exists for that exact email.")
    return target_id


async def users_blocked(db: Scoped, first: uuid.UUID, second: uuid.UUID) -> bool:
    return bool((await db.execute(
        sa_text("SELECT fn_community_users_blocked(:first, :second)"),
        {"first": first, "second": second},
    )).scalar_one())


async def users_connected(db: Scoped, first: uuid.UUID, second: uuid.UUID) -> bool:
    return bool((await db.execute(
        sa_text("SELECT fn_community_users_connected(:first, :second)"),
        {"first": first, "second": second},
    )).scalar_one())
