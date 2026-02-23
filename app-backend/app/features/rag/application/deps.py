from functools import lru_cache

from app.features.rag.application.rag_service import RagService
from app.features.rag.application.chat_service import ChatService


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService()


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService(get_rag_service())
