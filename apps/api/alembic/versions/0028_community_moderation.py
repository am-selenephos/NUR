"""Complete bounded Community social, feed, and moderation ledgers.

Revision ID: 0028_community_moderation
Revises: 0027_translation_contract
"""

from alembic import op


revision = "0028_community_moderation"
down_revision = "0027_translation_contract"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
UID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = (
    "current_setting('app.current_user_id', true) IS NOT NULL "
    "AND current_setting('app.current_user_id', true) <> ''"
)


def _enable(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")


def _member(alias: str) -> str:
    return f"fn_community_room_role({alias}.room_id, {UID}) IS NOT NULL"


def _moderator(alias: str) -> str:
    return (
        f"fn_community_room_role({alias}.room_id, {UID}) "
        "IN ('OWNER','MODERATOR')"
    )


def upgrade() -> None:
    op.execute(
        "CREATE POLICY p_community_memberships_definer_read ON community_memberships "
        "FOR SELECT TO nur_admin USING (true)"
    )
    op.execute(
        "CREATE POLICY p_community_rooms_definer_sequence_select ON community_rooms "
        "FOR SELECT TO nur_admin USING (true)"
    )
    op.execute(
        "CREATE POLICY p_community_rooms_definer_sequence_update ON community_rooms "
        "FOR UPDATE TO nur_admin USING (true) WITH CHECK (true)"
    )
    for table in ("community_messages", "community_posts", "community_comments"):
        op.execute(
            f"CREATE POLICY p_{table}_definer_select ON {table} "
            "FOR SELECT TO nur_admin USING (true)"
        )
        op.execute(
            f"CREATE POLICY p_{table}_definer_update ON {table} "
            "FOR UPDATE TO nur_admin USING (true) WITH CHECK (true)"
        )
    op.execute("""
        CREATE FUNCTION fn_community_room_role(rid uuid, uid uuid) RETURNS text
        LANGUAGE sql SECURITY DEFINER STABLE SET search_path = public, pg_temp AS
        $$
            SELECT role FROM community_memberships
            WHERE room_id = rid AND user_id = uid
            LIMIT 1
        $$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION fn_community_room_role(uuid, uuid) TO nur_app"
    )
    op.execute("""
        CREATE FUNCTION fn_next_community_message_sequence(rid uuid) RETURNS integer
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS
        $$
        DECLARE
            uid uuid := NULLIF(current_setting('app.current_user_id', true), '')::uuid;
            allocated integer;
        BEGIN
            IF uid IS NULL OR fn_community_room_role(rid, uid) IS NULL THEN
                RAISE EXCEPTION 'community room membership required'
                    USING ERRCODE = '42501';
            END IF;
            UPDATE community_rooms
            SET next_message_sequence = next_message_sequence + 1,
                updated_at = now()
            WHERE id = rid AND status = 'ACTIVE'
            RETURNING next_message_sequence - 1 INTO allocated;
            IF allocated IS NULL THEN
                RAISE EXCEPTION 'active community room not found'
                    USING ERRCODE = 'P0002';
            END IF;
            RETURN allocated;
        END;
        $$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION fn_next_community_message_sequence(uuid) TO nur_app"
    )
    op.execute("DROP POLICY p_community_memberships_select ON community_memberships")
    op.execute(
        f"CREATE POLICY p_community_memberships_select ON community_memberships "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND (user_id = {UID} "
        f"OR room_owner_user_id = {UID} OR "
        f"fn_community_room_role(room_id, {UID}) IN ('OWNER','MODERATOR')))"
    )
    op.execute("DROP POLICY p_community_memberships_owner_delete ON community_memberships")
    op.execute(
        f"CREATE POLICY p_community_memberships_bounded_delete ON community_memberships "
        f"FOR DELETE TO {APP_ROLE} USING ({HAS_USER} AND ("
        f"(user_id = {UID} AND role <> 'OWNER') OR room_owner_user_id = {UID} OR ("
        f"fn_community_room_role(room_id, {UID}) = 'MODERATOR' "
        "AND role IN ('MEMBER','WITNESS'))))"
    )
    op.execute(
        f"CREATE POLICY p_community_memberships_owner_update ON community_memberships "
        f"FOR UPDATE TO {APP_ROLE} USING (room_owner_user_id = {UID}) "
        f"WITH CHECK (room_owner_user_id = {UID} AND user_id <> room_owner_user_id)"
    )

    op.execute(
        "ALTER TABLE community_rooms ADD COLUMN next_message_sequence INTEGER NOT NULL DEFAULT 1"
    )
    op.execute("ALTER TABLE community_messages ADD COLUMN sequence INTEGER")
    op.execute("""
        WITH ranked AS (
            SELECT id, row_number() OVER (
                PARTITION BY room_id ORDER BY created_at, id
            )::integer AS sequence
            FROM community_messages
        )
        UPDATE community_messages message
        SET sequence = ranked.sequence
        FROM ranked
        WHERE message.id = ranked.id
    """)
    op.execute("ALTER TABLE community_messages ALTER COLUMN sequence SET NOT NULL")
    op.execute(
        "CREATE UNIQUE INDEX uq_community_messages_room_sequence "
        "ON community_messages(room_id, sequence)"
    )
    op.execute("""
        UPDATE community_rooms room
        SET next_message_sequence = COALESCE((
            SELECT max(message.sequence) + 1
            FROM community_messages message
            WHERE message.room_id = room.id
        ), 1)
    """)

    for table in ("community_messages", "community_posts", "community_comments"):
        op.execute(
            f"ALTER TABLE {table} ADD COLUMN revision_number INTEGER NOT NULL DEFAULT 1"
        )
        op.execute(
            f"ALTER TABLE {table} ADD COLUMN status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE' "
            "CHECK (status IN ('ACTIVE','EDITED','HIDDEN','REMOVED'))"
        )
    op.execute("ALTER TABLE community_messages ADD COLUMN edited_at TIMESTAMPTZ")
    op.execute("ALTER TABLE community_comments ADD COLUMN edited_at TIMESTAMPTZ")

    op.execute("""
        CREATE TABLE community_content_revisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_kind VARCHAR(24) NOT NULL
                CHECK (target_kind IN ('POST','COMMENT','MESSAGE')),
            target_id UUID NOT NULL,
            revision_number INTEGER NOT NULL CHECK (revision_number >= 2),
            previous_title TEXT,
            previous_body TEXT NOT NULL,
            current_title TEXT,
            current_body TEXT NOT NULL,
            reason VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(target_kind, target_id, revision_number),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_revisions_room_target "
        "ON community_content_revisions(room_id, target_kind, target_id, revision_number DESC)"
    )
    op.execute("""
        CREATE TABLE community_saves (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            room_id UUID NOT NULL REFERENCES community_rooms(id) ON DELETE CASCADE,
            target_kind VARCHAR(24) NOT NULL
                CHECK (target_kind IN ('POST','COMMENT','MESSAGE')),
            target_id UUID NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, target_kind, target_id)
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_saves_owner_created "
        "ON community_saves(owner_user_id, created_at DESC)"
    )
    op.execute("""
        CREATE TABLE community_relationships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            relationship_kind VARCHAR(24) NOT NULL
                CHECK (relationship_kind IN ('FOLLOW','BLOCK','MUTE')),
            status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE','REVOKED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (owner_user_id <> target_user_id),
            UNIQUE(owner_user_id, target_user_id, relationship_kind)
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_relationships_owner_kind "
        "ON community_relationships(owner_user_id, relationship_kind, updated_at DESC)"
    )
    op.execute("""
        CREATE TABLE community_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_kind VARCHAR(24) NOT NULL
                CHECK (target_kind IN ('POST','COMMENT','MESSAGE')),
            target_id UUID NOT NULL,
            target_owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(48) NOT NULL CHECK (category IN (
                'HARASSMENT','HATE','THREAT','SPAM','MISINFORMATION',
                'PRIVACY','SELF_HARM','OTHER'
            )),
            details TEXT,
            status VARCHAR(24) NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN','UNDER_REVIEW','ACTIONED','DISMISSED','APPEALED','CLOSED')),
            response_due_at TIMESTAMPTZ NOT NULL,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(owner_user_id, target_kind, target_id, category),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_reports_queue "
        "ON community_reports(room_id, status, response_due_at, created_at)"
    )
    op.execute("""
        CREATE TABLE community_moderation_actions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            report_id UUID NOT NULL REFERENCES community_reports(id) ON DELETE CASCADE,
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL,
            actor_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            action_kind VARCHAR(32) NOT NULL CHECK (action_kind IN (
                'NO_ACTION','WARN','HIDE_CONTENT','REMOVE_CONTENT','MUTE_MEMBER','REMOVE_MEMBER'
            )),
            rationale TEXT NOT NULL,
            status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE','REVERSED')),
            reversible_until TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_moderation_actions_report "
        "ON community_moderation_actions(report_id, created_at DESC)"
    )
    op.execute("""
        CREATE TABLE community_appeals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            report_id UUID NOT NULL REFERENCES community_reports(id) ON DELETE CASCADE,
            action_id UUID NOT NULL REFERENCES community_moderation_actions(id) ON DELETE CASCADE,
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            body TEXT NOT NULL,
            status VARCHAR(24) NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN','UPHELD','OVERTURNED','DENIED')),
            reviewer_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            review_rationale TEXT,
            response_due_at TIMESTAMPTZ NOT NULL,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(action_id, owner_user_id),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_appeals_queue "
        "ON community_appeals(room_id, status, response_due_at, created_at)"
    )
    op.execute("""
        CREATE TABLE community_room_sanctions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL,
            target_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            actor_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            action_id UUID REFERENCES community_moderation_actions(id) ON DELETE SET NULL,
            sanction_kind VARCHAR(24) NOT NULL CHECK (sanction_kind IN ('MUTE','READ_ONLY','BAN')),
            reason TEXT NOT NULL,
            status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE','EXPIRED','REVERSED')),
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_room_sanctions_active "
        "ON community_room_sanctions(room_id, target_user_id, status, expires_at)"
    )
    op.execute("""
        CREATE TABLE community_moderation_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL,
            report_id UUID REFERENCES community_reports(id) ON DELETE SET NULL,
            actor_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            event_type VARCHAR(48) NOT NULL,
            event_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            visible_to_subject BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_community_moderation_events_room "
        "ON community_moderation_events(room_id, created_at DESC)"
    )

    new_tables = (
        "community_content_revisions",
        "community_saves",
        "community_relationships",
        "community_reports",
        "community_moderation_actions",
        "community_appeals",
        "community_room_sanctions",
        "community_moderation_events",
    )
    for table in new_tables:
        _enable(table)

    op.execute(
        "CREATE POLICY p_community_relationships_definer_read ON community_relationships "
        "FOR SELECT TO nur_admin USING (true)"
    )
    op.execute(
        "CREATE POLICY p_community_reports_definer_select ON community_reports "
        "FOR SELECT TO nur_admin USING (true)"
    )
    op.execute(
        "CREATE POLICY p_community_reports_definer_update ON community_reports "
        "FOR UPDATE TO nur_admin USING (true) WITH CHECK (true)"
    )

    op.execute(
        f"CREATE POLICY p_community_revisions_select ON community_content_revisions "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND (owner_user_id = {UID} OR "
        f"room_owner_user_id = {UID} OR {_member('community_content_revisions')}))"
    )
    op.execute(
        f"CREATE POLICY p_community_revisions_insert ON community_content_revisions "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND owner_user_id = {UID} "
        f"AND {_member('community_content_revisions')})"
    )
    op.execute(
        f"CREATE POLICY p_community_saves_owner ON community_saves FOR ALL TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {UID}) "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_community_relationships_owner ON community_relationships "
        f"FOR ALL TO {APP_ROLE} USING ({HAS_USER} AND owner_user_id = {UID}) "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_community_reports_select ON community_reports FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND (owner_user_id = {UID} OR target_owner_user_id = {UID} "
        f"OR {_moderator('community_reports')}))"
    )
    op.execute(
        f"CREATE POLICY p_community_reports_insert ON community_reports FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID} "
        f"AND {_member('community_reports')})"
    )
    op.execute(
        f"CREATE POLICY p_community_reports_moderator_update ON community_reports "
        f"FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND {_moderator('community_reports')}) "
        f"WITH CHECK ({HAS_USER} AND {_moderator('community_reports')})"
    )
    op.execute(
        f"CREATE POLICY p_community_actions_select ON community_moderation_actions "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND (actor_user_id = {UID} "
        f"OR target_user_id = {UID} OR {_moderator('community_moderation_actions')}))"
    )
    op.execute(
        f"CREATE POLICY p_community_actions_moderator_insert ON community_moderation_actions "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND actor_user_id = {UID} "
        f"AND {_moderator('community_moderation_actions')})"
    )
    op.execute(
        f"CREATE POLICY p_community_actions_moderator_update ON community_moderation_actions "
        f"FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND {_moderator('community_moderation_actions')}) "
        f"WITH CHECK ({HAS_USER} AND {_moderator('community_moderation_actions')})"
    )
    op.execute(
        f"CREATE POLICY p_community_appeals_select ON community_appeals FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND (owner_user_id = {UID} OR {_moderator('community_appeals')}))"
    )
    op.execute(
        f"CREATE POLICY p_community_appeals_subject_insert ON community_appeals "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND owner_user_id = {UID} "
        "AND EXISTS (SELECT 1 FROM community_moderation_actions action "
        f"WHERE action.id = community_appeals.action_id AND action.target_user_id = {UID}))"
    )
    op.execute(
        f"CREATE POLICY p_community_appeals_moderator_update ON community_appeals "
        f"FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND {_moderator('community_appeals')}) "
        f"WITH CHECK ({HAS_USER} AND {_moderator('community_appeals')})"
    )
    op.execute(
        f"CREATE POLICY p_community_sanctions_select ON community_room_sanctions "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND (target_user_id = {UID} "
        f"OR {_moderator('community_room_sanctions')}))"
    )
    op.execute(
        f"CREATE POLICY p_community_sanctions_moderator_insert ON community_room_sanctions "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND actor_user_id = {UID} "
        f"AND {_moderator('community_room_sanctions')})"
    )
    op.execute(
        f"CREATE POLICY p_community_sanctions_moderator_update ON community_room_sanctions "
        f"FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND {_moderator('community_room_sanctions')}) "
        f"WITH CHECK ({HAS_USER} AND {_moderator('community_room_sanctions')})"
    )
    op.execute(
        f"CREATE POLICY p_community_moderation_events_select ON community_moderation_events "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND (actor_user_id = {UID} OR "
        f"(visible_to_subject AND target_user_id = {UID}) OR {_moderator('community_moderation_events')}))"
    )
    op.execute(
        f"CREATE POLICY p_community_moderation_events_insert ON community_moderation_events "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND actor_user_id = {UID} "
        f"AND ({_member('community_moderation_events')} OR target_user_id = {UID}))"
    )

    op.execute("""
        CREATE FUNCTION fn_mark_community_report_appealed() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS
        $$
        BEGIN
            UPDATE community_reports
            SET status = 'APPEALED', updated_at = now()
            WHERE id = NEW.report_id AND status = 'ACTIONED';
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_mark_community_report_appealed
        AFTER INSERT ON community_appeals
        FOR EACH ROW EXECUTE FUNCTION fn_mark_community_report_appealed()
    """)

    for table in ("community_messages", "community_posts", "community_comments"):
        op.execute(f"DROP POLICY p_{table}_member_select ON {table}")
        op.execute(
            f"CREATE POLICY p_{table}_member_select ON {table} FOR SELECT TO {APP_ROLE} "
            f"USING ({HAS_USER} AND (owner_user_id = {UID} OR room_owner_user_id = {UID} "
            f"OR {_member(table)}) AND (status NOT IN ('HIDDEN','REMOVED') "
            f"OR owner_user_id = {UID} OR room_owner_user_id = {UID} OR {_moderator(table)}))"
        )

    op.execute("""
        CREATE FUNCTION fn_community_users_blocked(a uuid, b uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE SET search_path = public, pg_temp AS
        $$
            SELECT EXISTS (
                SELECT 1 FROM community_relationships relation
                WHERE relation.status = 'ACTIVE'
                  AND relation.relationship_kind = 'BLOCK'
                  AND ((relation.owner_user_id = a AND relation.target_user_id = b)
                    OR (relation.owner_user_id = b AND relation.target_user_id = a))
            )
        $$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION fn_community_users_blocked(uuid, uuid) TO nur_app"
    )
    op.execute("""
        CREATE FUNCTION fn_community_users_connected(a uuid, b uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE SET search_path = public, pg_temp AS
        $$
            SELECT EXISTS (
                SELECT 1 FROM community_relationships first_follow
                WHERE first_follow.owner_user_id = a
                  AND first_follow.target_user_id = b
                  AND first_follow.relationship_kind = 'FOLLOW'
                  AND first_follow.status = 'ACTIVE'
            ) AND EXISTS (
                SELECT 1 FROM community_relationships second_follow
                WHERE second_follow.owner_user_id = b
                  AND second_follow.target_user_id = a
                  AND second_follow.relationship_kind = 'FOLLOW'
                  AND second_follow.status = 'ACTIVE'
            )
        $$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION fn_community_users_connected(uuid, uuid) TO nur_app"
    )
    op.execute("""
        CREATE FUNCTION fn_set_community_content_status(
            content_kind text, content_id uuid, rid uuid, next_status text
        ) RETURNS boolean
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS
        $$
        DECLARE
            uid uuid := NULLIF(current_setting('app.current_user_id', true), '')::uuid;
            affected integer := 0;
        BEGIN
            IF uid IS NULL OR fn_community_room_role(rid, uid)
                NOT IN ('OWNER','MODERATOR') THEN
                RAISE EXCEPTION 'community moderation permission required'
                    USING ERRCODE = '42501';
            END IF;
            IF next_status NOT IN ('ACTIVE','EDITED','HIDDEN','REMOVED') THEN
                RAISE EXCEPTION 'unsupported community content status'
                    USING ERRCODE = '22023';
            END IF;
            IF content_kind = 'POST' THEN
                UPDATE community_posts SET status = next_status, updated_at = now()
                WHERE id = content_id AND room_id = rid;
            ELSIF content_kind = 'COMMENT' THEN
                UPDATE community_comments SET status = next_status
                WHERE id = content_id AND room_id = rid;
            ELSIF content_kind = 'MESSAGE' THEN
                UPDATE community_messages SET status = next_status
                WHERE id = content_id AND room_id = rid;
            ELSE
                RAISE EXCEPTION 'unsupported community content kind'
                    USING ERRCODE = '22023';
            END IF;
            GET DIAGNOSTICS affected = ROW_COUNT;
            RETURN affected = 1;
        END;
        $$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION "
        "fn_set_community_content_status(text, uuid, uuid, text) TO nur_app"
    )


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS "
        "fn_set_community_content_status(text, uuid, uuid, text)"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_mark_community_report_appealed ON community_appeals"
    )
    op.execute("DROP FUNCTION IF EXISTS fn_mark_community_report_appealed()")
    op.execute("DROP FUNCTION IF EXISTS fn_community_users_connected(uuid, uuid)")
    op.execute("DROP FUNCTION IF EXISTS fn_community_users_blocked(uuid, uuid)")

    for table in ("community_messages", "community_posts", "community_comments"):
        op.execute(f"DROP POLICY p_{table}_member_select ON {table}")
        op.execute(
            f"CREATE POLICY p_{table}_member_select ON {table} FOR SELECT TO {APP_ROLE} "
            f"USING ({HAS_USER} AND (owner_user_id = {UID} OR room_owner_user_id = {UID} "
            "OR EXISTS (SELECT 1 FROM community_memberships gm "
            f"WHERE gm.room_id = {table}.room_id AND gm.user_id = {UID})))"
        )
        op.execute(f"DROP POLICY p_{table}_definer_update ON {table}")
        op.execute(f"DROP POLICY p_{table}_definer_select ON {table}")

    op.execute("DROP POLICY p_community_memberships_owner_update ON community_memberships")
    op.execute("DROP POLICY p_community_memberships_bounded_delete ON community_memberships")
    op.execute(
        f"CREATE POLICY p_community_memberships_owner_delete ON community_memberships "
        f"FOR DELETE TO {APP_ROLE} USING (room_owner_user_id = {UID})"
    )

    op.execute("DROP POLICY p_community_memberships_select ON community_memberships")
    op.execute(
        f"CREATE POLICY p_community_memberships_select ON community_memberships "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND "
        f"(user_id = {UID} OR room_owner_user_id = {UID}))"
    )

    for table in (
        "community_moderation_events",
        "community_room_sanctions",
        "community_appeals",
        "community_moderation_actions",
        "community_reports",
        "community_relationships",
        "community_saves",
        "community_content_revisions",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    op.execute("DROP FUNCTION IF EXISTS fn_next_community_message_sequence(uuid)")
    op.execute("DROP FUNCTION IF EXISTS fn_community_room_role(uuid, uuid)")
    op.execute(
        "DROP POLICY p_community_rooms_definer_sequence_update ON community_rooms"
    )
    op.execute(
        "DROP POLICY p_community_rooms_definer_sequence_select ON community_rooms"
    )
    op.execute(
        "DROP POLICY p_community_memberships_definer_read ON community_memberships"
    )

    op.execute("ALTER TABLE community_comments DROP COLUMN edited_at")
    op.execute("ALTER TABLE community_messages DROP COLUMN edited_at")
    for table in ("community_comments", "community_posts", "community_messages"):
        op.execute(f"ALTER TABLE {table} DROP COLUMN status")
        op.execute(f"ALTER TABLE {table} DROP COLUMN revision_number")
    op.execute("DROP INDEX uq_community_messages_room_sequence")
    op.execute("ALTER TABLE community_messages DROP COLUMN sequence")
    op.execute("ALTER TABLE community_rooms DROP COLUMN next_message_sequence")
