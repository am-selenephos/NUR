"""SOL living system: Today, seven Systems, goals, schedules, and Glow depth."""

from alembic import op


revision = "0012_sol_living_system"
down_revision = "0011_track_a_glow_translation"
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
    op.execute("ALTER TABLE glow_rules ADD COLUMN weekly_cap INTEGER CHECK (weekly_cap IS NULL OR weekly_cap >= 0)")
    op.execute("ALTER TABLE glow_rules ADD COLUMN spam_window_seconds INTEGER NOT NULL DEFAULT 0 CHECK (spam_window_seconds >= 0)")
    op.execute("ALTER TABLE glow_rules ADD COLUMN action_type TEXT")
    op.execute("ALTER TABLE glow_rules ADD COLUMN system_slug TEXT")
    op.execute("ALTER TABLE glow_rules ADD COLUMN requires_persistence BOOLEAN NOT NULL DEFAULT true")
    op.execute("ALTER TABLE glow_transactions ADD COLUMN system_slug TEXT")
    op.execute("CREATE INDEX ix_glow_transactions_owner_system ON glow_transactions(owner_user_id, system_slug, created_at DESC)")
    op.execute("UPDATE glow_rules SET action_type=event_type, weekly_cap=daily_cap * 7 WHERE action_type IS NULL")
    op.execute("UPDATE glow_rules SET spam_window_seconds=30 WHERE event_type='talk_meaningful'")

    op.execute("""
        INSERT INTO glow_rules(
            event_type, base_points, daily_cap, weekly_cap, spam_window_seconds,
            action_type, requires_persistence, description
        ) VALUES
          ('goal.created', 8, 32, 96, 0, 'goal.created', true, 'A persisted owner Goal.'),
          ('objective.created', 6, 36, 108, 0, 'objective.created', true, 'A persisted Goal objective.'),
          ('schedule.created', 5, 30, 90, 0, 'schedule.created', true, 'A persisted scheduled action.'),
          ('system.checklist_answered', 3, 21, 63, 0, 'system.checklist_answered', true, 'A persisted Star System diagnostic.'),
          ('system.action_marked', 6, 42, 126, 0, 'system.action_marked', true, 'A completed persisted Star System action.'),
          ('missed_step_returned', 7, 21, 63, 0, 'missed_step_returned', true, 'A missed action returned to movement.'),
          ('feasibility.created', 5, 20, 60, 0, 'feasibility.created', true, 'A persisted feasibility assessment.')
        ON CONFLICT (event_type) DO NOTHING
    """)

    op.execute("""
        CREATE TABLE goals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            system_slug TEXT NOT NULL,
            title TEXT NOT NULL,
            why TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','COMPLETED','PAUSED','ARCHIVED')),
            progress_percent INTEGER NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
            target_date DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_goals_owner_system ON goals(owner_user_id, system_slug, created_at DESC)")
    op.execute("CREATE INDEX ix_goals_owner_status ON goals(owner_user_id, status)")

    op.execute("""
        CREATE TABLE objectives (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','COMPLETED','PAUSED','ARCHIVED')),
            progress_percent INTEGER NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
            target_date DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_objectives_owner_goal ON objectives(owner_user_id, goal_id)")

    op.execute("""
        CREATE TABLE system_diagnostics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            system_slug TEXT NOT NULL,
            answers JSONB NOT NULL DEFAULT '{}'::jsonb,
            score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
            blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
            strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_system_diagnostics_owner_system ON system_diagnostics(owner_user_id, system_slug, created_at DESC)")

    op.execute("""
        CREATE TABLE system_actions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            system_slug TEXT NOT NULL,
            diagnostic_id UUID REFERENCES system_diagnostics(id) ON DELETE SET NULL,
            goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
            objective_id UUID REFERENCES objectives(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','COMPLETED','MISSED','CANCELLED')),
            due_at TIMESTAMPTZ,
            effort_minutes INTEGER CHECK (effort_minutes IS NULL OR effort_minutes BETWEEN 1 AND 1440),
            completed_at TIMESTAMPTZ,
            missed_at TIMESTAMPTZ,
            easier_from_id UUID REFERENCES system_actions(id) ON DELETE SET NULL,
            outcome_id UUID REFERENCES outcomes(id) ON DELETE SET NULL,
            action_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_system_actions_owner_system ON system_actions(owner_user_id, system_slug, created_at DESC)")
    op.execute("CREATE INDEX ix_system_actions_owner_status_due ON system_actions(owner_user_id, status, due_at)")

    op.execute("""
        CREATE TABLE scheduled_actions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            system_slug TEXT NOT NULL,
            goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
            objective_id UUID REFERENCES objectives(id) ON DELETE SET NULL,
            system_action_id UUID REFERENCES system_actions(id) ON DELETE SET NULL,
            plan_step_id UUID REFERENCES plan_steps(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            scheduled_for TIMESTAMPTZ NOT NULL,
            duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes BETWEEN 1 AND 1440),
            status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED','COMPLETED','MISSED','CANCELLED')),
            completed_at TIMESTAMPTZ,
            missed_at TIMESTAMPTZ,
            schedule_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_scheduled_actions_owner_due ON scheduled_actions(owner_user_id, scheduled_for)")
    op.execute("CREATE INDEX ix_scheduled_actions_owner_status ON scheduled_actions(owner_user_id, status)")

    op.execute("""
        CREATE TABLE today_checkins (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            checkin_date DATE NOT NULL,
            energy INTEGER NOT NULL CHECK (energy BETWEEN 0 AND 10),
            pain INTEGER NOT NULL CHECK (pain BETWEEN 0 AND 10),
            sleep_quality INTEGER NOT NULL CHECK (sleep_quality BETWEEN 0 AND 10),
            nourishment INTEGER NOT NULL CHECK (nourishment BETWEEN 0 AND 10),
            movement INTEGER NOT NULL CHECK (movement BETWEEN 0 AND 10),
            emotional_load INTEGER NOT NULL CHECK (emotional_load BETWEEN 0 AND 10),
            clarity INTEGER NOT NULL CHECK (clarity BETWEEN 0 AND 10),
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, checkin_date)
        )
    """)
    op.execute("CREATE INDEX ix_today_checkins_owner_date ON today_checkins(owner_user_id, checkin_date DESC)")

    op.execute("""
        CREATE TABLE glow_achievements (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            achievement_key TEXT NOT NULL,
            source_transaction_id UUID NOT NULL REFERENCES glow_transactions(id) ON DELETE CASCADE,
            achievement_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            unlocked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, achievement_key)
        )
    """)
    op.execute("CREATE INDEX ix_glow_achievements_owner ON glow_achievements(owner_user_id, unlocked_at DESC)")

    for table in [
        "goals",
        "objectives",
        "system_diagnostics",
        "system_actions",
        "scheduled_actions",
        "today_checkins",
        "glow_achievements",
    ]:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        _owner_all(table)


def downgrade() -> None:
    for table in [
        "glow_achievements",
        "today_checkins",
        "scheduled_actions",
        "system_actions",
        "system_diagnostics",
        "objectives",
        "goals",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("DROP INDEX IF EXISTS ix_glow_transactions_owner_system")
    op.execute("ALTER TABLE glow_transactions DROP COLUMN IF EXISTS system_slug")
    for column in [
        "requires_persistence",
        "system_slug",
        "action_type",
        "spam_window_seconds",
        "weekly_cap",
    ]:
        op.execute(f"ALTER TABLE glow_rules DROP COLUMN IF EXISTS {column}")
