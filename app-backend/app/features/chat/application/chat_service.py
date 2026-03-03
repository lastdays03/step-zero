"""ChatService — 통합 StepZero AI 챗봇 SSE 스트리밍 서비스.

의도 분류 기반 5카테고리 분기 + SSE 스트리밍 응답 생성.

카테고리별 처리:
- current_step / other_step → ContextBuilder + LLM astream
- legal_general → RagService.query (미사용 시 LLM 폴백 + warning)
- general → LLM astream (일반 창업 도우미)
- out_of_scope → SSE error 이벤트
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, AsyncGenerator
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.features.chat.application.intent_classifier import (
    IntentClassifier,
    IntentResult,
    StepInfo,
)
from app.features.chat.application.session_service import SessionService
from app.features.rag.application.rag_service import RagService
from app.features.roadmaps.application.context_builder import RoadmapContextBuilder
from app.repositories.roadmap_chat_repository import RoadmapChatRepository
from app.repositories.roadmap_repository import RoadmapRepository

if TYPE_CHECKING:
    from app.models.roadmap import Roadmap, RoadmapStep

logger = get_logger(__name__)


def _sse_event(event_type: str, data: dict) -> str:
    """SSE 이벤트 문자열 생성."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


_GENERAL_SYSTEM_PROMPT = (
    "당신은 한국 창업자를 위한 친절한 AI 어시스턴트 'StepZero AI'입니다.\n"
    "명확하고 간결하게 한국어로 답변하세요.\n"
    "모르는 것은 솔직히 모른다고 말하세요."
)

_LEGAL_FALLBACK_PROMPT = (
    "당신은 한국 창업 법률·행정 전문 AI 어시스턴트입니다.\n"
    "한국어로 답변하세요. 확실하지 않은 정보는 "
    "'확인이 필요합니다'라고 명시하세요."
)

_OUT_OF_SCOPE_MESSAGE = (
    "이 질문은 전문가 상담을 권장합니다. "
    "세금, 소송, 의료, 투자 등의 전문 분야는 "
    "해당 분야 전문가에게 문의해 주세요."
)


class ChatService:
    """통합 StepZero AI 챗봇 서비스.

    의도 분류 → 카테고리별 분기 → SSE 스트리밍 응답.
    """

    _HEARTBEAT_INTERVAL = 15

    def __init__(
        self,
        session_service: SessionService,
        intent_classifier: IntentClassifier | None,
        chat_repo: RoadmapChatRepository,
        context_builder: RoadmapContextBuilder,
        rag_service: RagService,
        roadmap_repo: RoadmapRepository,
    ) -> None:
        self._session_svc = session_service
        self._classifier = intent_classifier
        self._chat_repo = chat_repo
        self._ctx_builder = context_builder
        self._rag = rag_service
        self._roadmap_repo = roadmap_repo

        settings = get_settings()
        self._llm_ready = False
        if settings.OPENAI_API_KEY:
            self._llm = ChatOpenAI(
                model=settings.OPENAI_CHAT_MODEL,
                api_key=settings.OPENAI_API_KEY,
                timeout=20,
                max_retries=2,
            )
            self._llm_ready = True

    # ------------------------------------------------------------------ #
    #  Public: SSE 스트리밍 엔트리포인트
    # ------------------------------------------------------------------ #

    async def stream(
        self,
        message: str,
        *,
        session_id: UUID | None = None,
        user_id: int,
        team_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """SSE 스트리밍 응답 생성.

        Args:
            message: 사용자 메시지
            session_id: 기존 세션 ID (None이면 새 세션 생성)
            user_id: 사용자 ID
            team_id: 팀 ID

        Yields:
            SSE 이벤트 문자열 (data: {...}\\n\\n)
        """
        # 1. 세션 resolve (기존 세션 또는 새 생성)
        if session_id is not None:
            try:
                thread = await self._session_svc.get_session(session_id, user_id)
            except Exception:
                thread = await self._session_svc.create_session(user_id=user_id)
        else:
            thread = await self._session_svc.create_session(user_id=user_id)

        # 2. 첫 메시지 자동 제목
        if thread.message_count == 0 and not thread.title:
            await self._session_svc.set_auto_title(thread.id, message)

        # 3. 사용자 메시지 DB 저장
        await self._chat_repo.add_message(
            thread_id=thread.id, role="user", content=message,
        )

        # 4. 로드맵 컨텍스트 조회
        roadmap, steps, current_step_id = await self._load_roadmap_context(
            team_id
        )

        # StepInfo 변환
        step_infos: list[StepInfo] | None = None
        if steps:
            step_infos = [
                StepInfo(
                    step_id=s.id,
                    step_order=s.step_order,
                    title=s.title,
                )
                for s in steps
            ]

        # 5. 의도 분류
        intent = await self._classify(message, step_infos, current_step_id)

        # 6. SSE meta 이벤트
        yield _sse_event("meta", {
            "session_id": str(thread.id),
            "intent": intent.category,
            "step_id": intent.step_id,
            "step_title": intent.step_title,
        })

        # 7. 카테고리별 응답 생성
        tokens: list[str] = []

        try:
            if intent.category == "out_of_scope":
                yield _sse_event("error", {
                    "code": "OUT_OF_SCOPE",
                    "message": _OUT_OF_SCOPE_MESSAGE,
                })
                tokens.append(_OUT_OF_SCOPE_MESSAGE)

            elif intent.category in ("current_step", "other_step"):
                async for event in self._handle_step_response(
                    message, intent, roadmap, steps, tokens
                ):
                    yield event

            elif intent.category == "legal_general":
                async for event in self._handle_legal_response(
                    message, tokens
                ):
                    yield event

            else:  # general
                async for event in self._handle_general_response(
                    message, tokens
                ):
                    yield event

        except Exception:
            logger.exception("ChatService stream error")
            yield _sse_event("error", {
                "code": "INTERNAL_ERROR",
                "message": "AI 응답 중 오류가 발생했습니다. "
                "잠시 후 다시 시도해 주세요.",
            })

        # 8. 어시스턴트 응답 DB 저장
        full_response = "".join(tokens)
        if full_response:
            await self._chat_repo.add_message(
                thread_id=thread.id,
                role="assistant",
                content=full_response,
                intent_category=intent.category,
            )

        # 9. SSE done 이벤트 (out_of_scope 제외)
        if intent.category != "out_of_scope":
            yield _sse_event("done", {})

    # ------------------------------------------------------------------ #
    #  의도 분류
    # ------------------------------------------------------------------ #

    async def _classify(
        self,
        query: str,
        step_infos: list[StepInfo] | None,
        current_step_id: int | None,
    ) -> IntentResult:
        """IntentClassifier 위임. 미사용 시 general 폴백."""
        if self._classifier is None:
            return IntentResult(category="general")
        return await self._classifier.classify(
            query=query,
            roadmap_steps=step_infos,
            current_step_id=current_step_id,
        )

    # ------------------------------------------------------------------ #
    #  로드맵 컨텍스트 로딩
    # ------------------------------------------------------------------ #

    async def _load_roadmap_context(
        self, team_id: UUID,
    ) -> tuple[Roadmap | None, list[RoadmapStep], int | None]:
        """팀의 최신 로드맵 + 단계 목록 조회."""
        roadmap = await self._roadmap_repo.get_latest_for_team(team_id)
        if roadmap is None:
            return None, [], None

        steps = await self._roadmap_repo.list_steps(roadmap.id)
        if not steps:
            return roadmap, [], None

        # 현재 단계: 첫 번째 PENDING 또는 IN_PROGRESS
        current_step_id: int | None = None
        for step in steps:
            if step.status in ("PENDING", "IN_PROGRESS"):
                current_step_id = step.id
                break

        return roadmap, steps, current_step_id

    # ------------------------------------------------------------------ #
    #  카테고리별 핸들러
    # ------------------------------------------------------------------ #

    async def _handle_step_response(
        self,
        message: str,
        intent: IntentResult,
        roadmap: Roadmap | None,
        steps: list[RoadmapStep],
        tokens: list[str],
    ) -> AsyncGenerator[str, None]:
        """current_step / other_step → ContextBuilder + LLM 스트리밍."""
        if not self._llm_ready:
            yield _sse_event("error", {
                "code": "LLM_UNAVAILABLE",
                "message": "현재 AI 어시스턴트를 사용할 수 없습니다.",
            })
            return

        if roadmap is None or not steps or intent.step_id is None:
            yield _sse_event("error", {
                "code": "NO_ROADMAP",
                "message": "로드맵 정보를 찾을 수 없습니다.",
            })
            return

        step = next((s for s in steps if s.id == intent.step_id), None)
        if step is None:
            yield _sse_event("error", {
                "code": "STEP_NOT_FOUND",
                "message": "해당 단계를 찾을 수 없습니다.",
            })
            return

        # ContextBuilder로 시스템 프롬프트 생성
        system_prompt, _ = await self._ctx_builder.build(roadmap, step)

        async for event in self._llm_stream(system_prompt, message, tokens):
            yield event

    async def _handle_legal_response(
        self,
        message: str,
        tokens: list[str],
    ) -> AsyncGenerator[str, None]:
        """legal_general → RAG 조회 (미사용 시 LLM 폴백 + warning)."""
        if self._rag.ready:
            answer = await self._rag.query(message)
            tokens.append(answer)
            yield _sse_event("token", {"token": answer})
            return

        # RAG 미사용 → LLM 폴백
        logger.warning("RAG unavailable, falling back to LLM for legal query")
        if not self._llm_ready:
            yield _sse_event("error", {
                "code": "LLM_UNAVAILABLE",
                "message": "현재 법령 검색 서비스를 사용할 수 없습니다.",
            })
            return

        yield _sse_event("warning", {
            "message": "법령 검색 서비스를 사용할 수 없어 "
            "일반 AI가 답변합니다.",
        })
        async for event in self._llm_stream(
            _LEGAL_FALLBACK_PROMPT, message, tokens
        ):
            yield event

    async def _handle_general_response(
        self,
        message: str,
        tokens: list[str],
    ) -> AsyncGenerator[str, None]:
        """general → LLM 스트리밍."""
        if not self._llm_ready:
            yield _sse_event("error", {
                "code": "LLM_UNAVAILABLE",
                "message": "현재 AI 어시스턴트를 사용할 수 없습니다. "
                "잠시 후 다시 시도해 주세요.",
            })
            return

        async for event in self._llm_stream(
            _GENERAL_SYSTEM_PROMPT, message, tokens
        ):
            yield event

    # ------------------------------------------------------------------ #
    #  LLM 토큰 스트리밍 (공통)
    # ------------------------------------------------------------------ #

    async def _llm_stream(
        self,
        system_prompt: str,
        user_message: str,
        tokens: list[str],
    ) -> AsyncGenerator[str, None]:
        """LLM 토큰 단위 SSE 스트리밍 + 하트비트.

        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
            tokens: 토큰 누적 리스트 (호출자가 전체 응답 조합용)
        """
        heartbeat_queue: asyncio.Queue[str] = asyncio.Queue()

        async def _heartbeat_loop() -> None:
            try:
                while True:
                    await asyncio.sleep(self._HEARTBEAT_INTERVAL)
                    await heartbeat_queue.put(": heartbeat\n\n")
            except asyncio.CancelledError:
                pass

        heartbeat_task = asyncio.create_task(_heartbeat_loop())

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]
            async for chunk in self._llm.astream(messages):
                # 하트비트 drain
                while not heartbeat_queue.empty():
                    yield heartbeat_queue.get_nowait()

                token = chunk.content if isinstance(chunk, AIMessage) else ""
                if token:
                    tokens.append(token)
                    yield _sse_event("token", {"token": token})

        except asyncio.CancelledError:
            logger.info("LLM 스트리밍 취소됨")
        except Exception:
            logger.exception("LLM streaming failed")
            yield _sse_event("error", {
                "code": "LLM_ERROR",
                "message": "AI 응답 중 오류가 발생했습니다. "
                "잠시 후 다시 시도해 주세요.",
            })
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
