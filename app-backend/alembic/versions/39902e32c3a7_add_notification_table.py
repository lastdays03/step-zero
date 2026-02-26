"""add notification table

Revision ID: 39902e32c3a7
Revises: f5b7b12c3036
Create Date: 2026-02-23 08:10:12.370545
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '39902e32c3a7'
down_revision = 'f5b7b12c3036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('notification',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('action_type', sa.String(), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('target_type', sa.String(), nullable=True),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['user.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_user_id'), 'notification', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notification_user_id'), table_name='notification')
    op.drop_table('notification')
