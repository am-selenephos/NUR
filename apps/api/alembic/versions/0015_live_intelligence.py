"""Evidence-linked insights, future timeline, and social Orbits."""

from alembic import op


revision = "0015_live_intelligence"
down_revision = "0014_am_projects"
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
    for value in ("PERSON", "GROUP", "COUNCIL", "COMMUNITY", "SYSTEM"):
        op.execute(f"ALTER TYPE orbit_kind ADD VALUE IF NOT EXISTS '{value}'")

    op.execute("""
        CREATE TABLE people (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            display_name VARCHAR(240) NOT NULL,
            handle VARCHAR(240),
            relationship_type VARCHAR(80),
            notes TEXT,
            privacy_scope VARCHAR(32) NOT NULL DEFAULT 'PRIVATE_ORBIT',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_people_owner_recent ON people(owner_user_id, updated_at DESC)")
    op.execute("ALTER TABLE orbits ADD COLUMN primary_person_id UUID REFERENCES people(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE orbits ADD COLUMN system_slug VARCHAR(48)")
    op.execute("ALTER TABLE orbits ADD COLUMN privacy_scope VARCHAR(32) NOT NULL DEFAULT 'PRIVATE_ORBIT'")
    op.execute("ALTER TABLE orbits ADD COLUMN orbit_metadata JSONB NOT NULL DEFAULT '{}'::jsonb")

    op.execute("""
        CREATE TABLE orbit_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
            role VARCHAR(80) NOT NULL DEFAULT 'MEMBER',
            closeness_score INTEGER NOT NULL DEFAULT 0 CHECK (closeness_score BETWEEN 0 AND 100),
            recent_activity_score INTEGER NOT NULL DEFAULT 0 CHECK (recent_activity_score BETWEEN 0 AND 100),
            unresolved_count INTEGER NOT NULL DEFAULT 0 CHECK (unresolved_count >= 0),
            shared_goal_count INTEGER NOT NULL DEFAULT 0 CHECK (shared_goal_count >= 0),
            last_interaction_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, orbit_id, person_id)
        )
    """)
    op.execute("CREATE INDEX ix_orbit_members_owner_orbit ON orbit_members(owner_user_id, orbit_id, recent_activity_score DESC)")
    op.execute("""
        CREATE TABLE orbit_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            event_type VARCHAR(80) NOT NULL,
            source_type VARCHAR(80),
            source_id UUID,
            summary TEXT NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            event_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_orbit_events_owner_orbit ON orbit_events(owner_user_id, orbit_id, occurred_at DESC)")

    op.execute("""
        CREATE TABLE timeline_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_type VARCHAR(80) NOT NULL,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            time_kind VARCHAR(24) NOT NULL DEFAULT 'FUTURE'
                CHECK (time_kind IN ('PAST','PRESENT','FUTURE','PREDICTION','PROJECT','PEOPLE','SYSTEM')),
            scheduled_for TIMESTAMPTZ,
            occurred_at TIMESTAMPTZ,
            source_type VARCHAR(80) NOT NULL,
            source_id UUID,
            system_slug VARCHAR(48),
            goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
            objective_id UUID REFERENCES objectives(id) ON DELETE SET NULL,
            plan_id UUID REFERENCES plans(id) ON DELETE SET NULL,
            project_id UUID REFERENCES am_projects(id) ON DELETE SET NULL,
            person_id UUID REFERENCES people(id) ON DELETE SET NULL,
            group_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
            status VARCHAR(24) NOT NULL DEFAULT 'PLANNED'
                CHECK (status IN ('PLANNED','DUE','COMPLETED','MISSED','CANCELLED')),
            importance INTEGER NOT NULL DEFAULT 50 CHECK (importance BETWEEN 0 AND 100),
            event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_timeline_events_owner_time ON timeline_events(owner_user_id, scheduled_for, created_at DESC)")

    op.execute("""
        CREATE TABLE insights (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            insight_type VARCHAR(48) NOT NULL,
            title VARCHAR(500) NOT NULL,
            claim TEXT NOT NULL,
            tone VARCHAR(48) NOT NULL DEFAULT 'DIRECT',
            confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
            valence VARCHAR(24) NOT NULL DEFAULT 'NEUTRAL'
                CHECK (valence IN ('POSITIVE','HARD','NEUTRAL','MIXED')),
            source_event_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            source_memory_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            source_research_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            affected_system_slug VARCHAR(48),
            affected_goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
            affected_project_id UUID REFERENCES am_projects(id) ON DELETE SET NULL,
            affected_person_id UUID REFERENCES people(id) ON DELETE SET NULL,
            evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
            counter_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
            what_nur_may_be_wrong_about TEXT NOT NULL,
            positive_interpretation TEXT,
            hard_interpretation TEXT,
            suggested_action TEXT,
            status VARCHAR(24) NOT NULL DEFAULT 'CANDIDATE'
                CHECK (status IN ('CANDIDATE','ACCEPTED','REJECTED','CORRECTED','ARCHIVED')),
            correction TEXT,
            provenance_label VARCHAR(64) NOT NULL DEFAULT 'INFERRED_OWNER_LEDGER',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_insights_owner_status ON insights(owner_user_id, status, updated_at DESC)")

    for table in ("people", "orbit_members", "orbit_events", "timeline_events", "insights"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        _owner_all(table)


def downgrade() -> None:
    for table in ("insights", "timeline_events", "orbit_events", "orbit_members"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS orbit_metadata")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS privacy_scope")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS system_slug")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS primary_person_id")
    op.execute("DROP TABLE IF EXISTS people CASCADE")
