import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Boolean, DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


def _owner() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


def _created() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False)


class GlowRule(Base):
    __tablename__ = "glow_rules"

    event_type: Mapped[str] = mapped_column(String, primary_key=True)
    base_points: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_cap: Mapped[int | None] = mapped_column(Integer)
    weekly_cap: Mapped[int | None] = mapped_column(Integer)
    spam_window_seconds: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    action_type: Mapped[str | None] = mapped_column(String)
    system_slug: Mapped[str | None] = mapped_column(String(48))
    requires_persistence: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    streak_key: Mapped[str | None] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at = _created()


class GlowBalance(Base):
    __tablename__ = "glow_balances"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    lifetime_points: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    updated_at = _created()


class GlowTransaction(Base):
    __tablename__ = "glow_transactions"

    id = uuid_pk()
    owner_user_id = _owner()
    event_type: Mapped[str] = mapped_column(String, ForeignKey("glow_rules.event_type"), nullable=False)
    source_kind: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL"))
    system_slug: Mapped[str | None] = mapped_column(String(48))
    base_points: Mapped[int] = mapped_column(Integer, nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Float, default=1, server_default=text("1"))
    final_points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    reversed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    reversal_reason: Mapped[str | None] = mapped_column(Text)
    anti_abuse_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    created_at = _created()


class GlowStreak(Base):
    __tablename__ = "glow_streaks"

    id = uuid_pk()
    owner_user_id = _owner()
    streak_key: Mapped[str] = mapped_column(String, nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    best_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    last_event_date: Mapped[dt.date | None] = mapped_column(Date)
    repairs_remaining: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    created_at = _created()
    updated_at = _created()


class GlowRewardEvent(Base):
    __tablename__ = "glow_reward_events"

    id = uuid_pk()
    owner_user_id = _owner()
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    source_kind: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="AWARDED", server_default="AWARDED")
    event_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    created_at = _created()


class Translation(Base):
    __tablename__ = "translations"

    id = uuid_pk()
    owner_user_id = _owner()
    source_hash: Mapped[str] = mapped_column(String, nullable=False)
    source_locale: Mapped[str | None] = mapped_column(String)
    target_locale: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str | None] = mapped_column(String)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at = _created()
    updated_at = _created()


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    category_settings: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    frequency: Mapped[str] = mapped_column(String(24), default="BALANCED", server_default="BALANCED")
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5))
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5))
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    updated_at = _created()


class Notification(Base):
    __tablename__ = "notifications"

    id = uuid_pk()
    owner_user_id = _owner()
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    route: Mapped[str | None] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(80), default="OWNER_REMINDER", server_default="OWNER_REMINDER")
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    provenance_label: Mapped[str] = mapped_column(String(48), default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    delivery_state: Mapped[str] = mapped_column(String(24), default="IN_APP", server_default="IN_APP")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
