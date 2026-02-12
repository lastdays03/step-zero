from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from app.services.rag.service import RagService

router = APIRouter()

class RagQueryRequest(BaseModel):
    question: str

class RagQueryResponse(BaseModel):
    answer: str

@router.post("/query", response_model=RagQueryResponse)
async def query_rag(
    request: RagQueryRequest,
    service: RagService = Depends(lambda: RagService())
) -> Any:
    """
    Query the RAG pipeline for legal guidance.
    """
    try:
        answer = await service.query(request.question)
        return RagQueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
