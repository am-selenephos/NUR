"""hashed, expiring password reset challenges

Revision ID: 0022_password_recovery
Revises: 0021_talk_stream_idempotency
"""

from alembic import op


revision = "0022_password_recovery"
down_revision = "0021_talk_stream_idempotency"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
AUTH_CTX = "current_setting('app.auth_context', true) = 'on'"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


def upgrade() -> None:
    op.execute("""
        CREATE TABLE password_reset_challenges (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_digest VARCHAR(64) NOT NULL UNIQUE,
            request_fingerprint VARCHAR(16) NOT NULL,
            delivery_adapter VARCHAR(32) NOT NULL,
            delivery_status VARCHAR(16) NOT NULL DEFAULT 'PENDING'
                CHECK (delivery_status IN ('PENDING','DELIVERED','FAILED')),
            expires_at TIMESTAMPTZ NOT NULL,
            delivered_at TIMESTAMPTZ,
            consumed_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_password_reset_expiry CHECK (expires_at > created_at)
        )
    """)
    op.execute("CREATE INDEX ix_password_reset_challenges_user_id ON password_reset_challenges(user_id)")
    op.execute("CREATE INDEX ix_password_reset_challenges_expires_at ON password_reset_challenges(expires_at)")
    op.execute("""
        CREATE INDEX ix_password_reset_challenges_active_user
        ON password_reset_challenges(user_id, created_at DESC)
        WHERE consumed_at IS NULL AND revoked_at IS NULL
    """)
    op.execute("ALTER TABLE password_reset_challenges ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE password_reset_challenges FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON password_reset_challenges TO {APP_ROLE}")
    op.execute(
        f"CREATE POLICY p_password_reset_auth_select ON password_reset_challenges "
        f"FOR SELECT TO {APP_ROLE} USING ({AUTH_CTX})"
    )
    op.execute(
        f"CREATE POLICY p_password_reset_auth_insert ON password_reset_challenges "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX})"
    )
    op.execute(
        f"CREATE POLICY p_password_reset_auth_update ON password_reset_challenges "
        f"FOR UPDATE TO {APP_ROLE} USING ({AUTH_CTX}) WITH CHECK ({AUTH_CTX})"
    )
    op.execute(
        f"CREATE POLICY p_sessions_owner_update ON sessions FOR UPDATE TO {APP_ROLE} "
        f"USING ({HAS_USER} AND user_id = {OWNER_UUID}) WITH CHECK (user_id = {OWNER_UUID})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS p_sessions_owner_update ON sessions")
    op.execute("DROP TABLE IF EXISTS password_reset_challenges CASCADE")
