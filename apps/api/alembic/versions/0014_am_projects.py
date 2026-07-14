"""AM Projects: owner project cockpit, work graph, runs, artifacts, evidence, reviews."""

from alembic import op


revision = "0014_am_projects"
down_revision = "0013_map_feasibility"
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
        CREATE TABLE am_projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            title VARCHAR(240) NOT NULL,
            objective TEXT NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE','PAUSED','COMPLETED','ARCHIVED')),
            system_slug VARCHAR(48),
            deadline TIMESTAMPTZ,
            budget_cents INTEGER CHECK (budget_cents IS NULL OR budget_cents >= 0),
            permission_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, orbit_id)
        )
    """)
    op.execute("CREATE INDEX ix_am_projects_owner_status ON am_projects(owner_user_id, status, updated_at DESC)")

    op.execute("""
        CREATE TABLE am_project_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES am_projects(id) ON DELETE CASCADE,
            parent_task_id UUID REFERENCES am_project_tasks(id) ON DELETE SET NULL,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            acceptance_criteria TEXT,
            status VARCHAR(32) NOT NULL DEFAULT 'BACKLOG'
                CHECK (status IN ('BACKLOG','READY','IN_PROGRESS','BLOCKED','REVIEW','DONE','CANCELLED')),
            priority INTEGER NOT NULL DEFAULT 50 CHECK (priority BETWEEN 0 AND 100),
            assigned_role VARCHAR(80),
            due_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_am_project_tasks_owner_project ON am_project_tasks(owner_user_id, project_id, status, priority DESC)")

    op.execute("""
        CREATE TABLE am_project_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES am_projects(id) ON DELETE CASCADE,
            task_id UUID REFERENCES am_project_tasks(id) ON DELETE SET NULL,
            role VARCHAR(80) NOT NULL,
            request_summary TEXT NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'PROPOSED'
                CHECK (status IN ('PROPOSED','APPROVED','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
            tool_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
            budget_cents INTEGER NOT NULL DEFAULT 0 CHECK (budget_cents >= 0),
            approval_required BOOLEAN NOT NULL DEFAULT true,
            approved_at TIMESTAMPTZ,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            result_summary TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_am_project_runs_owner_project ON am_project_runs(owner_user_id, project_id, created_at DESC)")

    op.execute("""
        CREATE TABLE am_project_artifacts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES am_projects(id) ON DELETE CASCADE,
            task_id UUID REFERENCES am_project_tasks(id) ON DELETE SET NULL,
            run_id UUID REFERENCES am_project_runs(id) ON DELETE SET NULL,
            artifact_kind VARCHAR(64) NOT NULL,
            title VARCHAR(500) NOT NULL,
            locator TEXT NOT NULL,
            checksum_sha256 VARCHAR(64),
            provenance_label VARCHAR(64) NOT NULL DEFAULT 'OWNER_SUPPLIED',
            review_status VARCHAR(32) NOT NULL DEFAULT 'UNREVIEWED'
                CHECK (review_status IN ('UNREVIEWED','ACCEPTED','REJECTED')),
            artifact_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_am_project_artifacts_owner_project ON am_project_artifacts(owner_user_id, project_id, created_at DESC)")

    op.execute("""
        CREATE TABLE am_project_evidence (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES am_projects(id) ON DELETE CASCADE,
            task_id UUID REFERENCES am_project_tasks(id) ON DELETE SET NULL,
            run_id UUID REFERENCES am_project_runs(id) ON DELETE SET NULL,
            evidence_kind VARCHAR(64) NOT NULL,
            summary TEXT NOT NULL,
            locator TEXT,
            checksum_sha256 VARCHAR(64),
            verification_status VARCHAR(32) NOT NULL DEFAULT 'UNVERIFIED'
                CHECK (verification_status IN ('UNVERIFIED','PASSED','FAILED')),
            verifier VARCHAR(120),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_am_project_evidence_owner_project ON am_project_evidence(owner_user_id, project_id, created_at DESC)")

    op.execute("""
        CREATE TABLE am_project_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES am_projects(id) ON DELETE CASCADE,
            run_id UUID REFERENCES am_project_runs(id) ON DELETE SET NULL,
            task_id UUID REFERENCES am_project_tasks(id) ON DELETE SET NULL,
            decision VARCHAR(32) NOT NULL CHECK (decision IN ('APPROVE','REJECT','CORRECT')),
            note TEXT,
            reviewer_label VARCHAR(80) NOT NULL DEFAULT 'OWNER',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_am_project_reviews_owner_project ON am_project_reviews(owner_user_id, project_id, created_at DESC)")

    for table in (
        "am_projects", "am_project_tasks", "am_project_runs",
        "am_project_artifacts", "am_project_evidence", "am_project_reviews",
    ):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        _owner_all(table)

    op.execute("""
        INSERT INTO glow_rules(
            event_type, base_points, daily_cap, weekly_cap, spam_window_seconds,
            action_type, requires_persistence, description
        ) VALUES
          ('project.created', 8, 32, 96, 0, 'project.created', true, 'A persisted AM Project with an explicit objective.'),
          ('project.task_completed', 8, 48, 144, 0, 'project.task_completed', true, 'A persisted AM Project task passed its completion gate.'),
          ('project.evidence_verified', 6, 36, 108, 0, 'project.evidence_verified', true, 'Persisted AM Project evidence passed verification.')
        ON CONFLICT (event_type) DO NOTHING
    """)


def downgrade() -> None:
    for table in (
        "am_project_reviews", "am_project_evidence", "am_project_artifacts",
        "am_project_runs", "am_project_tasks", "am_projects",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("DELETE FROM glow_rules WHERE event_type IN ('project.created','project.task_completed','project.evidence_verified')")
