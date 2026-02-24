"""add_actionkit_checklists

Revision ID: c6bfb5d417cb
Revises: aa927d92dc91
Create Date: 2026-02-24 02:23:17.569981
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c6bfb5d417cb'
down_revision = 'aa927d92dc91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('actionkit_checklists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['actionkit_items.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_actionkit_checklists_item_id'), 'actionkit_checklists', ['item_id'], unique=False)
    op.create_index(op.f('ix_actionkit_checklists_sort_order'), 'actionkit_checklists', ['sort_order'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_actionkit_checklists_sort_order'), table_name='actionkit_checklists')
    op.drop_index(op.f('ix_actionkit_checklists_item_id'), table_name='actionkit_checklists')
    op.drop_table('actionkit_checklists')
