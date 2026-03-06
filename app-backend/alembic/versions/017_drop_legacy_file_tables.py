"""017 Drop legacy file tables

Revision ID: 017_drop_legacy_files
Revises: 016_fk_remap_files
Create Date: 2026-03-06

Changes:
- Drop table `actionkit_files` (replaced by unified `files` table)
- Drop table `growthclubpostattachment` (replaced by unified `files` table)

Note: This is an irreversible migration. The data was already migrated to the
`files` table in Phase A (PR #25). The `userprofile.profile_img` column is
intentionally kept for AuthorRead compatibility.
"""

from alembic import op

revision = "017_drop_legacy_files"
down_revision = "016_fk_remap_files"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("actionkit_files")
    op.drop_table("growthclubpostattachment")


def downgrade() -> None:
    raise NotImplementedError(
        "Irreversible migration: legacy file tables cannot be restored. "
        "Data was migrated to the unified 'files' table."
    )
