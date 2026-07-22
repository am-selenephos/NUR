"""Group intelligence, research provenance, and correctable insight ledgers."""

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


def _json_list() -> Mapped[list]:
    return mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)


class GroupNURSynthesis(Base):
    __tablename__ = "group_nur_syntheses"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = _user()
    owner_user_id: Mapped[uuid.UUID] = _user()
    consultation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="SET NULL")
    )
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("group_nur_syntheses.id", ondelete="SET NULL")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="PUBLISHED", server_default="PUBLISHED", nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    current_question: Mapped[str] = mapped_column(Text, nullable=False)
    decisions = _json_list()
    tensions = _json_list()
    minority_positions = _json_list()
    evidence = _json_list()
    counterevidence = _json_list()
    unresolved_questions = _json_list()
    tasks = _json_list()
    source_message_ids = _json_list()
    source_post_ids = _json_list()
    source_contribution_ids = _json_list()
    what_may_be_wrong: Mapped[str] = mapped_column(Text, nullable=False)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    language_tag: Mapped[str] = mapped_column(
        String(20), default="en", server_default="en", nullable=False
    )
    provenance_label: Mapped[str] = mapped_column(
        String(48), default="MEMBER_SYNTHESIZED", server_default="MEMBER_SYNTHESIZED", nullable=False
    )
    created_at = _created()


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    research_brief_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_briefs.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    query_preview: Mapped[str] = mapped_column(Text, nullable=False)
    external_scope_approved: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    failure_code: Mapped[str | None] = mapped_column(String(80))
    failure_detail: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    research_brief_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_briefs.id", ondelete="CASCADE"), nullable=False
    )
    research_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_jobs.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(300))
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    authority: Mapped[str] = mapped_column(String(24), nullable=False)
    reliability: Mapped[str] = mapped_column(String(24), nullable=False)
    retrieval_status: Mapped[str] = mapped_column(String(24), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    untrusted_external_content: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    provenance_label: Mapped[str] = mapped_column(String(48), nullable=False)
    created_at = _created()


class ResearchClaim(Base):
    __tablename__ = "research_claims"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    research_brief_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_briefs.id", ondelete="CASCADE"), nullable=False
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    uncertainty: Mapped[str] = mapped_column(Text, nullable=False)
    citation_alignment: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="SUPPORTED", server_default="SUPPORTED", nullable=False
    )
    revision_number: Mapped[int] = mapped_column(
        Integer, default=1, server_default=text("1"), nullable=False
    )
    created_at = _created()
    updated_at = _created()


class ResearchCitation(Base):
    __tablename__ = "research_citations"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_claims.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_sources.id", ondelete="CASCADE"), nullable=False
    )
    relationship: Mapped[str] = mapped_column(String(16), nullable=False)
    locator: Mapped[str | None] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(Text)
    created_at = _created()


class ResearchClaimRevision(Base):
    __tablename__ = "research_claim_revisions"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_claims.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    current_claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    previous_uncertainty: Mapped[str] = mapped_column(Text, nullable=False)
    current_uncertainty: Mapped[str] = mapped_column(Text, nullable=False)
    correction_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at = _created()


class WebWatchlist(Base):
    __tablename__ = "web_watchlists"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    web_signal_question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("web_signal_questions.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    schedule: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    connector_status: Mapped[str] = mapped_column(
        String(24), default="NOT_CONNECTED", server_default="NOT_CONNECTED", nullable=False
    )
    alert_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    relevance_scope: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    last_content_hash: Mapped[str | None] = mapped_column(String(64))
    last_checked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    next_check_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class WebSignalSnapshot(Base):
    __tablename__ = "web_signal_snapshots"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("web_watchlists.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_from_previous: Mapped[bool] = mapped_column(Boolean, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    capture_method: Mapped[str] = mapped_column(String(24), nullable=False)
    captured_at = _created()


class WebSignalAlert(Base):
    __tablename__ = "web_signal_alerts"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("web_watchlists.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("web_signal_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), default="UNREAD", server_default="UNREAD", nullable=False
    )
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at = _created()
    updated_at = _created()


class ExpertProfile(Base):
    __tablename__ = "expert_profiles"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    display_name: Mapped[str] = mapped_column(String(240), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    domains = _json_list()
    verification_status: Mapped[str] = mapped_column(
        String(24), default="UNVERIFIED", server_default="UNVERIFIED", nullable=False
    )
    verification_scope: Mapped[str] = mapped_column(
        String(48), default="SELF_DECLARED", server_default="SELF_DECLARED", nullable=False
    )
    moderation_state: Mapped[str] = mapped_column(
        String(24), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    conflicts = _json_list()
    created_at = _created()
    updated_at = _created()


class ExpertVerification(Base):
    __tablename__ = "expert_verifications"

    id = uuid_pk()
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expert_profiles.id", ondelete="CASCADE"), nullable=False
    )
    owner_user_id: Mapped[uuid.UUID] = _user()
    verifier_user_id: Mapped[uuid.UUID] = _user()
    claim_type: Mapped[str] = mapped_column(String(24), nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="PENDING", server_default="PENDING", nullable=False
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class ExpertContribution(Base):
    __tablename__ = "expert_contributions"

    id = uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_owner_user_id: Mapped[uuid.UUID] = _user()
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expert_profiles.id", ondelete="CASCADE"), nullable=False
    )
    owner_user_id: Mapped[uuid.UUID] = _user()
    body: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids = _json_list()
    conflict_disclosure: Mapped[str] = mapped_column(Text, nullable=False)
    verification_label: Mapped[str] = mapped_column(String(48), nullable=False)
    moderation_state: Mapped[str] = mapped_column(
        String(24), default="PENDING", server_default="PENDING", nullable=False
    )
    moderator_user_id: Mapped[uuid.UUID | None] = _user(nullable=True)
    moderation_note: Mapped[str | None] = mapped_column(Text)
    created_at = _created()
    updated_at = _created()


class TenderInsight(Base):
    __tablename__ = "tender_insights"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = _user()
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tender_insights.id", ondelete="SET NULL")
    )
    scope_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    insight: Mapped[str] = mapped_column(Text, nullable=False)
    uncertainty: Mapped[str] = mapped_column(Text, nullable=False)
    counterexample: Mapped[str] = mapped_column(Text, nullable=False)
    conditions = _json_list()
    source_ids = _json_list()
    status: Mapped[str] = mapped_column(
        String(24), default="PROPOSED", server_default="PROPOSED", nullable=False
    )
    correction_reason: Mapped[str | None] = mapped_column(Text)
    provenance_label: Mapped[str] = mapped_column(
        String(48), default="OWNER_AUTHORED", server_default="OWNER_AUTHORED", nullable=False
    )
    created_at = _created()
    updated_at = _created()
