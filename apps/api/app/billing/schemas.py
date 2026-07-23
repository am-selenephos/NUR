import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, Field


class PlanFeatureOut(BaseModel):
    feature_key: str
    allowed: bool
    usage_limit: int | None


class BillingPlanOut(BaseModel):
    code: str
    name: str
    description: str
    price_minor: int
    currency: str
    billing_interval: str
    seat_cap: int | None
    seats_remaining: int | None
    is_free: bool
    active: bool
    legal_copy_version: str
    features: list[PlanFeatureOut]


class CheckoutCreate(BaseModel):
    plan_code: str = Field(min_length=1, max_length=48, pattern=r"^[a-z0-9_]+$")


class CheckoutOut(BaseModel):
    session_id: uuid.UUID
    plan_code: str
    provider: str
    checkout_url: str
    status: str
    is_test: bool
    reservation_expires_at: dt.datetime
    renews_automatically: bool
    terms_url: str | None
    privacy_url: str | None
    refund_policy_url: str | None


class EntitlementOut(BaseModel):
    feature_key: str
    allowed: bool
    usage_limit: int | None
    usage_consumed: int
    valid_until: dt.datetime | None
    reason: str
    projection_version: int
    model_config = {"from_attributes": True}


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    plan_code: str
    provider: str
    provider_status: str
    status: str
    is_test: bool
    current_period_start: dt.datetime | None
    current_period_end: dt.datetime | None
    cancel_at_period_end: bool
    cancelled_at: dt.datetime | None
    ended_at: dt.datetime | None
    latest_receipt_url: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class RefundOut(BaseModel):
    id: uuid.UUID
    amount_minor: int | None
    currency: str | None
    status: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class BillingStateOut(BaseModel):
    subscription: SubscriptionOut | None
    entitlements: list[EntitlementOut]
    refunds: list[RefundOut]
    provider_configured: bool
    portal_available: bool
    cancellation_note: str
    terms_url: str | None
    privacy_url: str | None
    refund_policy_url: str | None


class PortalOut(BaseModel):
    url: str
    expires_at: dt.datetime
    purpose: Literal["MANAGE_CANCEL_INVOICES"] = "MANAGE_CANCEL_INVOICES"


class WebhookAck(BaseModel):
    accepted: bool
    duplicate: bool
    processing_status: Literal["PROCESSED", "IGNORED"]
    outcome_code: str
