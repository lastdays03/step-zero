"""add growth club post reports table

Revision ID: 20260221_06
Revises: 0cfaf7ebe7af
Create Date: 2026-02-21 15:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260221_06"
down_revision = "0cfaf7ebe7af"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "growthclubpostreport",
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("growthclubpostreport")
