"""add structured intake fields to roadmap

Revision ID: 20260220_06
Revises: 20260220_05
Create Date: 2026-02-20 23:50:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260220_06"
down_revision = "20260220_05"
branch_labels = None
depends_on = None


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _column_exists(inspector, "roadmap", "startup_type"):
        op.add_column("roadmap", sa.Column("startup_type", sa.String(), nullable=True))
    if not _column_exists(inspector, "roadmap", "open_timeline"):
        op.add_column("roadmap", sa.Column("open_timeline", sa.String(), nullable=True))
    if not _column_exists(inspector, "roadmap", "budget_range"):
        op.add_column("roadmap", sa.Column("budget_range", sa.String(), nullable=True))
    if not _column_exists(inspector, "roadmap", "additional_notes"):
        op.add_column(
            "roadmap",
            sa.Column("additional_notes", sa.String(), nullable=False, server_default=""),
        )
        op.alter_column("roadmap", "additional_notes", server_default=None)

    if _column_exists(inspector, "roadmap", "description") and _column_exists(
        inspector, "roadmap", "additional_notes"
    ):
        op.execute(
            sa.text(
                "UPDATE roadmap SET additional_notes = description "
                "WHERE (additional_notes IS NULL OR additional_notes = '') AND description IS NOT NULL"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _column_exists(inspector, "roadmap", "additional_notes"):
        op.drop_column("roadmap", "additional_notes")
    if _column_exists(inspector, "roadmap", "budget_range"):
        op.drop_column("roadmap", "budget_range")
    if _column_exists(inspector, "roadmap", "open_timeline"):
        op.drop_column("roadmap", "open_timeline")
    if _column_exists(inspector, "roadmap", "startup_type"):
        op.drop_column("roadmap", "startup_type")
