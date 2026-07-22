"""Group NUR, evidence research, watchlists, expert, and Tender ledgers.

Revision ID: 0024_group_research
Revises: 0023_community_moderation
"""

from alembic import op


revision = "0024_group_research"
down_revision = "0023_community_moderation"
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


def _owner_policy(table: str) -> None:
    op.execute(
        f"CREATE POLICY p_{table}_owner ON {table} FOR ALL TO {APP_ROLE} "
        f"USING ({HAS_USER} AND owner_user_id = {UID}) "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID})"
    )


def upgrade() -> None:
    # Existing rows remain readable. New stage rows must carry the durable fields
    # required by the ORIENT -> RETURN contract.
    op.execute("""
        ALTER TABLE consultation_stage_records
        ADD CONSTRAINT ck_consultation_stage_payload_contract CHECK (
            (stage = 'ORIENT' AND stage_payload ?& ARRAY['actual_question','affected_people']) OR
            (stage = 'GATHER' AND stage_payload ?& ARRAY['facts','constraints']) OR
            (stage = 'MAP' AND stage_payload ?& ARRAY['options','minority_positions']) OR
            (stage = 'MOVE' AND stage_payload ?& ARRAY['selected_action','success_signal']) OR
            (stage = 'RETURN' AND stage_payload ?& ARRAY['outcome','prediction_comparison'])
        ) NOT VALID
    """)
    op.execute(
        "ALTER TABLE consultations ADD CONSTRAINT uq_consultations_id_room "
        "UNIQUE(id, room_id)"
    )
    op.execute(
        "ALTER TABLE research_briefs ADD CONSTRAINT uq_research_briefs_id_owner "
        "UNIQUE(id, owner_user_id)"
    )
    op.execute(
        "ALTER TABLE web_signal_questions ADD CONSTRAINT uq_web_signal_questions_id_owner "
        "UNIQUE(id, owner_user_id)"
    )

    op.execute("""
        CREATE TABLE group_nur_syntheses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            consultation_id UUID,
            supersedes_id UUID,
            version INTEGER NOT NULL CHECK (version > 0),
            trigger_kind VARCHAR(24) NOT NULL CHECK (
                trigger_kind IN ('ON_DEMAND','SCHEDULED','TRANSITION','CORRECTION')
            ),
            status VARCHAR(24) NOT NULL DEFAULT 'PUBLISHED' CHECK (
                status IN ('PUBLISHED','CORRECTED','RETRACTED')
            ),
            summary TEXT NOT NULL,
            current_question TEXT NOT NULL,
            decisions JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(decisions) = 'array'),
            tensions JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(tensions) = 'array'),
            minority_positions JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(minority_positions) = 'array'),
            evidence JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(evidence) = 'array'),
            counterevidence JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(counterevidence) = 'array'),
            unresolved_questions JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(unresolved_questions) = 'array'),
            tasks JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(tasks) = 'array'),
            source_message_ids JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_message_ids) = 'array'),
            source_post_ids JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_post_ids) = 'array'),
            source_contribution_ids JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_contribution_ids) = 'array'),
            what_may_be_wrong TEXT NOT NULL,
            correction_reason TEXT,
            language_tag VARCHAR(20) NOT NULL DEFAULT 'en',
            provenance_label VARCHAR(48) NOT NULL DEFAULT 'MEMBER_SYNTHESIZED',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, room_id),
            UNIQUE(room_id, version),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE,
            FOREIGN KEY(consultation_id, room_id)
                REFERENCES consultations(id, room_id) ON DELETE SET NULL (consultation_id),
            FOREIGN KEY(supersedes_id, room_id)
                REFERENCES group_nur_syntheses(id, room_id) ON DELETE SET NULL (supersedes_id),
            CHECK ((supersedes_id IS NULL AND correction_reason IS NULL) OR
                   (supersedes_id IS NOT NULL AND correction_reason IS NOT NULL))
        )
    """)
    op.execute(
        "CREATE INDEX ix_group_nur_room_created "
        "ON group_nur_syntheses(room_id, version DESC)"
    )

    op.execute("""
        CREATE TABLE research_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            research_brief_id UUID NOT NULL,
            mode VARCHAR(16) NOT NULL CHECK (mode IN ('QUICK','DEEP')),
            provider_name VARCHAR(48) NOT NULL,
            status VARCHAR(24) NOT NULL CHECK (status IN (
                'RUNNING','SUCCEEDED','FAILED','CANCELLED','NOT_CONNECTED'
            )),
            query_preview TEXT NOT NULL,
            external_scope_approved BOOLEAN NOT NULL DEFAULT false,
            failure_code VARCHAR(80),
            failure_detail TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id),
            FOREIGN KEY(research_brief_id, owner_user_id)
                REFERENCES research_briefs(id, owner_user_id) ON DELETE CASCADE,
            CHECK ((status IN ('FAILED','NOT_CONNECTED') AND failure_code IS NOT NULL) OR
                   (status NOT IN ('FAILED','NOT_CONNECTED')))
        )
    """)
    op.execute(
        "CREATE INDEX ix_research_jobs_owner_status "
        "ON research_jobs(owner_user_id, status, created_at DESC)"
    )
    op.execute("""
        CREATE TABLE research_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            research_brief_id UUID NOT NULL,
            research_job_id UUID,
            title VARCHAR(500) NOT NULL,
            url TEXT NOT NULL,
            publisher VARCHAR(300),
            source_kind VARCHAR(24) NOT NULL CHECK (
                source_kind IN ('WEB','RSS','API','OWNER_SOURCE','DOCUMENT')
            ),
            authority VARCHAR(24) NOT NULL CHECK (
                authority IN ('PRIMARY','SECONDARY','TERTIARY','UNKNOWN')
            ),
            reliability VARCHAR(24) NOT NULL CHECK (
                reliability IN ('HIGH','MEDIUM','LOW','UNASSESSED')
            ),
            retrieval_status VARCHAR(24) NOT NULL CHECK (
                retrieval_status IN ('OWNER_SUBMITTED','RETRIEVED','FAILED')
            ),
            excerpt TEXT NOT NULL,
            content_hash VARCHAR(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
            published_at TIMESTAMPTZ,
            fetched_at TIMESTAMPTZ,
            untrusted_external_content BOOLEAN NOT NULL DEFAULT true,
            provenance_label VARCHAR(48) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id),
            UNIQUE(owner_user_id, research_brief_id, url, content_hash),
            FOREIGN KEY(research_brief_id, owner_user_id)
                REFERENCES research_briefs(id, owner_user_id) ON DELETE CASCADE,
            FOREIGN KEY(research_job_id, owner_user_id)
                REFERENCES research_jobs(id, owner_user_id) ON DELETE SET NULL (research_job_id)
        )
    """)
    op.execute(
        "CREATE INDEX ix_research_sources_brief "
        "ON research_sources(research_brief_id, created_at DESC)"
    )
    op.execute("""
        CREATE TABLE research_claims (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            research_brief_id UUID NOT NULL,
            claim_text TEXT NOT NULL,
            uncertainty TEXT NOT NULL,
            citation_alignment VARCHAR(16) NOT NULL CHECK (
                citation_alignment IN ('HIGH','MEDIUM','LOW')
            ),
            status VARCHAR(24) NOT NULL DEFAULT 'SUPPORTED' CHECK (
                status IN ('SUPPORTED','CORRECTED','REJECTED')
            ),
            revision_number INTEGER NOT NULL DEFAULT 1 CHECK (revision_number > 0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id),
            FOREIGN KEY(research_brief_id, owner_user_id)
                REFERENCES research_briefs(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_research_claims_brief "
        "ON research_claims(research_brief_id, created_at DESC)"
    )
    op.execute("""
        CREATE TABLE research_citations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_id UUID NOT NULL,
            source_id UUID NOT NULL,
            relationship VARCHAR(16) NOT NULL CHECK (
                relationship IN ('SUPPORTS','COUNTERS','CONTEXT')
            ),
            locator VARCHAR(500),
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(claim_id, source_id, relationship),
            FOREIGN KEY(claim_id, owner_user_id)
                REFERENCES research_claims(id, owner_user_id) ON DELETE CASCADE,
            FOREIGN KEY(source_id, owner_user_id)
                REFERENCES research_sources(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE TABLE research_claim_revisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_id UUID NOT NULL,
            revision_number INTEGER NOT NULL CHECK (revision_number >= 2),
            previous_claim_text TEXT NOT NULL,
            current_claim_text TEXT NOT NULL,
            previous_uncertainty TEXT NOT NULL,
            current_uncertainty TEXT NOT NULL,
            correction_reason TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(claim_id, revision_number),
            FOREIGN KEY(claim_id, owner_user_id)
                REFERENCES research_claims(id, owner_user_id) ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE TABLE web_watchlists (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            web_signal_question_id UUID,
            name VARCHAR(240) NOT NULL,
            source_url TEXT NOT NULL,
            schedule VARCHAR(16) NOT NULL CHECK (
                schedule IN ('MANUAL','HOURLY','DAILY','WEEKLY')
            ),
            status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE' CHECK (
                status IN ('ACTIVE','PAUSED','ARCHIVED')
            ),
            connector_status VARCHAR(24) NOT NULL DEFAULT 'NOT_CONNECTED' CHECK (
                connector_status IN ('NOT_CONNECTED','AVAILABLE','DEGRADED')
            ),
            alert_enabled BOOLEAN NOT NULL DEFAULT true,
            relevance_scope JSONB NOT NULL DEFAULT '{}'::jsonb,
            last_content_hash VARCHAR(64),
            last_checked_at TIMESTAMPTZ,
            next_check_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id),
            UNIQUE(owner_user_id, source_url),
            FOREIGN KEY(web_signal_question_id, owner_user_id)
                REFERENCES web_signal_questions(id, owner_user_id)
                ON DELETE SET NULL (web_signal_question_id)
        )
    """)
    op.execute("""
        CREATE TABLE web_signal_snapshots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            watchlist_id UUID NOT NULL,
            title VARCHAR(500) NOT NULL,
            summary TEXT NOT NULL,
            content_hash VARCHAR(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
            changed_from_previous BOOLEAN NOT NULL,
            change_summary TEXT,
            capture_method VARCHAR(24) NOT NULL CHECK (
                capture_method IN ('OWNER_CAPTURE','CONNECTOR_FETCH')
            ),
            captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id),
            UNIQUE(watchlist_id, content_hash),
            FOREIGN KEY(watchlist_id, owner_user_id)
                REFERENCES web_watchlists(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE TABLE web_signal_alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            watchlist_id UUID NOT NULL,
            snapshot_id UUID NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'UNREAD' CHECK (
                status IN ('UNREAD','READ','DISMISSED')
            ),
            change_summary TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(snapshot_id),
            FOREIGN KEY(watchlist_id, owner_user_id)
                REFERENCES web_watchlists(id, owner_user_id) ON DELETE CASCADE,
            FOREIGN KEY(snapshot_id, owner_user_id)
                REFERENCES web_signal_snapshots(id, owner_user_id) ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE TABLE expert_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            display_name VARCHAR(240) NOT NULL,
            bio TEXT NOT NULL,
            domains JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(domains) = 'array'),
            verification_status VARCHAR(24) NOT NULL DEFAULT 'UNVERIFIED' CHECK (
                verification_status IN ('UNVERIFIED','PENDING','PEER_ATTESTED','REJECTED','EXPIRED')
            ),
            verification_scope VARCHAR(48) NOT NULL DEFAULT 'SELF_DECLARED',
            moderation_state VARCHAR(24) NOT NULL DEFAULT 'ACTIVE' CHECK (
                moderation_state IN ('ACTIVE','PAUSED','REMOVED')
            ),
            conflicts JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(conflicts) = 'array'),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id)
        )
    """)
    op.execute("""
        CREATE TABLE expert_verifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id UUID NOT NULL,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            verifier_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_type VARCHAR(24) NOT NULL CHECK (claim_type IN ('IDENTITY','CREDENTIAL')),
            claim TEXT NOT NULL,
            evidence_url TEXT NOT NULL,
            method VARCHAR(32) NOT NULL CHECK (method = 'PEER_ATTESTATION'),
            status VARCHAR(24) NOT NULL DEFAULT 'PENDING' CHECK (
                status IN ('PENDING','ATTESTED','REJECTED','EXPIRED')
            ),
            reviewer_note TEXT,
            expires_at TIMESTAMPTZ,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (owner_user_id <> verifier_user_id),
            UNIQUE(profile_id, verifier_user_id, claim_type, claim),
            FOREIGN KEY(profile_id, owner_user_id)
                REFERENCES expert_profiles(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE TABLE expert_contributions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id UUID NOT NULL,
            room_owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            profile_id UUID NOT NULL,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            body TEXT NOT NULL,
            source_ids JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_ids) = 'array'),
            conflict_disclosure TEXT NOT NULL,
            verification_label VARCHAR(48) NOT NULL,
            moderation_state VARCHAR(24) NOT NULL DEFAULT 'PENDING' CHECK (
                moderation_state IN ('PENDING','APPROVED','REJECTED','REMOVED')
            ),
            moderator_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            moderation_note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            FOREIGN KEY(room_id, room_owner_user_id)
                REFERENCES community_rooms(id, owner_user_id) ON DELETE CASCADE,
            FOREIGN KEY(profile_id, owner_user_id)
                REFERENCES expert_profiles(id, owner_user_id) ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX ix_expert_contributions_room "
        "ON expert_contributions(room_id, moderation_state, created_at DESC)"
    )

    op.execute("""
        CREATE TABLE tender_insights (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            supersedes_id UUID,
            scope_kind VARCHAR(24) NOT NULL CHECK (
                scope_kind IN ('ORBIT','SYSTEM','PROJECT','ROOM','GENERAL')
            ),
            scope_id UUID,
            version INTEGER NOT NULL CHECK (version > 0),
            insight TEXT NOT NULL,
            uncertainty TEXT NOT NULL,
            counterexample TEXT NOT NULL,
            conditions JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(conditions) = 'array'),
            source_ids JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_ids) = 'array'),
            status VARCHAR(24) NOT NULL DEFAULT 'PROPOSED' CHECK (
                status IN ('PROPOSED','KEPT','ACCEPTED','REJECTED','CORRECTED')
            ),
            correction_reason TEXT,
            provenance_label VARCHAR(48) NOT NULL DEFAULT 'OWNER_AUTHORED',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(id, owner_user_id),
            FOREIGN KEY(supersedes_id, owner_user_id)
                REFERENCES tender_insights(id, owner_user_id)
                ON DELETE SET NULL (supersedes_id),
            CHECK ((supersedes_id IS NULL AND correction_reason IS NULL) OR
                   (supersedes_id IS NOT NULL AND correction_reason IS NOT NULL))
        )
    """)
    op.execute(
        "CREATE INDEX ix_tender_owner_scope "
        "ON tender_insights(owner_user_id, scope_kind, scope_id, created_at DESC)"
    )

    tables = (
        "group_nur_syntheses",
        "research_jobs",
        "research_sources",
        "research_claims",
        "research_citations",
        "research_claim_revisions",
        "web_watchlists",
        "web_signal_snapshots",
        "web_signal_alerts",
        "expert_profiles",
        "expert_verifications",
        "expert_contributions",
        "tender_insights",
    )
    for table in tables:
        _enable(table)

    op.execute(
        f"CREATE POLICY p_group_nur_select ON group_nur_syntheses FOR SELECT TO {APP_ROLE} "
        f"USING ({HAS_USER} AND (owner_user_id = {UID} OR room_owner_user_id = {UID} "
        f"OR fn_community_room_role(room_id, {UID}) IS NOT NULL))"
    )
    op.execute(
        f"CREATE POLICY p_group_nur_insert ON group_nur_syntheses FOR INSERT TO {APP_ROLE} "
        f"WITH CHECK ({HAS_USER} AND owner_user_id = {UID} "
        f"AND fn_community_room_role(room_id, {UID}) IN ('OWNER','MODERATOR'))"
    )
    op.execute(
        "CREATE POLICY p_group_nur_definer_select ON group_nur_syntheses "
        "FOR SELECT TO nur_admin USING (true)"
    )
    op.execute(
        "CREATE POLICY p_group_nur_definer_update ON group_nur_syntheses "
        "FOR UPDATE TO nur_admin USING (true) WITH CHECK (true)"
    )
    op.execute("""
        CREATE FUNCTION fn_mark_group_nur_superseded() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS
        $$
        BEGIN
            IF NEW.supersedes_id IS NOT NULL THEN
                UPDATE group_nur_syntheses
                SET status = 'CORRECTED'
                WHERE id = NEW.supersedes_id AND room_id = NEW.room_id;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_mark_group_nur_superseded
        AFTER INSERT ON group_nur_syntheses
        FOR EACH ROW EXECUTE FUNCTION fn_mark_group_nur_superseded()
    """)

    for table in (
        "research_jobs",
        "research_sources",
        "research_claims",
        "research_citations",
        "research_claim_revisions",
        "web_watchlists",
        "web_signal_snapshots",
        "web_signal_alerts",
        "expert_profiles",
        "tender_insights",
    ):
        _owner_policy(table)

    op.execute(
        "CREATE POLICY p_expert_profiles_definer_select ON expert_profiles "
        "FOR SELECT TO nur_admin USING (true)"
    )
    op.execute(
        "CREATE POLICY p_expert_profiles_definer_update ON expert_profiles "
        "FOR UPDATE TO nur_admin USING (true) WITH CHECK (true)"
    )
    op.execute(
        f"CREATE POLICY p_expert_verifications_select ON expert_verifications "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND "
        f"(owner_user_id = {UID} OR verifier_user_id = {UID}))"
    )
    op.execute(
        f"CREATE POLICY p_expert_verifications_owner_insert ON expert_verifications "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND owner_user_id = {UID} "
        f"AND verifier_user_id <> {UID})"
    )
    op.execute(
        f"CREATE POLICY p_expert_verifications_verifier_update ON expert_verifications "
        f"FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND verifier_user_id = {UID}) "
        f"WITH CHECK (verifier_user_id = {UID})"
    )
    op.execute(
        f"CREATE POLICY p_expert_contributions_select ON expert_contributions "
        f"FOR SELECT TO {APP_ROLE} USING ({HAS_USER} AND (owner_user_id = {UID} "
        f"OR room_owner_user_id = {UID} "
        f"OR fn_community_room_role(room_id, {UID}) IN ('OWNER','MODERATOR') "
        f"OR (moderation_state = 'APPROVED' "
        f"AND fn_community_room_role(room_id, {UID}) IS NOT NULL)))"
    )
    op.execute(
        f"CREATE POLICY p_expert_contributions_insert ON expert_contributions "
        f"FOR INSERT TO {APP_ROLE} WITH CHECK ({HAS_USER} AND owner_user_id = {UID} "
        f"AND fn_community_room_role(room_id, {UID}) IS NOT NULL)"
    )
    op.execute(
        f"CREATE POLICY p_expert_contributions_moderate ON expert_contributions "
        f"FOR UPDATE TO {APP_ROLE} USING ({HAS_USER} AND "
        f"fn_community_room_role(room_id, {UID}) IN ('OWNER','MODERATOR')) "
        f"WITH CHECK (fn_community_room_role(room_id, {UID}) IN ('OWNER','MODERATOR'))"
    )

    op.execute("""
        CREATE FUNCTION fn_refresh_expert_profile_attestation() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS
        $$
        BEGIN
            IF NEW.status = 'ATTESTED' THEN
                UPDATE expert_profiles
                SET verification_status = 'PEER_ATTESTED',
                    verification_scope = 'PEER_ATTESTATION_ONLY',
                    updated_at = now()
                WHERE id = NEW.profile_id;
            ELSIF NEW.status = 'REJECTED' AND NOT EXISTS (
                SELECT 1 FROM expert_verifications verification
                WHERE verification.profile_id = NEW.profile_id
                  AND verification.status = 'ATTESTED'
            ) THEN
                UPDATE expert_profiles
                SET verification_status = 'REJECTED',
                    verification_scope = 'SELF_DECLARED',
                    updated_at = now()
                WHERE id = NEW.profile_id;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_refresh_expert_profile_attestation
        AFTER UPDATE OF status ON expert_verifications
        FOR EACH ROW EXECUTE FUNCTION fn_refresh_expert_profile_attestation()
    """)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_mark_group_nur_superseded "
        "ON group_nur_syntheses"
    )
    op.execute("DROP FUNCTION IF EXISTS fn_mark_group_nur_superseded()")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_refresh_expert_profile_attestation "
        "ON expert_verifications"
    )
    op.execute("DROP FUNCTION IF EXISTS fn_refresh_expert_profile_attestation()")
    for table in (
        "tender_insights",
        "expert_contributions",
        "expert_verifications",
        "expert_profiles",
        "web_signal_alerts",
        "web_signal_snapshots",
        "web_watchlists",
        "research_claim_revisions",
        "research_citations",
        "research_claims",
        "research_sources",
        "research_jobs",
        "group_nur_syntheses",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute(
        "ALTER TABLE consultation_stage_records "
        "DROP CONSTRAINT IF EXISTS ck_consultation_stage_payload_contract"
    )
    op.execute(
        "ALTER TABLE web_signal_questions "
        "DROP CONSTRAINT IF EXISTS uq_web_signal_questions_id_owner"
    )
    op.execute(
        "ALTER TABLE research_briefs "
        "DROP CONSTRAINT IF EXISTS uq_research_briefs_id_owner"
    )
    op.execute(
        "ALTER TABLE consultations "
        "DROP CONSTRAINT IF EXISTS uq_consultations_id_room"
    )
