from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.deps import DB, Identity, Scoped, require_csrf
from app.billing import service
from app.billing.schemas import (
    BillingPlanOut,
    BillingStateOut,
    CheckoutCreate,
    CheckoutOut,
    EntitlementOut,
    PlanFeatureOut,
    PortalOut,
    RefundOut,
    SubscriptionOut,
    WebhookAck,
)
from app.core.config import get_settings
from app.observability.metrics import record_counter

router = APIRouter(prefix="/billing", tags=["billing"])

IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=160,
        pattern=r"^[A-Za-z0-9._:-]+$",
    ),
]
WebhookSignature = Annotated[
    str,
    Header(alias="X-Signature", min_length=32, max_length=256),
]


def _raise_service_error(exc: Exception) -> None:
    if isinstance(exc, service.BillingNotFound):
        raise HTTPException(404, str(exc)) from exc
    if isinstance(exc, service.BillingConflict):
        raise HTTPException(409, str(exc)) from exc
    if isinstance(exc, service.BillingUnavailable):
        raise HTTPException(503, str(exc)) from exc
    if isinstance(exc, service.BillingWebhookRejected):
        raise HTTPException(422, str(exc)) from exc
    raise exc


@router.get("/plans", response_model=list[BillingPlanOut])
async def plans(db: DB) -> list[BillingPlanOut]:
    rows = await service.list_plans(db)
    return [
        BillingPlanOut(
            code=item.plan.code,
            name=item.plan.name,
            description=item.plan.description,
            price_minor=item.plan.price_minor,
            currency=item.plan.currency,
            billing_interval=item.plan.billing_interval,
            seat_cap=item.plan.seat_cap,
            seats_remaining=item.seats_remaining,
            is_free=item.plan.is_free,
            active=item.plan.active,
            legal_copy_version=item.plan.legal_copy_version,
            features=[
                PlanFeatureOut(
                    feature_key=feature_key,
                    allowed=bool(value.get("allowed", True)),
                    usage_limit=(
                        value.get("limit")
                        if isinstance(value.get("limit"), int)
                        else None
                    ),
                )
                for feature_key, value in sorted(item.plan.entitlements.items())
                if isinstance(value, dict)
            ],
        )
        for item in rows
    ]


@router.post(
    "/checkout",
    response_model=CheckoutOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def checkout(
    payload: CheckoutCreate,
    idempotency_key: IdempotencyKey,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> CheckoutOut:
    settings = get_settings()
    try:
        row = await service.create_checkout(
            db,
            owner_user_id=identity[0],
            plan_code=payload.plan_code,
            idempotency_key=idempotency_key,
            settings=settings,
        )
    except Exception as exc:
        _raise_service_error(exc)
    await db.commit()
    record_counter(
        request,
        "nur_billing_checkout_total",
        (("provider", row.provider), ("mode", "test" if row.is_test else "live")),
    )
    return CheckoutOut(
        session_id=row.id,
        plan_code=row.plan_code,
        provider=row.provider,
        checkout_url=row.checkout_url or "",
        status=row.status,
        is_test=row.is_test,
        reservation_expires_at=row.reservation_expires_at,
        renews_automatically=True,
        terms_url=settings.billing_terms_url or None,
        privacy_url=settings.billing_privacy_url or None,
        refund_policy_url=settings.billing_refund_policy_url or None,
    )


@router.post("/webhooks/{provider}", response_model=WebhookAck)
async def webhook(
    provider: str,
    signature: WebhookSignature,
    request: Request,
    db: DB,
) -> WebhookAck:
    settings = get_settings()
    if provider not in {"test", "lemon_squeezy"}:
        raise HTTPException(404, "Billing provider not found.")
    if settings.billing_provider != provider:
        raise HTTPException(503, "This billing webhook provider is not configured.")
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > 512_000:
        raise HTTPException(413, "Webhook body is too large.")
    raw_body = await request.body()
    if len(raw_body) > 512_000:
        raise HTTPException(413, "Webhook body is too large.")
    try:
        if not service.verify_webhook_signature(settings, raw_body, signature):
            raise HTTPException(400, "Webhook signature is invalid.")
        payload = service.decode_webhook_body(raw_body)
        result = await service.process_webhook(
            db,
            provider=provider,
            payload=payload,
            raw_body=raw_body,
            signature=signature,
            settings=settings,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_service_error(exc)
    await db.commit()
    record_counter(
        request,
        "nur_billing_webhook_total",
        (("provider", provider), ("outcome", result.outcome_code)),
    )
    return WebhookAck(
        accepted=True,
        duplicate=result.duplicate,
        processing_status=result.processing_status,
        outcome_code=result.outcome_code,
    )


@router.get("/subscription", response_model=BillingStateOut)
async def subscription(db: Scoped, identity: Identity) -> BillingStateOut:
    settings = get_settings()
    row, entitlements, refunds = await service.subscription_state(
        db, owner_user_id=identity[0]
    )
    portal_available = bool(
        row
        and row.provider == settings.billing_provider
        and row.status not in {"expired", "refunded", "chargeback"}
    )
    if row is None:
        cancellation_note = "No paid subscription. Orbit Scan Free remains available."
    elif row.status == "cancel_at_period_end":
        cancellation_note = "Cancellation is scheduled; access remains until the paid period ends."
    elif row.status in {"expired", "cancelled", "refunded", "chargeback"}:
        cancellation_note = "Paid access has ended. No further renewal is scheduled."
    else:
        cancellation_note = "Manage renewal, invoices, or cancellation in the provider portal."
    return BillingStateOut(
        subscription=SubscriptionOut.model_validate(row) if row else None,
        entitlements=[EntitlementOut.model_validate(item) for item in entitlements],
        refunds=[RefundOut.model_validate(item) for item in refunds],
        provider_configured=settings.billing_provider != "disabled",
        portal_available=portal_available,
        cancellation_note=cancellation_note,
        terms_url=settings.billing_terms_url or None,
        privacy_url=settings.billing_privacy_url or None,
        refund_policy_url=settings.billing_refund_policy_url or None,
    )


@router.post(
    "/portal",
    response_model=PortalOut,
    dependencies=[Depends(require_csrf)],
)
async def portal(db: Scoped, identity: Identity) -> PortalOut:
    try:
        url, expires_at = await service.create_portal(
            db,
            owner_user_id=identity[0],
            settings=get_settings(),
        )
    except Exception as exc:
        _raise_service_error(exc)
    await db.commit()
    return PortalOut(url=url, expires_at=expires_at)
