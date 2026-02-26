"""add suspension_reason to user

Revision ID: e8a182b8c9d0
Revises: c554bada5305
Create Date: 2026-02-26 12:15:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = 'e8a182b8c9d0'
down_revision = 'c554bada5305'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('user', sa.Column('suspension_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'suspension_reason')
