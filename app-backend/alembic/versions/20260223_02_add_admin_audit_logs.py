"""add admin audit logs table

Revision ID: 20260223_02
Revises: 20260223_01
Create Date: 2026-02-23 17:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260223_02"
down_revision = "20260223_01"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "admin_audit_logs"):
        op.create_table(
            "admin_audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("admin_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("target_type", sa.String(), nullable=False),
            sa.Column("target_id", sa.String(), nullable=True),
            sa.Column("reason", sa.String(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "admin_audit_logs", "ix_admin_audit_logs_admin_id"):
        op.create_index("ix_admin_audit_logs_admin_id", "admin_audit_logs", ["admin_id"], unique=False)
    if not _index_exists(inspector, "admin_audit_logs", "ix_admin_audit_logs_action"):
        op.create_index("ix_admin_audit_logs_action", "admin_audit_logs", ["action"], unique=False)
    if not _index_exists(inspector, "admin_audit_logs", "ix_admin_audit_logs_target_type"):
        op.create_index("ix_admin_audit_logs_target_type", "admin_audit_logs", ["target_type"], unique=False)
    if not _index_exists(inspector, "admin_audit_logs", "ix_admin_audit_logs_created_at"):
        op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_target_type", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_action", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_admin_id", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
