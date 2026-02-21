"""add growth club attachments table

Revision ID: 20260220_04
Revises: 20260220_03
Create Date: 2026-02-20 16:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260220_04"
down_revision = "20260220_03"
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

    if not _table_exists(inspector, "growthclubpostattachment"):
        op.create_table(
            "growthclubpostattachment",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("growthclubpost.id"), nullable=False),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("object_key", sa.String(), nullable=False),
            sa.Column("original_filename", sa.String(), nullable=True),
            sa.Column("mime_type", sa.String(), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "growthclubpostattachment", "ix_growthclubpostattachment_post_id"):
        op.create_index(
            "ix_growthclubpostattachment_post_id",
            "growthclubpostattachment",
            ["post_id"],
            unique=False,
        )
    if not _index_exists(inspector, "growthclubpostattachment", "ix_growthclubpostattachment_kind"):
        op.create_index(
            "ix_growthclubpostattachment_kind",
            "growthclubpostattachment",
            ["kind"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_growthclubpostattachment_kind", table_name="growthclubpostattachment")
    op.drop_index("ix_growthclubpostattachment_post_id", table_name="growthclubpostattachment")
    op.drop_table("growthclubpostattachment")
