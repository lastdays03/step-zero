"""AI 코치 채팅 SSE 라우터.

로드맵 단계별 AI 코치와의 실시간 스트리밍 채팅 엔드포인트.
- POST /{roadmap_id}/steps/{step_id}/chat/stream — SSE 스트리밍 채팅
- GET  /{roadmap_id}/steps/{step_id}/chat/threads — 대화 스레드 목록
- GET  /{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages — 메시지 조회
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.schemas import (
    ChatMessageResponse,
    StepChatRequest,
    ThreadSummary,
)
from app.core.db import get_session
from app.core.logging import get_logger
from app.features.roadmaps.application.deps import get_roadmap_chat_service
from app.models.team import Team
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_chat_repository import RoadmapChatRepository
from app.repositories.roadmap_repository import RoadmapRepository

logger = get_logger(__name__)

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────
# 공통 검증 헬퍼
# ──────────────────────────────────────────────────────────────────────


async def _validate_roadmap_and_step(
    *,
    roadmap_id: UUID,
    step_id: int,
    team: Team,
    session: AsyncSession,
    require_active: bool = False,
):
    """로드맵 소유권 + 단계 존재 + (선택) 활성 상태 검증.

    Returns: (roadmap, step) 튜플
    """
    repo = RoadmapRepository(session)

    roadmap = await repo.get_by_id_for_team(roadmap_id, team.id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    step = await repo.get_step_for_team(step_id, team.id)
    if not step or step.roadmap_id != roadmap.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    if require_active and step.status not in ("IN_PROGRESS", "COMPLETED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat is only available for IN_PROGRESS or COMPLETED steps",
        )

    return roadmap, step


# ──────────────────────────────────────────────────────────────────────
# 1. SSE 스트리밍 채팅
# ──────────────────────────────────────────────────────────────────────


@router.post(
    "/{roadmap_id}/steps/{step_id}/chat/stream",
    summary="AI 코치 SSE 스트리밍 채팅",
    description="로드맵 단계 컨텍스트 기반 AI 코치와 실시간 SSE 스트리밍 대화.",
    response_description="text/event-stream SSE 응답",
)
async def step_chat_stream(
    request: StepChatRequest,
    roadmap_id: UUID = Path(..., description="로드맵 ID"),
    step_id: int = Path(..., description="로드맵 단계 ID"),
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    # 로드맵 + 단계 검증 (IN_PROGRESS 또는 COMPLETED만 허용)
    roadmap, step = await _validate_roadmap_and_step(
        roadmap_id=roadmap_id,
        step_id=step_id,
        team=current_team,
        session=session,
        require_active=True,
    )

    # 스레드 가져오기 또는 생성
    chat_repo = RoadmapChatRepository(session)
    if request.thread_id:
        thread = await chat_repo.get_thread(request.thread_id)
        if not thread or thread.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found",
            )
    else:
        thread = await chat_repo.get_or_create_thread(
            roadmap_id=roadmap.id,
            step_id=step.id,
            user_id=current_user.id,
        )

    # ChatService 생성 + 스트리밍
    chat_service = get_roadmap_chat_service(session)

    return StreamingResponse(
        chat_service.stream(
            roadmap=roadmap,
            step=step,
            thread=thread,
            user_message=request.message,
            session=session,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ──────────────────────────────────────────────────────────────────────
# 2. 대화 스레드 목록 조회
# ──────────────────────────────────────────────────────────────────────


@router.get(
    "/{roadmap_id}/steps/{step_id}/chat/threads",
    response_model=list[ThreadSummary],
    summary="대화 스레드 목록 조회",
    description="특정 로드맵 단계의 채팅 스레드 목록을 반환합니다.",
)
async def list_chat_threads(
    roadmap_id: UUID = Path(..., description="로드맵 ID"),
    step_id: int = Path(..., description="로드맵 단계 ID"),
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    await _validate_roadmap_and_step(
        roadmap_id=roadmap_id,
        step_id=step_id,
        team=current_team,
        session=session,
    )

    chat_repo = RoadmapChatRepository(session)
    threads = await chat_repo.list_threads(
        roadmap_id, step_id, user_id=current_user.id
    )

    return [
        ThreadSummary(
            thread_id=t.id,
            message_count=t.message_count,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
        )
        for t in threads
    ]


# ──────────────────────────────────────────────────────────────────────
# 3. 스레드 메시지 조회
# ──────────────────────────────────────────────────────────────────────


@router.get(
    "/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
    response_model=list[ChatMessageResponse],
    summary="스레드 메시지 조회",
    description="특정 스레드의 메시지 목록을 반환합니다.",
)
async def get_thread_messages(
    roadmap_id: UUID = Path(..., description="로드맵 ID"),
    step_id: int = Path(..., description="로드맵 단계 ID"),
    thread_id: UUID = Path(..., description="스레드 ID"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    limit: int = Query(20, ge=1, le=100, description="조회 개수"),
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    await _validate_roadmap_and_step(
        roadmap_id=roadmap_id,
        step_id=step_id,
        team=current_team,
        session=session,
    )

    # 스레드 소유권 검증
    chat_repo = RoadmapChatRepository(session)
    thread = await chat_repo.get_thread(thread_id)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    messages = await chat_repo.get_recent_messages(
        thread_id, limit=limit, offset=offset
    )

    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=m.sources_json if m.sources_json else None,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]
