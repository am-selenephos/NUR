"""Track A persisted Glow economy and translation foundation."""

from alembic import op


revision = "0011_track_a_glow_translation"
down_revision = "0010_product_surfaces_i18n"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


def _owner_all(table: str) -> None:
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
    op.execute(
        f"CREATE POLICY p_{table}_owner_update ON {table} FOR UPDATE TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) "
        f"WITH CHECK (owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_{table}_owner_delete ON {table} FOR DELETE TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE glow_rules (
            event_type TEXT PRIMARY KEY,
            base_points INTEGER NOT NULL CHECK (base_points >= 0),
            daily_cap INTEGER CHECK (daily_cap IS NULL OR daily_cap >= 0),
            streak_key TEXT,
            active BOOLEAN NOT NULL DEFAULT true,
            description TEXT NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("GRANT SELECT ON glow_rules TO nur_app")
    op.execute("""
        INSERT INTO glow_rules(event_type, base_points, daily_cap, streak_key, description) VALUES
          ('daily_checkin', 2, 2, 'daily_orbit', 'A persisted private daily check-in.'),
          ('talk_meaningful', 2, 10, 'talk', 'A persisted meaningful Talk turn.'),
          ('journal_saved', 4, 12, 'journal', 'A persisted Journal entry.'),
          ('plan_created', 4, 8, 'plan_movement', 'A persisted Plan.'),
          ('plan_step_completed', 8, 32, 'plan_movement', 'A completed owned Plan step.'),
          ('task_made_smaller', 3, 12, 'plan_movement', 'A Plan step reduced to a more workable move.'),
          ('outcome_returned', 15, 45, 'outcome_return', 'A persisted real-world outcome.')
    """)

    op.execute("""
        CREATE TABLE glow_balances (
            owner_user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            balance INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
            lifetime_points INTEGER NOT NULL DEFAULT 0 CHECK (lifetime_points >= 0),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE glow_transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_type TEXT NOT NULL REFERENCES glow_rules(event_type),
            source_kind TEXT NOT NULL,
            source_id UUID NOT NULL,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            base_points INTEGER NOT NULL CHECK (base_points >= 0),
            multiplier NUMERIC(8,3) NOT NULL DEFAULT 1 CHECK (multiplier >= 0),
            final_points INTEGER NOT NULL CHECK (final_points >= 0),
            reason TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            reversed BOOLEAN NOT NULL DEFAULT false,
            reversal_reason TEXT,
            anti_abuse_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, idempotency_key)
        )
    """)
    op.execute("CREATE INDEX ix_glow_transactions_owner_created ON glow_transactions(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_glow_transactions_source ON glow_transactions(owner_user_id, source_kind, source_id)")

    op.execute("""
        CREATE TABLE glow_streaks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            streak_key TEXT NOT NULL,
            current_count INTEGER NOT NULL DEFAULT 0 CHECK (current_count >= 0),
            best_count INTEGER NOT NULL DEFAULT 0 CHECK (best_count >= 0),
            last_event_date DATE,
            repairs_remaining INTEGER NOT NULL DEFAULT 0 CHECK (repairs_remaining >= 0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, streak_key)
        )
    """)
    op.execute("CREATE INDEX ix_glow_streaks_owner ON glow_streaks(owner_user_id)")

    op.execute("""
        CREATE TABLE glow_reward_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            source_id UUID NOT NULL,
            idempotency_key TEXT NOT NULL,
            transaction_id UUID NOT NULL REFERENCES glow_transactions(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'AWARDED',
            event_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, idempotency_key)
        )
    """)

    op.execute("""
        CREATE TABLE translations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_hash TEXT NOT NULL,
            source_locale TEXT,
            target_locale TEXT NOT NULL,
            content_type TEXT NOT NULL,
            source_text TEXT NOT NULL,
            translated_text TEXT,
            status TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT,
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_translations_owner_created ON translations(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_translations_cache ON translations(owner_user_id, source_hash, target_locale, content_type, provider)")

    for table in [
        "glow_balances",
        "glow_transactions",
        "glow_streaks",
        "glow_reward_events",
        "translations",
    ]:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        _owner_all(table)


def downgrade() -> None:
    for table in [
        "translations",
        "glow_reward_events",
        "glow_streaks",
        "glow_transactions",
        "glow_balances",
        "glow_rules",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
