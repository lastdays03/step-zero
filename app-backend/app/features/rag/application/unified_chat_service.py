"""UnifiedChatService: 글로벌 챗봇 + AI 코치를 통합하는 디스패처 서비스.

roadmap_id + step_id 유무에 따라:
- 있으면 → RoadmapChatService (AI 코치) 위임
- 없으면 → ChatService (글로벌 챗봇) 위임
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator
from uuid import UUID

from app.core.logging import get_logger
from app.features.rag.application.chat_service import _sse_event
from app.repositories.roadmap_chat_repository import RoadmapChatRepository
from app.repositories.roadmap_repository import RoadmapRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.features.rag.application.chat_service import ChatService
    from app.features.roadmaps.application.roadmap_chat_service import (
        RoadmapChatService,
    )

logger = get_logger(__name__)


class UnifiedChatService:
    """글로벌 챗봇과 AI 코치를 통합하는 디스패처."""

    def __init__(
        self,
        chat_service: ChatService,
        roadmap_chat_service: RoadmapChatService,
        chat_repo: RoadmapChatRepository,
        session: AsyncSession,
    ):
        self.chat_service = chat_service
        self.roadmap_chat_service = roadmap_chat_service
        self.chat_repo = chat_repo
        self.session = session

    async def stream(
        self,
        *,
        message: str,
        user_id: int,
        team_id: UUID,
        roadmap_id: UUID | None = None,
        step_id: int | None = None,
        thread_id: UUID | None = None,
    ) -> AsyncGenerator[str, None]:
        """통합 SSE 스트리밍.

        roadmap_id + step_id → AI 코치 모드 (RoadmapChatService 위임)
        그 외 → 글로벌 챗봇 모드 (ChatService.stream() 위임)
        """
        if roadmap_id is not None and step_id is not None:
            async for event in self._stream_coach(
                message=message,
                user_id=user_id,
                team_id=team_id,
                roadmap_id=roadmap_id,
                step_id=step_id,
                thread_id=thread_id,
            ):
                yield event
        else:
            async for event in self.chat_service.stream(message):
                yield event

    async def _stream_coach(
        self,
        *,
        message: str,
        user_id: int,
        team_id: UUID,
        roadmap_id: UUID,
        step_id: int,
        thread_id: UUID | None,
    ) -> AsyncGenerator[str, None]:
        """AI 코치 모드: 로드맵 검증 후 RoadmapChatService에 위임."""
        repo = RoadmapRepository(self.session)

        # 로드맵 소유권 검증
        roadmap = await repo.get_by_id_for_team(roadmap_id, team_id)
        if not roadmap:
            yield _sse_event("error", {
                "code": "NOT_FOUND",
                "message": "로드맵을 찾을 수 없습니다.",
            })
            return

        # 스텝 조회 + 소유권 검증
        step = await repo.get_step_for_team(step_id, team_id)
        if not step or step.roadmap_id != roadmap.id:
            yield _sse_event("error", {
                "code": "NOT_FOUND",
                "message": "로드맵 단계를 찾을 수 없습니다.",
            })
            return

        # 스레드 가져오기 또는 생성
        if thread_id:
            thread = await self.chat_repo.get_thread(thread_id)
            if not thread or thread.user_id != user_id:
                yield _sse_event("error", {
                    "code": "NOT_FOUND",
                    "message": "스레드를 찾을 수 없습니다.",
                })
                return
        else:
            thread = await self.chat_repo.get_or_create_thread(
                roadmap_id=roadmap.id,
                step_id=step.id,
                user_id=user_id,
            )

        # RoadmapChatService에 위임
        async for event in self.roadmap_chat_service.stream(
            roadmap=roadmap,
            step=step,
            thread=thread,
            user_message=message,
            session=self.session,
        ):
            yield event
