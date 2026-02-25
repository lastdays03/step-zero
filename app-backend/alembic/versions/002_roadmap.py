"""002 roadmap: roadmap, roadmapstep, jobs, details, actions

Revision ID: 002_roadmap
Revises: 001_core
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

revision = "002_roadmap"
down_revision = "001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- roadmap --
    op.create_table(
        "roadmap",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("business_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("location", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
        sa.Column("startup_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("open_timeline", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("budget_range", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("additional_notes", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmap_id", "roadmap", ["id"])
    op.create_index("ix_roadmap_team_id", "roadmap", ["team_id"])
    op.create_index("ix_roadmap_created_at", "roadmap", ["created_at"])

    # -- roadmapstep --
    op.create_table(
        "roadmapstep",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("roadmap_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmap.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmapstep_roadmap_id", "roadmapstep", ["roadmap_id"])
    op.create_index("ix_roadmapstep_step_order", "roadmapstep", ["step_order"])

    # -- roadmap_generation_jobs --
    op.create_table(
        "roadmap_generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="QUEUED"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stage", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="QUEUED"),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("error_code", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("roadmap_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmap.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmap_generation_jobs_id", "roadmap_generation_jobs", ["id"])
    op.create_index("ix_roadmap_generation_jobs_team_id", "roadmap_generation_jobs", ["team_id"])
    op.create_index("ix_roadmap_generation_jobs_user_id", "roadmap_generation_jobs", ["user_id"])
    op.create_index("ix_roadmap_generation_jobs_status", "roadmap_generation_jobs", ["status"])
    op.create_index("ix_roadmap_generation_jobs_roadmap_id", "roadmap_generation_jobs", ["roadmap_id"])
    op.create_index("ix_roadmap_generation_jobs_created_at", "roadmap_generation_jobs", ["created_at"])

    # -- roadmap_step_details --
    op.create_table(
        "roadmap_step_details",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("roadmap_step_id", sa.Integer(), nullable=False),
        sa.Column("phase", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="기본"),
        sa.Column("objective", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
        sa.Column("estimated_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_notes", sa.JSON(), nullable=False),
        sa.Column("generation_mode", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="RAG"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["roadmap_step_id"], ["roadmapstep.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmap_step_details_roadmap_step_id", "roadmap_step_details", ["roadmap_step_id"], unique=True)

    # -- roadmap_step_actions --
    op.create_table(
        "roadmap_step_actions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("roadmap_step_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
        sa.Column("source_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["roadmap_step_id"], ["roadmapstep.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmap_step_actions_roadmap_step_id", "roadmap_step_actions", ["roadmap_step_id"])
    op.create_index("ix_roadmap_step_actions_action_type", "roadmap_step_actions", ["action_type"])


def downgrade() -> None:
    op.drop_table("roadmap_step_actions")
    op.drop_table("roadmap_step_details")
    op.drop_table("roadmap_generation_jobs")
    op.drop_table("roadmapstep")
    op.drop_table("roadmap")
