"""chat.application.schemas — 통합 챗봇 요청/응답 스키마."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  요청 스키마
# ------------------------------------------------------------------ #


class ChatStreamRequest(BaseModel):
    """SSE 스트리밍 채팅 요청."""

    message: str = Field(min_length=1, max_length=2000)
    session_id: UUID | None = None
    roadmap_id: UUID | None = None


class SessionCreateRequest(BaseModel):
    """새 세션 생성 요청 (빈 바디)."""

    pass


class SessionUpdateRequest(BaseModel):
    """세션 제목 수정 요청."""

    title: str = Field(min_length=1, max_length=100)


# ------------------------------------------------------------------ #
#  응답 스키마
# ------------------------------------------------------------------ #


class SessionResponse(BaseModel):
    """단일 세션 응답."""

    id: UUID
    title: str | None = None
    message_count: int
    roadmap_id: UUID | None = None
    step_id: int | None = None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    """세션 목록 응답."""

    sessions: list[SessionResponse]
    total: int


class MessageResponse(BaseModel):
    """단일 메시지 응답."""

    id: int
    role: str
    content: str
    sources_json: list[dict] | None = None
    intent_category: str | None = None
    created_at: datetime


class MessageListResponse(BaseModel):
    """메시지 목록 응답."""

    messages: list[MessageResponse]
    total: int
