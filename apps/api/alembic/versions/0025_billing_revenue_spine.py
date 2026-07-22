"""provider-verified billing, subscriptions, and entitlements

Revision ID: 0025_billing_revenue_spine
Revises: 0024_teach_nur_pipeline
"""

from alembic import op


revision = "0025_billing_revenue_spine"
down_revision = "0024_teach_nur_pipeline"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = (
    "current_setting('app.current_user_id', true) IS NOT NULL AND "
    "current_setting('app.current_user_id', true) <> ''"
)


def _owner_policies(table: str, *, update: bool = True) -> None:
    privileges = "SELECT, INSERT"
    if update:
        privileges += ", UPDATE"
    op.execute(f"GRANT {privileges} ON {table} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY p_{table}_owner_select ON {table} FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_{table}_owner_insert ON {table} FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    if update:
        op.execute(
            f"CREATE POLICY p_{table}_owner_update ON {table} FOR UPDATE TO {APP_ROLE} "
            f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) "
            f"WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
        )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE billing_plans (
            code VARCHAR(48) PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            description TEXT NOT NULL,
            price_minor INTEGER NOT NULL CHECK (price_minor >= 0),
            currency VARCHAR(3) NOT NULL CHECK (currency = upper(currency)),
            billing_interval VARCHAR(16) NOT NULL
                CHECK (billing_interval IN ('none','month','year')),
            seat_cap INTEGER CHECK (seat_cap > 0),
            is_free BOOLEAN NOT NULL,
            active BOOLEAN NOT NULL DEFAULT true,
            entitlements JSONB NOT NULL DEFAULT '{}'::jsonb,
            legal_copy_version VARCHAR(32) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK ((is_free AND price_minor = 0 AND billing_interval = 'none') OR
                   (NOT is_free AND price_minor > 0 AND billing_interval <> 'none'))
        )
    """)
    op.execute("GRANT SELECT ON billing_plans TO nur_app")
    op.get_bind().exec_driver_sql("""
        INSERT INTO billing_plans (
            code, name, description, price_minor, currency, billing_interval,
            seat_cap, is_free, active, entitlements, legal_copy_version
        ) VALUES
        (
            'orbit_scan_free', 'Orbit Scan Free',
            'Private orientation and a grounded first next step.',
            0, 'USD', 'none', NULL, true, true,
            '{"ai.daily_requests":{"limit":50},"orbit_scan":{"allowed":true}}',
            'beta-2026-07-13'
        ),
        (
            'founding_orbit', 'Founding Orbit',
            'Annual founder cohort access. Limited to the first 50 real paid seats.',
            9900, 'USD', 'year', 50, false, true,
            '{"ai.daily_requests":{"limit":200},"paid_continuity":{"allowed":true},"memory.persistent":{"allowed":true},"galaxy.full":{"allowed":true},"planning.advanced":{"allowed":true},"weekly.reflection":{"allowed":true}}',
            'beta-2026-07-13'
        ),
        (
            'nur_plus_monthly', 'NUR Plus',
            'Monthly personal continuity, full galaxy, planning, and reflections.',
            1299, 'USD', 'month', NULL, false, true,
            '{"ai.daily_requests":{"limit":150},"paid_continuity":{"allowed":true},"memory.persistent":{"allowed":true},"galaxy.full":{"allowed":true},"planning.advanced":{"allowed":true},"weekly.reflection":{"allowed":true}}',
            'beta-2026-07-13'
        ),
        (
            'nur_plus_annual', 'Annual Plus',
            'Annual personal continuity, full galaxy, planning, and reflections.',
            12900, 'USD', 'year', NULL, false, true,
            '{"ai.daily_requests":{"limit":200},"paid_continuity":{"allowed":true},"memory.persistent":{"allowed":true},"galaxy.full":{"allowed":true},"planning.advanced":{"allowed":true},"weekly.reflection":{"allowed":true}}',
            'beta-2026-07-13'
        )
    """)

    op.execute("""
        CREATE TABLE billing_checkout_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan_code VARCHAR(48) NOT NULL REFERENCES billing_plans(code),
            provider VARCHAR(32) NOT NULL,
            provider_checkout_id VARCHAR(160),
            checkout_url TEXT,
            latest_receipt_url TEXT,
            idempotency_key VARCHAR(160) NOT NULL,
            status VARCHAR(24) NOT NULL CHECK (
                status IN ('PENDING','CREATED','COMPLETED','EXPIRED','FAILED')
            ),
            is_test BOOLEAN NOT NULL,
            reservation_expires_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, idempotency_key)
        )
    """)
    op.execute(
        "CREATE INDEX ix_billing_checkout_plan_reservation "
        "ON billing_checkout_sessions(plan_code, reservation_expires_at) "
        "WHERE status IN ('PENDING','CREATED')"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_billing_checkout_one_open_per_owner_mode "
        "ON billing_checkout_sessions(owner_user_id, is_test) "
        "WHERE status IN ('PENDING','CREATED')"
    )

    op.execute("""
        CREATE TABLE billing_customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider VARCHAR(32) NOT NULL,
            provider_customer_id VARCHAR(160) NOT NULL,
            is_test BOOLEAN NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(provider, provider_customer_id),
            UNIQUE(owner_user_id, provider, is_test)
        )
    """)

    op.execute("""
        CREATE TABLE billing_subscriptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            customer_id UUID REFERENCES billing_customers(id) ON DELETE SET NULL,
            checkout_session_id UUID
                REFERENCES billing_checkout_sessions(id) ON DELETE SET NULL,
            plan_code VARCHAR(48) NOT NULL REFERENCES billing_plans(code),
            provider VARCHAR(32) NOT NULL,
            provider_subscription_id VARCHAR(160) NOT NULL,
            provider_status VARCHAR(48) NOT NULL,
            status VARCHAR(32) NOT NULL CHECK (status IN (
                'trialing','active','past_due','paused','cancel_at_period_end',
                'cancelled','expired','refunded','chargeback'
            )),
            is_test BOOLEAN NOT NULL,
            current_period_start TIMESTAMPTZ,
            current_period_end TIMESTAMPTZ,
            cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
            cancelled_at TIMESTAMPTZ,
            ended_at TIMESTAMPTZ,
            last_provider_event_at TIMESTAMPTZ NOT NULL,
            last_provider_event_rank INTEGER NOT NULL,
            last_provider_event_key VARCHAR(160) NOT NULL,
            latest_receipt_url TEXT,
            latest_portal_url TEXT,
            latest_portal_expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(provider, provider_subscription_id)
        )
    """)
    op.execute(
        "CREATE INDEX ix_billing_subscription_owner_status "
        "ON billing_subscriptions(owner_user_id, status, updated_at DESC)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_billing_subscription_one_open_per_owner_mode "
        "ON billing_subscriptions(owner_user_id, is_test) "
        "WHERE status IN ("
        "'trialing','active','past_due','paused','cancel_at_period_end'"
        ")"
    )

    op.execute("""
        CREATE TABLE billing_entitlements (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subscription_id UUID NOT NULL
                REFERENCES billing_subscriptions(id) ON DELETE CASCADE,
            feature_key VARCHAR(96) NOT NULL,
            allowed BOOLEAN NOT NULL,
            usage_limit INTEGER CHECK (usage_limit IS NULL OR usage_limit >= 0),
            usage_consumed INTEGER NOT NULL DEFAULT 0 CHECK (usage_consumed >= 0),
            valid_until TIMESTAMPTZ,
            reason VARCHAR(120) NOT NULL,
            projection_version INTEGER NOT NULL CHECK (projection_version >= 1),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, feature_key)
        )
    """)

    op.execute("""
        CREATE TABLE billing_entitlement_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subscription_id UUID NOT NULL
                REFERENCES billing_subscriptions(id) ON DELETE CASCADE,
            feature_key VARCHAR(96) NOT NULL,
            action VARCHAR(16) NOT NULL CHECK (action IN ('GRANTED','CHANGED','REVOKED')),
            usage_limit INTEGER CHECK (usage_limit IS NULL OR usage_limit >= 0),
            valid_until TIMESTAMPTZ,
            reason VARCHAR(120) NOT NULL,
            provider_event_key VARCHAR(160) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, feature_key, provider_event_key)
        )
    """)

    op.execute("""
        CREATE TABLE billing_webhook_receipts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider VARCHAR(32) NOT NULL,
            provider_event_key VARCHAR(160) NOT NULL,
            event_name VARCHAR(80) NOT NULL,
            resource_type VARCHAR(64) NOT NULL,
            resource_id VARCHAR(160) NOT NULL,
            payload_digest VARCHAR(64) NOT NULL,
            signature_digest VARCHAR(64) NOT NULL,
            provider_event_at TIMESTAMPTZ NOT NULL,
            event_rank INTEGER NOT NULL,
            processing_status VARCHAR(24) NOT NULL CHECK (
                processing_status IN ('PROCESSED','IGNORED','REJECTED')
            ),
            outcome_code VARCHAR(64) NOT NULL,
            processed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(provider, provider_event_key)
        )
    """)
    op.execute(
        "CREATE INDEX ix_billing_receipt_owner_created "
        "ON billing_webhook_receipts(owner_user_id, created_at DESC)"
    )

    op.execute("""
        CREATE TABLE billing_refund_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subscription_id UUID NOT NULL
                REFERENCES billing_subscriptions(id) ON DELETE CASCADE,
            provider VARCHAR(32) NOT NULL,
            provider_refund_id VARCHAR(160) NOT NULL,
            amount_minor BIGINT CHECK (amount_minor IS NULL OR amount_minor >= 0),
            currency VARCHAR(3),
            status VARCHAR(24) NOT NULL CHECK (
                status IN ('REFUNDED','PARTIALLY_REFUNDED','CHARGEBACK')
            ),
            provider_event_key VARCHAR(160) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(provider, provider_refund_id)
        )
    """)

    for table in (
        "billing_checkout_sessions",
        "billing_customers",
        "billing_subscriptions",
        "billing_entitlements",
    ):
        _owner_policies(table)
    for table in (
        "billing_entitlement_events",
        "billing_webhook_receipts",
        "billing_refund_events",
    ):
        _owner_policies(table, update=False)
    for table in ("billing_checkout_sessions", "billing_subscriptions"):
        op.execute(
            f"CREATE POLICY p_{table}_schema_owner ON {table} FOR SELECT TO nur_admin "
            "USING (true)"
        )
    op.execute("""
        CREATE FUNCTION billing_real_seats_claimed(requested_plan VARCHAR)
        RETURNS BIGINT
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
            SELECT
                (SELECT count(*) FROM public.billing_subscriptions
                 WHERE plan_code = requested_plan
                   AND NOT is_test
                   AND status IN (
                       'trialing','active','past_due','paused','cancel_at_period_end'
                   ))
              + (SELECT count(*) FROM public.billing_checkout_sessions
                 WHERE plan_code = requested_plan
                   AND NOT is_test
                   AND status IN ('PENDING','CREATED')
                   AND reservation_expires_at > now())
        $$
    """)
    op.execute("REVOKE ALL ON FUNCTION billing_real_seats_claimed(VARCHAR) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION billing_real_seats_claimed(VARCHAR) TO nur_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS billing_real_seats_claimed(VARCHAR)")
    for table in (
        "billing_refund_events",
        "billing_webhook_receipts",
        "billing_entitlement_events",
        "billing_entitlements",
        "billing_subscriptions",
        "billing_customers",
        "billing_checkout_sessions",
        "billing_plans",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
