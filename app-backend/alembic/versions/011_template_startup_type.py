"""011 add startup_type to roadmap_templates

Revision ID: 011_template_startup_type
Revises: 010_roadmap_templates
Create Date: 2026-03-02
"""

import sqlalchemy as sa

from alembic import op

revision = "011_template_startup_type"
down_revision = "010_roadmap_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. startup_type 컬럼 추가
    op.add_column(
        "roadmap_templates",
        sa.Column("startup_type", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_roadmap_templates_startup_type",
        "roadmap_templates",
        ["startup_type"],
    )

    # 2. 기존 복합 인덱스 교체 (2-tier → 3-tier)
    op.drop_index(
        "ix_roadmap_templates_btype_smethod_status",
        table_name="roadmap_templates",
    )
    op.create_index(
        "ix_roadmap_templates_btype_smethod_stype_status",
        "roadmap_templates",
        ["business_type", "startup_method", "startup_type", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_roadmap_templates_btype_smethod_stype_status",
        table_name="roadmap_templates",
    )
    op.create_index(
        "ix_roadmap_templates_btype_smethod_status",
        "roadmap_templates",
        ["business_type", "startup_method", "status"],
    )
    op.drop_index(
        "ix_roadmap_templates_startup_type",
        table_name="roadmap_templates",
    )
    op.drop_column("roadmap_templates", "startup_type")
