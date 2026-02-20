"""add user profile table

Revision ID: 20260220_01
Revises: 20260219_01
Create Date: 2026-02-20 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260220_01"
down_revision = "20260219_01"
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

    if not _table_exists(inspector, "userprofile"):
        op.create_table(
            "userprofile",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, unique=True),
            sa.Column("nickname", sa.String(), nullable=True),
            sa.Column("profile_img", sa.String(), nullable=True, server_default="default.png"),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("category", sa.String(), nullable=True),
            sa.Column("region", sa.String(), nullable=True),
            sa.Column("philosophy", sa.String(), nullable=True),
            sa.Column("experiences", sa.JSON(), nullable=False),
            sa.Column("awards", sa.JSON(), nullable=False),
            sa.Column("certificates", sa.JSON(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "userprofile", "ix_userprofile_user_id"):
        op.create_index("ix_userprofile_user_id", "userprofile", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_userprofile_user_id", table_name="userprofile")
    op.drop_table("userprofile")

