"""Persisted feasibility assessments for Map, Insights, and Today."""

from alembic import op


revision = "0013_map_feasibility"
down_revision = "0012_sol_living_system"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


def upgrade() -> None:
    op.execute("""
        CREATE TABLE feasibility_assessments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            system_slug TEXT NOT NULL,
            subject_kind TEXT NOT NULL,
            subject_id UUID,
            title TEXT NOT NULL,
            desired_outcome TEXT NOT NULL,
            capacity_required INTEGER NOT NULL CHECK (capacity_required BETWEEN 0 AND 100),
            current_capacity INTEGER NOT NULL CHECK (current_capacity BETWEEN 0 AND 100),
            time_required_minutes INTEGER NOT NULL CHECK (time_required_minutes >= 0),
            time_available_minutes INTEGER NOT NULL CHECK (time_available_minutes >= 0),
            money_required_cents BIGINT NOT NULL CHECK (money_required_cents >= 0),
            money_available_cents BIGINT NOT NULL CHECK (money_available_cents >= 0),
            risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
            result TEXT NOT NULL CHECK (result IN ('FEASIBLE','FEASIBLE_IF_SMALLER','NOT_FEASIBLE_NOW')),
            rationale TEXT NOT NULL,
            checks JSONB NOT NULL DEFAULT '{}'::jsonb,
            suggestions JSONB NOT NULL DEFAULT '[]'::jsonb,
            source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_feasibility_owner_created ON feasibility_assessments(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_feasibility_owner_system ON feasibility_assessments(owner_user_id, system_slug)")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON feasibility_assessments TO nur_app")
    op.execute("ALTER TABLE feasibility_assessments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE feasibility_assessments FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY p_feasibility_assessments_owner_select ON feasibility_assessments "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        "CREATE POLICY p_feasibility_assessments_owner_insert ON feasibility_assessments "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        "CREATE POLICY p_feasibility_assessments_owner_update ON feasibility_assessments "
        f"FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) "
        f"WITH CHECK (owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        "CREATE POLICY p_feasibility_assessments_owner_delete ON feasibility_assessments "
        f"FOR DELETE TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS feasibility_assessments CASCADE")
