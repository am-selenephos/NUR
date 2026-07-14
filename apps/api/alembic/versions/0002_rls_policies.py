"""Row Level Security: default-deny, owner-only access, narrow auth-context policies.

Runtime role `nur_app` (LOGIN, NOBYPASSRLS, not table owner) is the ONLY role the
API uses. Tables are owned by the migration role, and RLS is FORCEd so even the
owner is subject to policies. With no matching policy, access is DENIED.

Context parameters (transaction-local, set via set_config(..., true)):
  app.current_user_id — authenticated user's UUID
  app.auth_context    — 'on' only inside register/login/session-validation paths

Phase 3 hook: System-scoped tables will add membership policies keyed on
app.current_user_id joined through room membership — same mechanism, documented
in docs/PRIVACY_MODEL.md. Phase 0 does NOT claim those exist.

Revision ID: 0002_rls_policies
Revises: 0001_initial_schema
"""
from alembic import op

revision = "0002_rls_policies"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"

# NULLIF guards the ::uuid cast — after a transaction-local set_config ends,
# the custom GUC survives on the pooled session as an EMPTY STRING, and a bare
# cast would 500 every later request on that connection.
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"
AUTH_CTX = "current_setting('app.auth_context', true) = 'on'"

TABLES = ["users", "profiles", "sessions", "orbits", "consent_records", "audit_events"]


def upgrade() -> None:
    # FAIL CLOSED. This migration must NEVER create a LOGIN role with a known
    # default password. Roles are provisioned by deployment — the compose init
    # script (infra/docker/postgres-init.sh) with secret-injected passwords, or
    # the manual SQL in docs/PRODUCTION_READINESS.md. We additionally refuse to
    # proceed if the role could bypass the very RLS this migration installs.
    op.execute(f"""
    DO $$
    DECLARE r pg_roles%ROWTYPE;
    BEGIN
      SELECT * INTO r FROM pg_roles WHERE rolname = '{APP_ROLE}';
      IF NOT FOUND THEN
        RAISE EXCEPTION USING MESSAGE =
          'role "{APP_ROLE}" does not exist. Provision roles before migrating '
          '(infra/docker/postgres-init.sh or docs/PRODUCTION_READINESS.md). '
          'This migration refuses to create LOGIN roles with default passwords.';
      END IF;
      IF r.rolsuper OR r.rolbypassrls THEN
        RAISE EXCEPTION USING MESSAGE =
          'role "{APP_ROLE}" is SUPERUSER or BYPASSRLS — refusing to grant '
          'RLS-scoped access to a role that can bypass row security.';
      END IF;
    END $$;
    """)

    for t in TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    # Grants: least privilege. No DELETE anywhere in Phase 0.
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON users, profiles, sessions, orbits, consent_records TO {APP_ROLE}")
    op.execute(f"GRANT INSERT ON audit_events TO {APP_ROLE}")  # append-only; no SELECT grant

    # ---- users ----
    op.execute(f"CREATE POLICY p_users_owner_select ON users FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_users_owner_update ON users FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND id = {OWNER_UUID}) WITH CHECK (id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_users_auth_select ON users FOR SELECT TO {APP_ROLE} USING ({AUTH_CTX})")
    op.execute(f"CREATE POLICY p_users_auth_insert ON users FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX})")

    # ---- profiles ----
    op.execute(f"CREATE POLICY p_profiles_owner_select ON profiles FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND user_id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_profiles_owner_update ON profiles FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND user_id = {OWNER_UUID}) WITH CHECK (user_id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_profiles_auth_insert ON profiles FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX})")

    # ---- sessions (auth bootstrap needs pre-identity lookup by PK) ----
    op.execute(f"CREATE POLICY p_sessions_auth_select ON sessions FOR SELECT TO {APP_ROLE} USING ({AUTH_CTX})")
    op.execute(f"CREATE POLICY p_sessions_auth_insert ON sessions FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX})")
    op.execute(f"CREATE POLICY p_sessions_auth_update ON sessions FOR UPDATE TO {APP_ROLE} USING ({AUTH_CTX}) WITH CHECK ({AUTH_CTX})")
    op.execute(f"CREATE POLICY p_sessions_owner_select ON sessions FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND user_id = {OWNER_UUID})")

    # ---- orbits ----
    op.execute(f"CREATE POLICY p_orbits_owner_select ON orbits FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND user_id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_orbits_owner_update ON orbits FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND user_id = {OWNER_UUID}) WITH CHECK (user_id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_orbits_auth_insert ON orbits FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX})")

    # ---- consent_records ----
    op.execute(f"CREATE POLICY p_consent_owner_select ON consent_records FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND user_id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_consent_owner_update ON consent_records FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND user_id = {OWNER_UUID}) WITH CHECK (user_id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_consent_auth_insert ON consent_records FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX})")

    # ---- audit_events: append-only from both contexts; unreadable by the app role ----
    op.execute(f"CREATE POLICY p_audit_insert ON audit_events FOR INSERT TO {APP_ROLE} WITH CHECK ({AUTH_CTX} OR ({HAS_USER} AND (actor_user_id IS NULL OR actor_user_id = {OWNER_UUID})))")


def downgrade() -> None:
    for t in TABLES:
        op.execute(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
    # policies drop with DISABLE? No — drop explicitly
    for stmt in [
        "DROP POLICY IF EXISTS p_users_owner_select ON users",
        "DROP POLICY IF EXISTS p_users_owner_update ON users",
        "DROP POLICY IF EXISTS p_users_auth_select ON users",
        "DROP POLICY IF EXISTS p_users_auth_insert ON users",
        "DROP POLICY IF EXISTS p_profiles_owner_select ON profiles",
        "DROP POLICY IF EXISTS p_profiles_owner_update ON profiles",
        "DROP POLICY IF EXISTS p_profiles_auth_insert ON profiles",
        "DROP POLICY IF EXISTS p_sessions_auth_select ON sessions",
        "DROP POLICY IF EXISTS p_sessions_auth_insert ON sessions",
        "DROP POLICY IF EXISTS p_sessions_auth_update ON sessions",
        "DROP POLICY IF EXISTS p_sessions_owner_select ON sessions",
        "DROP POLICY IF EXISTS p_orbits_owner_select ON orbits",
        "DROP POLICY IF EXISTS p_orbits_owner_update ON orbits",
        "DROP POLICY IF EXISTS p_orbits_auth_insert ON orbits",
        "DROP POLICY IF EXISTS p_consent_owner_select ON consent_records",
        "DROP POLICY IF EXISTS p_consent_owner_update ON consent_records",
        "DROP POLICY IF EXISTS p_consent_auth_insert ON consent_records",
        "DROP POLICY IF EXISTS p_audit_insert ON audit_events",
        "REVOKE ALL ON users, profiles, sessions, orbits, consent_records, audit_events FROM nur_app",
    ]:
        op.execute(stmt)
