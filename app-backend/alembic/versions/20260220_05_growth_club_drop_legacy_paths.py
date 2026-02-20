"""drop legacy growth club single-file columns

Revision ID: 20260220_05
Revises: 20260220_04
Create Date: 2026-02-20 16:55:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260220_05"
down_revision = "20260220_04"
branch_labels = None
depends_on = None


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _column_exists(inspector, "growthclubpost", "image_path"):
        op.drop_column("growthclubpost", "image_path")
    if _column_exists(inspector, "growthclubpost", "file_path"):
        op.drop_column("growthclubpost", "file_path")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _column_exists(inspector, "growthclubpost", "image_path"):
        op.add_column("growthclubpost", sa.Column("image_path", sa.String(), nullable=True))
    if not _column_exists(inspector, "growthclubpost", "file_path"):
        op.add_column("growthclubpost", sa.Column("file_path", sa.String(), nullable=True))
