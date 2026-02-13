import asyncio
from fastapi.concurrency import run_in_threadpool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_postgres import PGVector
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("services.rag")

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

        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        try:
            self.vector_store = PGVector(
                embeddings=self.embeddings,
                collection_name="law_vectors",
                connection=sync_db_url,
                use_jsonb=True,
            )
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            self.llm = ChatOpenAI(
                model=settings.OPENAI_CHAT_MODEL,
                api_key=settings.OPENAI_API_KEY,
                timeout=20,
                max_retries=2,
            )

            self.prompt = ChatPromptTemplate.from_template("""
            You are an AI assistant for startup founders in Korea.
            Answer the question based ONLY on the following context.
            If the answer is not in the context, say "제공된 법령 문서에서는 해당 정보를 찾을 수 없습니다."

            Context:
            {context}

            Question: {question}

            Answer (in Korean):
            """)

            def format_docs(docs):
                if not docs:
                    return "No relevant legal documents found."
                return "\n\n".join(doc.page_content for doc in docs)

            self.chain = (
                {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
            self.ready = True
        except Exception as exc:
            self.unavailable_reason = f"RAG initialization failed: {exc.__class__.__name__}"
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
