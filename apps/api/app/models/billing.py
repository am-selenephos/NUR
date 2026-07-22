import datetime as dt
import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Boolean, DateTime

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
        default=now_utc,
        server_default=text("now()"),
        nullable=False,
    )


class BillingPlan(Base):
    __tablename__ = "billing_plans"

    code: Mapped[str] = mapped_column(String(48), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    billing_interval: Mapped[str] = mapped_column(String(16), nullable=False)
    seat_cap: Mapped[int | None] = mapped_column(Integer)
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    entitlements: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    legal_copy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at = _created()
    updated_at = _created()


class BillingCheckoutSession(Base):
    __tablename__ = "billing_checkout_sessions"

    id = uuid_pk()
    owner_user_id = _owner()
    plan_code: Mapped[str] = mapped_column(
        String(48), ForeignKey("billing_plans.code"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_checkout_id: Mapped[str | None] = mapped_column(String(160))
    checkout_url: Mapped[str | None] = mapped_column(Text)
    latest_receipt_url: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reservation_expires_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()
    updated_at = _created()


class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    id = uuid_pk()
    owner_user_id = _owner()
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_customer_id: Mapped[str] = mapped_column(String(160), nullable=False)
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at = _created()
    updated_at = _created()


class BillingSubscription(Base):
    __tablename__ = "billing_subscriptions"

    id = uuid_pk()
    owner_user_id = _owner()
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_customers.id", ondelete="SET NULL"),
    )
    checkout_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_checkout_sessions.id", ondelete="SET NULL"),
    )
    plan_code: Mapped[str] = mapped_column(
        String(48), ForeignKey("billing_plans.code"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_subscription_id: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_status: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False)
    current_period_start: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    current_period_end: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    last_provider_event_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_provider_event_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    last_provider_event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    latest_receipt_url: Mapped[str | None] = mapped_column(Text)
    latest_portal_url: Mapped[str | None] = mapped_column(Text)
    latest_portal_expires_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at = _created()
    updated_at = _created()


class BillingEntitlement(Base):
    __tablename__ = "billing_entitlements"

    id = uuid_pk()
    owner_user_id = _owner()
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_key: Mapped[str] = mapped_column(String(96), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    usage_consumed: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    valid_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    projection_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at = _created()
    updated_at = _created()


class BillingEntitlementEvent(Base):
    __tablename__ = "billing_entitlement_events"

    id = uuid_pk()
    owner_user_id = _owner()
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_key: Mapped[str] = mapped_column(String(96), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    valid_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at = _created()


class BillingWebhookReceipt(Base):
    __tablename__ = "billing_webhook_receipts"

    id = uuid_pk()
    owner_user_id = _owner()
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    event_name: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(160), nullable=False)
    payload_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_event_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    event_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(24), nullable=False)
    outcome_code: Mapped[str] = mapped_column(String(64), nullable=False)
    processed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at = _created()


class BillingRefundEvent(Base):
    __tablename__ = "billing_refund_events"

    id = uuid_pk()
    owner_user_id = _owner()
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_refund_id: Mapped[str] = mapped_column(String(160), nullable=False)
    amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    provider_event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at = _created()
