import datetime as dt
import uuid

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Boolean, DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _owner() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


def _orbit_nullable() -> Mapped[uuid.UUID | None]:
    return mapped_column(UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL"), nullable=True)


def _created() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False)


def _updated() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False)


class ResearchBrief(Base):
    __tablename__ = "research_briefs"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id = _orbit_nullable()
    question: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="LOCAL_DRAFT", server_default="LOCAL_DRAFT")
    provider_status: Mapped[str] = mapped_column(String, default="LOCAL_ONLY", server_default="LOCAL_ONLY")
    provenance_label: Mapped[str] = mapped_column(String, default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    created_at = _created()
    updated_at = _updated()


class ResearchSourceNote(Base):
    __tablename__ = "research_source_notes"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id = _orbit_nullable()
    research_brief_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("research_briefs.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String, default="OWNER_NOTE", server_default="OWNER_NOTE")
    trust_state: Mapped[str] = mapped_column(String, default="OWNER_SUPPLIED", server_default="OWNER_SUPPLIED")
    provenance_label: Mapped[str] = mapped_column(String, default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    created_at = _created()
    updated_at = _updated()


class CommunityConsultationNote(Base):
    __tablename__ = "community_consultation_notes"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id = _orbit_nullable()
    title: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str] = mapped_column(String, nullable=False)
    collaborator_label: Mapped[str | None] = mapped_column(String)
    capsule_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("context_capsules.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String, default="LOCAL_NOTE", server_default="LOCAL_NOTE")
    provenance_label: Mapped[str] = mapped_column(String, default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    created_at = _created()
    updated_at = _updated()


class WebSignalQuestion(Base):
    __tablename__ = "web_signal_questions"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id = _orbit_nullable()
    question: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="STAGED", server_default="STAGED")
    provider_status: Mapped[str] = mapped_column(String, default="NOT_CONNECTED", server_default="NOT_CONNECTED")
    provenance_label: Mapped[str] = mapped_column(String, default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    created_at = _created()
    updated_at = _updated()


class WebSignalNote(Base):
    __tablename__ = "web_signal_notes"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id = _orbit_nullable()
    web_signal_question_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("web_signal_questions.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String)
    provenance_label: Mapped[str] = mapped_column(String, default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    created_at = _created()
    updated_at = _updated()


class ProviderCapability(Base):
    __tablename__ = "provider_capabilities"

    id = uuid_pk()
    owner_user_id = _owner()
    provider_name: Mapped[str] = mapped_column(String, nullable=False)
    capability_key: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="NOT_CONNECTED", server_default="NOT_CONNECTED")
    reason: Mapped[str] = mapped_column(String, nullable=False)
    configured: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at = _created()
    updated_at = _updated()
