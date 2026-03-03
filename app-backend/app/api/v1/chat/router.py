"""통합 챗봇 API 라우터.

엔드포인트:
- POST /stream          — SSE 스트리밍 채팅
- GET  /sessions        — 세션 목록
- POST /sessions        — 새 세션 생성
- GET  /sessions/{id}/messages — 메시지 조회
- PATCH /sessions/{id}  — 제목 변경
- DELETE /sessions/{id} — 소프트 삭제
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.db import get_session
from app.features.chat.application.deps import get_chat_service, get_session_service
from app.features.chat.application.schemas import (
    ChatStreamRequest,
    MessageListResponse,
    MessageResponse,
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
    SessionUpdateRequest,
)
from app.models.team import Team
from app.models.user import AuthenticatedUser

router = APIRouter()


# ------------------------------------------------------------------ #
#  SSE 스트리밍 채팅
# ------------------------------------------------------------------ #


@router.post(
    "/stream",
    summary="통합 AI 챗 SSE 스트리밍",
    description="StepZero AI 통합 챗봇 SSE 스트리밍. "
    "session_id가 없으면 새 세션 자동 생성.",
    response_description="text/event-stream SSE 응답",
)
async def chat_stream(
    request: ChatStreamRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    service = get_chat_service(session)

    async def _stream_and_commit():
        async for event in service.stream(
            request.message,
            session_id=request.session_id,
            user_id=current_user.id,
            team_id=current_team.id,
            roadmap_id=request.roadmap_id,
        ):
            yield event
        await session.commit()

    return StreamingResponse(
        _stream_and_commit(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ------------------------------------------------------------------ #
#  세션 CRUD
# ------------------------------------------------------------------ #


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="세션 목록 조회",
)
async def list_sessions(
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SessionListResponse:
    svc = get_session_service(session)
    sessions, total = await svc.list_sessions(
        current_user.id, limit=limit, offset=offset
    )
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=t.id,
                title=t.title,
                message_count=t.message_count,
                roadmap_id=t.roadmap_id,
                step_id=t.step_id,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in sessions
        ],
        total=total,
    )


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 세션 생성",
)
async def create_session(
    _body: SessionCreateRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SessionResponse:
    svc = get_session_service(session)
    thread = await svc.create_session(user_id=current_user.id)
    await session.commit()
    return SessionResponse(
        id=thread.id,
        title=thread.title,
        message_count=thread.message_count,
        roadmap_id=thread.roadmap_id,
        step_id=thread.step_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=MessageListResponse,
    summary="세션 메시지 조회",
)
async def get_session_messages(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> MessageListResponse:
    svc = get_session_service(session)
    messages, total = await svc.get_messages(
        session_id, current_user.id, limit=limit, offset=offset
    )
    return MessageListResponse(
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources_json=m.sources_json,
                intent_category=m.intent_category,
                created_at=m.created_at,
            )
            for m in messages
        ],
        total=total,
    )


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="세션 제목 변경",
)
async def update_session_title(
    session_id: UUID,
    body: SessionUpdateRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SessionResponse:
    svc = get_session_service(session)
    thread = await svc.update_title(session_id, current_user.id, body.title)
    await session.commit()
    return SessionResponse(
        id=thread.id,
        title=thread.title,
        message_count=thread.message_count,
        roadmap_id=thread.roadmap_id,
        step_id=thread.step_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="세션 삭제 (소프트)",
)
async def delete_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    svc = get_session_service(session)
    await svc.soft_delete(session_id, current_user.id)
    await session.commit()
