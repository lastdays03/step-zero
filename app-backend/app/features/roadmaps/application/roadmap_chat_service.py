"""RoadmapChatService: SSE 스트리밍 AI 코치 채팅 서비스.

로드맵 단계별 컨텍스트를 주입한 AI 코치와의 실시간 대화를 제공한다.
- SemanticRouter로 범위 외 질문 차단
- RoadmapContextBuilder로 3레이어 시스템 프롬프트 생성
- ChatOpenAI.astream()으로 토큰 단위 SSE 스트리밍
- 출처 파싱 ([법령 N], [서류 N]) 후 DB 저장
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.features.roadmaps.application.context_builder import RoadmapContextBuilder
from app.repositories.roadmap_chat_repository import RoadmapChatRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.features.rag.application.semantic_router import SemanticRouter
    from app.models.roadmap import Roadmap, RoadmapStep, RoadmapStepAction
    from app.models.roadmap_chat import RoadmapChatThread

logger = get_logger(__name__)

# 출처 인용 패턴: [법령 1], [서류 2] 등
_CITATION_PATTERN = re.compile(r"\[(법령|서류)\s*(\d+)\]")

# SSE 하트비트 간격 (초)
_HEARTBEAT_INTERVAL = 15

# LLM 응답 타임아웃 (초)
_STREAM_TIMEOUT = 30


def _sse_event(event_type: str, data: dict) -> str:
    """SSE 이벤트 문자열 생성."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class RoadmapChatService:
    """SSE 스트리밍 기반 로드맵 AI 코치 채팅 서비스."""

    def __init__(
        self,
        context_builder: RoadmapContextBuilder,
        semantic_router: SemanticRouter | None,
        chat_repo: RoadmapChatRepository,
    ):
        self.context_builder = context_builder
        self.semantic_router = semantic_router
        self.chat_repo = chat_repo

        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            api_key=settings.OPENAI_API_KEY,
            streaming=True,
            timeout=_STREAM_TIMEOUT,
            max_retries=2,
            temperature=0.3,
            max_tokens=1000,
        )

    async def stream(
        self,
        *,
        roadmap: Roadmap,
        step: RoadmapStep,
        thread: RoadmapChatThread,
        user_message: str,
        session: AsyncSession,
    ) -> AsyncGenerator[str, None]:
        """SSE 이벤트 스트림 생성.

        플로우:
        1. SemanticRouter로 OUT_OF_SCOPE 차단
        2. 사용자 메시지 DB 저장
        3. 컨텍스트 빌드 (3레이어 시스템 프롬프트)
        4. LLM 스트리밍 + 토큰 전송
        5. 출처 파싱
        6. 어시스턴트 응답 DB 저장
        7. 메타 + 완료 이벤트
        """
        # 1. 범위 외 질문 차단
        if self.semantic_router:
            try:
                category = await self.semantic_router.classify(user_message)
                if category == "out_of_scope":
                    yield _sse_event("error", {
                        "code": "OUT_OF_SCOPE",
                        "message": "이 질문은 전문가 상담을 권장합니다. "
                        "세금, 소송, 의료, 투자 등의 전문 분야는 "
                        "해당 분야 전문가에게 문의해 주세요.",
                    })
                    return
            except Exception:
                logger.warning("SemanticRouter 분류 실패, 계속 진행")

        # 2. 사용자 메시지 DB 저장
        await self.chat_repo.add_message(
            thread_id=thread.id,
            role="user",
            content=user_message,
        )

        # 3. 최근 대화 조회 + 컨텍스트 빌드
        recent = await self.chat_repo.get_recent_messages(thread.id, limit=5)
        system_prompt, step_actions = await self.context_builder.build(
            roadmap, step
        )

        # 4. LangChain 메시지 배열 구성
        messages = self._build_chat_messages(system_prompt, recent, user_message)

        # 5. LLM 스트리밍 + 하트비트
        full_response = ""
        heartbeat_queue: asyncio.Queue[str] = asyncio.Queue()

        async def _heartbeat_loop() -> None:
            try:
                while True:
                    await asyncio.sleep(_HEARTBEAT_INTERVAL)
                    await heartbeat_queue.put(": heartbeat\n\n")
            except asyncio.CancelledError:
                pass

        heartbeat_task = asyncio.create_task(_heartbeat_loop())

        try:
            async for chunk in self.llm.astream(messages):
                # 하트비트 큐에서 대기 중인 이벤트 drain
                while not heartbeat_queue.empty():
                    yield heartbeat_queue.get_nowait()

                token = chunk.content if isinstance(chunk, AIMessage) else ""
                if token:
                    full_response += token
                    yield _sse_event("token", {"token": token})
        except asyncio.CancelledError:
            # 연결 끊김 — 부분 응답이라도 저장
            logger.info("SSE 스트리밍 취소됨, 부분 응답 저장")
        except Exception:
            logger.exception("LLM 스트리밍 오류")
            yield _sse_event("error", {
                "code": "LLM_ERROR",
                "message": "AI 응답 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
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
                "message": "AI가 응답을 생성하지 못했습니다. 질문을 다시 입력해 주세요.",
            })
            return

        # 6. 출처 파싱 (build()에서 이미 조회한 actions 재활용)
        sources = self._parse_citations(full_response, step_actions)
        if sources:
            yield _sse_event("sources", {"sources": sources})

        # 7. 어시스턴트 응답 DB 저장 (flush via add_message)
        msg = await self.chat_repo.add_message(
            thread_id=thread.id,
            role="assistant",
            content=full_response,
            sources_json=sources if sources else None,
            token_count=len(full_response) // 4,
        )

        yield _sse_event("meta", {
            "thread_id": str(thread.id),
            "message_id": msg.id,
        })
        yield _sse_event("done", {})

        # 8. 최종 커밋 (SSE 제너레이터 종료 직전 — 라우터 레벨 불가)
        await session.commit()

    # ------------------------------------------------------------------ #
    #  메시지 배열 구성
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_chat_messages(
        system_prompt: str,
        recent: list,
        user_message: str,
    ) -> list:
        """LangChain 메시지 배열 구성.

        system_prompt + 최근 대화 이력(system prompt에 요약 포함되므로 여기선 직접 포함) + 현재 질문.
        """
        messages = [SystemMessage(content=system_prompt)]

        # 최근 대화 이력을 메시지로 변환 (컨텍스트 보강)
        for msg in recent:
            role = getattr(msg, "role", "user")
            content = getattr(msg, "content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # 현재 사용자 메시지 (이력에 이미 포함된 마지막 메시지와 중복 방지)
        if not recent or getattr(recent[-1], "content", "") != user_message:
            messages.append(HumanMessage(content=user_message))

        return messages

    # ------------------------------------------------------------------ #
    #  출처 파싱
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_citations(
        response: str,
        actions: list[RoadmapStepAction],
    ) -> list[dict]:
        """[법령 N], [서류 N] 패턴을 파싱하여 출처 목록 반환.

        시스템 프롬프트에서 법령/서류를 1-indexed로 번호 매겼으므로,
        동일 순서로 action 목록에서 매칭한다.
        """
        legal_actions = [a for a in actions if a.action_type == "LEGAL_BASIS"]
        doc_actions = [a for a in actions if a.action_type == "DOCUMENT"]

        found: list[dict] = []
        seen: set[str] = set()

        for match in _CITATION_PATTERN.finditer(response):
            cite_type = match.group(1)  # "법령" 또는 "서류"
            cite_num = int(match.group(2))  # 1-indexed

            key = f"{cite_type}_{cite_num}"
            if key in seen:
                continue
            seen.add(key)

            if cite_type == "법령" and 1 <= cite_num <= len(legal_actions):
                action = legal_actions[cite_num - 1]
                item_id = (action.metadata_json or {}).get("actionkit_item_id")
                found.append({
                    "id": cite_num,
                    "type": "legal_basis",
                    "title": action.title,
                    "url": action.source_url
                    or (f"/api/v1/actionkits/items/{item_id}" if item_id else None),
                })
            elif cite_type == "서류" and 1 <= cite_num <= len(doc_actions):
                action = doc_actions[cite_num - 1]
                found.append({
                    "id": cite_num,
                    "type": "document",
                    "title": action.title,
                    "url": action.source_url,
                })

        return found

