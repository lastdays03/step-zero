import asyncio
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import get_settings
from app.core.logging import get_logger
from app.features.rag.application.rag_service import RagService

logger = get_logger("services.chat")

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
    ]
)

GENERAL_SYSTEM_PROMPT = (
    "You are a friendly AI assistant for startup founders in Korea. "
    "Answer clearly and concisely in Korean. "
    "If you don't know, say so honestly."
)


def classify_query(message: str) -> Literal["legal", "general"]:
    for keyword in LEGAL_KEYWORDS:
        if keyword in message:
            return "legal"
    return "general"


class ChatService:
    def __init__(self, rag_service: RagService):
        self.rag_service = rag_service
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

    async def chat(self, message: str) -> tuple[str, str]:
        source = classify_query(message)

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
            return "요청 처리 시간이 초과되었습니다. 질문을 조금 더 짧게 입력해 주세요.", "general"
        except Exception:
            logger.exception("General chat failed")
            return "AI 응답 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.", "general"
