"""004 growth_club: posts, comments, likes, attachments, reports, tags

Revision ID: 004_growth_club
Revises: 003_actionkit
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

revision = "004_growth_club"
down_revision = "003_actionkit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- growthclubtag (tags first, referenced by link table) --
    op.create_table(
        "growthclubtag",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growthclubtag_name", "growthclubtag", ["name"], unique=True)

    # -- growthclubpost --
    op.create_table(
        "growthclubpost",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("neighborhood", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("industry", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_blinded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- growthclubcomment --
    op.create_table(
        "growthclubcomment",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_blinded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["growthclubcomment.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- growthclubpostlike --
    op.create_table(
        "growthclubpostlike",
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("post_id", "user_id"),
    )

    # -- growthclubpostattachment --
    op.create_table(
        "growthclubpostattachment",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("kind", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="file"),
        sa.Column("object_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("original_filename", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("mime_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growthclubpostattachment_post_id", "growthclubpostattachment", ["post_id"])
    op.create_index("ix_growthclubpostattachment_kind", "growthclubpostattachment", ["kind"])

    # -- growthclubpostreport --
    op.create_table(
        "growthclubpostreport",
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("post_id", "user_id"),
    )

    # -- growthclubposttaglink --
    op.create_table(
        "growthclubposttaglink",
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["growthclubtag.id"]),
        sa.PrimaryKeyConstraint("post_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("growthclubposttaglink")
    op.drop_table("growthclubpostreport")
    op.drop_table("growthclubpostattachment")
    op.drop_table("growthclubpostlike")
    op.drop_table("growthclubcomment")
    op.drop_table("growthclubpost")
    op.drop_table("growthclubtag")
