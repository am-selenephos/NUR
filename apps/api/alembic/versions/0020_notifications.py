"""Owner-scoped notification preferences and truthful in-app reminders."""

from alembic import op

revision = "0020_notifications"
down_revision = "0019_consultations"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
UID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("""
        CREATE TABLE notification_preferences (
            owner_user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            category_settings JSONB NOT NULL DEFAULT '{}'::jsonb,
            frequency VARCHAR(24) NOT NULL DEFAULT 'BALANCED',
            quiet_hours_start VARCHAR(5),
            quiet_hours_end VARCHAR(5),
            push_enabled BOOLEAN NOT NULL DEFAULT false,
            email_enabled BOOLEAN NOT NULL DEFAULT false,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(48) NOT NULL,
            title VARCHAR(240) NOT NULL,
            body TEXT NOT NULL,
            route VARCHAR(500),
            source_type VARCHAR(80) NOT NULL DEFAULT 'OWNER_REMINDER',
            source_id UUID,
            provenance_label VARCHAR(48) NOT NULL DEFAULT 'OWNER_WRITTEN',
            delivery_state VARCHAR(24) NOT NULL DEFAULT 'IN_APP',
            is_demo BOOLEAN NOT NULL DEFAULT false,
            scheduled_at TIMESTAMPTZ,
            read_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_notifications_owner_created ON notifications(owner_user_id, created_at DESC)")
    for table in ("notification_preferences", "notifications"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        owner = "owner_user_id"
        op.execute(f"CREATE POLICY p_{table}_select ON {table} FOR SELECT TO {APP_ROLE} USING ({owner} = {UID})")
        op.execute(f"CREATE POLICY p_{table}_insert ON {table} FOR INSERT TO {APP_ROLE} WITH CHECK ({owner} = {UID})")
        op.execute(f"CREATE POLICY p_{table}_update ON {table} FOR UPDATE TO {APP_ROLE} USING ({owner} = {UID}) WITH CHECK ({owner} = {UID})")
        op.execute(f"CREATE POLICY p_{table}_delete ON {table} FOR DELETE TO {APP_ROLE} USING ({owner} = {UID})")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notifications CASCADE")
    op.execute("DROP TABLE IF EXISTS notification_preferences CASCADE")
