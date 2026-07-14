"""Glow rules for bounded Community, Group NUR, and Council contributions.

The rows these rules reward are persisted by 0016_group_nur; the award itself
stays server-calculated, source-linked, idempotent, capped, and anti-spam
gated exactly like every earlier Glow rule. Demo-marked content never earns
Glow (enforced in the service layer, not here).
"""

from alembic import op


revision = "0017_community_glow"
down_revision = "0016_group_nur"
branch_labels = None
depends_on = None

EVENT_TYPES = (
    "community.message_posted",
    "community.post_created",
    "community.comment_created",
    "council.position_added",
    "council.decision_recorded",
)


def upgrade() -> None:
    # Membership grants resolve an invitee's email without any read access to
    # the users table (owner-context RLS shows a user only themself), the same
    # SECURITY DEFINER pattern capsules use — narrowed to active accounts.
    op.execute("""
        CREATE FUNCTION fn_active_user_id_by_email(em text) RETURNS uuid
        LANGUAGE sql SECURITY DEFINER STABLE AS
        $$ SELECT id FROM users WHERE email = lower(trim(em)) AND status = 'active' $$
    """)
    op.execute("GRANT EXECUTE ON FUNCTION fn_active_user_id_by_email(text) TO nur_app")

    op.execute("""
        INSERT INTO glow_rules(
            event_type, base_points, daily_cap, weekly_cap, spam_window_seconds,
            action_type, requires_persistence, description
        ) VALUES
          ('community.message_posted', 2, 10, 70, 30,
           'community.message_posted', true, 'A persisted meaningful Group NUR message.'),
          ('community.post_created', 4, 12, 84, 60,
           'community.post_created', true, 'A persisted Community post.'),
          ('community.comment_created', 2, 10, 70, 30,
           'community.comment_created', true, 'A persisted Community comment or reply.'),
          ('council.position_added', 4, 12, 84, 60,
           'council.position_added', true, 'A persisted Council position with its evidence.'),
          ('council.decision_recorded', 6, 12, 84, 0,
           'council.decision_recorded', true, 'A persisted Council decision by the room owner.')
        ON CONFLICT (event_type) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS fn_active_user_id_by_email(text)")
    quoted = ", ".join(f"'{event_type}'" for event_type in EVENT_TYPES)
    op.execute(f"DELETE FROM glow_rules WHERE event_type IN ({quoted})")
