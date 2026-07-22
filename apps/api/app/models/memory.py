import datetime as dt
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _created() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, default=now_utc, server_default=text("now()"))


class PersonalMemory(Base):
    __tablename__ = "memories"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL"))
    scope: Mapped[str] = mapped_column(PGEnum("EPHEMERAL", "PRIVATE_ORBIT", "SYSTEM_SHARED", "LEARNING_CANDIDATE", name="memory_scope", create_type=False), default="PRIVATE_ORBIT", server_default="PRIVATE_ORBIT")
    memory_type: Mapped[str] = mapped_column(String(32), default="SEMANTIC", server_default="SEMANTIC")
    canonical_text: Mapped[str] = mapped_column(String, nullable=False)
    structured_value: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    source_object_ids: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    provenance_label: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, server_default=text("0.5"))
    sensitivity: Mapped[str] = mapped_column(String(24), default="PRIVATE", server_default="PRIVATE")
    status: Mapped[str] = mapped_column(String(24), default="APPROVED", server_default="APPROVED")
    created_by: Mapped[str] = mapped_column(String(16), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    superseded_by_memory_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="SET NULL"))
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class MemoryVersion(Base):
    __tablename__ = "memory_versions"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    canonical_text: Mapped[str] = mapped_column(String, nullable=False)
    structured_value: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    provenance_label: Mapped[str] = mapped_column(String(40), nullable=False)
    change_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    correction_reason: Mapped[str | None] = mapped_column(String)
    changed_by: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at = _created()


class MemoryEdge(Base):
    __tablename__ = "memory_edges"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    relation: Mapped[str] = mapped_column(String(24), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    edge_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    created_at = _created()


class MemoryAccessEvent(Base):
    __tablename__ = "memory_access_events"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="SET NULL"))
    access_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    context_ref: Mapped[str | None] = mapped_column(String(160))
    created_at = _created()
