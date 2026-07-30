"""AM Projects G14: real execution spine + owner-scoped object storage.

Adds:
  * am_project_agents — persisted, owner-scoped agent definitions (adapter + safe
    capability allow-list; no secrets).
  * am_project_files — metadata for real stored bytes (opaque object key, checksum,
    size, storage/scan/provenance state) under forced RLS.
  * execution columns on am_project_runs (adapter, capability sets, idempotency,
    timeout, worker identity, attempt, failure code, output artifact, timestamps)
    and an extended status domain (QUEUED / CANCEL_REQUESTED / REJECTED).

Existing G10–G13 data and the six original AM Project tables are preserved.
"""

from alembic import op


revision = "0030_project_execution_storage"
down_revision = "0029_group_research"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"

_RUN_STATUSES_NEW = (
    "'PROPOSED','APPROVED','QUEUED','RUNNING','SUCCEEDED',"
    "'FAILED','CANCELLED','CANCEL_REQUESTED','REJECTED'"
)
_RUN_STATUSES_OLD = "'PROPOSED','APPROVED','RUNNING','SUCCEEDED','FAILED','CANCELLED'"


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
    # --- agent definitions -------------------------------------------------
    op.execute("""
        CREATE TABLE am_project_agents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES am_projects(id) ON DELETE CASCADE,
            name VARCHAR(120) NOT NULL,
            adapter_key VARCHAR(64) NOT NULL,
            description TEXT,
            allowed_capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
            version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_am_project_agents_owner_project ON am_project_agents(owner_user_id, project_id, is_active)")

    # --- stored object metadata -------------------------------------------
    op.execute("""
        CREATE TABLE am_project_files (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES am_projects(id) ON DELETE CASCADE,
            task_id UUID REFERENCES am_project_tasks(id) ON DELETE SET NULL,
            run_id UUID REFERENCES am_project_runs(id) ON DELETE SET NULL,
            artifact_id UUID REFERENCES am_project_artifacts(id) ON DELETE SET NULL,
            object_key VARCHAR(64) NOT NULL UNIQUE,
            original_filename VARCHAR(255) NOT NULL,
            safe_filename VARCHAR(255) NOT NULL,
            media_type VARCHAR(180) NOT NULL DEFAULT 'application/octet-stream',
            byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
            checksum_sha256 VARCHAR(64) NOT NULL,
            storage_backend VARCHAR(32) NOT NULL DEFAULT 'local',
            storage_state VARCHAR(32) NOT NULL DEFAULT 'STORED'
                CHECK (storage_state IN ('STORED','QUARANTINED','DELETED')),
            quarantine_reason TEXT,
            scan_state VARCHAR(32) NOT NULL DEFAULT 'SCAN_NOT_CONNECTED'
                CHECK (scan_state IN ('SCAN_NOT_CONNECTED','CLEAN','INFECTED','SKIPPED')),
            provenance VARCHAR(32) NOT NULL DEFAULT 'OWNER_UPLOAD'
                CHECK (provenance IN ('OWNER_UPLOAD','RUN_OUTPUT')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_am_project_files_owner_project ON am_project_files(owner_user_id, project_id, storage_state, created_at DESC)")
    op.execute("CREATE INDEX ix_am_project_files_run ON am_project_files(owner_user_id, run_id)")

    # --- run execution spine ----------------------------------------------
    op.execute("ALTER TABLE am_project_runs DROP CONSTRAINT IF EXISTS am_project_runs_status_check")
    op.execute(f"ALTER TABLE am_project_runs ADD CONSTRAINT am_project_runs_status_check CHECK (status IN ({_RUN_STATUSES_NEW}))")
    op.execute("""
        ALTER TABLE am_project_runs
            ADD COLUMN adapter_key VARCHAR(64),
            ADD COLUMN agent_id UUID REFERENCES am_project_agents(id) ON DELETE SET NULL,
            ADD COLUMN requested_capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN approved_capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN input_refs JSONB NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN idempotency_key VARCHAR(200),
            ADD COLUMN timeout_seconds INTEGER CHECK (timeout_seconds IS NULL OR timeout_seconds > 0),
            ADD COLUMN cost_cents INTEGER NOT NULL DEFAULT 0 CHECK (cost_cents >= 0),
            ADD COLUMN attempt INTEGER NOT NULL DEFAULT 0 CHECK (attempt >= 0),
            ADD COLUMN worker_id VARCHAR(120),
            ADD COLUMN failure_code VARCHAR(64),
            ADD COLUMN output_artifact_id UUID REFERENCES am_project_artifacts(id) ON DELETE SET NULL,
            ADD COLUMN queued_at TIMESTAMPTZ,
            ADD COLUMN failed_at TIMESTAMPTZ,
            ADD COLUMN cancelled_at TIMESTAMPTZ
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_am_project_runs_idempotency "
        "ON am_project_runs(owner_user_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
    )

    for table in ("am_project_agents", "am_project_files"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        _owner_all(table)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_am_project_runs_idempotency")
    op.execute("""
        ALTER TABLE am_project_runs
            DROP COLUMN IF EXISTS adapter_key,
            DROP COLUMN IF EXISTS agent_id,
            DROP COLUMN IF EXISTS requested_capabilities,
            DROP COLUMN IF EXISTS approved_capabilities,
            DROP COLUMN IF EXISTS input_refs,
            DROP COLUMN IF EXISTS idempotency_key,
            DROP COLUMN IF EXISTS timeout_seconds,
            DROP COLUMN IF EXISTS cost_cents,
            DROP COLUMN IF EXISTS attempt,
            DROP COLUMN IF EXISTS worker_id,
            DROP COLUMN IF EXISTS failure_code,
            DROP COLUMN IF EXISTS output_artifact_id,
            DROP COLUMN IF EXISTS queued_at,
            DROP COLUMN IF EXISTS failed_at,
            DROP COLUMN IF EXISTS cancelled_at
    """)
    op.execute("ALTER TABLE am_project_runs DROP CONSTRAINT IF EXISTS am_project_runs_status_check")
    op.execute(
        "UPDATE am_project_runs SET status = 'CANCELLED' "
        "WHERE status IN ('QUEUED','CANCEL_REQUESTED','REJECTED')"
    )
    op.execute(f"ALTER TABLE am_project_runs ADD CONSTRAINT am_project_runs_status_check CHECK (status IN ({_RUN_STATUSES_OLD}))")
    op.execute("DROP TABLE IF EXISTS am_project_files CASCADE")
    op.execute("DROP TABLE IF EXISTS am_project_agents CASCADE")
