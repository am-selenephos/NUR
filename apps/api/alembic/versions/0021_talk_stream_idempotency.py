"""talk stream request idempotency

Revision ID: 0021_talk_stream_idempotency
Revises: 0020_notifications
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0021_talk_stream_idempotency"
down_revision = "0020_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("model_runs", sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(
        "uq_model_runs_owner_request",
        "model_runs",
        ["owner_user_id", "request_id"],
        unique=True,
        postgresql_where=sa.text("request_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_model_runs_owner_request", table_name="model_runs")
    op.drop_column("model_runs", "request_id")
