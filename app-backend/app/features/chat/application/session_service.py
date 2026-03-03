"""SessionService — 채팅 세션(스레드) 생명주기 관리.

CRUD + 소유권 검증 + 자동 제목 생성을 담당한다.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.core.logging import get_logger
from app.models.roadmap_chat import RoadmapChatMessage, RoadmapChatThread
from app.repositories.roadmap_chat_repository import RoadmapChatRepository

logger = get_logger(__name__)

# 자동 제목 생성에 사용할 최대 문자 수
_AUTO_TITLE_MAX_LENGTH = 40


class SessionService:
    """채팅 세션 CRUD + 소유권 검증."""

    def __init__(self, chat_repo: RoadmapChatRepository) -> None:
        self._repo = chat_repo

    # ------------------------------------------------------------------ #
    #  생성
    # ------------------------------------------------------------------ #

    async def create_session(
        self,
        *,
        user_id: int,
        roadmap_id: Optional[UUID] = None,
        step_id: Optional[int] = None,
        title: Optional[str] = None,
    ) -> RoadmapChatThread:
        """새 채팅 세션 생성."""
        return await self._repo.create_session(
            user_id=user_id,
            roadmap_id=roadmap_id,
            step_id=step_id,
            title=title,
        )

    # ------------------------------------------------------------------ #
    #  조회
    # ------------------------------------------------------------------ #

    async def list_sessions(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RoadmapChatThread], int]:
        """사용자의 활성 세션 목록 + total count."""
        return await self._repo.list_sessions(
            user_id, limit=limit, offset=offset
        )

    async def get_session(
        self, session_id: UUID, user_id: int
    ) -> RoadmapChatThread:
        """세션 조회 + 소유권 검증."""
        thread = await self._repo.get_thread(session_id)
        self._verify_ownership(thread, user_id)
        return thread  # type: ignore[return-value]

    async def get_messages(
        self,
        session_id: UUID,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RoadmapChatMessage], int]:
        """세션 메시지 조회 + 소유권 검증.

        Returns:
            (messages, total_count)
        """
        thread = await self.get_session(session_id, user_id)
        messages = await self._repo.get_recent_messages(
            session_id, limit=limit, offset=offset
        )
        return messages, thread.message_count

    # ------------------------------------------------------------------ #
    #  수정
    # ------------------------------------------------------------------ #

    async def update_title(
        self, session_id: UUID, user_id: int, title: str
    ) -> RoadmapChatThread:
        """세션 제목 수정 후 갱신된 세션 반환."""
        await self.get_session(session_id, user_id)
        return await self._repo.update_thread_title(session_id, title)

    async def soft_delete(self, session_id: UUID, user_id: int) -> None:
        """세션 소프트 삭제."""
        await self.get_session(session_id, user_id)
        await self._repo.soft_delete_thread(session_id)

    # ------------------------------------------------------------------ #
    #  자동 제목 설정
    # ------------------------------------------------------------------ #

    async def set_auto_title(
        self, session_id: UUID, first_message: str
    ) -> None:
        """첫 메시지 기반 자동 제목 설정.

        소유권 검증 없이 호출 (내부 서비스 전용).
        호출자가 이미 thread.title 없음을 확인한 후 호출해야 한다.
        """
        stripped = first_message.strip()
        title = stripped[:_AUTO_TITLE_MAX_LENGTH]
        if len(stripped) > _AUTO_TITLE_MAX_LENGTH:
            title += "…"
        await self._repo.update_thread_title(session_id, title)

    # ------------------------------------------------------------------ #
    #  내부 헬퍼
    # ------------------------------------------------------------------ #

    @staticmethod
    def _verify_ownership(
        thread: RoadmapChatThread | None, user_id: int
    ) -> None:
        """세션 존재 + 소유권 확인. 실패 시 HTTPException."""
        if thread is None or thread.is_deleted:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        if thread.user_id != user_id:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
