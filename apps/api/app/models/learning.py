import datetime as dt
import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _created() -> Mapped[dt.datetime]:
    return mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )


class TeachNURContribution(Base):
    __tablename__ = "teach_nur_contributions"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL")
    )
    contribution_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    language_tag: Mapped[str] = mapped_column(String(35), default="und", server_default="und")
    consent_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    consent_policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    consent_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provenance_label: Mapped[str] = mapped_column(String(40), nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(24), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, server_default=text("1"))
    source_refs: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    risk_flags: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    deidentification_status: Mapped[str] = mapped_column(String(24), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="PENDING_REVIEW", server_default="PENDING_REVIEW"
    )
    request_key: Mapped[str | None] = mapped_column(String(160))
    payload_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class TeachNURCandidate(Base):
    __tablename__ = "teach_nur_candidates"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_contributions.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_text: Mapped[str] = mapped_column(String, nullable=False)
    original_text_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    deidentified_text: Mapped[str | None] = mapped_column(String)
    provenance_label: Mapped[str] = mapped_column(String(40), nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(24), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, server_default=text("1"))
    source_refs: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    risk_flags: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    contradiction_refs: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    disagreement_map: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(
        String(24), default="PENDING_REVIEW", server_default="PENDING_REVIEW"
    )
    current_knowledge_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_knowledge_versions.id", ondelete="SET NULL"),
    )
    created_at = _created()
    updated_at = _created()


class TeachNURKnowledgeVersion(Base):
    __tablename__ = "teach_nur_knowledge_versions"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_contributions.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_knowledge_versions.id", ondelete="SET NULL"),
    )
    canonical_text: Mapped[str] = mapped_column(String, nullable=False)
    retrieval_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    provenance_label: Mapped[str] = mapped_column(String(40), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    evaluation_result: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    why_changed: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    rolled_back_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()


class TeachNURConsentEvent(Base):
    __tablename__ = "teach_nur_consent_events"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_contributions.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    consent_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at = _created()


class TeachNURReview(Base):
    __tablename__ = "teach_nur_reviews"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_contributions.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    prior_status: Mapped[str] = mapped_column(String(24), nullable=False)
    resulting_status: Mapped[str] = mapped_column(String(24), nullable=False)
    note_digest: Mapped[str | None] = mapped_column(String(64))
    request_key: Mapped[str | None] = mapped_column(String(160))
    payload_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at = _created()


class TeachNUREvaluationRun(Base):
    __tablename__ = "teach_nur_evaluation_runs"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_contributions.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    knowledge_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_knowledge_versions.id", ondelete="SET NULL"),
    )
    suite_version: Mapped[str] = mapped_column(String(32), nullable=False)
    checks: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at = _created()


class TeachNURKnowledgeAccessEvent(Base):
    __tablename__ = "teach_nur_knowledge_access_events"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teach_nur_knowledge_versions.id", ondelete="SET NULL"),
    )
    access_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    context_ref: Mapped[str | None] = mapped_column(String(160))
    created_at = _created()
