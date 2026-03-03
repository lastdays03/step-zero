from typing import Optional
from uuid import UUID

from sqlalchemy import update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import utc_now
from app.models.roadmap_chat import RoadmapChatMessage, RoadmapChatThread


class RoadmapChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_thread(
        self,
        *,
        roadmap_id: UUID,
        step_id: int,
        user_id: int,
    ) -> RoadmapChatThread:
        """기존 스레드 반환 또는 새 스레드 생성 (1 thread per roadmap+step+user).

        UNIQUE constraint 위반 시 (race condition) 기존 스레드를 재조회한다.
        """
        stmt = select(RoadmapChatThread).where(
            RoadmapChatThread.roadmap_id == roadmap_id,
            RoadmapChatThread.step_id == step_id,
            RoadmapChatThread.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        thread = result.scalar_one_or_none()
        if thread:
            return thread

        thread = RoadmapChatThread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        self.session.add(thread)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            result = await self.session.execute(stmt)
            thread = result.scalar_one()
        return thread

    async def get_thread(self, thread_id: UUID) -> RoadmapChatThread | None:
        """스레드 ID로 조회."""
        stmt = select(RoadmapChatThread).where(
            RoadmapChatThread.id == thread_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_threads(
        self,
        roadmap_id: UUID,
        step_id: int,
        user_id: int | None = None,
    ) -> list[RoadmapChatThread]:
        """특정 로드맵 단계의 스레드 목록 (user_id 필터 지원)."""
        stmt = (
            select(RoadmapChatThread)
            .where(
                RoadmapChatThread.roadmap_id == roadmap_id,
                RoadmapChatThread.step_id == step_id,
            )
            .order_by(RoadmapChatThread.updated_at.desc())
        )
        if user_id is not None:
            stmt = stmt.where(RoadmapChatThread.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self,
        *,
        thread_id: UUID,
        role: str,
        content: str,
        sources_json: dict | None = None,
        intent_category: str | None = None,
        token_count: int | None = None,
    ) -> RoadmapChatMessage:
        """메시지 추가 + 스레드 message_count/updated_at 갱신."""
        message = RoadmapChatMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            sources_json=sources_json,
            intent_category=intent_category,
            token_count=token_count,
        )
        self.session.add(message)

        # 스레드 카운터 및 타임스탬프 갱신 (SELECT 없이 UPDATE)
        await self.session.execute(
            sa_update(RoadmapChatThread)
            .where(RoadmapChatThread.id == thread_id)
            .values(
                message_count=RoadmapChatThread.message_count + 1,
                updated_at=utc_now(),
            )
        )

        await self.session.flush()
        return message

    async def get_recent_messages(
        self, thread_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[RoadmapChatMessage]:
        """최근 메시지 조회 (시간순 정렬, offset 기반 역방향 페이지네이션).

        offset=0: 가장 최근 N개 메시지 반환.
        offset=N: 최근 N개를 건너뛴 후 다음 limit개 반환 (오래된 메시지 로드).
        결과는 항상 시간순(오래된 것 먼저) 정렬.
        """
        stmt = (
            select(RoadmapChatMessage)
            .where(RoadmapChatMessage.thread_id == thread_id)
            .order_by(RoadmapChatMessage.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def count_messages(self, thread_id: UUID) -> int:
        """스레드 내 메시지 수 조회."""
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(RoadmapChatMessage)
            .where(RoadmapChatMessage.thread_id == thread_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------ #
    #  세션 관리 확장 메서드 (통합 챗봇용)
    # ------------------------------------------------------------------ #

    async def create_session(
        self,
        *,
        user_id: int,
        roadmap_id: Optional[UUID] = None,
        step_id: Optional[int] = None,
        title: Optional[str] = None,
    ) -> RoadmapChatThread:
        """새 채팅 세션 생성.

        roadmap_id/step_id가 None이면 일반(글로벌) 대화 세션.
        """
        thread = RoadmapChatThread(
            user_id=user_id,
            roadmap_id=roadmap_id,
            step_id=step_id,
            title=title,
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def list_sessions(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RoadmapChatThread], int]:
        """사용자의 활성 세션 목록 (soft delete 제외, 최근 업데이트순).

        Returns:
            (sessions, total_count)
        """
        from sqlalchemy import func

        base_filter = (
            RoadmapChatThread.user_id == user_id,
            RoadmapChatThread.is_deleted == False,  # noqa: E712
        )

        # total count
        count_stmt = (
            select(func.count())
            .select_from(RoadmapChatThread)
            .where(*base_filter)
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # paginated list
        list_stmt = (
            select(RoadmapChatThread)
            .where(*base_filter)
            .order_by(RoadmapChatThread.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        list_result = await self.session.execute(list_stmt)
        sessions = list(list_result.scalars().all())

        return sessions, total

    async def update_thread_title(
        self, thread_id: UUID, title: str
    ) -> RoadmapChatThread:
        """세션 제목 업데이트 후 갱신된 스레드 반환."""
        await self.session.execute(
            sa_update(RoadmapChatThread)
            .where(RoadmapChatThread.id == thread_id)
            .values(
                title=title,
                updated_at=utc_now(),
            )
        )
        await self.session.flush()
        # 갱신된 상태 반환을 위해 재조회
        stmt = select(RoadmapChatThread).where(
            RoadmapChatThread.id == thread_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def soft_delete_thread(self, thread_id: UUID) -> None:
        """세션 소프트 삭제 (is_deleted=True)."""
        await self.session.execute(
            sa_update(RoadmapChatThread)
            .where(RoadmapChatThread.id == thread_id)
            .values(
                is_deleted=True,
                updated_at=utc_now(),
            )
        )
        await self.session.flush()
