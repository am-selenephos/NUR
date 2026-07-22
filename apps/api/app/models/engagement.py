import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, text
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
    rule_version: Mapped[int] = mapped_column(
        Integer, default=1, server_default=text("1"), nullable=False
    )
    default_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(8, 3), default=Decimal("1"), server_default=text("1"), nullable=False
    )
    multiplier_reason: Mapped[str] = mapped_column(
        String(120), default="BASE", server_default="BASE", nullable=False
    )
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
    spent_points: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    reversal_debt: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    updated_at = _created()


class GlowTransaction(Base):
    __tablename__ = "glow_transactions"

    id = uuid_pk()
    owner_user_id = _owner()
    event_type: Mapped[str] = mapped_column(String, ForeignKey("glow_rules.event_type"), nullable=False)
    source_kind: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domain_events.id", ondelete="CASCADE"), nullable=False
    )
    orbit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL"))
    system_slug: Mapped[str | None] = mapped_column(String(48))
    base_points: Mapped[int] = mapped_column(Integer, nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(
        Numeric(8, 3), default=Decimal("1"), server_default=text("1"), nullable=False
    )
    multiplier_reason: Mapped[str] = mapped_column(String(120), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    final_points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    reversed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    reversal_reason: Mapped[str | None] = mapped_column(Text)
    anti_abuse_state: Mapped[str] = mapped_column(
        String(24), default="CLEAR", server_default="CLEAR", nullable=False
    )
    anti_abuse_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC", nullable=False)
    local_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    created_at = _created()


class GlowSourceClaim(Base):
    __tablename__ = "glow_source_claims"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id", "event_type", "source_kind", "source_id",
            name="uq_glow_source_claim",
        ),
    )

    id = uuid_pk()
    owner_user_id = _owner()
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    source_kind: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domain_events.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    claimed_at = _created()


class GlowReversal(Base):
    __tablename__ = "glow_reversals"

    id = uuid_pk()
    owner_user_id = _owner()
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domain_events.id", ondelete="CASCADE"), nullable=False
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_effect: Mapped[int] = mapped_column(Integer, nullable=False)
    debt_effect: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    reversed_at = _created()


class GlowFraudFlag(Base):
    __tablename__ = "glow_fraud_flags"

    id = uuid_pk()
    owner_user_id = _owner()
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="SET NULL")
    )
    source_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="OPEN", server_default="OPEN", nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    signal_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at = _created()


class GlowStreak(Base):
    __tablename__ = "glow_streaks"

    id = uuid_pk()
    owner_user_id = _owner()
    streak_key: Mapped[str] = mapped_column(String, nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    best_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    last_event_date: Mapped[dt.date | None] = mapped_column(Date)
    last_event_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    checkpoint_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    next_reward_at: Mapped[int] = mapped_column(Integer, default=7, server_default=text("7"))
    grace_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    state_reason: Mapped[str] = mapped_column(
        String(160), default="VERIFIED_EVENT", server_default="VERIFIED_EVENT"
    )
    repairs_remaining: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    created_at = _created()
    updated_at = _created()


class GlowStreakDefinition(Base):
    __tablename__ = "streak_definitions"

    streak_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    eligible_event_types: Mapped[list] = mapped_column(JSONB, nullable=False)
    grace_hours: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    repair_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    checkpoint_interval: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class GlowStreakEvent(Base):
    __tablename__ = "streak_events"

    id = uuid_pk()
    owner_user_id = _owner()
    streak_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_streaks.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="CASCADE")
    )
    event_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    local_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    event_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    occurred_at = _created()


class GlowStreakRepair(Base):
    __tablename__ = "streak_repairs"

    id = uuid_pk()
    owner_user_id = _owner()
    streak_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_streaks.id", ondelete="CASCADE"), nullable=False
    )
    repaired_local_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    cost_points: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at = _created()


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


class GlowQuestDefinition(Base):
    __tablename__ = "quest_templates"
    __table_args__ = (
        UniqueConstraint("quest_key", "rule_version", name="uq_quest_template_version"),
    )

    id = uuid_pk()
    quest_key: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    cadence: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    target_event_types: Mapped[list] = mapped_column(JSONB, nullable=False)
    base_target: Mapped[int] = mapped_column(Integer, nullable=False)
    low_capacity_target: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_points: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(24), nullable=False)
    rationale: Mapped[str] = mapped_column(String(500), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class GlowQuest(Base):
    __tablename__ = "user_quests"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id", "template_id", "local_period_key",
            name="uq_user_quest_period",
        ),
    )

    id = uuid_pk()
    owner_user_id = _owner()
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quest_templates.id", ondelete="RESTRICT"), nullable=False
    )
    local_period_key: Mapped[str] = mapped_column(String(32), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    period_start: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_count: Mapped[int] = mapped_column(Integer, nullable=False)
    progress_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", server_default="ACTIVE")
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    claimed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    claim_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="SET NULL")
    )
    created_at = _created()
    updated_at = _created()


class GlowLevelDefinition(Base):
    __tablename__ = "level_definitions"

    level: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    unlock_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class GlowUserLevel(Base):
    __tablename__ = "user_levels"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    level: Mapped[int] = mapped_column(
        Integer, ForeignKey("level_definitions.level", ondelete="RESTRICT"), nullable=False
    )
    lifetime_points: Mapped[int] = mapped_column(Integer, nullable=False)
    reached_at = _created()
    updated_at = _created()


class GlowLevelEvent(Base):
    __tablename__ = "level_events"

    id = uuid_pk()
    owner_user_id = _owner()
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    event_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    source_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="CASCADE")
    )
    source_reversal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_reversals.id", ondelete="CASCADE")
    )
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    created_at = _created()


class GlowAchievementDefinition(Base):
    __tablename__ = "achievement_definitions"

    achievement_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    reversible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class GlowAchievementEvent(Base):
    __tablename__ = "achievement_events"

    id = uuid_pk()
    owner_user_id = _owner()
    achievement_key: Mapped[str] = mapped_column(String(100), nullable=False)
    event_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    source_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_transactions.id", ondelete="CASCADE")
    )
    source_reversal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("glow_reversals.id", ondelete="CASCADE")
    )
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    created_at = _created()


class GlowRewardDefinition(Base):
    __tablename__ = "reward_inventory"

    reward_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    cost_points: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_level: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class GlowRewardRedemption(Base):
    __tablename__ = "user_rewards"

    id = uuid_pk()
    owner_user_id = _owner()
    reward_key: Mapped[str] = mapped_column(
        String(100), ForeignKey("reward_inventory.reward_key", ondelete="RESTRICT"), nullable=False
    )
    cost_points: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    redeemed_at = _created()


class EngagementExperimentDefinition(Base):
    __tablename__ = "engagement_experiment_definitions"

    experiment_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    hypothesis: Mapped[str] = mapped_column(String(500), nullable=False)
    primary_metric: Mapped[str] = mapped_column(String(120), nullable=False)
    guardrail_metrics: Mapped[list] = mapped_column(JSONB, nullable=False)
    variants: Mapped[list] = mapped_column(JSONB, nullable=False)
    target_cohort: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sample_rule: Mapped[dict] = mapped_column(JSONB, nullable=False)
    stop_rule: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class EngagementExperimentAssignment(Base):
    __tablename__ = "engagement_experiment_assignments"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id", "experiment_key", "experiment_version",
            name="uq_engagement_experiment_assignment",
        ),
    )

    id = uuid_pk()
    owner_user_id = _owner()
    experiment_key: Mapped[str] = mapped_column(String(100), nullable=False)
    experiment_version: Mapped[int] = mapped_column(Integer, nullable=False)
    variant: Mapped[str] = mapped_column(String(80), nullable=False)
    assignment_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    assigned_at = _created()


class EngagementExperimentExposure(Base):
    __tablename__ = "engagement_experiment_exposures"

    id = uuid_pk()
    owner_user_id = _owner()
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("engagement_experiment_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    surface: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    exposure_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    exposed_at = _created()


class Translation(Base):
    __tablename__ = "translations"

    id = uuid_pk()
    owner_user_id = _owner()
    source_hash: Mapped[str] = mapped_column(String, nullable=False)
    source_locale: Mapped[str | None] = mapped_column(String)
    target_locale: Mapped[str] = mapped_column(String, nullable=False)
    detected_source_locale: Mapped[str | None] = mapped_column(String(16))
    source_writing_preference: Mapped[str] = mapped_column(
        String(16), default="default", server_default="default", nullable=False
    )
    target_writing_preference: Mapped[str] = mapped_column(
        String(16), default="default", server_default="default", nullable=False
    )
    source_direction: Mapped[str] = mapped_column(
        String(3), default="ltr", server_default="ltr", nullable=False
    )
    target_direction: Mapped[str] = mapped_column(
        String(3), default="ltr", server_default="ltr", nullable=False
    )
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    scope: Mapped[str] = mapped_column(
        String(32), default="PRIVATE_ORBIT", server_default="PRIVATE_ORBIT", nullable=False
    )
    source_object_type: Mapped[str | None] = mapped_column(String(80))
    source_object_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_ref: Mapped[str | None] = mapped_column(String(180))
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str | None] = mapped_column(String)
    provider_version: Mapped[str | None] = mapped_column(String(160))
    cache_key: Mapped[str | None] = mapped_column(String(64))
    quality_state: Mapped[str] = mapped_column(
        String(40), default="MISSING_REVIEW", server_default="MISSING_REVIEW", nullable=False
    )
    translation_version: Mapped[int] = mapped_column(
        default=1, server_default=text("1"), nullable=False
    )
    moderation_context_preserved: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    feedback: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
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
    in_app_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    paused_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    max_daily: Mapped[int] = mapped_column(Integer, default=3, server_default=text("3"))
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
    idempotency_key: Mapped[str | None] = mapped_column(String(240))
    provenance_label: Mapped[str] = mapped_column(String(48), default="OWNER_WRITTEN", server_default="OWNER_WRITTEN")
    delivery_state: Mapped[str] = mapped_column(String(24), default="IN_APP", server_default="IN_APP")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = uuid_pk()
    owner_user_id = _owner()
    notification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    provider_message_id: Mapped[str | None] = mapped_column(String(240))
    failure_code: Mapped[str | None] = mapped_column(String(80))
    deliver_after: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()
