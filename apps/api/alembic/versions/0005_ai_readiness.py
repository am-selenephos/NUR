"""Gate 5.5 readiness: server AI model runs and intelligence kernel ledgers."""
from alembic import op

revision = "0005_ai_readiness"
down_revision = "0004_shared_orbit"
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
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) WITH CHECK (owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_{table}_owner_delete ON {table} FOR DELETE TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE model_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            provider TEXT NOT NULL,
            model TEXT,
            mode TEXT NOT NULL DEFAULT 'talk',
            status TEXT NOT NULL DEFAULT 'COMPLETED',
            input_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            output_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            run_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            response_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            usage JSONB NOT NULL DEFAULT '{}'::jsonb,
            error JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_model_runs_owner_created ON model_runs(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_model_runs_input_event ON model_runs(input_event_id)")

    op.execute("""
        CREATE TABLE model_run_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            model_run_id UUID NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
            source_kind TEXT NOT NULL,
            source_id UUID,
            excerpt TEXT,
            rank REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_model_run_sources_run ON model_run_sources(model_run_id)")

    op.execute("""
        CREATE TABLE model_evaluations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            model_run_id UUID REFERENCES model_runs(id) ON DELETE SET NULL,
            verdict TEXT NOT NULL,
            checks JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE user_corrections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            target_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            correction_text TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE memory_candidates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            source_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            candidate_text TEXT NOT NULL,
            scope memory_scope NOT NULL DEFAULT 'LEARNING_CANDIDATE',
            status TEXT NOT NULL DEFAULT 'CANDIDATE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE predictions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            source_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            statement TEXT NOT NULL,
            expected_observation JSONB NOT NULL DEFAULT '{}'::jsonb,
            status TEXT NOT NULL DEFAULT 'OPEN',
            outcome_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    for table in [
        "model_runs", "model_run_sources", "model_evaluations",
        "user_corrections", "memory_candidates", "predictions",
    ]:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        _owner_all(table)


def downgrade() -> None:
    for table in [
        "predictions", "memory_candidates", "user_corrections",
        "model_evaluations", "model_run_sources", "model_runs",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
