"""Bounded ORIENT to RETURN Consultation lifecycle with FORCE RLS."""

from alembic import op


revision = "0019_consultations"
down_revision = "0018_council_demo_markers"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
UID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


def _enable(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")


def upgrade() -> None:
    op.execute("""
        CREATE TABLE consultations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            room_id UUID REFERENCES community_rooms(id) ON DELETE SET NULL,
            room_owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            system_slug VARCHAR(48),
            title VARCHAR(240) NOT NULL,
            question TEXT NOT NULL,
            purpose TEXT NOT NULL,
            desired_outcome TEXT NOT NULL,
            scope_statement TEXT NOT NULL,
            current_stage VARCHAR(16) NOT NULL DEFAULT 'ORIENT'
                CHECK (current_stage IN ('ORIENT','GATHER','MAP','MOVE','RETURN')),
            status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE','COMPLETED','CLOSED')),
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id),
            CHECK ((room_id IS NULL AND room_owner_user_id IS NULL) OR
                   (room_id IS NOT NULL AND room_owner_user_id IS NOT NULL))
        )
    """)
    op.execute("CREATE INDEX ix_consultations_owner ON consultations(owner_user_id, updated_at DESC)")
    op.execute("CREATE INDEX ix_consultations_room ON consultations(room_id, updated_at DESC)")
    op.execute("""
        CREATE TABLE consultation_contributions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            consultation_id UUID NOT NULL,
            consultation_owner_user_id UUID NOT NULL,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contribution_type VARCHAR(48) NOT NULL,
            body TEXT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
            language_tag VARCHAR(20) NOT NULL DEFAULT 'en',
            provenance_label VARCHAR(48) NOT NULL DEFAULT 'MEMBER_WRITTEN',
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            FOREIGN KEY(consultation_id, consultation_owner_user_id)
                REFERENCES consultations(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute("CREATE INDEX ix_consultation_contributions_consultation ON consultation_contributions(consultation_id, created_at)")
    op.execute("""
        CREATE TABLE consultation_stage_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            consultation_id UUID NOT NULL,
            consultation_owner_user_id UUID NOT NULL,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stage VARCHAR(16) NOT NULL CHECK (stage IN ('ORIENT','GATHER','MAP','MOVE','RETURN')),
            stage_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            provenance_label VARCHAR(48) NOT NULL DEFAULT 'OWNER_WRITTEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(consultation_id, stage),
            FOREIGN KEY(consultation_id, consultation_owner_user_id)
                REFERENCES consultations(id, owner_user_id) ON DELETE CASCADE
        )
    """)

    for table in ("consultations", "consultation_contributions", "consultation_stage_records"):
        _enable(table)

    room_member = (
        "EXISTS (SELECT 1 FROM community_memberships cm "
        f"WHERE cm.room_id = consultations.room_id AND cm.user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_consultations_select ON consultations FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND (owner_user_id = {UID} OR {room_member}))"
    )
    op.execute(
        f"CREATE POLICY p_consultations_insert ON consultations FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID} AND (room_id IS NULL OR {room_member}))"
    )
    op.execute(
        f"CREATE POLICY p_consultations_owner_update ON consultations FOR UPDATE TO {APP_ROLE} "
        f"USING (owner_user_id = {UID}) WITH CHECK (owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_consultations_owner_delete ON consultations FOR DELETE TO {APP_ROLE} "
        f"USING (owner_user_id = {UID})"
    )

    access = (
        "EXISTS (SELECT 1 FROM consultations c WHERE c.id = {table}.consultation_id "
        f"AND (c.owner_user_id = {UID} OR EXISTS (SELECT 1 FROM community_memberships cm "
        f"WHERE cm.room_id = c.room_id AND cm.user_id = {UID})))"
    )
    for table in ("consultation_contributions", "consultation_stage_records"):
        table_access = access.format(table=table)
        op.execute(
            f"CREATE POLICY p_{table}_select ON {table} FOR SELECT TO {APP_ROLE} "
            f"USING ({HAS_USER} AND {table_access})"
        )
    contribution_access = access.format(table="consultation_contributions")
    op.execute(
        f"CREATE POLICY p_consultation_contributions_insert ON consultation_contributions FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID} AND {contribution_access})"
    )
    op.execute(
        f"CREATE POLICY p_consultation_contributions_author_update ON consultation_contributions FOR UPDATE TO {APP_ROLE} "
        f"USING (owner_user_id = {UID}) WITH CHECK (owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_consultation_contributions_author_delete ON consultation_contributions FOR DELETE TO {APP_ROLE} "
        f"USING (owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_consultation_stage_records_owner_insert ON consultation_stage_records FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID} AND consultation_owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_consultation_stage_records_owner_update ON consultation_stage_records FOR UPDATE TO {APP_ROLE} "
        f"USING (consultation_owner_user_id = {UID}) WITH CHECK (owner_user_id = {UID} AND consultation_owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_consultation_stage_records_owner_delete ON consultation_stage_records FOR DELETE TO {APP_ROLE} "
        f"USING (consultation_owner_user_id = {UID})"
    )

    op.execute("""
        INSERT INTO glow_rules(event_type, base_points, daily_cap, weekly_cap,
            spam_window_seconds, action_type, requires_persistence, streak_key, description)
        VALUES ('consultation_return', 18, 36, 72, 60, 'CONSULTATION_RETURN', true,
                'consultation', 'Return a real bounded Consultation with a persisted outcome.')
        ON CONFLICT (event_type) DO UPDATE SET
            base_points = EXCLUDED.base_points,
            daily_cap = EXCLUDED.daily_cap,
            weekly_cap = EXCLUDED.weekly_cap,
            spam_window_seconds = EXCLUDED.spam_window_seconds,
            action_type = EXCLUDED.action_type,
            requires_persistence = EXCLUDED.requires_persistence,
            streak_key = EXCLUDED.streak_key,
            description = EXCLUDED.description,
            active = true
    """)


def downgrade() -> None:
    op.execute("DELETE FROM glow_rules WHERE event_type = 'consultation_return'")
    for table in ("consultation_stage_records", "consultation_contributions", "consultations"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
