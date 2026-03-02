"""Dependency injection singletons for roadmap generation."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.features.rag.application.deps import get_rag_service, get_semantic_router
from app.features.roadmaps.application.actionkit_matcher import ActionKitMatcher
from app.features.roadmaps.application.context_builder import RoadmapContextBuilder
from app.features.roadmaps.application.llm_personalizer import LLMPersonalizer
from app.features.roadmaps.application.roadmap_chat_service import RoadmapChatService
from app.repositories.roadmap_chat_repository import RoadmapChatRepository
from app.repositories.roadmap_repository import RoadmapRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_actionkit_matcher() -> ActionKitMatcher:
    return ActionKitMatcher(rag_service=get_rag_service())


@lru_cache(maxsize=1)
def get_llm_personalizer() -> LLMPersonalizer:
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.OPENAI_CHAT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        timeout=30,
        max_retries=2,
    )
    return LLMPersonalizer(llm=llm)


def get_roadmap_chat_service(session: AsyncSession) -> RoadmapChatService:
    """세션 바인딩 RoadmapChatService 생성 (요청 스코프)."""
    roadmap_repo = RoadmapRepository(session)
    context_builder = RoadmapContextBuilder(roadmap_repo)
    chat_repo = RoadmapChatRepository(session)

    semantic_router = None
    try:
        semantic_router = get_semantic_router()
    except Exception:
        logger.warning("SemanticRouter 로드 실패, 범위 분류 없이 동작")

    return RoadmapChatService(
        context_builder=context_builder,
        semantic_router=semantic_router,
        chat_repo=chat_repo,
    )
