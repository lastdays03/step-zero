"""add composite indexes for admin audit logs queries

Revision ID: 20260223_04
Revises: 20260223_03
Create Date: 2026-02-23 19:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260223_04"
down_revision = "20260223_03"
branch_labels = None
depends_on = None


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _index_exists(inspector, "admin_audit_logs", "ix_admin_audit_logs_action_target_type_created_at"):
        op.create_index(
            "ix_admin_audit_logs_action_target_type_created_at",
            "admin_audit_logs",
            ["action", "target_type", "created_at"],
            unique=False,
        )

    if not _index_exists(inspector, "admin_audit_logs", "ix_admin_audit_logs_admin_id_created_at"):
        op.create_index(
            "ix_admin_audit_logs_admin_id_created_at",
            "admin_audit_logs",
            ["admin_id", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_logs_admin_id_created_at", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_action_target_type_created_at", table_name="admin_audit_logs")
