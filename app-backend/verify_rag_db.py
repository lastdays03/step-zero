import asyncio
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings

async def verify_db():
    settings = get_settings()
    # Override DB URL for localhost
    # Assuming standard postgresql:// user:pass @ host : port / dbname
    # Docker service 'db' maps to localhost:5432
    # So we should valid connection string.
    
    # Check if we need async driver
    # langchain-postgres usually recommends "postgresql+psycopg://..."
    
    db_url = settings.DATABASE_URL.replace("@db:", "@localhost:")
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    print(f"Testing connection to: {db_url}")
    
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    
    try:
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name="law_vectors",
            connection=db_url,
            use_jsonb=True,
        )
        print("PGVector initialized successfully.")
    except Exception as e:
        print(f"PGVector initialization failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_db())
