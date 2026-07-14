"""Add explicit DEMO provenance to Council contributions.

0016 may already exist in a persistent owner database. IF NOT EXISTS keeps the
forward migration valid both there and in a fresh extract where the columns
are already present in the consolidated 0016 definition.
"""

from alembic import op


revision = "0018_council_demo_markers"
down_revision = "0017_community_glow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE council_positions "
        "ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE council_decisions "
        "ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE council_decisions DROP COLUMN IF EXISTS is_demo")
    op.execute("ALTER TABLE council_positions DROP COLUMN IF EXISTS is_demo")
