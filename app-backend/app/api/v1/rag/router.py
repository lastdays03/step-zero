from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.schemas import (
    ChatRequest,
    ChatResponse,
    RagQueryRequest,
    RagQueryResponse,
    UnifiedChatRequest,
)
from app.core.db import get_session
from app.features.rag.application.chat_service import ChatService
from app.features.rag.application.deps import (
    get_chat_service,
    get_rag_service,
    get_unified_chat_service,
)
from app.features.rag.application.rag_service import RagService
from app.models.team import Team
from app.models.user import AuthenticatedUser

router = APIRouter()


@router.post(
    "/query",
    response_model=RagQueryResponse,
    summary="법률 가이드 질의",
    description="RAG 파이프라인에 질문을 전달해 법률/행정 가이드를 생성합니다.",
    response_description="질문에 대한 생성 답변을 반환합니다.",
)
async def query_rag(
    request: RagQueryRequest,
    service: RagService = Depends(get_rag_service),
) -> Any:
    """
    Query the RAG pipeline for legal guidance.
    """
    try:
        answer = await service.query(request.question)
        return RagQueryResponse(answer=answer)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service unavailable",
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="하이브리드 AI 챗",
    description="법률 질문은 RAG, 일반 질문은 LLM 직접 응답합니다.",
)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> Any:
    try:
        answer, source = await service.chat(request.message)
        return ChatResponse(answer=answer, source=source)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service unavailable",
        )


@router.post(
    "/chat/stream",
    summary="통합 AI 챗 SSE 스트리밍",
    description="글로벌 챗봇과 AI 코치를 통합하는 SSE 스트리밍 엔드포인트. "
    "roadmap_id + step_id를 함께 보내면 AI 코치 모드, 없으면 글로벌 챗봇 모드.",
    response_description="text/event-stream SSE 응답",
)
async def unified_chat_stream(
    request: UnifiedChatRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    service = get_unified_chat_service(session)

    return StreamingResponse(
        service.stream(
            message=request.message,
            user_id=current_user.id,
            team_id=current_team.id,
            roadmap_id=request.roadmap_id,
            step_id=request.step_id,
            thread_id=request.thread_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
