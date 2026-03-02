from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class RoadmapChatThread(SQLModel, table=True):
    """로드맵 단계별 AI 코치 채팅 스레드.

    1 Thread per (roadmap, step, user) — 단계별 컨텍스트 격리.
    """

    __tablename__ = "roadmap_chat_threads"
    __table_args__ = (
        Index(
            "ix_roadmap_chat_threads_roadmap_step",
            "roadmap_id",
            "step_id",
        ),
        UniqueConstraint(
            "roadmap_id",
            "step_id",
            "user_id",
            name="uq_thread_roadmap_step_user",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    roadmap_id: UUID = Field(
        foreign_key="roadmap.id", index=True, ondelete="CASCADE"
    )
    step_id: int = Field(
        foreign_key="roadmapstep.id", index=True, ondelete="CASCADE"
    )
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    title: str | None = None  # 자동 요약 (향후)
    message_count: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class RoadmapChatMessage(SQLModel, table=True):
    """AI 코치 채팅 메시지 (user / assistant / system)."""

    __tablename__ = "roadmap_chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: UUID = Field(
        foreign_key="roadmap_chat_threads.id", index=True, ondelete="CASCADE"
    )
    role: str  # "user" | "assistant" | "system"
    content: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    sources_json: dict | None = Field(
        default=None, sa_column=sa.Column(sa.JSON, nullable=True)
    )
    token_count: int | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
