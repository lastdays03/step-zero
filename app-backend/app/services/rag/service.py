from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_postgres import PGVector
from app.core.config import get_settings

class RagService:
    def __init__(self):
        settings = get_settings()
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        
        # We need the sync URL for extension creation/init (handled by langachain-postgres internally if not exists)
        # And the async URL for FastAPI's async execution if using async methods.
        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        # Initialize PGVector. 
        # Note: In langchain-postgres 0.0.9+, it uses SQLAlchemy. 
        # If we provide a sync connection string, it uses sync SQLAlchemy.
        # But if we call 'ainvoke', it might try to use an async engine.
        
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name="law_vectors",
            connection=sync_db_url, # Using sync for stable init
            use_jsonb=True,
        )
        # Search for top 3 relevant documents
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview", api_key=settings.OPENAI_API_KEY)
        
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

    async def query(self, question: str) -> str:
        from fastapi.concurrency import run_in_threadpool
        # Use sync 'invoke' wrapped in threadpool to avoid _async_engine missing error
        return await run_in_threadpool(self.chain.invoke, question)
