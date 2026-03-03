from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, String
from sqlmodel import Field, SQLModel


class RoadmapChatThread(SQLModel, table=True):
    """AI 코치 채팅 스레드.

    roadmap_id/step_id가 NULL이면 일반(글로벌) 대화,
    값이 있으면 로드맵 단계별 컨텍스트 대화.
    """

    __tablename__ = "roadmap_chat_threads"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    roadmap_id: Optional[UUID] = Field(
        default=None,
        foreign_key="roadmap.id",
        index=True,
        ondelete="CASCADE",
        nullable=True,
    )
    step_id: Optional[int] = Field(
        default=None,
        foreign_key="roadmapstep.id",
        index=True,
        ondelete="CASCADE",
        nullable=True,
    )
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    title: str | None = None  # 자동 요약 (향후)
    message_count: int = Field(default=0)
    is_deleted: bool = Field(
        sa_column=Column(Boolean, default=False, server_default="false", nullable=False)
    )
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
    sources_json: list[dict] | None = Field(
        default=None, sa_column=sa.Column(sa.JSON, nullable=True)
    )
    intent_category: str | None = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )
    token_count: int | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
