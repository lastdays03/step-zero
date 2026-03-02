"""012 roadmap chat thread and message tables

Revision ID: 012_roadmap_chat
Revises: 011_template_startup_type
Create Date: 2026-03-02
"""

import sqlalchemy as sa

from alembic import op

revision = "012_roadmap_chat"
down_revision = "011_template_startup_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. roadmap_chat_threads 테이블 생성
    op.create_table(
        "roadmap_chat_threads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("roadmap_id", sa.Uuid(), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["roadmap_id"], ["roadmap.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["step_id"], ["roadmapstep.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_roadmap_chat_threads_roadmap_id",
        "roadmap_chat_threads",
        ["roadmap_id"],
    )
    op.create_index(
        "ix_roadmap_chat_threads_step_id",
        "roadmap_chat_threads",
        ["step_id"],
    )
    op.create_index(
        "ix_roadmap_chat_threads_roadmap_step",
        "roadmap_chat_threads",
        ["roadmap_id", "step_id"],
    )
    op.create_unique_constraint(
        "uq_thread_roadmap_step_user",
        "roadmap_chat_threads",
        ["roadmap_id", "step_id", "user_id"],
    )

    # 2. roadmap_chat_messages 테이블 생성
    op.create_table(
        "roadmap_chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("thread_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.JSON(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["thread_id"], ["roadmap_chat_threads.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_roadmap_chat_messages_thread_id",
        "roadmap_chat_messages",
        ["thread_id"],
    )


def downgrade() -> None:
    # 역순 삭제
    op.drop_index(
        "ix_roadmap_chat_messages_thread_id",
        table_name="roadmap_chat_messages",
    )
    op.drop_table("roadmap_chat_messages")

    op.drop_constraint(
        "uq_thread_roadmap_step_user",
        "roadmap_chat_threads",
        type_="unique",
    )
    op.drop_index(
        "ix_roadmap_chat_threads_roadmap_step",
        table_name="roadmap_chat_threads",
    )
    op.drop_index(
        "ix_roadmap_chat_threads_step_id",
        table_name="roadmap_chat_threads",
    )
    op.drop_index(
        "ix_roadmap_chat_threads_roadmap_id",
        table_name="roadmap_chat_threads",
    )
    op.drop_table("roadmap_chat_threads")
