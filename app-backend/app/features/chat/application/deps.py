"""chat.application.deps — 통합 챗봇 의존성 팩토리."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.features.chat.application.session_service import SessionService
from app.features.rag.application.deps import get_semantic_router
from app.repositories.roadmap_chat_repository import RoadmapChatRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.features.chat.application.chat_service import ChatService
    from app.features.chat.application.intent_classifier import IntentClassifier

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_intent_classifier() -> IntentClassifier | None:
    """Singleton IntentClassifier; SemanticRouter 없으면 None."""
    from app.features.chat.application.intent_classifier import IntentClassifier

    router = get_semantic_router()
    if router is None:
        logger.warning("IntentClassifier 비활성: SemanticRouter 없음")
        return None
    return IntentClassifier(semantic_router=router)


def get_session_service(session: AsyncSession) -> SessionService:
    """요청 스코프 SessionService 생성."""
    repo = RoadmapChatRepository(session)
    return SessionService(chat_repo=repo)


def get_chat_service(session: AsyncSession) -> "ChatService":
    """요청 스코프 ChatService 생성 (SSE 스트리밍용).

    DB 세션 바인딩 서비스들을 조합하여 ChatService를 구성한다.
    """
    from app.features.chat.application.chat_service import ChatService
    from app.features.rag.application.deps import get_rag_service
    from app.features.roadmaps.application.context_builder import (
        RoadmapContextBuilder,
    )
    from app.repositories.roadmap_repository import RoadmapRepository

    chat_repo = RoadmapChatRepository(session)
    roadmap_repo = RoadmapRepository(session)

    return ChatService(
        session_service=SessionService(chat_repo=chat_repo),
        intent_classifier=get_intent_classifier(),
        chat_repo=chat_repo,
        context_builder=RoadmapContextBuilder(roadmap_repo=roadmap_repo),
        rag_service=get_rag_service(),
        roadmap_repo=roadmap_repo,
    )


def get_chat_stream_deps(session: AsyncSession) -> dict:
    """채팅 스트리밍에 필요한 전체 의존성 조합.

    Returns:
        dict with keys: chat_service, session_service, chat_repo, session
    """
    from app.features.chat.application.chat_service import ChatService
    from app.features.rag.application.deps import get_rag_service
    from app.features.roadmaps.application.context_builder import (
        RoadmapContextBuilder,
    )
    from app.repositories.roadmap_repository import RoadmapRepository

    chat_repo = RoadmapChatRepository(session)
    roadmap_repo = RoadmapRepository(session)
    session_svc = SessionService(chat_repo=chat_repo)

    chat_service = ChatService(
        session_service=session_svc,
        intent_classifier=get_intent_classifier(),
        chat_repo=chat_repo,
        context_builder=RoadmapContextBuilder(roadmap_repo=roadmap_repo),
        rag_service=get_rag_service(),
        roadmap_repo=roadmap_repo,
    )

    return {
        "chat_service": chat_service,
        "session_service": session_svc,
        "intent_classifier": get_intent_classifier(),
        "chat_repo": chat_repo,
        "session": session,
    }
