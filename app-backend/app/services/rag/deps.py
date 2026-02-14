from functools import lru_cache

from app.services.rag.service import RagService


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService()
