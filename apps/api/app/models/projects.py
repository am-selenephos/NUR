import datetime as dt
import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _owner() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


def _created() -> Mapped[dt.datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False
    )


def _updated() -> Mapped[dt.datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False
    )


class AMProject(Base):
    __tablename__ = "am_projects"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default="ACTIVE")
    system_slug: Mapped[str | None] = mapped_column(String(48))
    deadline: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    budget_cents: Mapped[int | None] = mapped_column(Integer)
    permission_policy: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at = _created()
    updated_at = _updated()


class AMProjectTask(Base):
    __tablename__ = "am_project_tasks"

    id = uuid_pk()
    owner_user_id = _owner()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_projects.id", ondelete="CASCADE"), nullable=False
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_tasks.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="BACKLOG", server_default="BACKLOG")
    priority: Mapped[int] = mapped_column(Integer, default=50, server_default=text("50"))
    assigned_role: Mapped[str | None] = mapped_column(String(80))
    due_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _updated()


class AMProjectRun(Base):
    __tablename__ = "am_project_runs"

    id = uuid_pk()
    owner_user_id = _owner()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_projects.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_tasks.id", ondelete="SET NULL")
    )
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    request_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PROPOSED", server_default="PROPOSED")
    tool_policy: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    budget_cents: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    approval_required: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    result_summary: Mapped[str | None] = mapped_column(Text)
    # --- Execution spine (G14) ---------------------------------------------
    adapter_key: Mapped[str | None] = mapped_column(String(64))
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_agents.id", ondelete="SET NULL")
    )
    requested_capabilities: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    approved_capabilities: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    input_refs: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(200))
    timeout_seconds: Mapped[int | None] = mapped_column(Integer)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    attempt: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    worker_id: Mapped[str | None] = mapped_column(String(120))
    failure_code: Mapped[str | None] = mapped_column(String(64))
    output_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_artifacts.id", ondelete="SET NULL")
    )
    queued_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _updated()


class AMProjectArtifact(Base):
    __tablename__ = "am_project_artifacts"

    id = uuid_pk()
    owner_user_id = _owner()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_projects.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_tasks.id", ondelete="SET NULL")
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_runs.id", ondelete="SET NULL")
    )
    artifact_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    locator: Mapped[str] = mapped_column(Text, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    provenance_label: Mapped[str] = mapped_column(
        String(64), default="OWNER_SUPPLIED", server_default="OWNER_SUPPLIED"
    )
    review_status: Mapped[str] = mapped_column(
        String(32), default="UNREVIEWED", server_default="UNREVIEWED"
    )
    artifact_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at = _created()
    updated_at = _updated()


class AMProjectEvidence(Base):
    __tablename__ = "am_project_evidence"

    id = uuid_pk()
    owner_user_id = _owner()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_projects.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_tasks.id", ondelete="SET NULL")
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_runs.id", ondelete="SET NULL")
    )
    evidence_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    locator: Mapped[str | None] = mapped_column(Text)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    verification_status: Mapped[str] = mapped_column(
        String(32), default="UNVERIFIED", server_default="UNVERIFIED"
    )
    verifier: Mapped[str | None] = mapped_column(String(120))
    created_at = _created()
    updated_at = _updated()


class AMProjectReview(Base):
    __tablename__ = "am_project_reviews"

    id = uuid_pk()
    owner_user_id = _owner()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_projects.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_runs.id", ondelete="SET NULL")
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_tasks.id", ondelete="SET NULL")
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    reviewer_label: Mapped[str] = mapped_column(
        String(80), default="OWNER", server_default="OWNER"
    )
    created_at = _created()


class AMProjectAgent(Base):
    """A persisted, owner-scoped agent definition: a named adapter binding with an
    explicit allow-list of safe capabilities. It never carries a secret and never
    grants authority beyond the deny-by-default catalog."""

    __tablename__ = "am_project_agents"

    id = uuid_pk()
    owner_user_id = _owner()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    allowed_capabilities: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at = _created()
    updated_at = _updated()


class AMProjectFile(Base):
    """Real stored bytes for a project. object_key is opaque, server-generated and
    never client-controlled; the bytes live under the runtime data root, not the
    web directory. Metadata is owner-scoped under forced RLS."""

    __tablename__ = "am_project_files"

    id = uuid_pk()
    owner_user_id = _owner()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_projects.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_tasks.id", ondelete="SET NULL")
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_runs.id", ondelete="SET NULL")
    )
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("am_project_artifacts.id", ondelete="SET NULL")
    )
    object_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    safe_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(180), default="application/octet-stream")
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(32), default="local", server_default="local")
    storage_state: Mapped[str] = mapped_column(String(32), default="STORED", server_default="STORED")
    quarantine_reason: Mapped[str | None] = mapped_column(Text)
    scan_state: Mapped[str] = mapped_column(
        String(32), default="SCAN_NOT_CONNECTED", server_default="SCAN_NOT_CONNECTED"
    )
    provenance: Mapped[str] = mapped_column(
        String(32), default="OWNER_UPLOAD", server_default="OWNER_UPLOAD"
    )
    created_at = _created()
    updated_at = _updated()
