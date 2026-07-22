import datetime as dt
import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.providers import (
    BillingProviderError,
    CheckoutRequest,
    build_billing_provider,
)
from app.core.config import Settings, get_settings
from app.db.rls import set_user_context
from app.models import (
    BillingCheckoutSession,
    BillingCustomer,
    BillingEntitlement,
    BillingEntitlementEvent,
    BillingPlan,
    BillingRefundEvent,
    BillingSubscription,
    BillingWebhookReceipt,
    User,
)
from app.models._mixins import now_utc
from app.services.domain_event_service import emit_domain_event


class BillingError(RuntimeError):
    pass


class BillingNotFound(BillingError):
    pass


class BillingConflict(BillingError):
    pass


class BillingUnavailable(BillingError):
    pass


class BillingWebhookRejected(BillingError):
    pass


@dataclass(frozen=True)
class PlanAvailability:
    plan: BillingPlan
    seats_remaining: int | None


@dataclass(frozen=True)
class WebhookResult:
    duplicate: bool
    processing_status: str
    outcome_code: str


@dataclass(frozen=True)
class ParsedWebhook:
    owner_user_id: uuid.UUID
    checkout_session_id: uuid.UUID
    plan_code: str
    event_name: str
    event_key: str
    event_at: dt.datetime
    event_rank: int
    resource_type: str
    resource_id: str
    attributes: dict[str, Any]
    is_test: bool


_PROJECTED_SUBSCRIPTION_EVENTS = {
    "subscription_created",
    "subscription_updated",
    "subscription_cancelled",
    "subscription_resumed",
    "subscription_expired",
    "subscription_paused",
    "subscription_unpaused",
    "subscription_payment_failed",
    "subscription_payment_success",
    "subscription_payment_recovered",
}
_ORDER_EVENTS = {"order_created"}
_REFUND_EVENTS = {"order_refunded", "subscription_payment_refunded"}
_CHARGEBACK_EVENTS = {"order_chargeback", "subscription_chargeback"}


def _secret(settings: Settings) -> bytes:
    configured = settings.billing_webhook_secret
    if configured is None:
        raise BillingUnavailable("Billing webhook verification is not configured.")
    return configured.get_secret_value().encode()


def verify_webhook_signature(settings: Settings, raw_body: bytes, signature: str) -> bool:
    if not signature or len(signature) > 256:
        return False
    expected = hmac.new(_secret(settings), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip().lower())


def checkout_binding(
    settings: Settings,
    *,
    provider: str,
    owner_user_id: uuid.UUID,
    checkout_session_id: uuid.UUID,
    plan_code: str,
) -> str:
    message = ":".join(
        (provider, str(owner_user_id), str(checkout_session_id), plan_code)
    ).encode()
    return hmac.new(_secret(settings), message, hashlib.sha256).hexdigest()


async def list_plans(db: AsyncSession) -> list[PlanAvailability]:
    rows = (
        await db.execute(
            select(BillingPlan)
            .where(BillingPlan.active.is_(True))
            .order_by(BillingPlan.price_minor, BillingPlan.code)
        )
    ).scalars().all()
    output: list[PlanAvailability] = []
    for row in rows:
        remaining = None
        if row.seat_cap is not None:
            claimed = (
                await db.execute(
                    text("SELECT billing_real_seats_claimed(:plan_code)"),
                    {"plan_code": row.code},
                )
            ).scalar_one()
            remaining = max(0, row.seat_cap - int(claimed))
        output.append(PlanAvailability(plan=row, seats_remaining=remaining))
    return output


async def create_checkout(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    plan_code: str,
    idempotency_key: str,
    settings: Settings | None = None,
) -> BillingCheckoutSession:
    settings = settings or get_settings()
    provider = build_billing_provider(settings)
    if provider.name == "disabled":
        raise BillingUnavailable("Billing checkout is not configured.")

    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
        {"lock_key": f"billing-owner:{owner_user_id}"},
    )
    now = now_utc()
    await db.execute(
        update(BillingCheckoutSession)
        .where(
            BillingCheckoutSession.owner_user_id == owner_user_id,
            BillingCheckoutSession.status.in_({"PENDING", "CREATED"}),
            BillingCheckoutSession.reservation_expires_at <= now,
        )
        .values(status="EXPIRED", updated_at=now)
    )
    existing = (
        await db.execute(
            select(BillingCheckoutSession).where(
                BillingCheckoutSession.owner_user_id == owner_user_id,
                BillingCheckoutSession.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.plan_code != plan_code:
            raise BillingConflict("This idempotency key belongs to another plan.")
        if (
            existing.status == "CREATED"
            and existing.checkout_url
            and existing.reservation_expires_at > now_utc()
        ):
            return existing
        if existing.reservation_expires_at <= now_utc():
            existing.status = "EXPIRED"
            existing.updated_at = now_utc()
        raise BillingConflict("This checkout attempt is no longer reusable.")

    plan = (
        await db.execute(
            select(BillingPlan).where(
                BillingPlan.code == plan_code,
                BillingPlan.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if plan is None:
        raise BillingNotFound("Billing plan not found.")
    if plan.is_free:
        raise BillingConflict("The free plan does not require checkout.")

    is_test = provider.name == "test" or settings.billing_test_mode
    active_subscription = (
        await db.execute(
            select(BillingSubscription.id).where(
                BillingSubscription.owner_user_id == owner_user_id,
                BillingSubscription.is_test == is_test,
                BillingSubscription.status.in_(
                    {
                        "trialing",
                        "active",
                        "past_due",
                        "paused",
                        "cancel_at_period_end",
                    }
                ),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if active_subscription is not None:
        raise BillingConflict(
            "An existing subscription must be managed through the billing portal."
        )
    open_checkout = (
        await db.execute(
            select(BillingCheckoutSession.id).where(
                BillingCheckoutSession.owner_user_id == owner_user_id,
                BillingCheckoutSession.is_test == is_test,
                BillingCheckoutSession.status.in_({"PENDING", "CREATED"}),
                BillingCheckoutSession.reservation_expires_at > now_utc(),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if open_checkout is not None:
        raise BillingConflict("An unexpired checkout already exists for this account.")
    if plan.seat_cap is not None and not is_test:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"billing-plan:{plan_code}"},
        )
        claimed = (
            await db.execute(
                text("SELECT billing_real_seats_claimed(:plan_code)"),
                {"plan_code": plan.code},
            )
        ).scalar_one()
        if int(claimed) >= plan.seat_cap:
            raise BillingConflict("This limited plan is sold out.")

    email = (
        await db.execute(select(User.email).where(User.id == owner_user_id))
    ).scalar_one()
    now = now_utc()
    row = BillingCheckoutSession(
        owner_user_id=owner_user_id,
        plan_code=plan.code,
        provider=provider.name,
        idempotency_key=idempotency_key,
        status="PENDING",
        is_test=is_test,
        reservation_expires_at=now
        + dt.timedelta(minutes=settings.billing_checkout_reservation_minutes),
    )
    db.add(row)
    await db.flush()
    custom_data = {
        "nur_owner_user_id": str(owner_user_id),
        "nur_checkout_session_id": str(row.id),
        "nur_plan_code": plan.code,
        "nur_binding": checkout_binding(
            settings,
            provider=provider.name,
            owner_user_id=owner_user_id,
            checkout_session_id=row.id,
            plan_code=plan.code,
        ),
    }
    try:
        result = await provider.create_checkout(
            CheckoutRequest(
                session_id=row.id,
                owner_user_id=owner_user_id,
                plan_code=plan.code,
                customer_email=email,
                custom_data=custom_data,
                redirect_url=(
                    f"{settings.web_origin.rstrip('/')}/settings/billing?checkout=complete"
                ),
                idempotency_key=hashlib.sha256(
                    f"{owner_user_id}:{idempotency_key}".encode()
                ).hexdigest(),
                expires_at=row.reservation_expires_at,
                expected_price_minor=plan.price_minor,
                expected_currency=plan.currency,
            )
        )
    except BillingProviderError as exc:
        raise BillingUnavailable(str(exc)) from exc
    row.provider_checkout_id = result.provider_checkout_id
    row.checkout_url = result.checkout_url
    row.status = "CREATED"
    row.updated_at = now_utc()
    await db.flush()
    return row


def _parse_datetime(value: object, *, required: bool = False) -> dt.datetime | None:
    if value in (None, ""):
        if required:
            raise BillingWebhookRejected("Webhook event timestamp is missing.")
        return None
    if not isinstance(value, str):
        raise BillingWebhookRejected("Webhook timestamp is invalid.")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BillingWebhookRejected("Webhook timestamp is invalid.") from exc
    if parsed.tzinfo is None:
        raise BillingWebhookRejected("Webhook timestamp must include a timezone.")
    return parsed.astimezone(dt.UTC)


def _trusted_https_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        return None
    return value


def _event_variant(attributes: dict[str, Any]) -> object:
    variant = attributes.get("variant_id")
    if variant not in (None, ""):
        return variant
    first_order_item = attributes.get("first_order_item")
    if isinstance(first_order_item, dict):
        return first_order_item.get("variant_id")
    return None


def _customer_document_url(attributes: dict[str, Any]) -> str | None:
    value = attributes.get("receipt_url")
    urls = attributes.get("urls")
    if value is None and isinstance(urls, dict):
        value = urls.get("receipt") or urls.get("invoice_url")
    return _trusted_https_url(value)


def _event_rank(event_name: str) -> int:
    ranks = {
        "order_created": 5,
        "subscription_created": 10,
        "subscription_updated": 20,
        "subscription_resumed": 30,
        "subscription_unpaused": 30,
        "subscription_payment_success": 35,
        "subscription_payment_recovered": 35,
        "subscription_cancelled": 50,
        "subscription_paused": 55,
        "subscription_payment_failed": 60,
        "subscription_expired": 90,
        "order_refunded": 100,
        "subscription_payment_refunded": 100,
        "order_chargeback": 110,
        "subscription_chargeback": 110,
    }
    return ranks.get(event_name, 0)


def _parse_webhook(
    settings: Settings,
    *,
    provider: str,
    payload: dict[str, Any],
    payload_digest: str,
) -> ParsedWebhook:
    meta = payload.get("meta")
    data = payload.get("data")
    if not isinstance(meta, dict) or not isinstance(data, dict):
        raise BillingWebhookRejected("Webhook payload shape is invalid.")
    attributes = data.get("attributes")
    custom = meta.get("custom_data")
    if not isinstance(attributes, dict) or not isinstance(custom, dict):
        raise BillingWebhookRejected("Webhook payload is missing trusted metadata.")
    event_name = meta.get("event_name")
    resource_type = data.get("type")
    resource_id = data.get("id")
    if not all(isinstance(value, str) and value for value in (event_name, resource_type, resource_id)):
        raise BillingWebhookRejected("Webhook event identity is invalid.")
    if len(event_name) > 80 or len(resource_type) > 64 or len(resource_id) > 160:
        raise BillingWebhookRejected("Webhook event identity is too long.")
    try:
        owner_user_id = uuid.UUID(str(custom["nur_owner_user_id"]))
        checkout_session_id = uuid.UUID(str(custom["nur_checkout_session_id"]))
        plan_code = str(custom["nur_plan_code"])
        supplied_binding = str(custom["nur_binding"])
    except (KeyError, ValueError, TypeError) as exc:
        raise BillingWebhookRejected("Webhook ownership binding is invalid.") from exc
    if len(plan_code) > 48:
        raise BillingWebhookRejected("Webhook plan binding is invalid.")
    expected_binding = checkout_binding(
        settings,
        provider=provider,
        owner_user_id=owner_user_id,
        checkout_session_id=checkout_session_id,
        plan_code=plan_code,
    )
    if not hmac.compare_digest(expected_binding, supplied_binding):
        raise BillingWebhookRejected("Webhook ownership binding is invalid.")
    test_mode = meta.get("test_mode")
    if not isinstance(test_mode, bool):
        raise BillingWebhookRejected("Webhook test mode is missing.")
    expected_test_mode = provider == "test" or settings.billing_test_mode
    if test_mode != expected_test_mode:
        raise BillingWebhookRejected("Webhook test mode does not match server mode.")
    event_at = _parse_datetime(
        attributes.get("updated_at") or attributes.get("created_at"), required=True
    )
    stable_id = meta.get("event_id") or meta.get("webhook_id")
    if isinstance(stable_id, str) and stable_id and len(stable_id) <= 120:
        event_key = stable_id
    else:
        event_key = hashlib.sha256(
            f"{event_name}:{resource_type}:{resource_id}:{event_at.isoformat()}:{payload_digest}".encode()
        ).hexdigest()
    return ParsedWebhook(
        owner_user_id=owner_user_id,
        checkout_session_id=checkout_session_id,
        plan_code=plan_code,
        event_name=event_name,
        event_key=event_key,
        event_at=event_at,
        event_rank=_event_rank(event_name),
        resource_type=resource_type,
        resource_id=resource_id,
        attributes=attributes,
        is_test=test_mode,
    )


def _canonical_status(event: ParsedWebhook) -> tuple[str, str]:
    provider_status = str(event.attributes.get("status") or event.event_name).lower()
    if event.event_name in _CHARGEBACK_EVENTS:
        return "chargeback", provider_status
    if event.event_name in _REFUND_EVENTS:
        return "refunded", provider_status
    if event.event_name == "subscription_expired":
        return "expired", provider_status
    if event.event_name == "subscription_cancelled":
        ends_at = _parse_datetime(event.attributes.get("ends_at"))
        if ends_at is not None and ends_at > now_utc():
            return "cancel_at_period_end", provider_status
        return "cancelled", provider_status
    if event.event_name in {
        "subscription_resumed",
        "subscription_unpaused",
        "subscription_payment_success",
        "subscription_payment_recovered",
    }:
        return "active", provider_status
    if event.event_name == "subscription_paused":
        return "paused", provider_status
    if event.event_name == "subscription_payment_failed":
        return "past_due", provider_status
    mapping = {
        "on_trial": "trialing",
        "trialing": "trialing",
        "active": "active",
        "past_due": "past_due",
        "unpaid": "past_due",
        "paused": "paused",
        "cancelled": "cancel_at_period_end",
        "canceled": "cancel_at_period_end",
        "expired": "expired",
    }
    status = mapping.get(provider_status)
    if status is None:
        raise BillingWebhookRejected("Webhook subscription status is unsupported.")
    if status == "cancel_at_period_end":
        ends_at = _parse_datetime(event.attributes.get("ends_at"))
        if ends_at is None or ends_at <= now_utc():
            status = "cancelled"
    return status, provider_status


def _access_window(
    settings: Settings,
    *,
    status: str,
    event_at: dt.datetime,
    period_end: dt.datetime | None,
) -> tuple[bool, dt.datetime | None]:
    now = now_utc()
    if status in {"trialing", "active", "cancel_at_period_end"}:
        allowed = period_end is None or period_end > now
        return allowed, period_end
    if status == "past_due":
        grace_end = event_at + dt.timedelta(days=settings.billing_past_due_grace_days)
        if period_end is not None:
            grace_end = min(grace_end, period_end)
        return grace_end > now, grace_end
    return False, event_at


async def _receipt(
    db: AsyncSession,
    *,
    event: ParsedWebhook,
    provider: str,
    payload_digest: str,
    signature_digest: str,
    processing_status: str,
    outcome_code: str,
) -> BillingWebhookReceipt:
    row = BillingWebhookReceipt(
        owner_user_id=event.owner_user_id,
        provider=provider,
        provider_event_key=event.event_key,
        event_name=event.event_name,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        payload_digest=payload_digest,
        signature_digest=signature_digest,
        provider_event_at=event.event_at,
        event_rank=event.event_rank,
        processing_status=processing_status,
        outcome_code=outcome_code,
        processed_at=now_utc(),
    )
    db.add(row)
    await db.flush()
    return row


async def _upsert_customer(
    db: AsyncSession,
    *,
    event: ParsedWebhook,
    provider: str,
) -> BillingCustomer | None:
    provider_customer_id = event.attributes.get("customer_id")
    if provider_customer_id in (None, ""):
        return None
    provider_customer_id = str(provider_customer_id)
    if len(provider_customer_id) > 160:
        raise BillingWebhookRejected("Webhook customer identity is too long.")
    row = (
        await db.execute(
            select(BillingCustomer).where(
                BillingCustomer.owner_user_id == event.owner_user_id,
                BillingCustomer.provider == provider,
                BillingCustomer.is_test == event.is_test,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = BillingCustomer(
            owner_user_id=event.owner_user_id,
            provider=provider,
            provider_customer_id=provider_customer_id,
            is_test=event.is_test,
        )
        db.add(row)
        await db.flush()
    elif row.provider_customer_id != provider_customer_id:
        row.provider_customer_id = provider_customer_id
        row.updated_at = now_utc()
    return row


async def _project_entitlements(
    db: AsyncSession,
    *,
    settings: Settings,
    event: ParsedWebhook,
    subscription: BillingSubscription,
    plan: BillingPlan,
) -> None:
    allowed, valid_until = _access_window(
        settings,
        status=subscription.status,
        event_at=event.event_at,
        period_end=subscription.current_period_end,
    )
    current = (
        await db.execute(
            select(BillingEntitlement)
            .where(BillingEntitlement.owner_user_id == event.owner_user_id)
            .with_for_update()
        )
    ).scalars().all()
    by_key = {item.feature_key: item for item in current}
    configured = plan.entitlements if isinstance(plan.entitlements, dict) else {}
    keys = set(by_key) | set(configured)
    reason = f"SUBSCRIPTION_{subscription.status.upper()}"
    for feature_key in sorted(keys):
        feature = configured.get(feature_key, {})
        if not isinstance(feature, dict):
            feature = {}
        feature_allowed = allowed and bool(feature.get("allowed", True))
        usage_limit = feature.get("limit")
        if not isinstance(usage_limit, int) or usage_limit < 0:
            usage_limit = None
        existing = by_key.get(feature_key)
        prior_allowed = existing.allowed if existing is not None else False
        changed = (
            existing is None
            or existing.allowed != feature_allowed
            or existing.usage_limit != usage_limit
            or existing.valid_until != valid_until
            or existing.reason != reason
            or existing.subscription_id != subscription.id
        )
        if existing is None:
            existing = BillingEntitlement(
                owner_user_id=event.owner_user_id,
                subscription_id=subscription.id,
                feature_key=feature_key,
                allowed=feature_allowed,
                usage_limit=usage_limit,
                usage_consumed=0,
                valid_until=valid_until,
                reason=reason,
                projection_version=1,
            )
            db.add(existing)
        elif changed:
            existing.subscription_id = subscription.id
            existing.allowed = feature_allowed
            existing.usage_limit = usage_limit
            existing.valid_until = valid_until
            existing.reason = reason
            existing.projection_version += 1
            existing.updated_at = now_utc()
        if changed:
            action = "GRANTED" if feature_allowed and not prior_allowed else "CHANGED"
            if prior_allowed and not feature_allowed:
                action = "REVOKED"
            db.add(
                BillingEntitlementEvent(
                    owner_user_id=event.owner_user_id,
                    subscription_id=subscription.id,
                    feature_key=feature_key,
                    action=action,
                    usage_limit=usage_limit,
                    valid_until=valid_until,
                    reason=reason,
                    provider_event_key=event.event_key,
                )
            )
    await db.flush()


async def _record_refund(
    db: AsyncSession,
    *,
    event: ParsedWebhook,
    provider: str,
    subscription: BillingSubscription,
) -> None:
    status = "CHARGEBACK" if event.event_name in _CHARGEBACK_EVENTS else "REFUNDED"
    if event.event_name in _REFUND_EVENTS and not _is_full_refund(event):
        status = "PARTIALLY_REFUNDED"
    amount = event.attributes.get("refunded_amount") or event.attributes.get("amount")
    amount_minor = int(amount) if isinstance(amount, (int, str)) and str(amount).isdigit() else None
    currency = event.attributes.get("currency")
    currency = str(currency).upper()[:3] if currency else None
    refund_id = str(event.attributes.get("refund_id") or event.event_key)
    if len(refund_id) > 160:
        raise BillingWebhookRejected("Webhook refund identity is too long.")
    existing = (
        await db.execute(
            select(BillingRefundEvent).where(
                BillingRefundEvent.provider == provider,
                BillingRefundEvent.provider_refund_id == refund_id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            BillingRefundEvent(
                owner_user_id=event.owner_user_id,
                subscription_id=subscription.id,
                provider=provider,
                provider_refund_id=refund_id,
                amount_minor=amount_minor,
                currency=currency,
                status=status,
                provider_event_key=event.event_key,
            )
        )


def _is_full_refund(event: ParsedWebhook) -> bool:
    if event.attributes.get("refunded") is True:
        return True
    if str(event.attributes.get("status", "")).lower() == "refunded":
        return True
    refunded_amount = event.attributes.get("refunded_amount")
    total = event.attributes.get("total")
    if all(isinstance(value, int) for value in (refunded_amount, total)):
        return total > 0 and refunded_amount >= total
    return False


async def process_webhook(
    db: AsyncSession,
    *,
    provider: str,
    payload: dict[str, Any],
    raw_body: bytes,
    signature: str,
    settings: Settings | None = None,
) -> WebhookResult:
    settings = settings or get_settings()
    if provider != settings.billing_provider or provider == "disabled":
        raise BillingUnavailable("This billing webhook provider is not configured.")
    payload_digest = hashlib.sha256(raw_body).hexdigest()
    signature_digest = hashlib.sha256(signature.encode()).hexdigest()
    event = _parse_webhook(
        settings,
        provider=provider,
        payload=payload,
        payload_digest=payload_digest,
    )
    await set_user_context(db, event.owner_user_id)
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
        {"lock_key": f"billing-event:{provider}:{event.event_key}"},
    )
    duplicate = (
        await db.execute(
            select(BillingWebhookReceipt).where(
                BillingWebhookReceipt.provider == provider,
                BillingWebhookReceipt.provider_event_key == event.event_key,
            )
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        return WebhookResult(
            duplicate=True,
            processing_status=duplicate.processing_status,
            outcome_code=duplicate.outcome_code,
        )

    checkout = (
        await db.execute(
            select(BillingCheckoutSession)
            .where(
                BillingCheckoutSession.id == event.checkout_session_id,
                BillingCheckoutSession.owner_user_id == event.owner_user_id,
                BillingCheckoutSession.plan_code == event.plan_code,
                BillingCheckoutSession.provider == provider,
                BillingCheckoutSession.is_test == event.is_test,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if checkout is None:
        raise BillingWebhookRejected("Webhook checkout binding does not exist.")

    plan = (
        await db.execute(
            select(BillingPlan).where(
                BillingPlan.code == event.plan_code,
                BillingPlan.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if plan is None or plan.is_free:
        raise BillingWebhookRejected("Webhook plan is not billable.")
    variant = _event_variant(event.attributes)
    if provider == "test":
        expected_variant = f"test:{event.plan_code}"
    else:
        expected_variant = settings.lemon_squeezy_variants.get(event.plan_code)
    if event.event_name in {"order_created", "subscription_created"} and variant in (
        None,
        "",
    ):
        raise BillingWebhookRejected("Webhook variant is missing.")
    if variant not in (None, "") and str(variant) != str(expected_variant):
        raise BillingWebhookRejected("Webhook variant does not match the bound plan.")

    recognized = (
        event.event_name in _PROJECTED_SUBSCRIPTION_EVENTS
        or event.event_name in _ORDER_EVENTS
        or event.event_name in _REFUND_EVENTS
        or event.event_name in _CHARGEBACK_EVENTS
    )
    if not recognized:
        await _receipt(
            db,
            event=event,
            provider=provider,
            payload_digest=payload_digest,
            signature_digest=signature_digest,
            processing_status="IGNORED",
            outcome_code="UNSUPPORTED_EVENT",
        )
        return WebhookResult(False, "IGNORED", "UNSUPPORTED_EVENT")

    if event.event_name == "order_created":
        if event.resource_type != "orders":
            raise BillingWebhookRejected("Order webhook resource type is invalid.")
        if event.event_at > checkout.reservation_expires_at:
            raise BillingWebhookRejected("The originating checkout had already expired.")
        subtotal = event.attributes.get("subtotal")
        currency = event.attributes.get("currency")
        if (
            not isinstance(subtotal, int)
            or subtotal != plan.price_minor
            or str(currency).upper() != plan.currency
        ):
            raise BillingWebhookRejected("Order amount does not match the bound plan.")
        if str(event.attributes.get("status", "")).lower() != "paid":
            raise BillingWebhookRejected("Order is not in a paid state.")
        receipt_url = _customer_document_url(event.attributes)
        if receipt_url is None:
            raise BillingWebhookRejected("Order receipt URL is invalid.")
        checkout.latest_receipt_url = receipt_url
        checkout.updated_at = now_utc()
        await _upsert_customer(db, event=event, provider=provider)
        attached_subscription = (
            await db.execute(
                select(BillingSubscription)
                .where(
                    BillingSubscription.owner_user_id == event.owner_user_id,
                    BillingSubscription.checkout_session_id == checkout.id,
                )
                .order_by(BillingSubscription.created_at.desc())
                .limit(1)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if attached_subscription is not None:
            attached_subscription.latest_receipt_url = receipt_url
            attached_subscription.updated_at = now_utc()
        await _receipt(
            db,
            event=event,
            provider=provider,
            payload_digest=payload_digest,
            signature_digest=signature_digest,
            processing_status="PROCESSED",
            outcome_code="ORDER_RECORDED",
        )
        return WebhookResult(False, "PROCESSED", "ORDER_RECORDED")

    provider_subscription_id = str(
        event.attributes.get("subscription_id") or event.resource_id
    )
    if len(provider_subscription_id) > 160:
        raise BillingWebhookRejected("Webhook subscription identity is too long.")
    subscription = (
        await db.execute(
            select(BillingSubscription)
            .where(
                BillingSubscription.owner_user_id == event.owner_user_id,
                BillingSubscription.provider == provider,
                BillingSubscription.provider_subscription_id == provider_subscription_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if subscription is None and event.event_name in (_REFUND_EVENTS | _CHARGEBACK_EVENTS):
        subscription = (
            await db.execute(
                select(BillingSubscription)
                .where(
                    BillingSubscription.owner_user_id == event.owner_user_id,
                    BillingSubscription.checkout_session_id == checkout.id,
                )
                .order_by(BillingSubscription.created_at.desc())
                .limit(1)
                .with_for_update()
            )
        ).scalar_one_or_none()
    if subscription is None and event.event_name != "subscription_created":
        raise BillingWebhookRejected(
            "A subscription-created event must establish the provider subscription first."
        )
    if (
        subscription is None
        and event.event_at > checkout.reservation_expires_at
    ):
        raise BillingWebhookRejected("The originating checkout had already expired.")
    if subscription is not None:
        stale = event.event_at < subscription.last_provider_event_at or (
            event.event_at == subscription.last_provider_event_at
            and event.event_rank <= subscription.last_provider_event_rank
        )
        if stale:
            await _receipt(
                db,
                event=event,
                provider=provider,
                payload_digest=payload_digest,
                signature_digest=signature_digest,
                processing_status="IGNORED",
                outcome_code="STALE_EVENT",
            )
            return WebhookResult(False, "IGNORED", "STALE_EVENT")

    if event.event_name in _REFUND_EVENTS and not _is_full_refund(event):
        if subscription is None:
            raise BillingWebhookRejected("Refund has no matching subscription.")
        await _record_refund(
            db,
            event=event,
            provider=provider,
            subscription=subscription,
        )
        subscription.last_provider_event_at = event.event_at
        subscription.last_provider_event_rank = event.event_rank
        subscription.last_provider_event_key = event.event_key
        subscription.updated_at = now_utc()
        await _receipt(
            db,
            event=event,
            provider=provider,
            payload_digest=payload_digest,
            signature_digest=signature_digest,
            processing_status="PROCESSED",
            outcome_code="PARTIAL_REFUND_RECORDED",
        )
        return WebhookResult(False, "PROCESSED", "PARTIAL_REFUND_RECORDED")

    status, provider_status = _canonical_status(event)
    if len(provider_status) > 48:
        raise BillingWebhookRejected("Webhook subscription status is too long.")
    customer = await _upsert_customer(db, event=event, provider=provider)
    period_start = _parse_datetime(event.attributes.get("created_at"))
    period_end = _parse_datetime(
        event.attributes.get("ends_at")
        or event.attributes.get("renews_at")
        or event.attributes.get("trial_ends_at")
    )
    if subscription is None:
        subscription = BillingSubscription(
            owner_user_id=event.owner_user_id,
            customer_id=customer.id if customer else None,
            checkout_session_id=checkout.id,
            plan_code=plan.code,
            provider=provider,
            provider_subscription_id=provider_subscription_id,
            provider_status=provider_status,
            status=status,
            is_test=event.is_test,
            current_period_start=period_start,
            current_period_end=period_end,
            cancel_at_period_end=status == "cancel_at_period_end",
            cancelled_at=event.event_at if status in {"cancel_at_period_end", "cancelled"} else None,
            ended_at=event.event_at if status in {"cancelled", "expired", "refunded", "chargeback"} else None,
            last_provider_event_at=event.event_at,
            last_provider_event_rank=event.event_rank,
            last_provider_event_key=event.event_key,
            latest_receipt_url=checkout.latest_receipt_url,
        )
        db.add(subscription)
        await db.flush()
    else:
        subscription.customer_id = customer.id if customer else subscription.customer_id
        subscription.plan_code = plan.code
        subscription.provider_status = provider_status
        subscription.status = status
        subscription.current_period_start = period_start or subscription.current_period_start
        subscription.current_period_end = period_end or subscription.current_period_end
        subscription.cancel_at_period_end = status == "cancel_at_period_end"
        if status in {"cancel_at_period_end", "cancelled"}:
            subscription.cancelled_at = event.event_at
        elif status in {"active", "trialing"}:
            subscription.cancelled_at = None
        subscription.ended_at = (
            event.event_at
            if status in {"cancelled", "expired", "refunded", "chargeback"}
            else None
        )
        subscription.last_provider_event_at = event.event_at
        subscription.last_provider_event_rank = event.event_rank
        subscription.last_provider_event_key = event.event_key
        subscription.updated_at = now_utc()

    checkout.status = "COMPLETED"
    checkout.completed_at = checkout.completed_at or event.event_at
    checkout.updated_at = now_utc()
    if event.event_name in (_REFUND_EVENTS | _CHARGEBACK_EVENTS):
        await _record_refund(
            db,
            event=event,
            provider=provider,
            subscription=subscription,
        )
    trusted_receipt_url = _customer_document_url(event.attributes)
    if trusted_receipt_url is not None:
        subscription.latest_receipt_url = trusted_receipt_url
    await _project_entitlements(
        db,
        settings=settings,
        event=event,
        subscription=subscription,
        plan=plan,
    )
    await emit_domain_event(
        db,
        owner_user_id=event.owner_user_id,
        event_type="subscription.changed",
        aggregate_type="billing_subscription",
        aggregate_id=subscription.id,
        idempotency_key=f"billing:{provider}:{event.event_key}",
        payload={
            "subscription_id": str(subscription.id),
            "plan_code": plan.code,
            "status": subscription.status,
            "is_test": subscription.is_test,
        },
    )
    await _receipt(
        db,
        event=event,
        provider=provider,
        payload_digest=payload_digest,
        signature_digest=signature_digest,
        processing_status="PROCESSED",
        outcome_code="SUBSCRIPTION_PROJECTED",
    )
    return WebhookResult(False, "PROCESSED", "SUBSCRIPTION_PROJECTED")


async def subscription_state(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
) -> tuple[BillingSubscription | None, list[BillingEntitlement], list[BillingRefundEvent]]:
    subscription = (
        await db.execute(
            select(BillingSubscription)
            .where(BillingSubscription.owner_user_id == owner_user_id)
            .order_by(BillingSubscription.updated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if subscription is None:
        return None, [], []
    entitlements = (
        await db.execute(
            select(BillingEntitlement)
            .where(
                BillingEntitlement.owner_user_id == owner_user_id,
                BillingEntitlement.subscription_id == subscription.id,
            )
            .order_by(BillingEntitlement.feature_key)
        )
    ).scalars().all()
    refunds = (
        await db.execute(
            select(BillingRefundEvent)
            .where(
                BillingRefundEvent.owner_user_id == owner_user_id,
                BillingRefundEvent.subscription_id == subscription.id,
            )
            .order_by(BillingRefundEvent.created_at.desc())
        )
    ).scalars().all()
    return subscription, list(entitlements), list(refunds)


async def create_portal(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    settings: Settings | None = None,
) -> tuple[str, dt.datetime]:
    settings = settings or get_settings()
    subscription, _, _ = await subscription_state(db, owner_user_id=owner_user_id)
    if subscription is None:
        raise BillingNotFound("No billing subscription exists.")
    if subscription.status in {"expired", "refunded", "chargeback"}:
        raise BillingConflict("This subscription no longer has a provider portal.")
    if subscription.provider != settings.billing_provider:
        raise BillingUnavailable("The subscription provider is not configured.")
    provider = build_billing_provider(settings)
    try:
        url = await provider.customer_portal_url(subscription.provider_subscription_id)
    except BillingProviderError as exc:
        raise BillingUnavailable(str(exc)) from exc
    expires_at = now_utc() + dt.timedelta(hours=24)
    subscription.latest_portal_url = url
    subscription.latest_portal_expires_at = expires_at
    subscription.updated_at = now_utc()
    await db.flush()
    return url, expires_at


def decode_webhook_body(raw_body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, RecursionError, UnicodeDecodeError) as exc:
        raise BillingWebhookRejected("Webhook body is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise BillingWebhookRejected("Webhook body must be a JSON object.")
    return payload
