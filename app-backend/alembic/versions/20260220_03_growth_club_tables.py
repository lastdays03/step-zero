"""add growth club tables

Revision ID: 20260220_03
Revises: 20260220_02
Create Date: 2026-02-20 23:59:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260220_03"
down_revision = "20260220_02"
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

    if not _table_exists(inspector, "growthclubpost"):
        op.create_table(
            "growthclubpost",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("neighborhood", sa.String(), nullable=True),
            sa.Column("industry", sa.String(), nullable=True),
            sa.Column("image_path", sa.String(), nullable=True),
            sa.Column("file_path", sa.String(), nullable=True),
            sa.Column("author_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_blinded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "growthclubpost", "ix_growthclubpost_author_id"):
        op.create_index("ix_growthclubpost_author_id", "growthclubpost", ["author_id"], unique=False)
    if not _index_exists(inspector, "growthclubpost", "ix_growthclubpost_category"):
        op.create_index("ix_growthclubpost_category", "growthclubpost", ["category"], unique=False)
    if not _index_exists(inspector, "growthclubpost", "ix_growthclubpost_created_at"):
        op.create_index("ix_growthclubpost_created_at", "growthclubpost", ["created_at"], unique=False)
    if not _index_exists(inspector, "growthclubpost", "ix_growthclubpost_is_blinded"):
        op.create_index("ix_growthclubpost_is_blinded", "growthclubpost", ["is_blinded"], unique=False)

    if not _table_exists(inspector, "growthclubcomment"):
        op.create_table(
            "growthclubcomment",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("growthclubpost.id"), nullable=False),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("growthclubcomment.id"), nullable=True),
            sa.Column("author_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_blinded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "growthclubcomment", "ix_growthclubcomment_post_id"):
        op.create_index("ix_growthclubcomment_post_id", "growthclubcomment", ["post_id"], unique=False)
    if not _index_exists(inspector, "growthclubcomment", "ix_growthclubcomment_parent_id"):
        op.create_index("ix_growthclubcomment_parent_id", "growthclubcomment", ["parent_id"], unique=False)
    if not _index_exists(inspector, "growthclubcomment", "ix_growthclubcomment_author_id"):
        op.create_index("ix_growthclubcomment_author_id", "growthclubcomment", ["author_id"], unique=False)
    if not _index_exists(inspector, "growthclubcomment", "ix_growthclubcomment_created_at"):
        op.create_index("ix_growthclubcomment_created_at", "growthclubcomment", ["created_at"], unique=False)

    if not _table_exists(inspector, "growthclubpostlike"):
        op.create_table(
            "growthclubpostlike",
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("growthclubpost.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("post_id", "user_id"),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "growthclubpostlike", "ix_growthclubpostlike_user_id"):
        op.create_index("ix_growthclubpostlike_user_id", "growthclubpostlike", ["user_id"], unique=False)
    if not _index_exists(inspector, "growthclubpostlike", "ix_growthclubpostlike_created_at"):
        op.create_index("ix_growthclubpostlike_created_at", "growthclubpostlike", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_growthclubpostlike_created_at", table_name="growthclubpostlike")
    op.drop_index("ix_growthclubpostlike_user_id", table_name="growthclubpostlike")
    op.drop_table("growthclubpostlike")

    op.drop_index("ix_growthclubcomment_created_at", table_name="growthclubcomment")
    op.drop_index("ix_growthclubcomment_author_id", table_name="growthclubcomment")
    op.drop_index("ix_growthclubcomment_parent_id", table_name="growthclubcomment")
    op.drop_index("ix_growthclubcomment_post_id", table_name="growthclubcomment")
    op.drop_table("growthclubcomment")

    op.drop_index("ix_growthclubpost_is_blinded", table_name="growthclubpost")
    op.drop_index("ix_growthclubpost_created_at", table_name="growthclubpost")
    op.drop_index("ix_growthclubpost_category", table_name="growthclubpost")
    op.drop_index("ix_growthclubpost_author_id", table_name="growthclubpost")
    op.drop_table("growthclubpost")
