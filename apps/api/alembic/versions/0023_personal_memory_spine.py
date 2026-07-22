"""versioned personal memory and durable domain-event spine

Revision ID: 0023_personal_memory_spine
Revises: 0022_password_recovery
"""

from alembic import op


revision = "0023_personal_memory_spine"
down_revision = "0022_password_recovery"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


def _owner_policies(table: str, *, update: bool = True, delete: bool = True) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    privileges = "SELECT, INSERT"
    if update:
        privileges += ", UPDATE"
    if delete:
        privileges += ", DELETE"
    op.execute(f"GRANT {privileges} ON {table} TO {APP_ROLE}")
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
            f"WITH CHECK (owner_user_id = {OWNER_UUID})"
        )
    if delete:
        op.execute(
            f"CREATE POLICY p_{table}_owner_delete ON {table} FOR DELETE TO {APP_ROLE} "
            f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
        )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE memories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            scope memory_scope NOT NULL DEFAULT 'PRIVATE_ORBIT',
            memory_type VARCHAR(32) NOT NULL DEFAULT 'SEMANTIC'
                CHECK (memory_type IN (
                    'EPISODIC','SEMANTIC','PROCEDURAL','SOCIAL','EVIDENCE',
                    'SELF','GOAL','META_COGNITIVE','ADAPTIVE_INTERFACE'
                )),
            canonical_text TEXT NOT NULL,
            structured_value JSONB NOT NULL DEFAULT '{}'::jsonb,
            source_object_ids JSONB NOT NULL DEFAULT '{}'::jsonb,
            provenance_label VARCHAR(40) NOT NULL
                CHECK (provenance_label IN (
                    'OWNER_WRITTEN','USER_CORRECTION','MODEL_GENERATED',
                    'OBSERVED_OUTCOME','SYSTEM_MEASURED','EXTERNAL_SOURCE',
                    'COMMUNITY_CONTRIBUTION','EXPERT_VERIFIED'
                )),
            confidence REAL NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
            sensitivity VARCHAR(24) NOT NULL DEFAULT 'PRIVATE'
                CHECK (sensitivity IN ('LOW','PRIVATE','SENSITIVE')),
            status VARCHAR(24) NOT NULL DEFAULT 'APPROVED'
                CHECK (status IN ('APPROVED','RETIRED','SUPERSEDED')),
            created_by VARCHAR(16) NOT NULL
                CHECK (created_by IN ('OWNER','MODEL','SYSTEM','REVIEWER')),
            version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
            superseded_by_memory_id UUID REFERENCES memories(id) ON DELETE SET NULL,
            expires_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_memories_owner_status ON memories(owner_user_id, status, updated_at DESC)")
    op.execute("CREATE INDEX ix_memories_owner_orbit ON memories(owner_user_id, orbit_id, updated_at DESC)")
    op.execute(
        "CREATE INDEX ix_memories_fts ON memories USING gin "
        "(to_tsvector('english', coalesce(canonical_text,'')))"
    )

    op.execute("""
        CREATE TABLE memory_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
            version INTEGER NOT NULL CHECK (version >= 1),
            canonical_text TEXT NOT NULL,
            structured_value JSONB NOT NULL DEFAULT '{}'::jsonb,
            provenance_label VARCHAR(40) NOT NULL
                CHECK (provenance_label IN (
                    'OWNER_WRITTEN','USER_CORRECTION','MODEL_GENERATED',
                    'OBSERVED_OUTCOME','SYSTEM_MEASURED','EXTERNAL_SOURCE',
                    'COMMUNITY_CONTRIBUTION','EXPERT_VERIFIED'
                )),
            change_kind VARCHAR(24) NOT NULL
                CHECK (change_kind IN ('APPROVED','OWNER_CREATED','EDITED','CORRECTED','SUPERSEDED')),
            correction_reason TEXT,
            changed_by VARCHAR(16) NOT NULL
                CHECK (changed_by IN ('OWNER','MODEL','SYSTEM','REVIEWER')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(memory_id, version)
        )
    """)
    op.execute("CREATE INDEX ix_memory_versions_owner_memory ON memory_versions(owner_user_id, memory_id, version)")

    op.execute("""
        CREATE TABLE memory_edges (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
            relation VARCHAR(24) NOT NULL
                CHECK (relation IN ('DERIVED_FROM','CORRECTS','SUPERSEDES','SUPPORTED_BY','CONTRADICTS')),
            source_kind VARCHAR(48) NOT NULL,
            source_id UUID NOT NULL,
            edge_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, memory_id, relation, source_kind, source_id)
        )
    """)
    op.execute("CREATE INDEX ix_memory_edges_owner_memory ON memory_edges(owner_user_id, memory_id)")

    op.execute("""
        CREATE TABLE memory_access_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            memory_id UUID REFERENCES memories(id) ON DELETE SET NULL,
            access_kind VARCHAR(24) NOT NULL
                CHECK (access_kind IN ('VIEWED','RETRIEVED','EXPORTED','EDITED','DELETED')),
            purpose VARCHAR(64) NOT NULL,
            context_ref VARCHAR(160),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_memory_access_owner_created ON memory_access_events(owner_user_id, created_at DESC)")

    op.execute("""
        CREATE TABLE domain_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_type VARCHAR(96) NOT NULL,
            aggregate_type VARCHAR(64) NOT NULL,
            aggregate_id UUID NOT NULL,
            event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            idempotency_key VARCHAR(240) NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            published_at TIMESTAMPTZ,
            delivery_attempts INTEGER NOT NULL DEFAULT 0 CHECK (delivery_attempts >= 0),
            last_error_code VARCHAR(80),
            UNIQUE(owner_user_id, idempotency_key)
        )
    """)
    op.execute("CREATE INDEX ix_domain_events_unpublished ON domain_events(occurred_at) WHERE published_at IS NULL")
    op.execute("CREATE INDEX ix_domain_events_owner_type ON domain_events(owner_user_id, event_type, occurred_at DESC)")

    op.execute("ALTER TABLE memory_candidates ADD COLUMN original_text TEXT NOT NULL DEFAULT ''")
    op.execute("UPDATE memory_candidates SET original_text = candidate_text")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN memory_type VARCHAR(32) NOT NULL DEFAULT 'SEMANTIC'")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN provenance_label VARCHAR(40) NOT NULL DEFAULT 'MODEL_GENERATED'")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN confidence REAL NOT NULL DEFAULT 0.5")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN sensitivity VARCHAR(24) NOT NULL DEFAULT 'PRIVATE'")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN created_by VARCHAR(16) NOT NULL DEFAULT 'MODEL'")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN source_object_ids JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN review_note TEXT")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN reviewed_at TIMESTAMPTZ")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    op.execute("ALTER TABLE memory_candidates ADD COLUMN approved_memory_id UUID REFERENCES memories(id) ON DELETE SET NULL")
    op.execute(
        "ALTER TABLE memory_candidates ADD CONSTRAINT ck_memory_candidate_status "
        "CHECK (status IN ('CANDIDATE','CORRECTED','APPROVED','REJECTED'))"
    )
    op.execute(
        "ALTER TABLE memory_candidates ADD CONSTRAINT ck_memory_candidate_confidence "
        "CHECK (confidence BETWEEN 0 AND 1)"
    )
    op.execute(
        "ALTER TABLE memory_candidates ADD CONSTRAINT ck_memory_candidate_sensitivity "
        "CHECK (sensitivity IN ('LOW','PRIVATE','SENSITIVE'))"
    )
    op.execute(
        "ALTER TABLE memory_candidates ADD CONSTRAINT ck_memory_candidate_type "
        "CHECK (memory_type IN ("
        "'EPISODIC','SEMANTIC','PROCEDURAL','SOCIAL','EVIDENCE',"
        "'SELF','GOAL','META_COGNITIVE','ADAPTIVE_INTERFACE'))"
    )
    op.execute(
        "ALTER TABLE memory_candidates ADD CONSTRAINT ck_memory_candidate_provenance "
        "CHECK (provenance_label IN ("
        "'OWNER_WRITTEN','USER_CORRECTION','MODEL_GENERATED','OBSERVED_OUTCOME',"
        "'SYSTEM_MEASURED','EXTERNAL_SOURCE','COMMUNITY_CONTRIBUTION','EXPERT_VERIFIED'))"
    )
    op.execute(
        "ALTER TABLE memory_candidates ADD CONSTRAINT ck_memory_candidate_created_by "
        "CHECK (created_by IN ('OWNER','MODEL','SYSTEM','REVIEWER'))"
    )
    op.execute("CREATE UNIQUE INDEX uq_memory_candidate_approved_memory ON memory_candidates(approved_memory_id) WHERE approved_memory_id IS NOT NULL")
    op.execute("CREATE INDEX ix_memory_candidates_owner_status ON memory_candidates(owner_user_id, status, created_at DESC)")

    for table in ("memories", "memory_versions", "memory_edges"):
        _owner_policies(table)
    _owner_policies("memory_access_events", update=False, delete=False)
    _owner_policies("domain_events", delete=False)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_memory_candidates_owner_status")
    op.execute("DROP INDEX IF EXISTS uq_memory_candidate_approved_memory")
    op.execute("ALTER TABLE memory_candidates DROP CONSTRAINT IF EXISTS ck_memory_candidate_created_by")
    op.execute("ALTER TABLE memory_candidates DROP CONSTRAINT IF EXISTS ck_memory_candidate_provenance")
    op.execute("ALTER TABLE memory_candidates DROP CONSTRAINT IF EXISTS ck_memory_candidate_type")
    op.execute("ALTER TABLE memory_candidates DROP CONSTRAINT IF EXISTS ck_memory_candidate_sensitivity")
    op.execute("ALTER TABLE memory_candidates DROP CONSTRAINT IF EXISTS ck_memory_candidate_confidence")
    op.execute("ALTER TABLE memory_candidates DROP CONSTRAINT IF EXISTS ck_memory_candidate_status")
    for column in (
        "approved_memory_id", "updated_at", "reviewed_at", "review_note",
        "source_object_ids", "created_by", "sensitivity", "confidence",
        "provenance_label", "memory_type", "original_text",
    ):
        op.execute(f"ALTER TABLE memory_candidates DROP COLUMN IF EXISTS {column}")
    for table in ("domain_events", "memory_access_events", "memory_edges", "memory_versions", "memories"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
