"""Gate 2 — private project memory substrate (NUR-Ω NOW organs).

Evolves `orbits` into the amendment's project-container shape (superset of the
Phase 0 personal orbit: existing rows become the user's PERSONAL_BRIDGE orbit,
no data loss) and lays down the owner-bound cognitive tables with FORCE RLS:
event ledger, journal, plans/steps, decisions, references/constraints/open
questions, hypotheses, experiments, outcomes, research drafts, semantic claims
+ claim evidence (provenance). FTS GIN indexes give real scoped retrieval now;
pgvector columns exist as infrastructure and stay honestly NULL until the
model gateway phase.
"""
from alembic import op

revision = "0003_cognitive_substrate"
down_revision = "0002_rls_policies"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"
AUTH_CTX = "current_setting('app.auth_context', true) = 'on'"

ENUMS = {
    "orbit_kind": ["PROJECT", "CREATIVE", "RESEARCH", "CARE", "PERSONAL_BRIDGE"],
    "orbit_status": ["ACTIVE", "ARCHIVED"],
    "memory_scope": ["EPHEMERAL", "PRIVATE_ORBIT", "SYSTEM_SHARED", "LEARNING_CANDIDATE"],
    "cognitive_event_kind": [
        "TALK_TURN", "JOURNAL_ENTRY", "PLAN_CREATED", "PLAN_STEP", "OUTCOME_REPORTED",
        "TOOL_OBSERVATION", "RESEARCH_DRAFT", "SYSTEM_EVENT", "USER_CORRECTION",
        "MODEL_RESPONSE", "EVALUATION_EVENT",
    ],
    "claim_status": ["EMERGING", "MIXED", "SUPPORTED", "DISPUTED", "ARCHIVED"],
    "hypothesis_status": ["PROPOSED", "TESTING", "SUPPORTED", "REFUTED", "INCONCLUSIVE", "ARCHIVED"],
    "experiment_status": ["DRAFT", "ACTIVE", "PAUSED", "COMPLETED", "ABANDONED"],
    "reference_kind": ["REFERENCE", "CONSTRAINT", "OPEN_QUESTION"],
}

OWNER_TABLES: list[str] = []  # filled as tables are created; policies applied at end


def _owner_policies(t: str, *, immutable: bool = False) -> list[str]:
    stmts = [
        f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY",
        f"CREATE POLICY p_{t}_owner_select ON {t} FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})",
        f"CREATE POLICY p_{t}_owner_insert ON {t} FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})",
    ]
    if not immutable:
        stmts += [
            f"CREATE POLICY p_{t}_owner_update ON {t} FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) WITH CHECK (owner_user_id = {OWNER_UUID})",
            f"CREATE POLICY p_{t}_owner_delete ON {t} FOR DELETE TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})",
        ]
    return stmts


def upgrade() -> None:
    for name, vals in ENUMS.items():
        op.execute(f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in vals)})")

    # ---- evolve orbits: personal 1:1 -> owner 1:N project containers -------
    op.execute("DROP POLICY IF EXISTS p_orbits_owner_select ON orbits")
    op.execute("DROP POLICY IF EXISTS p_orbits_owner_insert ON orbits")
    op.execute("DROP POLICY IF EXISTS p_orbits_owner_update ON orbits")
    op.execute("DROP POLICY IF EXISTS p_orbits_owner_delete ON orbits")
    op.execute("DROP POLICY IF EXISTS p_orbits_auth_insert ON orbits")
    op.execute("ALTER TABLE orbits RENAME COLUMN user_id TO owner_user_id")
    op.execute("ALTER TABLE orbits DROP CONSTRAINT IF EXISTS orbits_user_id_key")
    op.execute("ALTER TABLE orbits ADD COLUMN title TEXT NOT NULL DEFAULT 'Personal Orbit'")
    op.execute("ALTER TABLE orbits ADD COLUMN kind orbit_kind NOT NULL DEFAULT 'PERSONAL_BRIDGE'")
    op.execute("ALTER TABLE orbits ADD COLUMN description TEXT")
    op.execute("ALTER TABLE orbits ADD COLUMN status orbit_status NOT NULL DEFAULT 'ACTIVE'")
    op.execute("CREATE INDEX ix_orbits_owner ON orbits (owner_user_id)")
    op.execute(
        f"CREATE POLICY p_orbits_owner_select ON orbits FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_orbits_owner_insert ON orbits FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_orbits_owner_update ON orbits FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) WITH CHECK (owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_orbits_owner_delete ON orbits FOR DELETE TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_orbits_auth_insert ON orbits FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX})"
    )

    # ---- Gate 2 tables ------------------------------------------------------
    op.execute("""
        CREATE TABLE cognitive_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            event_kind cognitive_event_kind NOT NULL,
            content_text TEXT,
            structured_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            source_ref TEXT,
            scope memory_scope NOT NULL DEFAULT 'PRIVATE_ORBIT',
            salience REAL NOT NULL DEFAULT 0,
            novelty REAL NOT NULL DEFAULT 0,
            confidence REAL NOT NULL DEFAULT 0.5,
            parent_event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            embedding REAL[],
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_cog_events_owner_created ON cognitive_events (owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_cog_events_fts ON cognitive_events USING gin (to_tsvector('english', coalesce(content_text,'')))")

    op.execute("""
        CREATE TABLE journal_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            body TEXT NOT NULL,
            event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_journal_owner_created ON journal_entries (owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_journal_fts ON journal_entries USING gin (to_tsvector('english', body))")

    op.execute("""
        CREATE TABLE plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE hypotheses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            question TEXT NOT NULL,
            hypothesis_text TEXT NOT NULL,
            alternative_hypotheses JSONB NOT NULL DEFAULT '[]'::jsonb,
            prediction JSONB NOT NULL DEFAULT '{}'::jsonb,
            confidence REAL NOT NULL DEFAULT 0.5,
            status hypothesis_status NOT NULL DEFAULT 'PROPOSED',
            linked_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE experiments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            hypothesis_id UUID REFERENCES hypotheses(id) ON DELETE SET NULL,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            intervention TEXT NOT NULL,
            success_criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
            failure_criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
            scope memory_scope NOT NULL DEFAULT 'PRIVATE_ORBIT',
            consent_required BOOLEAN NOT NULL DEFAULT false,
            status experiment_status NOT NULL DEFAULT 'DRAFT',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE plan_steps (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            body TEXT,
            position INT NOT NULL DEFAULT 0,
            done BOOLEAN NOT NULL DEFAULT false,
            done_at TIMESTAMPTZ,
            experiment_id UUID REFERENCES experiments(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_plan_steps_plan ON plan_steps (plan_id, position)")

    op.execute("""
        CREATE TABLE decisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            statement TEXT NOT NULL,
            rationale TEXT,
            status TEXT NOT NULL DEFAULT 'HELD',
            decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_decisions_orbit ON decisions (orbit_id, created_at DESC)")
    op.execute("CREATE INDEX ix_decisions_fts ON decisions USING gin (to_tsvector('english', statement || ' ' || coalesce(rationale,'')))")

    op.execute("""
        CREATE TABLE orbit_references (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            kind reference_kind NOT NULL DEFAULT 'REFERENCE',
            title TEXT NOT NULL,
            body TEXT,
            url TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_orbit_refs_orbit ON orbit_references (orbit_id, created_at DESC)")
    op.execute("CREATE INDEX ix_orbit_refs_fts ON orbit_references USING gin (to_tsvector('english', title || ' ' || coalesce(body,'')))")

    op.execute("""
        CREATE TABLE outcomes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            experiment_id UUID REFERENCES experiments(id) ON DELETE SET NULL,
            plan_step_id UUID REFERENCES plan_steps(id) ON DELETE SET NULL,
            observed_result TEXT NOT NULL,
            structured_measurements JSONB NOT NULL DEFAULT '{}'::jsonb,
            self_reported BOOLEAN NOT NULL DEFAULT true,
            confidence REAL,
            difference_from_prediction JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE research_drafts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            question TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'STAGED',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_research_fts ON research_drafts USING gin (to_tsvector('english', question || ' ' || coalesce(notes,'')))")

    op.execute("""
        CREATE TABLE semantic_claims (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_text TEXT NOT NULL,
            subject_ref TEXT,
            predicate TEXT,
            object_value JSONB NOT NULL DEFAULT '{}'::jsonb,
            confidence REAL NOT NULL DEFAULT 0.5,
            status claim_status NOT NULL DEFAULT 'EMERGING',
            evidence_count INT NOT NULL DEFAULT 0,
            counterevidence_count INT NOT NULL DEFAULT 0,
            last_evaluated_at TIMESTAMPTZ,
            embedding REAL[],
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE claim_evidence (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_id UUID NOT NULL REFERENCES semantic_claims(id) ON DELETE CASCADE,
            event_id UUID REFERENCES cognitive_events(id) ON DELETE SET NULL,
            outcome_id UUID REFERENCES outcomes(id) ON DELETE SET NULL,
            supports BOOLEAN NOT NULL,
            weight REAL NOT NULL DEFAULT 1,
            rationale TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    mutable = [
        "journal_entries", "plans", "plan_steps", "decisions", "orbit_references",
        "hypotheses", "experiments", "outcomes", "research_drafts",
        "semantic_claims", "claim_evidence",
    ]

    # table privileges for the app role (RLS then gates rows)
    op.execute(f"GRANT SELECT, INSERT ON cognitive_events TO {APP_ROLE}")
    for t in ["journal_entries", "plans", "plan_steps", "decisions", "orbit_references",
              "hypotheses", "experiments", "outcomes", "research_drafts",
              "semantic_claims", "claim_evidence"]:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO {APP_ROLE}")
    for stmt in _owner_policies("cognitive_events", immutable=True):
        op.execute(stmt)
    for t in mutable:
        for stmt in _owner_policies(t):
            op.execute(stmt)


def downgrade() -> None:
    for t in [
        "claim_evidence", "semantic_claims", "research_drafts", "outcomes",
        "decisions", "orbit_references", "plan_steps", "experiments",
        "hypotheses", "plans", "journal_entries", "cognitive_events",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS description")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS kind")
    op.execute("ALTER TABLE orbits DROP COLUMN IF EXISTS title")
    op.execute("ALTER TABLE orbits RENAME COLUMN owner_user_id TO user_id")
    op.execute("ALTER TABLE orbits ADD CONSTRAINT orbits_user_id_key UNIQUE (user_id)")
    for name in reversed(list(ENUMS)):
        op.execute(f"DROP TYPE IF EXISTS {name}")
