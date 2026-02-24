from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import ChatRequest, ChatResponse, RagQueryRequest, RagQueryResponse
from app.features.rag.application.deps import get_chat_service, get_rag_service
from app.features.rag.application.chat_service import ChatService
from app.features.rag.application.rag_service import RagService

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
