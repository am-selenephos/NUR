"""Gate 3 — Shared Orbit / Context Capsule tables (amendment §3, verbatim).

A scope is a description, never an authorization: recipient access exists ONLY
through an active, unrevoked, unexpired capsule_grant addressed to them, and
retrieval joins ONLY through capsule_sources. Every access is auditable via
append-only capsule_access_events. Includes the Gate 4 collaboration-outcome
capture table.
"""
from alembic import op

revision = "0004_shared_orbit"
down_revision = "0003_cognitive_substrate"
branch_labels = None
depends_on = None

APP_ROLE = "nur_app"
OWNER_UUID = "NULLIF(current_setting('app.current_user_id', true), '')::uuid"
HAS_USER = "current_setting('app.current_user_id', true) IS NOT NULL AND current_setting('app.current_user_id', true) <> ''"

ENUMS = {
    "orbit_source_kind": [
        "COGNITIVE_EVENT", "JOURNAL_ENTRY", "PLAN", "PLAN_STEP",
        "OUTCOME", "REFERENCE", "DECISION", "RESEARCH_DRAFT",
    ],
    "inclusion_mode": ["FULL", "SUMMARY_ONLY", "METADATA_ONLY"],
    "capsule_visibility": ["NAMED_RECIPIENTS_ONLY", "LINK_WITH_PASSCODE"],
    "capsule_capability": ["READ_ONLY", "ASK_SCOPED_QUESTIONS", "COMMENT_ONLY"],
    "included_representation": ["FULL", "OWNER_APPROVED_SUMMARY", "METADATA_ONLY"],
    "access_event_kind": [
        "VIEWED", "QUESTION_ASKED", "ANSWER_SHOWN", "COMMENT_CREATED",
        "EXPORT_ATTEMPTED", "REVOKED", "EXPIRED",
    ],
    "question_status": ["PENDING", "ANSWERED", "NOT_AVAILABLE", "REJECTED_BY_POLICY"],
    "answer_mode": ["DIRECT_STATEMENT", "APPROVED_CONTEXT_SUMMARY", "INFERENCE", "NOT_AVAILABLE"],
}

# recipient's active-grant predicate for a capsule row `c`
ACTIVE_GRANT = (
    "EXISTS (SELECT 1 FROM capsule_grants g WHERE g.capsule_id = c.id"
    f" AND g.recipient_user_id = {OWNER_UUID}"
    " AND g.revoked_at IS NULL AND (g.expires_at IS NULL OR g.expires_at > now()))"
    " AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at > now())"
)


def upgrade() -> None:
    for name, vals in ENUMS.items():
        op.execute(f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in vals)})")

    op.execute("""
        CREATE TABLE orbit_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_kind orbit_source_kind NOT NULL,
            source_id UUID NOT NULL,
            inclusion_mode inclusion_mode NOT NULL DEFAULT 'FULL',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (orbit_id, source_kind, source_id)
        )""")

    op.execute("""
        CREATE TABLE context_capsules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            orbit_id UUID NOT NULL REFERENCES orbits(id) ON DELETE CASCADE,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            purpose TEXT NOT NULL,
            recipient_instructions TEXT,
            visibility capsule_visibility NOT NULL DEFAULT 'NAMED_RECIPIENTS_ONLY',
            capability capsule_capability NOT NULL DEFAULT 'READ_ONLY',
            expires_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            version INT NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE capsule_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            capsule_id UUID NOT NULL REFERENCES context_capsules(id) ON DELETE CASCADE,
            capsule_version INT NOT NULL,
            orbit_source_id UUID NOT NULL REFERENCES orbit_sources(id) ON DELETE CASCADE,
            included_representation included_representation NOT NULL DEFAULT 'FULL',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (capsule_id, capsule_version, orbit_source_id)
        )""")

    op.execute("""
        CREATE TABLE capsule_grants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            capsule_id UUID NOT NULL REFERENCES context_capsules(id) ON DELETE CASCADE,
            recipient_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            recipient_email_hash TEXT,
            capability capsule_capability NOT NULL DEFAULT 'READ_ONLY',
            expires_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            last_accessed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (recipient_user_id IS NOT NULL OR recipient_email_hash IS NOT NULL)
        )""")

    op.execute("""
        CREATE TABLE capsule_access_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            capsule_id UUID NOT NULL REFERENCES context_capsules(id) ON DELETE CASCADE,
            grant_id UUID REFERENCES capsule_grants(id) ON DELETE SET NULL,
            actor_user_id UUID,
            event_kind access_event_kind NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        )""")

    op.execute("""
        CREATE TABLE capsule_questions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            capsule_id UUID NOT NULL REFERENCES context_capsules(id) ON DELETE CASCADE,
            grant_id UUID NOT NULL REFERENCES capsule_grants(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            status question_status NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE capsule_answers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            question_id UUID NOT NULL REFERENCES capsule_questions(id) ON DELETE CASCADE,
            answer_text TEXT NOT NULL,
            answer_mode answer_mode NOT NULL,
            source_refs JSONB NOT NULL,
            confidence NUMERIC,
            policy_explanation TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    op.execute("""
        CREATE TABLE collaboration_outcomes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            capsule_id UUID NOT NULL REFERENCES context_capsules(id) ON DELETE CASCADE,
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            onboarding_faster BOOLEAN,
            decisions_respected BOOLEAN,
            answered_correctly BOOLEAN,
            time_saved_minutes INT,
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

    # ------------------------------ RLS -------------------------------------
    # Cross-table policy references would recurse (capsules<->grants). The
    # canonical break: SECURITY DEFINER predicate functions owned by the
    # migration role, which reads via its own explicit definer policies.
    for t in ["orbit_sources", "context_capsules", "capsule_sources", "capsule_grants",
              "capsule_access_events", "capsule_questions", "capsule_answers",
              "collaboration_outcomes"]:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
    for t in ["context_capsules", "capsule_grants", "capsule_sources", "capsule_questions",
              "orbit_sources", "decisions", "orbit_references", "journal_entries",
              "plans", "plan_steps", "outcomes", "cognitive_events", "research_drafts"]:
        op.execute(f"CREATE POLICY p_{t}_definer_read ON {t} FOR SELECT TO nur_admin USING (true)")

    op.execute("""
        CREATE FUNCTION fn_owns_capsule(cap uuid, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (SELECT 1 FROM context_capsules WHERE id = cap AND owner_user_id = usr) $$""")
    op.execute("""
        CREATE FUNCTION fn_has_grant(cap uuid, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (SELECT 1 FROM capsule_grants g WHERE g.capsule_id = cap AND g.recipient_user_id = usr) $$""")
    op.execute("""
        CREATE FUNCTION fn_has_active_grant(cap uuid, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (
             SELECT 1 FROM capsule_grants g JOIN context_capsules c ON c.id = g.capsule_id
             WHERE g.capsule_id = cap AND g.recipient_user_id = usr
               AND g.revoked_at IS NULL AND (g.expires_at IS NULL OR g.expires_at > now())
               AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at > now())) $$""")
    op.execute("""
        CREATE FUNCTION fn_grant_active_ask(gid uuid, cap uuid, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (
             SELECT 1 FROM capsule_grants g JOIN context_capsules c ON c.id = g.capsule_id
             WHERE g.id = gid AND g.capsule_id = cap AND g.recipient_user_id = usr
               AND g.capability = 'ASK_SCOPED_QUESTIONS'
               AND g.revoked_at IS NULL AND (g.expires_at IS NULL OR g.expires_at > now())
               AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at > now())) $$""")
    op.execute("""
        CREATE FUNCTION fn_grant_addressed(gid uuid, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (SELECT 1 FROM capsule_grants g WHERE g.id = gid AND g.recipient_user_id = usr) $$""")
    op.execute("""
        CREATE FUNCTION fn_question_owner(qid uuid, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (SELECT 1 FROM capsule_questions q JOIN context_capsules c ON c.id = q.capsule_id
                          WHERE q.id = qid AND c.owner_user_id = usr) $$""")
    op.execute("""
        CREATE FUNCTION fn_question_recipient_active(qid uuid, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (
             SELECT 1 FROM capsule_questions q
             JOIN capsule_grants g ON g.id = q.grant_id
             JOIN context_capsules c ON c.id = g.capsule_id
             WHERE q.id = qid AND g.recipient_user_id = usr
               AND g.revoked_at IS NULL AND (g.expires_at IS NULL OR g.expires_at > now())
               AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at > now())) $$""")
    op.execute("""
        CREATE FUNCTION fn_source_visible(cap uuid, ver int, usr uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT EXISTS (
             SELECT 1 FROM context_capsules c JOIN capsule_grants g ON g.capsule_id = c.id
             WHERE c.id = cap AND c.version = ver AND g.recipient_user_id = usr
               AND g.revoked_at IS NULL AND (g.expires_at IS NULL OR g.expires_at > now())
               AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at > now())) $$""")
    for fn in ["fn_owns_capsule(uuid,uuid)", "fn_has_grant(uuid,uuid)", "fn_has_active_grant(uuid,uuid)",
               "fn_grant_active_ask(uuid,uuid,uuid)", "fn_grant_addressed(uuid,uuid)",
               "fn_question_owner(uuid,uuid)", "fn_question_recipient_active(uuid,uuid)",
               "fn_source_visible(uuid,int,uuid)"]:
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO {APP_ROLE}")


    # table privileges (append-only tables get no UPDATE/DELETE)
    for t in ["orbit_sources", "context_capsules", "capsule_grants", "capsule_questions",
              "collaboration_outcomes", "capsule_sources"]:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON capsule_access_events TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON capsule_answers TO {APP_ROLE}")
    # owner management (direct owner column)
    for t in ["orbit_sources", "context_capsules", "collaboration_outcomes"]:
        op.execute(f"CREATE POLICY p_{t}_owner_all ON {t} FOR ALL TO {APP_ROLE} "
                   f"USING ({HAS_USER} AND owner_user_id = {OWNER_UUID}) "
                   f"WITH CHECK (owner_user_id = {OWNER_UUID})")
    # owner management via parent capsule (definer predicate — no recursion)
    for t in ["capsule_sources", "capsule_grants", "capsule_questions"]:
        op.execute(f"CREATE POLICY p_{t}_owner_all ON {t} FOR ALL TO {APP_ROLE} "
                   f"USING ({HAS_USER} AND fn_owns_capsule(capsule_id, {OWNER_UUID})) "
                   f"WITH CHECK (fn_owns_capsule(capsule_id, {OWNER_UUID}))")
    op.execute(f"CREATE POLICY p_capsule_answers_owner_all ON capsule_answers FOR ALL TO {APP_ROLE} "
               f"USING ({HAS_USER} AND fn_question_owner(question_id, {OWNER_UUID})) "
               f"WITH CHECK (fn_question_owner(question_id, {OWNER_UUID}))")

    # recipient access
    op.execute(f"CREATE POLICY p_capsules_recipient_select ON context_capsules FOR SELECT TO {APP_ROLE} "
               f"USING ({HAS_USER} AND fn_has_grant(id, {OWNER_UUID}))")
    op.execute(f"CREATE POLICY p_capsule_sources_recipient_select ON capsule_sources FOR SELECT TO {APP_ROLE} "
               f"USING ({HAS_USER} AND fn_source_visible(capsule_id, capsule_version, {OWNER_UUID}))")
    op.execute(f"CREATE POLICY p_capsule_grants_recipient_select ON capsule_grants FOR SELECT TO {APP_ROLE} "
               f"USING ({HAS_USER} AND recipient_user_id = {OWNER_UUID})")
    op.execute(f"CREATE POLICY p_capsule_questions_recipient ON capsule_questions FOR SELECT TO {APP_ROLE} "
               f"USING ({HAS_USER} AND fn_grant_addressed(grant_id, {OWNER_UUID}))")
    op.execute(f"CREATE POLICY p_capsule_questions_recipient_insert ON capsule_questions FOR INSERT TO {APP_ROLE} "
               f"WITH CHECK ({HAS_USER} AND fn_grant_active_ask(grant_id, capsule_id, {OWNER_UUID}))")
    op.execute(f"CREATE POLICY p_capsule_answers_recipient ON capsule_answers FOR SELECT TO {APP_ROLE} "
               f"USING ({HAS_USER} AND fn_question_recipient_active(question_id, {OWNER_UUID}))")
    op.execute(f"CREATE POLICY p_capsule_answers_recipient_insert ON capsule_answers FOR INSERT TO {APP_ROLE} "
               f"WITH CHECK ({HAS_USER} AND fn_question_recipient_active(question_id, {OWNER_UUID}))")

    # audit: append-only; owner reads; actor inserts own events
    op.execute(f"CREATE POLICY p_access_events_owner_select ON capsule_access_events FOR SELECT TO {APP_ROLE} "
               f"USING ({HAS_USER} AND fn_owns_capsule(capsule_id, {OWNER_UUID}))")
    op.execute(f"CREATE POLICY p_access_events_actor_insert ON capsule_access_events FOR INSERT TO {APP_ROLE} "
               f"WITH CHECK ({HAS_USER} AND actor_user_id = {OWNER_UUID})")

    # email-grant binding: the owner types an email; a definer resolves it to
    # a uuid (nothing else), and an unbound grant is claimed by the matching
    # recipient on first arrival.
    op.execute("CREATE POLICY p_users_definer_read ON users FOR SELECT TO nur_admin USING (true)")
    op.execute("CREATE POLICY p_capsule_grants_definer_write ON capsule_grants FOR UPDATE TO nur_admin USING (true) WITH CHECK (true)")
    op.execute("CREATE POLICY p_capsule_questions_definer_write ON capsule_questions FOR UPDATE TO nur_admin USING (true) WITH CHECK (true)")
    op.execute("""
        CREATE FUNCTION fn_user_id_by_email(em text) RETURNS uuid
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT id FROM users WHERE email = lower(trim(em)) $$""")
    op.execute("""
        CREATE FUNCTION fn_claim_grants(usr uuid, ehash text) RETURNS int
        LANGUAGE sql SECURITY DEFINER VOLATILE AS
        $$ WITH u AS (UPDATE capsule_grants SET recipient_user_id = usr
                      WHERE recipient_user_id IS NULL AND recipient_email_hash = ehash
                      RETURNING 1)
           SELECT count(*)::int FROM u $$""")
    op.execute(f"GRANT EXECUTE ON FUNCTION fn_user_id_by_email(text) TO {APP_ROLE}")
    op.execute(f"GRANT EXECUTE ON FUNCTION fn_claim_grants(uuid,text) TO {APP_ROLE}")
    op.execute("""
        CREATE FUNCTION fn_touch_grant(gid uuid, usr uuid) RETURNS void
        LANGUAGE sql SECURITY DEFINER VOLATILE AS
        $$ UPDATE capsule_grants SET last_accessed_at = now()
           WHERE id = gid AND recipient_user_id = usr $$""")
    op.execute(f"GRANT EXECUTE ON FUNCTION fn_touch_grant(uuid,uuid) TO {APP_ROLE}")
    op.execute("""
        CREATE FUNCTION fn_set_question_status(qid uuid, usr uuid, st text) RETURNS void
        LANGUAGE sql SECURITY DEFINER VOLATILE AS
        $$ UPDATE capsule_questions q SET status = st::question_status
           WHERE q.id = qid
             AND EXISTS (SELECT 1 FROM capsule_grants g
                         WHERE g.id = q.grant_id AND g.recipient_user_id = usr) $$""")
    op.execute(f"GRANT EXECUTE ON FUNCTION fn_set_question_status(uuid,uuid,text) TO {APP_ROLE}")
    # The ONE door hydration passes through (Rule 5/6): owner or active
    # grantee, current version only, kind-joined titles/bodies.
    op.execute("""
        CREATE FUNCTION fn_hydrate_capsule(cap uuid, usr uuid)
        RETURNS TABLE(capsule_source_id uuid, orbit_source_id uuid, source_kind text,
                      source_id uuid, representation text, title text, body text)
        LANGUAGE sql SECURITY DEFINER STABLE AS $$
          WITH c AS (SELECT * FROM context_capsules WHERE id = cap),
          ok AS (SELECT 1 FROM c WHERE c.owner_user_id = usr
                 UNION ALL SELECT 1 WHERE fn_has_active_grant(cap, usr))
          SELECT cs.id, os.id, os.source_kind::text, os.source_id,
                 cs.included_representation::text,
                 COALESCE(d.statement, r.title, left(j.body,80), p.title, ps.title,
                          left(o.observed_result,80), left(e.content_text,80),
                          rd.question, '(missing)'),
                 COALESCE(d.rationale,
                          coalesce(r.body,'') || CASE WHEN r.id IS NULL THEN NULL
                              WHEN r.url IS NULL THEN '' ELSE ' ('||r.url||')' END,
                          j.body, p.status, ps.body, o.observed_result,
                          e.content_text, rd.notes, '')
          FROM capsule_sources cs
          JOIN c ON c.id = cs.capsule_id AND cs.capsule_version = c.version
          JOIN orbit_sources os ON os.id = cs.orbit_source_id
          LEFT JOIN decisions d        ON os.source_kind='DECISION'        AND d.id  = os.source_id
          LEFT JOIN orbit_references r ON os.source_kind='REFERENCE'       AND r.id  = os.source_id
          LEFT JOIN journal_entries j  ON os.source_kind='JOURNAL_ENTRY'   AND j.id  = os.source_id
          LEFT JOIN plans p            ON os.source_kind='PLAN'            AND p.id  = os.source_id
          LEFT JOIN plan_steps ps      ON os.source_kind='PLAN_STEP'       AND ps.id = os.source_id
          LEFT JOIN outcomes o         ON os.source_kind='OUTCOME'         AND o.id  = os.source_id
          LEFT JOIN cognitive_events e ON os.source_kind='COGNITIVE_EVENT' AND e.id  = os.source_id
          LEFT JOIN research_drafts rd ON os.source_kind='RESEARCH_DRAFT'  AND rd.id = os.source_id
          WHERE EXISTS (SELECT 1 FROM ok)
        $$""")
    op.execute(f"GRANT EXECUTE ON FUNCTION fn_hydrate_capsule(uuid,uuid) TO {APP_ROLE}")
    # visible boundary: what was withheld, as kind+count ONLY (titles never leave)
    op.execute("""
        CREATE FUNCTION fn_excluded_summary(cap uuid, usr uuid)
        RETURNS TABLE(source_kind text, cnt int)
        LANGUAGE sql SECURITY DEFINER STABLE AS $$
          WITH c AS (SELECT * FROM context_capsules WHERE id = cap),
          ok AS (SELECT 1 FROM c WHERE c.owner_user_id = usr
                 UNION ALL SELECT 1 WHERE fn_has_active_grant(cap, usr))
          SELECT os.source_kind::text, count(*)::int
          FROM orbit_sources os, c
          WHERE os.orbit_id = c.orbit_id
            AND EXISTS (SELECT 1 FROM ok)
            AND os.id NOT IN (SELECT cs.orbit_source_id FROM capsule_sources cs
                              WHERE cs.capsule_id = c.id AND cs.capsule_version = c.version)
          GROUP BY os.source_kind
        $$""")
    op.execute(f"GRANT EXECUTE ON FUNCTION fn_excluded_summary(uuid,uuid) TO {APP_ROLE}")

    # minimal disclosure: a grantee may read the granter's chosen name
    op.execute(f"CREATE POLICY p_profiles_capsule_recipient ON profiles FOR SELECT TO {APP_ROLE} "
               f"USING ({HAS_USER} AND EXISTS (SELECT 1 FROM context_capsules c "
               f"JOIN capsule_grants g ON g.capsule_id = c.id "
               f"WHERE c.owner_user_id = profiles.user_id AND g.recipient_user_id = {OWNER_UUID}))")


def downgrade() -> None:
    for fn in ["fn_owns_capsule(uuid,uuid)", "fn_has_grant(uuid,uuid)", "fn_has_active_grant(uuid,uuid)",
               "fn_grant_active_ask(uuid,uuid,uuid)", "fn_grant_addressed(uuid,uuid)",
               "fn_question_owner(uuid,uuid)", "fn_question_recipient_active(uuid,uuid)",
               "fn_source_visible(uuid,int,uuid)", "fn_user_id_by_email(text)",
               "fn_claim_grants(uuid,text)", "fn_touch_grant(uuid,uuid)", "fn_hydrate_capsule(uuid,uuid)", "fn_excluded_summary(uuid,uuid)", "fn_set_question_status(uuid,uuid,text)"]:
        op.execute(f"DROP FUNCTION IF EXISTS {fn}")
    op.execute("DROP POLICY IF EXISTS p_profiles_capsule_recipient ON profiles")
    for t in ["collaboration_outcomes", "capsule_answers", "capsule_questions",
              "capsule_access_events", "capsule_grants", "capsule_sources",
              "context_capsules", "orbit_sources"]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    for name in reversed(list(ENUMS)):
        op.execute(f"DROP TYPE IF EXISTS {name}")
