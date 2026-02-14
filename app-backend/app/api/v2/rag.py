from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v2.schemas import RagQueryRequest, RagQueryResponse
from app.services.rag.deps import get_rag_service
from app.services.rag.service import RagService

router = APIRouter()


@router.post("/query", response_model=RagQueryResponse)
async def query_rag(
    request: RagQueryRequest,
    service: RagService = Depends(get_rag_service),
) -> Any:
    try:
        answer = await service.query(request.question)
        return RagQueryResponse(answer=answer)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service unavailable",
        )
