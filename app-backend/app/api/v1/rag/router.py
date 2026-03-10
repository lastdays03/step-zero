from typing import Any

from fastapi import APIRouter, Depends

from app.api.v1.schemas import RagQueryRequest, RagQueryResponse
from app.core.exceptions import RagServiceUnavailableError
from app.features.rag.application.deps import get_rag_service
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
    """Query the RAG pipeline for legal guidance."""
    answer = await service.query(request.question)
    return RagQueryResponse(answer=answer)
