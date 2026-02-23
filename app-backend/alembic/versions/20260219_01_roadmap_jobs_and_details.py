"""roadmap jobs and step details

Revision ID: 20260219_01
Revises: 20260213_01
Create Date: 2026-02-19 15:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260219_01"
down_revision = "20260213_01"
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

    if not _table_exists(inspector, "roadmap_generation_jobs"):
        op.create_table(
            "roadmap_generation_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("team.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("stage", sa.String(), nullable=False, server_default="QUEUED"),
            sa.Column("input_payload", sa.JSON(), nullable=False),
            sa.Column("error_code", sa.String(), nullable=True),
            sa.Column("error_message", sa.String(), nullable=True),
            sa.Column("roadmap_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roadmap.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "roadmap_generation_jobs", "ix_roadmap_generation_jobs_id"):
        op.create_index("ix_roadmap_generation_jobs_id", "roadmap_generation_jobs", ["id"], unique=False)
    if not _index_exists(inspector, "roadmap_generation_jobs", "ix_roadmap_generation_jobs_team_id"):
        op.create_index("ix_roadmap_generation_jobs_team_id", "roadmap_generation_jobs", ["team_id"], unique=False)
    if not _index_exists(inspector, "roadmap_generation_jobs", "ix_roadmap_generation_jobs_user_id"):
        op.create_index("ix_roadmap_generation_jobs_user_id", "roadmap_generation_jobs", ["user_id"], unique=False)
    if not _index_exists(inspector, "roadmap_generation_jobs", "ix_roadmap_generation_jobs_status"):
        op.create_index("ix_roadmap_generation_jobs_status", "roadmap_generation_jobs", ["status"], unique=False)
    if not _index_exists(inspector, "roadmap_generation_jobs", "ix_roadmap_generation_jobs_roadmap_id"):
        op.create_index("ix_roadmap_generation_jobs_roadmap_id", "roadmap_generation_jobs", ["roadmap_id"], unique=False)
    if not _index_exists(inspector, "roadmap_generation_jobs", "ix_roadmap_generation_jobs_created_at"):
        op.create_index("ix_roadmap_generation_jobs_created_at", "roadmap_generation_jobs", ["created_at"], unique=False)

    if not _table_exists(inspector, "roadmap_step_details"):
        op.create_table(
            "roadmap_step_details",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("roadmap_step_id", sa.Integer(), sa.ForeignKey("roadmapstep.id"), nullable=False, unique=True),
            sa.Column("phase", sa.String(), nullable=False, server_default="기본"),
            sa.Column("objective", sa.String(), nullable=False, server_default=""),
            sa.Column("estimated_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("risk_notes", sa.JSON(), nullable=False),
            sa.Column("generation_mode", sa.String(), nullable=False, server_default="RAG"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "roadmap_step_details", "ix_roadmap_step_details_roadmap_step_id"):
        op.create_index("ix_roadmap_step_details_roadmap_step_id", "roadmap_step_details", ["roadmap_step_id"], unique=True)

    if not _table_exists(inspector, "roadmap_step_actions"):
        op.create_table(
            "roadmap_step_actions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("roadmap_step_id", sa.Integer(), sa.ForeignKey("roadmapstep.id"), nullable=False),
            sa.Column("action_type", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False, server_default=""),
            sa.Column("source_url", sa.String(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)

    if not _index_exists(inspector, "roadmap_step_actions", "ix_roadmap_step_actions_roadmap_step_id"):
        op.create_index("ix_roadmap_step_actions_roadmap_step_id", "roadmap_step_actions", ["roadmap_step_id"], unique=False)
    if not _index_exists(inspector, "roadmap_step_actions", "ix_roadmap_step_actions_action_type"):
        op.create_index("ix_roadmap_step_actions_action_type", "roadmap_step_actions", ["action_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_roadmap_step_actions_action_type", table_name="roadmap_step_actions")
    op.drop_index("ix_roadmap_step_actions_roadmap_step_id", table_name="roadmap_step_actions")
    op.drop_table("roadmap_step_actions")

    op.drop_index("ix_roadmap_step_details_roadmap_step_id", table_name="roadmap_step_details")
    op.drop_table("roadmap_step_details")

    op.drop_index("ix_roadmap_generation_jobs_created_at", table_name="roadmap_generation_jobs")
    op.drop_index("ix_roadmap_generation_jobs_roadmap_id", table_name="roadmap_generation_jobs")
    op.drop_index("ix_roadmap_generation_jobs_status", table_name="roadmap_generation_jobs")
    op.drop_index("ix_roadmap_generation_jobs_user_id", table_name="roadmap_generation_jobs")
    op.drop_index("ix_roadmap_generation_jobs_team_id", table_name="roadmap_generation_jobs")
    op.drop_index("ix_roadmap_generation_jobs_id", table_name="roadmap_generation_jobs")
    op.drop_table("roadmap_generation_jobs")
