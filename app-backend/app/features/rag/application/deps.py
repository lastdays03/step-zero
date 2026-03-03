from __future__ import annotations

from functools import lru_cache

from app.features.rag.application.rag_service import RagService


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService()


def _get_embeddings():
    """Reuse the embeddings instance from RagService if available."""
    rag = get_rag_service()
    if rag.ready and hasattr(rag, "embeddings"):
        return rag.embeddings

    # Fallback: create standalone embeddings (e.g. when RAG DB is unavailable)
    from langchain_openai import OpenAIEmbeddings

    from app.core.config import get_settings

    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return None
    return OpenAIEmbeddings(
        model=settings.OPENAI_EMBED_MODEL,
        api_key=settings.OPENAI_API_KEY,
    )


@lru_cache(maxsize=1)
def get_semantic_router():
    """Singleton SemanticRouter; returns None when embeddings are unavailable."""
    from app.features.rag.application.semantic_router import SemanticRouter

    embeddings = _get_embeddings()
    if embeddings is None:
        return None
    return SemanticRouter(embeddings=embeddings)
