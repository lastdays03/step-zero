from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import RagQueryRequest, RagQueryResponse
from app.features.rag.application.deps import get_rag_service
from app.features.rag.application.rag_service import RagService

router = APIRouter()

@router.post("/query", response_model=RagQueryResponse)
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
