"""016 FK remap actionkit_file_id → files table

Revision ID: 016_fk_remap_files
Revises: 015_goal_horizon
Create Date: 2026-03-06

Changes:
- Drop FK from roadmap_template_actions.actionkit_file_id → actionkit_files.id
- Create FK from roadmap_template_actions.actionkit_file_id → files.id
- Drop temporary _file_id_mapping table (created by migrate_files_table.py)
"""

import sqlalchemy as sa

from alembic import op

revision = "016_fk_remap_files"
down_revision = "015_goal_horizon"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "roadmap_template_actions_actionkit_file_id_fkey",
        "roadmap_template_actions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "roadmap_template_actions_actionkit_file_id_fkey",
        "roadmap_template_actions",
        "files",
        ["actionkit_file_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("DROP TABLE IF EXISTS _file_id_mapping")


def downgrade() -> None:
    op.drop_constraint(
        "roadmap_template_actions_actionkit_file_id_fkey",
        "roadmap_template_actions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "roadmap_template_actions_actionkit_file_id_fkey",
        "roadmap_template_actions",
        "actionkit_files",
        ["actionkit_file_id"],
        ["id"],
        ondelete="SET NULL",
    )
