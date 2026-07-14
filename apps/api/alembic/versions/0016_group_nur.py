"""Bounded Community rooms, Group NUR conversations, and Council facilitation."""

from alembic import op


revision = "0016_group_nur"
down_revision = "0015_live_intelligence"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
UID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"


def _enable(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")


def _member_exists(alias: str) -> str:
    return (
        "EXISTS (SELECT 1 FROM community_memberships gm "
        f"WHERE gm.room_id = {alias}.room_id AND gm.user_id = {UID})"
    )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE community_rooms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            orbit_id UUID REFERENCES orbits(id) ON DELETE SET NULL,
            title VARCHAR(240) NOT NULL,
            description TEXT,
            room_kind VARCHAR(32) NOT NULL DEFAULT 'GROUP'
                CHECK (room_kind IN ('GROUP','COUNCIL','SYSTEM','PROJECT','COMMUNITY')),
            system_slug VARCHAR(48),
            language_tag VARCHAR(20) NOT NULL DEFAULT 'en',
            status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE','ARCHIVED','CLOSED')),
            is_demo BOOLEAN NOT NULL DEFAULT false,
            room_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id)
        )
    """)
    op.execute("CREATE INDEX ix_community_rooms_owner ON community_rooms(owner_user_id, updated_at DESC)")
    op.execute("""
        CREATE TABLE community_memberships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(32) NOT NULL DEFAULT 'MEMBER'
                CHECK (role IN ('OWNER','MODERATOR','MEMBER','WITNESS')),
            joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(room_id, user_id),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute("CREATE INDEX ix_community_memberships_user ON community_memberships(user_id, joined_at DESC)")

    shared_columns = """
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        room_id UUID NOT NULL,
        room_owner_user_id UUID NOT NULL,
        owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    """
    shared_fk = """
        FOREIGN KEY(room_id, room_owner_user_id)
            REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
    """
    op.execute(f"""
        CREATE TABLE community_messages (
            {shared_columns}
            body TEXT NOT NULL,
            language_tag VARCHAR(20) NOT NULL DEFAULT 'en',
            provenance_label VARCHAR(48) NOT NULL DEFAULT 'MEMBER_WRITTEN',
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            {shared_fk}
        )
    """)
    op.execute(f"""
        CREATE TABLE community_posts (
            {shared_columns}
            title VARCHAR(500) NOT NULL,
            body TEXT NOT NULL,
            language_tag VARCHAR(20) NOT NULL DEFAULT 'en',
            provenance_label VARCHAR(48) NOT NULL DEFAULT 'MEMBER_WRITTEN',
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            {shared_fk}
        )
    """)
    op.execute(f"""
        CREATE TABLE community_comments (
            {shared_columns}
            post_id UUID NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
            parent_comment_id UUID REFERENCES community_comments(id) ON DELETE CASCADE,
            body TEXT NOT NULL,
            language_tag VARCHAR(20) NOT NULL DEFAULT 'en',
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            {shared_fk}
        )
    """)
    op.execute(f"""
        CREATE TABLE community_reactions (
            {shared_columns}
            target_kind VARCHAR(24) NOT NULL CHECK (target_kind IN ('POST','COMMENT','MESSAGE')),
            target_id UUID NOT NULL,
            reaction VARCHAR(32) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, target_kind, target_id, reaction),
            {shared_fk}
        )
    """)
    op.execute(f"""
        CREATE TABLE council_positions (
            {shared_columns}
            position TEXT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
            is_minority BOOLEAN NOT NULL DEFAULT false,
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            {shared_fk}
        )
    """)
    op.execute(f"""
        CREATE TABLE council_decisions (
            {shared_columns}
            decision TEXT NOT NULL,
            rationale TEXT,
            minority_opinion TEXT,
            return_check_at TIMESTAMPTZ,
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            {shared_fk}
        )
    """)

    for table in (
        "community_rooms", "community_memberships", "community_messages",
        "community_posts", "community_comments", "community_reactions",
        "council_positions", "council_decisions",
    ):
        _enable(table)

    op.execute(
        f"CREATE POLICY p_community_rooms_select ON community_rooms FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND (owner_user_id = {UID} OR EXISTS ("
        f"SELECT 1 FROM community_memberships gm WHERE gm.room_id = community_rooms.id AND gm.user_id = {UID})))"
    )
    op.execute(
        f"CREATE POLICY p_community_rooms_owner_insert ON community_rooms FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_community_rooms_owner_update ON community_rooms FOR UPDATE TO {APP_ROLE} "
        f"USING (owner_user_id = {UID}) WITH CHECK (owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_community_rooms_owner_delete ON community_rooms FOR DELETE TO {APP_ROLE} "
        f"USING (owner_user_id = {UID})"
    )

    op.execute(
        f"CREATE POLICY p_community_memberships_select ON community_memberships FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND (user_id = {UID} OR room_owner_user_id = {UID}))"
    )
    op.execute(
        f"CREATE POLICY p_community_memberships_owner_insert ON community_memberships FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND room_owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_community_memberships_owner_delete ON community_memberships FOR DELETE TO {APP_ROLE} "
        f"USING (room_owner_user_id = {UID})"
    )

    for table in (
        "community_messages", "community_posts", "community_comments",
        "community_reactions", "council_positions",
    ):
        op.execute(
            f"CREATE POLICY p_{table}_member_select ON {table} FOR SELECT TO {APP_ROLE} "
            f"USING ({HAS_USER} AND (owner_user_id = {UID} OR room_owner_user_id = {UID} OR {_member_exists(table)}))"
        )
        op.execute(
            f"CREATE POLICY p_{table}_member_insert ON {table} FOR INSERT TO {APP_ROLE} "
            f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID} AND (room_owner_user_id = {UID} OR {_member_exists(table)}))"
        )
        op.execute(
            f"CREATE POLICY p_{table}_author_update ON {table} FOR UPDATE TO {APP_ROLE} "
            f"USING (owner_user_id = {UID}) WITH CHECK (owner_user_id = {UID})"
        )
        op.execute(
            f"CREATE POLICY p_{table}_author_delete ON {table} FOR DELETE TO {APP_ROLE} "
            f"USING (owner_user_id = {UID})"
        )

    # A Council position belongs to its author, but the final decision belongs
    # to the room owner. API checks mirror this rule; RLS remains the authority.
    op.execute(
        f"CREATE POLICY p_council_decisions_member_select ON council_decisions FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND (room_owner_user_id = {UID} OR {_member_exists('council_decisions')}))"
    )
    op.execute(
        f"CREATE POLICY p_council_decisions_owner_insert ON council_decisions FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID} AND room_owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_council_decisions_owner_update ON council_decisions FOR UPDATE TO {APP_ROLE} "
        f"USING (room_owner_user_id = {UID}) WITH CHECK (owner_user_id = {UID} AND room_owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_council_decisions_owner_delete ON council_decisions FOR DELETE TO {APP_ROLE} "
        f"USING (room_owner_user_id = {UID})"
    )


def downgrade() -> None:
    for table in (
        "council_decisions", "council_positions", "community_reactions",
        "community_comments", "community_posts", "community_messages",
        "community_memberships", "community_rooms",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
