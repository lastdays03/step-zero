"""014 files table

Revision ID: 014_files_table
Revises: 013_chat_session_ext
Create Date: 2026-03-06

Changes:
- Create files table for unified file metadata storage (R2 migration)
- Indexes: owner_type, owner_id, version, is_current, kind
- Composite indexes: (owner_type, owner_id), (owner_type, owner_id, is_current)
"""

import sqlalchemy as sa

from alembic import op

revision = "014_files_table"
down_revision = "013_chat_session_ext"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_type", sa.String(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False, server_default="document"),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=True),
        sa.Column("kind", sa.String(), nullable=True),
        sa.Column("metadata_extra", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index("ix_files_owner_type", "files", ["owner_type"])
    op.create_index("ix_files_owner_id", "files", ["owner_id"])
    op.create_index("ix_files_version", "files", ["version"])
    op.create_index("ix_files_is_current", "files", ["is_current"])
    op.create_index("ix_files_kind", "files", ["kind"])
    op.create_index(
        "ix_files_owner_type_owner_id", "files", ["owner_type", "owner_id"]
    )
    op.create_index(
        "ix_files_owner_type_owner_id_is_current",
        "files",
        ["owner_type", "owner_id", "is_current"],
    )


def downgrade() -> None:
    op.drop_table("files")
