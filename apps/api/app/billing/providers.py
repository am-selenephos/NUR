import datetime as dt
import uuid
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote, urlparse

import httpx

from app.core.config import Settings


class BillingProviderError(RuntimeError):
    pass


class BillingProviderDisabled(BillingProviderError):
    pass


@dataclass(frozen=True)
class CheckoutRequest:
    session_id: uuid.UUID
    owner_user_id: uuid.UUID
    plan_code: str
    customer_email: str
    custom_data: dict[str, str]
    redirect_url: str
    idempotency_key: str
    expires_at: dt.datetime
    expected_price_minor: int
    expected_currency: str


@dataclass(frozen=True)
class CheckoutResult:
    provider_checkout_id: str
    checkout_url: str


class BillingProvider(Protocol):
    name: str

    async def create_checkout(self, request: CheckoutRequest) -> CheckoutResult: ...

    async def customer_portal_url(self, provider_subscription_id: str) -> str: ...


def _safe_https_url(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise BillingProviderError(f"Billing provider returned no valid {label} URL.")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise BillingProviderError(f"Billing provider returned no valid {label} URL.")
    return value


class DisabledBillingProvider:
    name = "disabled"

    async def create_checkout(self, request: CheckoutRequest) -> CheckoutResult:
        del request
        raise BillingProviderDisabled("Billing checkout is not configured.")

    async def customer_portal_url(self, provider_subscription_id: str) -> str:
        del provider_subscription_id
        raise BillingProviderDisabled("Billing portal is not configured.")


class TestBillingProvider:
    """Deterministic no-charge adapter for integration tests and local demos."""

    name = "test"

    async def create_checkout(self, request: CheckoutRequest) -> CheckoutResult:
        checkout_id = f"test_checkout_{request.session_id.hex}"
        return CheckoutResult(
            provider_checkout_id=checkout_id,
            checkout_url=f"https://billing.test/checkout/{checkout_id}",
        )

    async def customer_portal_url(self, provider_subscription_id: str) -> str:
        safe_id = quote(provider_subscription_id, safe="")
        return f"https://billing.test/portal/{safe_id}"


class LemonSqueezyBillingProvider:
    name = "lemon_squeezy"
    _base_url = "https://api.lemonsqueezy.com/v1"

    def __init__(self, settings: Settings):
        self._settings = settings

    def _headers(self, *, idempotency_key: str | None = None) -> dict[str, str]:
        api_key = self._settings.lemon_squeezy_api_key
        if api_key is None:
            raise BillingProviderDisabled("Lemon Squeezy billing is not configured.")
        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    async def create_checkout(self, request: CheckoutRequest) -> CheckoutResult:
        variant_id = self._settings.lemon_squeezy_variants.get(request.plan_code, "")
        if not variant_id:
            raise BillingProviderDisabled("This plan has no configured checkout variant.")
        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": request.customer_email,
                        "custom": request.custom_data,
                    },
                    "product_options": {
                        "redirect_url": request.redirect_url,
                        "enabled_variants": [int(variant_id)],
                    },
                    "checkout_options": {"embed": False, "discount": False},
                    "test_mode": self._settings.billing_test_mode,
                    "expires_at": request.expires_at.isoformat(),
                    "preview": True,
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": self._settings.lemon_squeezy_store_id,
                        }
                    },
                    "variant": {"data": {"type": "variants", "id": variant_id}},
                },
            }
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self._base_url}/checkouts",
                    headers=self._headers(idempotency_key=request.idempotency_key),
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()["data"]
            checkout_id = str(data["id"])
            attributes = data.get("attributes", {})
            checkout_url = _safe_https_url(attributes.get("url"), label="checkout")
            preview = attributes["preview"]
            if (
                int(preview["subtotal"]) != request.expected_price_minor
                or str(preview["currency"]).upper() != request.expected_currency
            ):
                raise BillingProviderError(
                    "The configured provider price does not match the NUR plan catalog."
                )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise BillingProviderError("The billing provider could not create checkout.") from exc
        return CheckoutResult(
            provider_checkout_id=checkout_id,
            checkout_url=checkout_url,
        )

    async def customer_portal_url(self, provider_subscription_id: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self._base_url}/subscriptions/"
                    f"{quote(provider_subscription_id, safe='')}",
                    headers=self._headers(),
                )
            response.raise_for_status()
            value = response.json()["data"]["attributes"]["urls"]["customer_portal"]
            return _safe_https_url(value, label="customer portal")
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise BillingProviderError(
                "The billing provider could not create a customer portal session."
            ) from exc


def build_billing_provider(settings: Settings) -> BillingProvider:
    if settings.billing_provider == "test":
        return TestBillingProvider()
    if settings.billing_provider == "lemon_squeezy":
        return LemonSqueezyBillingProvider(settings)
    return DisabledBillingProvider()
