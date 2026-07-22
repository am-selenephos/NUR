"""consented Teach NUR review and versioned retrieval knowledge

Revision ID: 0024_teach_nur_pipeline
Revises: 0023_personal_memory_spine
"""

from alembic import op


revision = "0024_teach_nur_pipeline"
down_revision = "0023_personal_memory_spine"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = (
    "current_setting('app.current_user_id', true) IS NOT NULL AND "
    "current_setting('app.current_user_id', true) <> ''"
)


def _owner_policies(table: str, *, update: bool = True) -> None:
    privileges = "SELECT, INSERT"
    if update:
        privileges += ", UPDATE"
    op.execute(f"GRANT {privileges} ON {table} TO {APP_ROLE}")
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
    if update:
        op.execute(
            f"CREATE POLICY p_{table}_owner_update ON {table} FOR UPDATE TO {APP_ROLE} "
            f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) "
            f"WITH CHECK ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
        )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE teach_nur_contributions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            contribution_kind VARCHAR(32) NOT NULL CHECK (contribution_kind IN (
                'FACT','LIVED_EXPERIENCE','CORRECTION','COUNTEREXAMPLE','LANGUAGE',
                'RESEARCH','EXPERTISE','MISUNDERSTANDING','OUTCOME_EVIDENCE'
            )),
            content TEXT NOT NULL,
            language_tag VARCHAR(35) NOT NULL DEFAULT 'und',
            consent_scope VARCHAR(32) NOT NULL CHECK (consent_scope IN (
                'PRIVATE_OWNER','DEIDENTIFIED_RESEARCH'
            )),
            consent_policy_version VARCHAR(32) NOT NULL,
            consent_granted BOOLEAN NOT NULL DEFAULT false,
            provenance_label VARCHAR(40) NOT NULL CHECK (provenance_label IN (
                'OWNER_WRITTEN','USER_CORRECTION','OBSERVED_OUTCOME','EXTERNAL_SOURCE'
            )),
            sensitivity VARCHAR(24) NOT NULL CHECK (sensitivity IN (
                'LOW','PRIVATE','SENSITIVE'
            )),
            confidence REAL NOT NULL DEFAULT 1 CHECK (confidence BETWEEN 0 AND 1),
            source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
            risk_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
            deidentification_status VARCHAR(24) NOT NULL CHECK (
                deidentification_status IN ('NOT_REQUIRED','ELIGIBLE','BLOCKED')
            ),
            verification_status VARCHAR(24) NOT NULL CHECK (
                verification_status IN (
                    'NOT_REQUIRED','MISSING','OWNER_SUPPLIED','VERIFIED','FAILED'
                )
            ),
            status VARCHAR(24) NOT NULL DEFAULT 'PENDING_REVIEW' CHECK (status IN (
                'PENDING_REVIEW','QUARANTINED','EDITED','APPROVED','REJECTED','CANARY',
                'ACTIVE','ROLLED_BACK','WITHDRAWN'
            )),
            request_key VARCHAR(160),
            payload_digest VARCHAR(64) NOT NULL,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (consent_granted OR status = 'WITHDRAWN'),
            CHECK (length(btrim(content)) > 0 OR status = 'WITHDRAWN')
        )
    """)
    op.execute(
        "CREATE INDEX ix_teach_contribution_owner_status "
        "ON teach_nur_contributions(owner_user_id, status, created_at DESC)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_teach_contribution_request "
        "ON teach_nur_contributions(owner_user_id, request_key) "
        "WHERE request_key IS NOT NULL"
    )

    op.execute("""
        CREATE TABLE teach_nur_candidates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contribution_id UUID NOT NULL UNIQUE
                REFERENCES teach_nur_contributions(id) ON DELETE CASCADE,
            candidate_text TEXT NOT NULL,
            original_text_digest VARCHAR(64) NOT NULL,
            deidentified_text TEXT,
            provenance_label VARCHAR(40) NOT NULL CHECK (provenance_label IN (
                'OWNER_WRITTEN','USER_CORRECTION','OBSERVED_OUTCOME','EXTERNAL_SOURCE'
            )),
            sensitivity VARCHAR(24) NOT NULL CHECK (sensitivity IN (
                'LOW','PRIVATE','SENSITIVE'
            )),
            confidence REAL NOT NULL DEFAULT 1 CHECK (confidence BETWEEN 0 AND 1),
            source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
            risk_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
            contradiction_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
            disagreement_map JSONB NOT NULL DEFAULT '{}'::jsonb,
            status VARCHAR(24) NOT NULL DEFAULT 'PENDING_REVIEW' CHECK (status IN (
                'PENDING_REVIEW','QUARANTINED','EDITED','APPROVED','REJECTED',
                'CANARY','ACTIVE','ROLLED_BACK','WITHDRAWN'
            )),
            current_knowledge_version_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (length(btrim(candidate_text)) > 0 OR status = 'WITHDRAWN')
        )
    """)
    op.execute(
        "CREATE INDEX ix_teach_candidate_owner_status "
        "ON teach_nur_candidates(owner_user_id, status, created_at DESC)"
    )

    op.execute("""
        CREATE TABLE teach_nur_knowledge_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contribution_id UUID NOT NULL
                REFERENCES teach_nur_contributions(id) ON DELETE CASCADE,
            candidate_id UUID NOT NULL REFERENCES teach_nur_candidates(id) ON DELETE CASCADE,
            version INTEGER NOT NULL CHECK (version >= 1),
            parent_version_id UUID REFERENCES teach_nur_knowledge_versions(id)
                ON DELETE SET NULL,
            canonical_text TEXT NOT NULL,
            retrieval_scope VARCHAR(32) NOT NULL CHECK (retrieval_scope IN (
                'PRIVATE_OWNER','DEIDENTIFIED_RESEARCH'
            )),
            provenance_label VARCHAR(40) NOT NULL CHECK (provenance_label IN (
                'OWNER_WRITTEN','USER_CORRECTION','OBSERVED_OUTCOME','EXTERNAL_SOURCE'
            )),
            verification_status VARCHAR(24) NOT NULL CHECK (
                verification_status IN (
                    'NOT_REQUIRED','MISSING','OWNER_SUPPLIED','VERIFIED','FAILED'
                )
            ),
            status VARCHAR(24) NOT NULL CHECK (status IN (
                'SHADOW','CANARY','ACTIVE','ROLLED_BACK'
            )),
            evaluation_result JSONB NOT NULL DEFAULT '{}'::jsonb,
            why_changed VARCHAR(1000) NOT NULL,
            created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            activated_at TIMESTAMPTZ,
            rolled_back_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(candidate_id, version),
            CHECK (length(btrim(canonical_text)) > 0 OR status = 'ROLLED_BACK')
        )
    """)
    op.execute(
        "CREATE INDEX ix_teach_knowledge_owner_status "
        "ON teach_nur_knowledge_versions(owner_user_id, status, created_at DESC)"
    )
    op.execute(
        "ALTER TABLE teach_nur_candidates ADD CONSTRAINT "
        "fk_teach_candidate_current_knowledge FOREIGN KEY (current_knowledge_version_id) "
        "REFERENCES teach_nur_knowledge_versions(id) ON DELETE SET NULL"
    )

    op.execute("""
        CREATE TABLE teach_nur_consent_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contribution_id UUID NOT NULL
                REFERENCES teach_nur_contributions(id) ON DELETE CASCADE,
            action VARCHAR(16) NOT NULL CHECK (action IN ('GRANTED','WITHDRAWN')),
            consent_scope VARCHAR(32) NOT NULL CHECK (consent_scope IN (
                'PRIVATE_OWNER','DEIDENTIFIED_RESEARCH'
            )),
            policy_version VARCHAR(32) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_teach_consent_owner_created "
        "ON teach_nur_consent_events(owner_user_id, created_at DESC)"
    )

    op.execute("""
        CREATE TABLE teach_nur_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contribution_id UUID NOT NULL
                REFERENCES teach_nur_contributions(id) ON DELETE CASCADE,
            candidate_id UUID NOT NULL REFERENCES teach_nur_candidates(id) ON DELETE CASCADE,
            reviewer_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            action VARCHAR(32) NOT NULL CHECK (action IN (
                'EDIT','APPROVE','APPROVE_BLOCKED','REJECT','START_CANARY',
                'ACTIVATE','ROLLBACK','WITHDRAW_CONSENT'
            )),
            prior_status VARCHAR(24) NOT NULL,
            resulting_status VARCHAR(24) NOT NULL,
            note_digest VARCHAR(64),
            request_key VARCHAR(160),
            payload_digest VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_teach_review_owner_contribution "
        "ON teach_nur_reviews(owner_user_id, contribution_id, created_at DESC)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_teach_review_request "
        "ON teach_nur_reviews(owner_user_id, contribution_id, request_key) "
        "WHERE request_key IS NOT NULL"
    )

    op.execute("""
        CREATE TABLE teach_nur_evaluation_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contribution_id UUID NOT NULL
                REFERENCES teach_nur_contributions(id) ON DELETE CASCADE,
            candidate_id UUID NOT NULL REFERENCES teach_nur_candidates(id) ON DELETE CASCADE,
            knowledge_version_id UUID REFERENCES teach_nur_knowledge_versions(id)
                ON DELETE SET NULL,
            suite_version VARCHAR(32) NOT NULL,
            checks JSONB NOT NULL DEFAULT '{}'::jsonb,
            passed BOOLEAN NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_teach_eval_owner_candidate "
        "ON teach_nur_evaluation_runs(owner_user_id, candidate_id, created_at DESC)"
    )

    op.execute("""
        CREATE TABLE teach_nur_knowledge_access_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            knowledge_version_id UUID REFERENCES teach_nur_knowledge_versions(id)
                ON DELETE SET NULL,
            access_kind VARCHAR(24) NOT NULL CHECK (access_kind IN (
                'VIEWED','RETRIEVED','EXPORTED'
            )),
            purpose VARCHAR(64) NOT NULL,
            context_ref VARCHAR(160),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_teach_access_owner_created "
        "ON teach_nur_knowledge_access_events(owner_user_id, created_at DESC)"
    )

    for table in (
        "teach_nur_contributions",
        "teach_nur_candidates",
        "teach_nur_knowledge_versions",
    ):
        _owner_policies(table)
    for table in (
        "teach_nur_consent_events",
        "teach_nur_reviews",
        "teach_nur_evaluation_runs",
        "teach_nur_knowledge_access_events",
    ):
        _owner_policies(table, update=False)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE teach_nur_candidates "
        "DROP CONSTRAINT IF EXISTS fk_teach_candidate_current_knowledge"
    )
    for table in (
        "teach_nur_knowledge_access_events",
        "teach_nur_evaluation_runs",
        "teach_nur_reviews",
        "teach_nur_consent_events",
        "teach_nur_knowledge_versions",
        "teach_nur_candidates",
        "teach_nur_contributions",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
