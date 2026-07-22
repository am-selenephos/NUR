"""Social graph, feed curation, and reviewable Community moderation ledgers."""

import datetime as dt
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _created() -> Mapped[dt.datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False
    )


def _user(*, nullable: bool = False) -> Mapped[uuid.UUID | None]:
    return mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=nullable
    )


class CommunityContentRevision(Base):
    __tablename__ = "community_content_revisions"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = _user()
    target_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_title: Mapped[str | None] = mapped_column(Text)
    previous_body: Mapped[str] = mapped_column(Text, nullable=False)
    current_title: Mapped[str | None] = mapped_column(Text)
    current_body: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    created_at = _created()


class CommunitySave(Base):
    __tablename__ = "community_saves"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at = _created()


class CommunityRelationship(Base):
    __tablename__ = "community_relationships"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    target_user_id: Mapped[uuid.UUID] = _user()
    relationship_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    created_at = _created()
    updated_at = _created()


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = _user()
    target_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_owner_user_id: Mapped[uuid.UUID] = _user()
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(24), default="OPEN", server_default="OPEN", nullable=False
    )
    response_due_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class CommunityModerationAction(Base):
    __tablename__ = "community_moderation_actions"

    id = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_reports.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_user_id: Mapped[uuid.UUID] = _user()
    target_user_id: Mapped[uuid.UUID] = _user()
    action_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    reversible_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class CommunityAppeal(Base):
    __tablename__ = "community_appeals"

    id = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_reports.id", ondelete="CASCADE"), nullable=False
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_moderation_actions.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = _user()
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="OPEN", server_default="OPEN", nullable=False
    )
    reviewer_user_id: Mapped[uuid.UUID | None] = _user(nullable=True)
    review_rationale: Mapped[str | None] = mapped_column(Text)
    response_due_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class CommunityRoomSanction(Base):
    __tablename__ = "community_room_sanctions"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_user_id: Mapped[uuid.UUID] = _user()
    actor_user_id: Mapped[uuid.UUID] = _user()
    action_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_moderation_actions.id", ondelete="SET NULL")
    )
    sanction_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class CommunityModerationEvent(Base):
    __tablename__ = "community_moderation_events"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_reports.id", ondelete="SET NULL")
    )
    actor_user_id: Mapped[uuid.UUID] = _user()
    target_user_id: Mapped[uuid.UUID | None] = _user(nullable=True)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    event_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    visible_to_subject: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    created_at = _created()
