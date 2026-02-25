import asyncio

from fastapi.concurrency import run_in_threadpool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("services.rag")

RAG_SYSTEM_PROMPT = """\
당신은 한국 창업 법률·행정 전문 AI 어시스턴트입니다.

[규칙]
1. 아래 제공된 컨텍스트 문서에 기반해서만 답변하세요.
2. 컨텍스트에 답변 근거가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다."라고 솔직히 답하세요.
3. 관련 법령이 있으면 법령명과 조항을 인용하세요.
4. 창업 초보자도 이해할 수 있는 쉬운 한국어로 설명하세요.
5. 핵심 내용은 불릿 포인트로 정리하세요.

[컨텍스트]
{context}

[질문]
{question}

[답변]"""


def format_docs_with_metadata(docs):
    """Format retrieved documents with source metadata for better citation."""
    if not docs:
        return "관련 법령 문서를 찾을 수 없습니다."
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        header = (
            f"[출처 {i}] {meta.get('title', '제목 없음')} ({meta.get('category', '')})"
        )
        ref = (
            f"법령 참조: {meta.get('law_reference', '')}"
            if meta.get("law_reference")
            else ""
        )
        content = doc.page_content
        part = f"{header}\n{ref}\n{content}" if ref else f"{header}\n{content}"
        parts.append(part)
    return "\n\n---\n\n".join(parts)


class RagService:
    def __init__(self):
        settings = get_settings()
        self.ready = False
        self.unavailable_reason = ""
        if not settings.OPENAI_API_KEY:
            self.unavailable_reason = "OPENAI_API_KEY is not configured"
            logger.warning("RAG disabled: OPENAI_API_KEY is missing")
            return

        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBED_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

        sync_db_url = settings.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        try:
            self.vector_store = PGVector(
                embeddings=self.embeddings,
                collection_name="law_vectors",
                connection=sync_db_url,
                use_jsonb=True,
            )
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
            self.llm = ChatOpenAI(
                model=settings.OPENAI_CHAT_MODEL,
                api_key=settings.OPENAI_API_KEY,
                timeout=20,
                max_retries=2,
            )

            self.prompt = ChatPromptTemplate.from_template(RAG_SYSTEM_PROMPT)

            self.chain = (
                {
                    "context": self.retriever | format_docs_with_metadata,
                    "question": RunnablePassthrough(),
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
            self.ready = True
        except Exception as exc:
            self.unavailable_reason = (
                f"RAG initialization failed: {exc.__class__.__name__}"
            )
            logger.exception("Failed to initialize RAG service")

    async def query(self, question: str) -> str:
        if not self.ready:
            return (
                "현재 법령 검색 서비스를 사용할 수 없습니다. "
                "잠시 후 다시 시도하거나 관리자에게 문의해 주세요."
            )
        try:
            return await asyncio.wait_for(
                run_in_threadpool(self.chain.invoke, question),
                timeout=25,
            )
        except asyncio.TimeoutError:
            logger.warning("RAG query timed out")
            return "요청 처리 시간이 초과되었습니다. 질문을 조금 더 구체적으로 입력해 주세요."
        except Exception:
            logger.exception("RAG query failed")
            return "법령 검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
