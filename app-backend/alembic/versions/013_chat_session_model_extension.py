"""013 chat session model extension

Revision ID: 013_chat_session_ext
Revises: 012_roadmap_chat
Create Date: 2026-03-03

Changes:
- roadmap_chat_threads.roadmap_id: NOT NULL → NULLABLE
- roadmap_chat_threads.step_id: NOT NULL → NULLABLE
- roadmap_chat_threads: add is_deleted column (Boolean, default false)
- roadmap_chat_threads: drop uq_thread_roadmap_step_user unique constraint
- roadmap_chat_messages: add intent_category column (String(20), nullable)
"""

import sqlalchemy as sa

from alembic import op

revision = "013_chat_session_ext"
down_revision = "012_roadmap_chat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. roadmap_id nullable 변경
    op.alter_column(
        "roadmap_chat_threads",
        "roadmap_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

    # 2. step_id nullable 변경
    op.alter_column(
        "roadmap_chat_threads",
        "step_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # 3. is_deleted 컬럼 추가
    op.add_column(
        "roadmap_chat_threads",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )

    # 4. UNIQUE 제약 제거 (일반 대화는 roadmap/step 없이 생성 가능)
    op.drop_constraint(
        "uq_thread_roadmap_step_user",
        "roadmap_chat_threads",
        type_="unique",
    )

    # 5. intent_category 컬럼 추가
    op.add_column(
        "roadmap_chat_messages",
        sa.Column("intent_category", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    # 5. intent_category 컬럼 삭제
    op.drop_column("roadmap_chat_messages", "intent_category")

    # 4. UNIQUE 제약 복원
    op.create_unique_constraint(
        "uq_thread_roadmap_step_user",
        "roadmap_chat_threads",
        ["roadmap_id", "step_id", "user_id"],
    )

    # 3. is_deleted 컬럼 삭제
    op.drop_column("roadmap_chat_threads", "is_deleted")

    # 2. step_id NOT NULL 복원
    op.alter_column(
        "roadmap_chat_threads",
        "step_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # 1. roadmap_id NOT NULL 복원
    op.alter_column(
        "roadmap_chat_threads",
        "roadmap_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
