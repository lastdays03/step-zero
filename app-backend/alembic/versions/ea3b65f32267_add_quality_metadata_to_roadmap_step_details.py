"""add quality metadata to roadmap_step_details

Revision ID: ea3b65f32267
Revises: 5afb882f37a0
Create Date: 2026-02-26 01:51:05.322267
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'ea3b65f32267'
down_revision = '5afb882f37a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('roadmap_step_details', sa.Column('source_count', sa.Integer(), nullable=True))
    op.add_column('roadmap_step_details', sa.Column('has_fallback', sa.Boolean(), nullable=True))
    op.add_column('roadmap_step_details', sa.Column('mapping_source', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    op.drop_column('roadmap_step_details', 'mapping_source')
    op.drop_column('roadmap_step_details', 'has_fallback')
    op.drop_column('roadmap_step_details', 'source_count')
