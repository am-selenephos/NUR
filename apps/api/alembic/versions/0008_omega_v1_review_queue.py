"""Omega v1 confirmation review queue.

Sensitive inferred claims never become owner memory silently. They are staged
here under the same owner-only RLS law as the rest of Omega.
"""
from alembic import op

revision = "0008_omega_v1_review_queue"
down_revision = "0007_nur_omega_research_layer"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


def upgrade() -> None:
    op.execute("""
        CREATE TABLE omega_review_queue (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            experience_id UUID REFERENCES omega_experiences(id) ON DELETE SET NULL,
            candidate_claim_text TEXT NOT NULL,
            candidate_claim_type TEXT NOT NULL DEFAULT 'UNKNOWN' CHECK (candidate_claim_type IN (
                'FACT', 'PREFERENCE', 'CONSTRAINT', 'DECISION', 'PATTERN', 'RISK', 'HYPOTHESIS', 'UNKNOWN'
            )),
            candidate_truth_status TEXT NOT NULL DEFAULT 'HYPOTHESIS' CHECK (candidate_truth_status IN (
                'INFERRED', 'HYPOTHESIS'
            )),
            sensitivity TEXT NOT NULL DEFAULT 'SENSITIVE' CHECK (sensitivity IN (
                'LOW', 'PRIVATE', 'SENSITIVE', 'SECRET_EXCLUDED'
            )),
            reason TEXT NOT NULL,
            model_candidate JSONB NOT NULL DEFAULT '{}'::jsonb,
            status TEXT NOT NULL DEFAULT 'PENDING_REVIEW' CHECK (status IN (
                'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'EDITED'
            )),
            created_claim_id UUID REFERENCES omega_claims(id) ON DELETE SET NULL,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_omega_review_owner_status ON omega_review_queue(owner_user_id, status, created_at DESC)")
    op.execute("CREATE INDEX ix_omega_review_experience ON omega_review_queue(experience_id)")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON omega_review_queue TO {APP_ROLE}")
    op.execute("ALTER TABLE omega_review_queue ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE omega_review_queue FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY p_omega_review_owner_select ON omega_review_queue FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_omega_review_owner_insert ON omega_review_queue FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_omega_review_owner_update ON omega_review_queue FOR UPDATE TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS omega_review_queue CASCADE")
