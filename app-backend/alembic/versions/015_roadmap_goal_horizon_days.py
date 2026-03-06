"""015 roadmap goal_horizon_days

Revision ID: 015_goal_horizon
Revises: 014_files_table
Create Date: 2026-03-06

Changes:
- Add goal_horizon_days column to roadmap table (default 30)
"""

import sqlalchemy as sa

from alembic import op

revision = "015_goal_horizon"
down_revision = "014_files_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "roadmap",
        sa.Column("goal_horizon_days", sa.Integer(), nullable=False, server_default="30"),
    )


def downgrade() -> None:
    op.drop_column("roadmap", "goal_horizon_days")
