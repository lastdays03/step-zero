"""010 roadmap template management tables

Revision ID: 010_roadmap_templates
Revises: 009_startup_method
Create Date: 2026-03-02
"""

import sqlalchemy as sa

from alembic import op

revision = "010_roadmap_templates"
down_revision = "009_startup_method"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. roadmap_templates 테이블 생성
    op.create_table(
        "roadmap_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("business_type", sa.String(), nullable=False),
        sa.Column("startup_method", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_roadmap_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["source_roadmap_id"], ["roadmap.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["user.id"]),
    )
    op.create_index("ix_roadmap_templates_business_type", "roadmap_templates", ["business_type"])
    op.create_index("ix_roadmap_templates_startup_method", "roadmap_templates", ["startup_method"])
    op.create_index("ix_roadmap_templates_status", "roadmap_templates", ["status"])
    op.create_index(
        "ix_roadmap_templates_btype_smethod_status",
        "roadmap_templates",
        ["business_type", "startup_method", "status"],
    )

    # 2. roadmap_template_steps 테이블 생성
    op.create_table(
        "roadmap_template_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("objective", sa.String(), nullable=False, server_default=""),
        sa.Column("estimated_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_notes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["template_id"], ["roadmap_templates.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_roadmap_template_steps_template_id", "roadmap_template_steps", ["template_id"])

    # 3. roadmap_template_actions 테이블 생성
    op.create_table(
        "roadmap_template_actions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_step_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("actionkit_item_id", sa.Integer(), nullable=True),
        sa.Column("actionkit_file_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["template_step_id"], ["roadmap_template_steps.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["actionkit_item_id"], ["actionkit_items.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["actionkit_file_id"], ["actionkit_files.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_roadmap_template_actions_template_step_id", "roadmap_template_actions", ["template_step_id"])
    op.create_index("ix_roadmap_template_actions_action_type", "roadmap_template_actions", ["action_type"])

    # 4. roadmap 테이블에 template_id 컬럼 추가
    op.add_column(
        "roadmap",
        sa.Column("template_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_roadmap_template_id",
        "roadmap",
        "roadmap_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_roadmap_template_id", "roadmap", ["template_id"])


def downgrade() -> None:
    # 역순 삭제
    op.drop_index("ix_roadmap_template_id", table_name="roadmap")
    op.drop_constraint("fk_roadmap_template_id", "roadmap", type_="foreignkey")
    op.drop_column("roadmap", "template_id")

    op.drop_index("ix_roadmap_template_actions_action_type", table_name="roadmap_template_actions")
    op.drop_index("ix_roadmap_template_actions_template_step_id", table_name="roadmap_template_actions")
    op.drop_table("roadmap_template_actions")

    op.drop_index("ix_roadmap_template_steps_template_id", table_name="roadmap_template_steps")
    op.drop_table("roadmap_template_steps")

    op.drop_index("ix_roadmap_templates_btype_smethod_status", table_name="roadmap_templates")
    op.drop_index("ix_roadmap_templates_status", table_name="roadmap_templates")
    op.drop_index("ix_roadmap_templates_startup_method", table_name="roadmap_templates")
    op.drop_index("ix_roadmap_templates_business_type", table_name="roadmap_templates")
    op.drop_table("roadmap_templates")
