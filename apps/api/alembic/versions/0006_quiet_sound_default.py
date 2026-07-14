"""Quiet sound is opt-in: default profile sound_enabled to false."""
from alembic import op

revision = "0006_quiet_sound_default"
down_revision = "0005_ai_readiness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE profiles ALTER COLUMN sound_enabled SET DEFAULT false")
    op.execute("UPDATE profiles SET sound_enabled=false WHERE sound_enabled IS TRUE")


def downgrade() -> None:
    op.execute("ALTER TABLE profiles ALTER COLUMN sound_enabled SET DEFAULT true")
