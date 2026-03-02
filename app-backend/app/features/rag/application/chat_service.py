from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, AsyncGenerator, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.features.rag.application.rag_service import RagService

if TYPE_CHECKING:
    from app.features.rag.application.semantic_router import SemanticRouter

logger = get_logger("services.chat")


def _sse_event(event_type: str, data: dict) -> str:
    """SSE 이벤트 문자열 생성."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

# Kept for backward compatibility and as keyword fallback inside SemanticRouter
LEGAL_KEYWORDS = frozenset(
    [
        "법",
        "허가",
        "등록",
        "신고",
        "인가",
        "규정",
        "법률",
        "법령",
        "조례",
        "면허",
        "신청",
        "영업",
        "위생",
        "행정심판",
        "행정조사",
        "소방",
        "개인정보",
        "근로계약",
        "보험",
        "세금",
    ]
)

GENERAL_SYSTEM_PROMPT = (
    "당신은 한국 창업자를 위한 친절한 AI 어시스턴트입니다.\n"
    "명확하고 간결하게 한국어로 답변하세요.\n"
    "모르는 것은 솔직히 모른다고 말하세요."
)


def classify_query(message: str) -> Literal["legal", "general"]:
    """Keyword-based query classifier (kept as internal fallback)."""
    for keyword in LEGAL_KEYWORDS:
        if keyword in message:
            return "legal"
    return "general"


class ChatService:
    def __init__(
        self,
        rag_service: RagService,
        semantic_router: SemanticRouter | None = None,
    ):
        self.rag_service = rag_service
        self.semantic_router = semantic_router
        settings = get_settings()

        self.general_ready = False
        if not settings.OPENAI_API_KEY:
            logger.warning("ChatService: general LLM disabled (no API key)")
            return

        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            api_key=settings.OPENAI_API_KEY,
            timeout=20,
            max_retries=2,
        )
        self.general_chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", GENERAL_SYSTEM_PROMPT),
                    ("human", "{message}"),
                ]
            )
            | self.llm
            | StrOutputParser()
        )
        self.general_ready = True

    async def _classify(self, message: str) -> str:
        """메시지 분류: legal / general / out_of_scope."""
        if self.semantic_router is not None:
            return await self.semantic_router.classify(message)
        return classify_query(message)

    async def chat(self, message: str) -> tuple[str, str]:
        # Use SemanticRouter if available, fall back to keyword classifier
        if self.semantic_router is not None:
            source = await self.semantic_router.classify(message)
        else:
            source = classify_query(message)

        if source == "out_of_scope":
            return (
                "이 질문은 전문가 상담을 권장합니다. "
                "세금, 소송, 의료, 투자 등의 전문 분야는 "
                "해당 분야 전문가에게 문의해 주세요.",
                "out_of_scope",
            )

        if source == "legal":
            answer = await self.rag_service.query(message)
            return answer, "legal_rag"

        if not self.general_ready:
            return (
                "현재 AI 어시스턴트를 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.",
                "general",
            )

        try:
            answer = await asyncio.wait_for(
                self.general_chain.ainvoke({"message": message}),
                timeout=25,
            )
            return answer, "general"
        except asyncio.TimeoutError:
            logger.warning("General chat timed out")
            return (
                "요청 처리 시간이 초과되었습니다. 질문을 조금 더 짧게 입력해 주세요.",
                "general",
            )
        except Exception:
            logger.exception("General chat failed")
            return (
                "AI 응답 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                "general",
            )

    # ------------------------------------------------------------------ #
    #  SSE 스트리밍 (통합 챗봇용)
    # ------------------------------------------------------------------ #

    _HEARTBEAT_INTERVAL = 15

    async def stream(self, message: str) -> AsyncGenerator[str, None]:
        """SSE 스트리밍 응답 생성.

        - out_of_scope → error 이벤트
        - legal → RAG 결과 단일 token + done
        - general → LLM astream 토큰 단위 SSE
        """
        source = await self._classify(message)

        if source == "out_of_scope":
            yield _sse_event("error", {
                "code": "OUT_OF_SCOPE",
                "message": "이 질문은 전문가 상담을 권장합니다. "
                "세금, 소송, 의료, 투자 등의 전문 분야는 "
                "해당 분야 전문가에게 문의해 주세요.",
            })
            return

        if source == "legal":
            answer = await self.rag_service.query(message)
            yield _sse_event("token", {"token": answer})
            yield _sse_event("done", {})
            return

        if not self.general_ready:
            yield _sse_event("error", {
                "code": "LLM_UNAVAILABLE",
                "message": "현재 AI 어시스턴트를 사용할 수 없습니다. "
                "잠시 후 다시 시도해 주세요.",
            })
            return

        # General mode — 토큰 단위 스트리밍 + 하트비트
        full_response = ""
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
                SystemMessage(content=GENERAL_SYSTEM_PROMPT),
                HumanMessage(content=message),
            ]
            async for chunk in self.llm.astream(messages):
                while not heartbeat_queue.empty():
                    yield heartbeat_queue.get_nowait()

                token = chunk.content if isinstance(chunk, AIMessage) else ""
                if token:
                    full_response += token
                    yield _sse_event("token", {"token": token})
        except asyncio.CancelledError:
            logger.info("General chat SSE 스트리밍 취소됨")
        except Exception:
            logger.exception("General chat streaming failed")
            yield _sse_event("error", {
                "code": "LLM_ERROR",
                "message": "AI 응답 중 오류가 발생했습니다. "
                "잠시 후 다시 시도해 주세요.",
            })
            return
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        if not full_response:
            yield _sse_event("error", {
                "code": "EMPTY_RESPONSE",
                "message": "AI가 응답을 생성하지 못했습니다. "
                "질문을 다시 입력해 주세요.",
            })
            return

        yield _sse_event("done", {})
