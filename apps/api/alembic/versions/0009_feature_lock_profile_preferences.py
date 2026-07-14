"""Feature lock profile preferences.

Adds owner-only preference fields used by the real Settings controls. Existing
profile RLS policies continue to apply because these are columns on profiles,
not a new table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0009_feature_lock_prefs"
down_revision = "0008_omega_v1_review_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("default_boundary", sa.String(32), nullable=False, server_default="PRIVATE_ORBIT"),
    )
    op.add_column(
        "profiles",
        sa.Column("active_orbit_id", UUID(as_uuid=True), sa.ForeignKey("orbits.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("omega_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_profiles_active_orbit", "profiles", ["active_orbit_id"])


def downgrade() -> None:
    op.drop_index("ix_profiles_active_orbit", table_name="profiles")
    op.drop_column("profiles", "omega_enabled")
    op.drop_column("profiles", "active_orbit_id")
    op.drop_column("profiles", "default_boundary")
