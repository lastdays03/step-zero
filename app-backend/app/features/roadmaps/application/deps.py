"""Dependency injection singletons for roadmap generation."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.features.rag.application.deps import get_rag_service
from app.features.roadmaps.application.actionkit_matcher import ActionKitMatcher
from app.features.roadmaps.application.llm_personalizer import LLMPersonalizer

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
