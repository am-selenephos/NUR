"""complete the scoped dynamic translation contract

Revision ID: 0027_translation_contract
Revises: 0026_glow_progression_spine
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0027_translation_contract"
down_revision = "0026_glow_progression_spine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("translations", sa.Column("detected_source_locale", sa.String(16)))
    op.add_column(
        "translations",
        sa.Column("source_writing_preference", sa.String(16), nullable=False, server_default="default"),
    )
    op.add_column(
        "translations",
        sa.Column("target_writing_preference", sa.String(16), nullable=False, server_default="default"),
    )
    op.add_column(
        "translations",
        sa.Column("source_direction", sa.String(3), nullable=False, server_default="ltr"),
    )
    op.add_column(
        "translations",
        sa.Column("target_direction", sa.String(3), nullable=False, server_default="ltr"),
    )
    op.add_column(
        "translations",
        sa.Column("scope", sa.String(32), nullable=False, server_default="PRIVATE_ORBIT"),
    )
    op.add_column("translations", sa.Column("source_object_type", sa.String(80)))
    op.add_column(
        "translations",
        sa.Column("source_object_id", postgresql.UUID(as_uuid=True)),
    )
    op.add_column("translations", sa.Column("source_ref", sa.String(180)))
    op.add_column("translations", sa.Column("provider_version", sa.String(160)))
    op.add_column("translations", sa.Column("cache_key", sa.String(64)))
    op.add_column(
        "translations",
        sa.Column("quality_state", sa.String(40), nullable=False, server_default="MISSING_REVIEW"),
    )
    op.add_column(
        "translations",
        sa.Column("translation_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "translations",
        sa.Column(
            "moderation_context_preserved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "translations",
        sa.Column(
            "feedback",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_check_constraint(
        "ck_translations_scope",
        "translations",
        "scope IN ('EPHEMERAL', 'PRIVATE_ORBIT', 'SYSTEM_SHARED', "
        "'LEARNING_CANDIDATE', 'COMMUNITY_ROOM')",
    )
    op.create_check_constraint(
        "ck_translations_directions",
        "translations",
        "source_direction IN ('ltr', 'rtl') AND target_direction IN ('ltr', 'rtl')",
    )
    op.create_index(
        "uq_translations_owner_cache_key",
        "translations",
        ["owner_user_id", "cache_key"],
        unique=True,
        postgresql_where=sa.text("cache_key IS NOT NULL"),
    )
    op.create_index(
        "ix_translations_source_object",
        "translations",
        ["owner_user_id", "source_object_type", "source_object_id"],
        postgresql_where=sa.text("source_object_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_translations_source_object", table_name="translations")
    op.drop_index("uq_translations_owner_cache_key", table_name="translations")
    op.drop_constraint("ck_translations_directions", "translations", type_="check")
    op.drop_constraint("ck_translations_scope", "translations", type_="check")
    for column in (
        "feedback",
        "moderation_context_preserved",
        "translation_version",
        "quality_state",
        "cache_key",
        "provider_version",
        "source_ref",
        "source_object_id",
        "source_object_type",
        "scope",
        "target_direction",
        "source_direction",
        "target_writing_preference",
        "source_writing_preference",
        "detected_source_locale",
    ):
        op.drop_column("translations", column)
