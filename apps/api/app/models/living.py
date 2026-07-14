"""Persisted daily operating state for Today and the seven Star Systems."""

import datetime as dt
import uuid

from sqlalchemy import Date, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _owner() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )


def _created() -> Mapped[dt.datetime]:
    return mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=now_utc,
        nullable=False,
    )


class Goal(Base):
    __tablename__ = "goals"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL")
    )
    system_slug: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    why: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(24), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    target_date: Mapped[dt.date | None] = mapped_column(Date)
    created_at = _created()
    updated_at = _created()


class Objective(Base):
    __tablename__ = "objectives"

    id = uuid_pk()
    owner_user_id = _owner()
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    target_date: Mapped[dt.date | None] = mapped_column(Date)
    created_at = _created()
    updated_at = _created()


class SystemDiagnostic(Base):
    __tablename__ = "system_diagnostics"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="CASCADE"), nullable=False
    )
    system_slug: Mapped[str] = mapped_column(String(48), nullable=False)
    answers: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    blockers: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    strengths: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    created_at = _created()


class SystemAction(Base):
    __tablename__ = "system_actions"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="CASCADE"), nullable=False
    )
    system_slug: Mapped[str] = mapped_column(String(48), nullable=False)
    diagnostic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("system_diagnostics.id", ondelete="SET NULL"),
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL")
    )
    objective_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objectives.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(24), default="OPEN", server_default="OPEN", nullable=False
    )
    due_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    effort_minutes: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    missed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    easier_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("system_actions.id", ondelete="SET NULL")
    )
    outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcomes.id", ondelete="SET NULL")
    )
    action_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at = _created()
    updated_at = _created()


class ScheduledAction(Base):
    __tablename__ = "scheduled_actions"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL")
    )
    system_slug: Mapped[str] = mapped_column(String(48), nullable=False)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL")
    )
    objective_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objectives.id", ondelete="SET NULL")
    )
    system_action_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("system_actions.id", ondelete="SET NULL")
    )
    plan_step_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plan_steps.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    scheduled_for: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(24), default="SCHEDULED", server_default="SCHEDULED", nullable=False
    )
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    missed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    schedule_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at = _created()
    updated_at = _created()


class TodayCheckIn(Base):
    __tablename__ = "today_checkins"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL")
    )
    checkin_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    energy: Mapped[int] = mapped_column(Integer, nullable=False)
    pain: Mapped[int] = mapped_column(Integer, nullable=False)
    sleep_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    nourishment: Mapped[int] = mapped_column(Integer, nullable=False)
    movement: Mapped[int] = mapped_column(Integer, nullable=False)
    emotional_load: Mapped[int] = mapped_column(Integer, nullable=False)
    clarity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at = _created()
    updated_at = _created()


class GlowAchievement(Base):
    __tablename__ = "glow_achievements"

    id = uuid_pk()
    owner_user_id = _owner()
    achievement_key: Mapped[str] = mapped_column(String(100), nullable=False)
    source_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("glow_transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    achievement_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    unlocked_at = _created()


class FeasibilityAssessment(Base):
    __tablename__ = "feasibility_assessments"

    id = uuid_pk()
    owner_user_id = _owner()
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL")
    )
    system_slug: Mapped[str] = mapped_column(String(48), nullable=False)
    subject_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    desired_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    capacity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    current_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    time_required_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    time_available_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    money_required_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    money_available_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(24), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    checks: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    suggestions: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    source_refs: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    created_at = _created()
    updated_at = _created()
