"""Final product surfaces, provider capabilities, and language preference."""
from alembic import op

revision = "0010_product_surfaces_i18n"
down_revision = "0009_feature_lock_prefs"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


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
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) WITH CHECK (owner_user_id = {OWNER_UUID})"
    )
    op.execute(
        f"CREATE POLICY p_{table}_owner_delete ON {table} FOR DELETE TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID})"
    )


def upgrade() -> None:
    for value in [
        "RESEARCH_BRIEF_CREATED",
        "RESEARCH_SOURCE_NOTE_ADDED",
        "COMMUNITY_NOTE_CREATED",
        "WEB_SIGNAL_QUESTION_STAGED",
        "WEB_SIGNAL_NOTE_ADDED",
    ]:
        op.execute(f"ALTER TYPE cognitive_event_kind ADD VALUE IF NOT EXISTS '{value}'")

    op.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS writing_preference TEXT NOT NULL DEFAULT 'default'")

    op.execute("""
        CREATE TABLE research_briefs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            question TEXT NOT NULL,
            summary TEXT,
            status TEXT NOT NULL DEFAULT 'LOCAL_DRAFT',
            provider_status TEXT NOT NULL DEFAULT 'LOCAL_ONLY',
            provenance_label TEXT NOT NULL DEFAULT 'OWNER_WRITTEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_research_briefs_owner_created ON research_briefs(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_research_briefs_orbit ON research_briefs(orbit_id)")

    op.execute("""
        CREATE TABLE research_source_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            research_brief_id UUID REFERENCES research_briefs(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            note TEXT NOT NULL,
            url TEXT,
            source_type TEXT NOT NULL DEFAULT 'OWNER_NOTE',
            trust_state TEXT NOT NULL DEFAULT 'OWNER_SUPPLIED',
            provenance_label TEXT NOT NULL DEFAULT 'OWNER_WRITTEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_research_source_notes_owner_created ON research_source_notes(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_research_source_notes_orbit ON research_source_notes(orbit_id)")

    op.execute("""
        CREATE TABLE community_consultation_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            note TEXT NOT NULL,
            collaborator_label TEXT,
            capsule_id UUID REFERENCES context_capsules(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'LOCAL_NOTE',
            provenance_label TEXT NOT NULL DEFAULT 'OWNER_WRITTEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_community_notes_owner_created ON community_consultation_notes(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_community_notes_orbit ON community_consultation_notes(orbit_id)")

    op.execute("""
        CREATE TABLE web_signal_questions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            question TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'STAGED',
            provider_status TEXT NOT NULL DEFAULT 'NOT_CONNECTED',
            provenance_label TEXT NOT NULL DEFAULT 'OWNER_WRITTEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_web_signal_questions_owner_created ON web_signal_questions(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_web_signal_questions_orbit ON web_signal_questions(orbit_id)")

    op.execute("""
        CREATE TABLE web_signal_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            web_signal_question_id UUID REFERENCES web_signal_questions(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            note TEXT NOT NULL,
            url TEXT,
            provenance_label TEXT NOT NULL DEFAULT 'OWNER_WRITTEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
    op.execute("CREATE INDEX ix_web_signal_notes_owner_created ON web_signal_notes(owner_user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_web_signal_notes_orbit ON web_signal_notes(orbit_id)")

    op.execute("""
        CREATE TABLE provider_capabilities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider_name TEXT NOT NULL,
            capability_key TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'NOT_CONNECTED',
            reason TEXT NOT NULL,
            configured BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, provider_name, capability_key)
        )""")
    op.execute("CREATE INDEX ix_provider_capabilities_owner ON provider_capabilities(owner_user_id)")

    for table in [
        "research_briefs",
        "research_source_notes",
        "community_consultation_notes",
        "web_signal_questions",
        "web_signal_notes",
        "provider_capabilities",
    ]:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        _owner_all(table)


def downgrade() -> None:
    for table in [
        "provider_capabilities",
        "web_signal_notes",
        "web_signal_questions",
        "community_consultation_notes",
        "research_source_notes",
        "research_briefs",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("ALTER TABLE profiles DROP COLUMN IF EXISTS writing_preference")
