"""009 startup_method column + source_url item-based migration

Revision ID: 009_startup_method
Revises: 008_feature_merge
Create Date: 2026-03-01
"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision = "009_startup_method"
down_revision = "008_feature_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── roadmap table: add startup_method column ──
    op.add_column(
        "roadmap",
        sa.Column("startup_method", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    # ── roadmap_step_actions: update source_url to item-based pattern ──
    # Uses PostgreSQL JSON operator ->>
    op.execute("""
        UPDATE roadmap_step_actions
        SET source_url = '/api/v1/actionkits/items/' || (metadata_json->>'actionkit_item_id')
        WHERE metadata_json->>'actionkit_item_id' IS NOT NULL
          AND metadata_json->>'actionkit_item_id' != ''
          AND action_type IN ('LEGAL_BASIS', 'DOCUMENT')
        """)


def downgrade() -> None:
    # source_url cannot be reverted to original values (they were already broken)
    op.drop_column("roadmap", "startup_method")
