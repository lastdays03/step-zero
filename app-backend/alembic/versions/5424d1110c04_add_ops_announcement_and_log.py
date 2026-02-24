"""add_ops_announcement_and_log

Revision ID: 5424d1110c04
Revises: 84852e175ccb
Create Date: 2026-02-24 02:58:54.039634
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '5424d1110c04'
down_revision = '84852e175ccb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ops_announcement table
    op.create_table(
        'ops_announcement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ops_announcement_admin_id'), 'ops_announcement', ['admin_id'], unique=False)
    op.create_index(op.f('ix_ops_announcement_published_at'), 'ops_announcement', ['published_at'], unique=False)
    op.create_index(op.f('ix_ops_announcement_status'), 'ops_announcement', ['status'], unique=False)
    op.create_index(op.f('ix_ops_announcement_title'), 'ops_announcement', ['title'], unique=False)

    # Create ops_audit_log table
    op.create_table(
        'ops_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ops_audit_log_action'), 'ops_audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_ops_audit_log_admin_id'), 'ops_audit_log', ['admin_id'], unique=False)
    op.create_index(op.f('ix_ops_audit_log_target_id'), 'ops_audit_log', ['target_id'], unique=False)
    op.create_index(op.f('ix_ops_audit_log_target_type'), 'ops_audit_log', ['target_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ops_audit_log_target_type'), table_name='ops_audit_log')
    op.drop_index(op.f('ix_ops_audit_log_target_id'), table_name='ops_audit_log')
    op.drop_index(op.f('ix_ops_audit_log_admin_id'), table_name='ops_audit_log')
    op.drop_index(op.f('ix_ops_audit_log_action'), table_name='ops_audit_log')
    op.drop_table('ops_audit_log')
    op.drop_index(op.f('ix_ops_announcement_title'), table_name='ops_announcement')
    op.drop_index(op.f('ix_ops_announcement_status'), table_name='ops_announcement')
    op.drop_index(op.f('ix_ops_announcement_published_at'), table_name='ops_announcement')
    op.drop_index(op.f('ix_ops_announcement_admin_id'), table_name='ops_announcement')
    op.drop_table('ops_announcement')
