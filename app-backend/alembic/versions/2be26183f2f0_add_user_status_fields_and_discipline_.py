"""add_user_status_fields_and_discipline_history

Revision ID: 2be26183f2f0
Revises: 0d55736ae708
Create Date: 2026-02-24 08:58:25.153812
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = '2be26183f2f0'
down_revision = '0d55736ae708'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # user_discipline_history 테이블 생성
    op.create_table('user_discipline_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('prev_status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('new_status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('suspended_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_discipline_history_suspended_until'), 'user_discipline_history', ['suspended_until'], unique=False)
    op.create_index(op.f('ix_user_discipline_history_user_id'), 'user_discipline_history', ['user_id'], unique=False)

    # user 테이블에 새 필드 추가
    op.add_column('user', sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), server_default='active', nullable=False))
    op.add_column('user', sa.Column('report_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('user', sa.Column('suspended_until', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_user_last_login_at'), 'user', ['last_login_at'], unique=False)
    op.create_index(op.f('ix_user_report_count'), 'user', ['report_count'], unique=False)
    op.create_index(op.f('ix_user_status'), 'user', ['status'], unique=False)
    op.create_index(op.f('ix_user_suspended_until'), 'user', ['suspended_until'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_suspended_until'), table_name='user')
    op.drop_index(op.f('ix_user_status'), table_name='user')
    op.drop_index(op.f('ix_user_report_count'), table_name='user')
    op.drop_index(op.f('ix_user_last_login_at'), table_name='user')
    op.drop_column('user', 'last_login_at')
    op.drop_column('user', 'suspended_until')
    op.drop_column('user', 'report_count')
    op.drop_column('user', 'status')
    op.drop_index(op.f('ix_user_discipline_history_user_id'), table_name='user_discipline_history')
    op.drop_index(op.f('ix_user_discipline_history_suspended_until'), table_name='user_discipline_history')
    op.drop_table('user_discipline_history')
