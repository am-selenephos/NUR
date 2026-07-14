"""NUR-Omega research layer: owner-only cognition research substrate."""
from alembic import op

revision = "0007_nur_omega_research_layer"
down_revision = "0006_quiet_sound_default"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


OMEGA_TABLES = [
    "omega_experiences",
    "omega_claims",
    "omega_evidence_edges",
    "omega_contradictions",
    "omega_workspace_frames",
    "omega_predictions",
    "omega_learning_proposals",
    "omega_consolidation_runs",
]


def _owner_only(table: str) -> None:
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {table} TO {APP_ROLE}")
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
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE omega_experiences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_kind TEXT NOT NULL,
            source_id UUID,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            event_kind TEXT NOT NULL,
            scope TEXT NOT NULL DEFAULT 'PRIVATE_ORBIT',
            language_tag TEXT NOT NULL DEFAULT 'und',
            summary TEXT NOT NULL,
            raw_ref JSONB,
            provenance_label TEXT NOT NULL CHECK (provenance_label IN (
                'OWNER_WRITTEN', 'OBSERVED_OUTCOME', 'MODEL_GENERATED', 'SYSTEM_MEASURED', 'USER_CORRECTION'
            )),
            sensitivity TEXT NOT NULL DEFAULT 'PRIVATE' CHECK (sensitivity IN (
                'LOW', 'PRIVATE', 'SENSITIVE', 'SECRET_EXCLUDED'
            )),
            confidence NUMERIC NOT NULL DEFAULT 1.0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_omega_experiences_owner_created ON omega_experiences(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_omega_experiences_source ON omega_experiences(source_kind, source_id)")

    op.execute("""
        CREATE TABLE omega_claims (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            claim_text TEXT NOT NULL,
            claim_type TEXT NOT NULL DEFAULT 'UNKNOWN' CHECK (claim_type IN (
                'FACT', 'PREFERENCE', 'CONSTRAINT', 'DECISION', 'PATTERN', 'RISK', 'HYPOTHESIS', 'UNKNOWN'
            )),
            truth_status TEXT NOT NULL DEFAULT 'HYPOTHESIS' CHECK (truth_status IN (
                'OBSERVED', 'INFERRED', 'HYPOTHESIS', 'CONTRADICTED', 'SUPERSEDED', 'RETIRED'
            )),
            confidence NUMERIC NOT NULL DEFAULT 0.5,
            support_count INT NOT NULL DEFAULT 0,
            contradiction_count INT NOT NULL DEFAULT 0,
            last_supported_at TIMESTAMPTZ,
            last_contradicted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_omega_claims_owner_status ON omega_claims(owner_user_id, truth_status, created_at DESC)")
    op.execute("CREATE INDEX ix_omega_claims_orbit ON omega_claims(orbit_id, created_at DESC)")

    op.execute("""
        CREATE TABLE omega_evidence_edges (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_id UUID NOT NULL REFERENCES omega_claims(id) ON DELETE CASCADE,
            evidence_kind TEXT NOT NULL CHECK (evidence_kind IN (
                'EXPERIENCE', 'OUTCOME', 'CORRECTION', 'MODEL_RUN', 'DECISION', 'REFERENCE', 'PLAN_STEP'
            )),
            evidence_id UUID NOT NULL,
            relation TEXT NOT NULL CHECK (relation IN (
                'SUPPORTS', 'CONTRADICTS', 'QUALIFIES', 'SUPERSEDES', 'CAUSED_BY', 'DERIVED_FROM'
            )),
            strength NUMERIC NOT NULL DEFAULT 1.0,
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_omega_edges_claim ON omega_evidence_edges(claim_id, created_at DESC)")
    op.execute("CREATE INDEX ix_omega_edges_evidence ON omega_evidence_edges(evidence_kind, evidence_id)")

    op.execute("""
        CREATE TABLE omega_contradictions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            claim_a_id UUID NOT NULL REFERENCES omega_claims(id) ON DELETE CASCADE,
            claim_b_id UUID NOT NULL REFERENCES omega_claims(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN (
                'OPEN', 'REVIEWED', 'RESOLVED', 'ACCEPTED_PARADOX', 'RETIRED'
            )),
            severity TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
            description TEXT NOT NULL,
            proposed_resolution TEXT,
            resolved_by_event_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_omega_contradictions_owner_status ON omega_contradictions(owner_user_id, status, severity)")

    op.execute("""
        CREATE TABLE omega_workspace_frames (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            task_mode TEXT NOT NULL,
            trigger_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            active_goal TEXT,
            active_question TEXT NOT NULL,
            attention_items JSONB NOT NULL DEFAULT '{}'::jsonb,
            retrieved_claim_ids UUID[] NOT NULL DEFAULT ARRAY[]::uuid[],
            retrieved_experience_ids UUID[] NOT NULL DEFAULT ARRAY[]::uuid[],
            active_hypothesis_ids UUID[] NOT NULL DEFAULT ARRAY[]::uuid[],
            active_contradiction_ids UUID[] NOT NULL DEFAULT ARRAY[]::uuid[],
            risk_flags TEXT[] NOT NULL DEFAULT ARRAY[]::text[],
            scope_statement TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CREATED' CHECK (status IN ('CREATED', 'USED', 'EVALUATED', 'RETIRED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_omega_frames_owner_created ON omega_workspace_frames(owner_user_id, created_at DESC)")

    op.execute("""
        CREATE TABLE omega_predictions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            model_run_id UUID REFERENCES model_runs(id) ON DELETE SET NULL,
            claim_id UUID REFERENCES omega_claims(id) ON DELETE SET NULL,
            plan_step_id UUID REFERENCES plan_steps(id) ON DELETE SET NULL,
            prediction_text TEXT NOT NULL,
            expected_observation TEXT NOT NULL,
            metric TEXT,
            time_window TEXT,
            confidence NUMERIC NOT NULL DEFAULT 0.5,
            status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN (
                'OPEN', 'CONFIRMED', 'DISCONFIRMED', 'PARTIAL', 'EXPIRED', 'RETIRED'
            )),
            outcome_id UUID REFERENCES outcomes(id) ON DELETE SET NULL,
            prediction_error NUMERIC,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            resolved_at TIMESTAMPTZ
        )""")
    op.execute("CREATE INDEX ix_omega_predictions_owner_status ON omega_predictions(owner_user_id, status, created_at DESC)")

    op.execute("""
        CREATE TABLE omega_learning_proposals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            proposal_kind TEXT NOT NULL CHECK (proposal_kind IN (
                'RETRIEVAL_WEIGHT', 'PROMPT_RULE', 'UI_HINT', 'MEMORY_POLICY', 'HYPOTHESIS_POLICY', 'PLANNING_HEURISTIC'
            )),
            description TEXT NOT NULL,
            evidence_summary TEXT NOT NULL,
            supporting_evaluation_ids UUID[] NOT NULL DEFAULT ARRAY[]::uuid[],
            risk_level TEXT NOT NULL DEFAULT 'LOW' CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'FORBIDDEN')),
            status TEXT NOT NULL DEFAULT 'PROPOSED' CHECK (status IN (
                'PROPOSED', 'SHADOW_TESTING', 'APPROVED', 'REJECTED', 'ROLLED_BACK'
            )),
            approved_by_owner BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_omega_learning_owner_status ON omega_learning_proposals(owner_user_id, status, risk_level)")

    op.execute("""
        CREATE TABLE omega_consolidation_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            run_kind TEXT NOT NULL DEFAULT 'MANUAL' CHECK (run_kind IN ('DAILY', 'MANUAL', 'ORBIT', 'POST_OUTCOME')),
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            input_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_claims INT NOT NULL DEFAULT 0,
            updated_claims INT NOT NULL DEFAULT 0,
            contradictions_found INT NOT NULL DEFAULT 0,
            predictions_resolved INT NOT NULL DEFAULT 0,
            proposals_created INT NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'STARTED' CHECK (status IN ('STARTED', 'COMPLETED', 'FAILED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            error_class TEXT
        )""")
    op.execute("CREATE INDEX ix_omega_consolidation_owner_created ON omega_consolidation_runs(owner_user_id, created_at DESC)")

    for table in OMEGA_TABLES:
        _owner_only(table)


def downgrade() -> None:
    for table in reversed(OMEGA_TABLES):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
