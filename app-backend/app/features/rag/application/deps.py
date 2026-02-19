from functools import lru_cache

from app.features.rag.application.rag_service import RagService


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService()
