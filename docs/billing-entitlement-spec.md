# Billing and Entitlement Contract

Date: 2026-07-29

## Readiness boundary

The server-side revenue spine is implemented with a deterministic no-charge
adapter and a Lemon Squeezy merchant-of-record adapter. Local integration
evidence is not a real paid entitlement. `REVENUE_SPINE_PASS` remains blocked
until the founder supplies a provider test account and one provider-hosted
checkout, signed webhook, entitlement, portal cancellation, and expiry/refund
path is captured end to end.

Live charges require all three conditions:

- `NUR_BILLING_PROVIDER=lemon_squeezy`;
- `NUR_BILLING_TEST_MODE=false`;
- `NUR_BILLING_LIVE_ENABLED=true`.

No provider key, webhook secret, checkout binding, or raw webhook is returned
to a browser or written to a domain event.

## Catalog

| Code | Offer | Price | Interval | Real seat cap |
|---|---|---:|---|---:|
| `orbit_scan_free` | Orbit Scan Free | $0 | none | none |
| `founding_orbit` | Founding Orbit | $99 | year | 50 |
| `nur_plus_monthly` | NUR Plus | $12.99 | month | none |
| `nur_plus_annual` | Annual Plus | $129 | year | none |

Founding Orbit availability counts non-test subscriptions and unexpired
non-test checkout reservations under a per-plan PostgreSQL advisory lock.
Provider checkout URLs receive the same expiry, one enabled variant, and a
server-verified catalog subtotal/currency. Test-mode purchases never consume a
real seat.

## HTTP contract

- `GET /api/v1/billing/plans` is public catalog truth. It exposes no customer
  data and reports real Founding Orbit seats remaining.
- `POST /api/v1/billing/checkout` requires an authenticated session, CSRF, and
  `Idempotency-Key`. It creates a provider checkout, never an entitlement.
- `POST /api/v1/billing/webhooks/{provider}` accepts no user session as proof.
  It verifies the provider HMAC over the raw body before parsing or writing.
- `GET /api/v1/billing/subscription` returns the current owner-scoped
  subscription, entitlements, refund state, and plain cancellation status.
- `POST /api/v1/billing/portal` requires authentication and CSRF and returns a
  provider-signed management URL with a 24-hour server expiry.

## Canonical states

`trialing`, `active`, `past_due`, `paused`, `cancel_at_period_end`,
`cancelled`, `expired`, `refunded`, and `chargeback` are the only persisted
subscription states.

- Trialing and active access last until the provider period end.
- Cancellation keeps access only through `ends_at`.
- Past-due access uses the configured bounded grace period.
- Paused, cancelled, expired, refunded, and chargeback states deny paid
  entitlements.
- Older or same-rank provider events cannot resurrect a newer terminal state.

## Trust and persistence

The provider webhook signature authenticates delivery. A second HMAC binding
ties provider custom data to `owner_user_id`, checkout session, original plan,
and provider. The server then verifies the owner-scoped checkout, mode, and
variant before projecting state.

Receipts retain event/resource identifiers plus payload and signature digests;
they do not retain raw webhook JSON. Replays return the prior outcome.
Subscription, entitlement, receipt, and refund tables have forced owner RLS.
Entitlement and webhook histories are append-only to the runtime role.

## Entitlement consumer contract

Backend domains consume:

```python
from app.billing.entitlements import require_entitlement, resolve_entitlement
```

`resolve_entitlement(...)` returns an explicit deny when no active projection
exists. `require_entitlement(...)` raises `EntitlementRequired`; callers map it
to their domain's HTTP policy. Never trust a frontend plan name or hide-only UI
gate. The AI boundary uses `ai.daily_requests` when paid access is active and
falls back to the configured free beta limit otherwise.

Every accepted provider state transition emits `subscription.changed` with
IDs, plan code, canonical status, and test/live mode only. G10-G15 consumers
must use this event or `resolve_entitlement`; they must not read provider
payloads or duplicate status mapping.

## Provider references

- Webhook signatures: https://docs.lemonsqueezy.com/help/webhooks/signing-requests
- Webhook lifecycle: https://docs.lemonsqueezy.com/guides/developer-guide/webhooks
- Expiring API checkouts: https://docs.lemonsqueezy.com/api/checkouts/create-checkout
- Customer portal: https://docs.lemonsqueezy.com/guides/developer-guide/customer-portal
- Subscription lifecycle: https://docs.lemonsqueezy.com/help/webhooks/event-types
