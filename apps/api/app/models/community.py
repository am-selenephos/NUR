"""Bounded multi-user Community, Group NUR, and Council ledgers."""

import datetime as dt
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _created() -> Mapped[dt.datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False
    )


def _owner() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


def _updated() -> Mapped[dt.datetime]:
    return _created()


class CommunityRoom(Base):
    __tablename__ = "community_rooms"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    room_kind: Mapped[str] = mapped_column(String(32), default="GROUP", server_default="GROUP", nullable=False)
    system_slug: Mapped[str | None] = mapped_column(String(48))
    language_tag: Mapped[str] = mapped_column(String(20), default="en", server_default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", server_default="ACTIVE", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    room_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at = _created()
    updated_at = _created()


class CommunityMembership(Base):
    __tablename__ = "community_memberships"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), default="MEMBER", server_default="MEMBER", nullable=False)
    joined_at = _created()


class CommunityMessage(Base):
    __tablename__ = "community_messages"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language_tag: Mapped[str] = mapped_column(String(20), default="en", server_default="en", nullable=False)
    provenance_label: Mapped[str] = mapped_column(
        String(48), default="MEMBER_WRITTEN", server_default="MEMBER_WRITTEN", nullable=False
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    created_at = _created()


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language_tag: Mapped[str] = mapped_column(String(20), default="en", server_default="en", nullable=False)
    provenance_label: Mapped[str] = mapped_column(
        String(48), default="MEMBER_WRITTEN", server_default="MEMBER_WRITTEN", nullable=False
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    created_at = _created()
    updated_at = _created()


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False
    )
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_comments.id", ondelete="CASCADE")
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language_tag: Mapped[str] = mapped_column(String(20), default="en", server_default="en", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    created_at = _created()


class CommunityReaction(Base):
    __tablename__ = "community_reactions"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reaction: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at = _created()


class CouncilPosition(Base):
    __tablename__ = "council_positions"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    is_minority: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    created_at = _created()


class CouncilDecision(Base):
    __tablename__ = "council_decisions"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    minority_opinion: Mapped[str | None] = mapped_column(Text)
    return_check_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    created_at = _created()


class Consultation(Base):
    __tablename__ = "consultations"

    id = uuid_pk()
    owner_user_id = _owner()
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_rooms.id", ondelete="SET NULL")
    )
    room_owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL")
    )
    system_slug: Mapped[str | None] = mapped_column(String(48))
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    desired_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    scope_statement: Mapped[str] = mapped_column(Text, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(16), default="ORIENT", server_default="ORIENT")
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", server_default="ACTIVE")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at = _created()
    updated_at = _updated()


class ConsultationContribution(Base):
    __tablename__ = "consultation_contributions"

    id = uuid_pk()
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )
    consultation_owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner_user_id = _owner()
    contribution_type: Mapped[str] = mapped_column(String(48), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    language_tag: Mapped[str] = mapped_column(String(20), default="en", server_default="en")
    provenance_label: Mapped[str] = mapped_column(String(48), default="MEMBER_WRITTEN", server_default="MEMBER_WRITTEN")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at = _created()


class ConsultationStageRecord(Base):
    __tablename__ = "consultation_stage_records"

    id = uuid_pk()
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )
    consultation_owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner_user_id = _owner()
    stage: Mapped[str] = mapped_column(String(16), nullable=False)
    stage_payload: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    provenance_label: Mapped[str] = mapped_column(String(48), default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    created_at = _created()
