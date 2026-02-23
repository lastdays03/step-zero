"""add announcements table

Revision ID: 20260223_03
Revises: 20260223_02
Create Date: 2026-02-23 18:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260223_03"
down_revision = "20260223_02"
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

    if not _table_exists(inspector, "announcements"):
        op.create_table(
            "announcements",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="draft"),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "announcements", "ix_announcements_status"):
        op.create_index("ix_announcements_status", "announcements", ["status"], unique=False)
    if not _index_exists(inspector, "announcements", "ix_announcements_created_by"):
        op.create_index("ix_announcements_created_by", "announcements", ["created_by"], unique=False)
    if not _index_exists(inspector, "announcements", "ix_announcements_updated_by"):
        op.create_index("ix_announcements_updated_by", "announcements", ["updated_by"], unique=False)
    if not _index_exists(inspector, "announcements", "ix_announcements_created_at"):
        op.create_index("ix_announcements_created_at", "announcements", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_announcements_created_at", table_name="announcements")
    op.drop_index("ix_announcements_updated_by", table_name="announcements")
    op.drop_index("ix_announcements_created_by", table_name="announcements")
    op.drop_index("ix_announcements_status", table_name="announcements")
    op.drop_table("announcements")
