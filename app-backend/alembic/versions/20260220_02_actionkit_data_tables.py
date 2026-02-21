"""add actionkit data tables

Revision ID: 20260220_02
Revises: 20260220_01
Create Date: 2026-02-20 23:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260220_02"
down_revision = "20260220_01"
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

    if not _table_exists(inspector, "actionkit_categories"):
        op.create_table(
            "actionkit_categories",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("domain", sa.String(), nullable=False),
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("domain", "slug", name="uq_actionkit_categories_domain_slug"),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "actionkit_categories", "ix_actionkit_categories_domain"):
        op.create_index("ix_actionkit_categories_domain", "actionkit_categories", ["domain"], unique=False)
    if not _index_exists(inspector, "actionkit_categories", "ix_actionkit_categories_slug"):
        op.create_index("ix_actionkit_categories_slug", "actionkit_categories", ["slug"], unique=False)
    if not _index_exists(inspector, "actionkit_categories", "ix_actionkit_categories_sort_order"):
        op.create_index("ix_actionkit_categories_sort_order", "actionkit_categories", ["sort_order"], unique=False)
    if not _index_exists(inspector, "actionkit_categories", "ix_actionkit_categories_is_active"):
        op.create_index("ix_actionkit_categories_is_active", "actionkit_categories", ["is_active"], unique=False)

    if not _table_exists(inspector, "actionkit_items"):
        op.create_table(
            "actionkit_items",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("domain", sa.String(), nullable=False),
            sa.Column("category_id", sa.Integer(), sa.ForeignKey("actionkit_categories.id"), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("summary", sa.String(), nullable=False),
            sa.Column("tag", sa.String(), nullable=True),
            sa.Column("ext", sa.String(), nullable=True),
            sa.Column("size_label", sa.String(), nullable=True),
            sa.Column("file_type", sa.String(), nullable=True),
            sa.Column("dday", sa.String(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "actionkit_items", "ix_actionkit_items_domain"):
        op.create_index("ix_actionkit_items_domain", "actionkit_items", ["domain"], unique=False)
    if not _index_exists(inspector, "actionkit_items", "ix_actionkit_items_category_id"):
        op.create_index("ix_actionkit_items_category_id", "actionkit_items", ["category_id"], unique=False)
    if not _index_exists(inspector, "actionkit_items", "ix_actionkit_items_sort_order"):
        op.create_index("ix_actionkit_items_sort_order", "actionkit_items", ["sort_order"], unique=False)
    if not _index_exists(inspector, "actionkit_items", "ix_actionkit_items_is_active"):
        op.create_index("ix_actionkit_items_is_active", "actionkit_items", ["is_active"], unique=False)

    if not _table_exists(inspector, "actionkit_item_highlights"):
        op.create_table(
            "actionkit_item_highlights",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("item_id", sa.Integer(), sa.ForeignKey("actionkit_items.id"), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "actionkit_item_highlights", "ix_actionkit_item_highlights_item_id"):
        op.create_index("ix_actionkit_item_highlights_item_id", "actionkit_item_highlights", ["item_id"], unique=False)
    if not _index_exists(inspector, "actionkit_item_highlights", "ix_actionkit_item_highlights_sort_order"):
        op.create_index("ix_actionkit_item_highlights_sort_order", "actionkit_item_highlights", ["sort_order"], unique=False)

    if not _table_exists(inspector, "actionkit_related_laws"):
        op.create_table(
            "actionkit_related_laws",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("item_id", sa.Integer(), sa.ForeignKey("actionkit_items.id"), nullable=False),
            sa.Column("law_name", sa.String(), nullable=False),
            sa.Column("law_summary", sa.String(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "actionkit_related_laws", "ix_actionkit_related_laws_item_id"):
        op.create_index("ix_actionkit_related_laws_item_id", "actionkit_related_laws", ["item_id"], unique=False)
    if not _index_exists(inspector, "actionkit_related_laws", "ix_actionkit_related_laws_sort_order"):
        op.create_index("ix_actionkit_related_laws_sort_order", "actionkit_related_laws", ["sort_order"], unique=False)

    if not _table_exists(inspector, "actionkit_files"):
        op.create_table(
            "actionkit_files",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("item_id", sa.Integer(), sa.ForeignKey("actionkit_items.id"), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("object_key", sa.String(), nullable=False),
            sa.Column("original_filename", sa.String(), nullable=True),
            sa.Column("mime_type", sa.String(), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("checksum", sa.String(), nullable=True),
            sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("uploaded_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("item_id", "version", name="uq_actionkit_files_item_id_version"),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "actionkit_files", "ix_actionkit_files_item_id"):
        op.create_index("ix_actionkit_files_item_id", "actionkit_files", ["item_id"], unique=False)
    if not _index_exists(inspector, "actionkit_files", "ix_actionkit_files_version"):
        op.create_index("ix_actionkit_files_version", "actionkit_files", ["version"], unique=False)
    if not _index_exists(inspector, "actionkit_files", "ix_actionkit_files_is_current"):
        op.create_index("ix_actionkit_files_is_current", "actionkit_files", ["is_current"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_actionkit_files_is_current", table_name="actionkit_files")
    op.drop_index("ix_actionkit_files_version", table_name="actionkit_files")
    op.drop_index("ix_actionkit_files_item_id", table_name="actionkit_files")
    op.drop_table("actionkit_files")

    op.drop_index("ix_actionkit_related_laws_sort_order", table_name="actionkit_related_laws")
    op.drop_index("ix_actionkit_related_laws_item_id", table_name="actionkit_related_laws")
    op.drop_table("actionkit_related_laws")

    op.drop_index("ix_actionkit_item_highlights_sort_order", table_name="actionkit_item_highlights")
    op.drop_index("ix_actionkit_item_highlights_item_id", table_name="actionkit_item_highlights")
    op.drop_table("actionkit_item_highlights")

    op.drop_index("ix_actionkit_items_is_active", table_name="actionkit_items")
    op.drop_index("ix_actionkit_items_sort_order", table_name="actionkit_items")
    op.drop_index("ix_actionkit_items_category_id", table_name="actionkit_items")
    op.drop_index("ix_actionkit_items_domain", table_name="actionkit_items")
    op.drop_table("actionkit_items")

    op.drop_index("ix_actionkit_categories_is_active", table_name="actionkit_categories")
    op.drop_index("ix_actionkit_categories_sort_order", table_name="actionkit_categories")
    op.drop_index("ix_actionkit_categories_slug", table_name="actionkit_categories")
    op.drop_index("ix_actionkit_categories_domain", table_name="actionkit_categories")
    op.drop_table("actionkit_categories")

