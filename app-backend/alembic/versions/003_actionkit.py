"""003 actionkit: categories, items, highlights, laws, files

Revision ID: 003_actionkit
Revises: 002_roadmap
Create Date: 2026-02-25
"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision = "003_actionkit"
down_revision = "002_roadmap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- actionkit_categories --
    op.create_table(
        "actionkit_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_actionkit_categories_domain", "actionkit_categories", ["domain"]
    )
    op.create_index("ix_actionkit_categories_slug", "actionkit_categories", ["slug"])
    op.create_index(
        "ix_actionkit_categories_sort_order", "actionkit_categories", ["sort_order"]
    )
    op.create_index(
        "ix_actionkit_categories_is_active", "actionkit_categories", ["is_active"]
    )

    # -- actionkit_items --
    op.create_table(
        "actionkit_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("summary", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("tag", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("ext", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("size_label", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("file_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("dday", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["actionkit_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_actionkit_items_domain", "actionkit_items", ["domain"])
    op.create_index(
        "ix_actionkit_items_category_id", "actionkit_items", ["category_id"]
    )
    op.create_index("ix_actionkit_items_sort_order", "actionkit_items", ["sort_order"])
    op.create_index("ix_actionkit_items_is_active", "actionkit_items", ["is_active"])

    # -- actionkit_item_highlights --
    op.create_table(
        "actionkit_item_highlights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["actionkit_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_actionkit_item_highlights_item_id", "actionkit_item_highlights", ["item_id"]
    )
    op.create_index(
        "ix_actionkit_item_highlights_sort_order",
        "actionkit_item_highlights",
        ["sort_order"],
    )

    # -- actionkit_related_laws --
    op.create_table(
        "actionkit_related_laws",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("law_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("law_summary", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["actionkit_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_actionkit_related_laws_item_id", "actionkit_related_laws", ["item_id"]
    )
    op.create_index(
        "ix_actionkit_related_laws_sort_order", "actionkit_related_laws", ["sort_order"]
    )

    # -- actionkit_files --
    op.create_table(
        "actionkit_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("object_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "original_filename", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("mime_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("checksum", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["actionkit_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_actionkit_files_item_id", "actionkit_files", ["item_id"])
    op.create_index("ix_actionkit_files_version", "actionkit_files", ["version"])
    op.create_index("ix_actionkit_files_is_current", "actionkit_files", ["is_current"])


def downgrade() -> None:
    op.drop_table("actionkit_files")
    op.drop_table("actionkit_related_laws")
    op.drop_table("actionkit_item_highlights")
    op.drop_table("actionkit_items")
    op.drop_table("actionkit_categories")
