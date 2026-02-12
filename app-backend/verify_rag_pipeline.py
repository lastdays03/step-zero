import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path="app-backend/.env")

# Add app directory to sys.path
sys.path.append(os.getcwd())

from app.services.law_fetcher import LocalFileSource
from app.services.law_etl import LawETLProcessor
from app.services.vector_store import VectorStoreService
from app.core.config import get_settings

async def main():
    root_dir = os.path.abspath(os.path.join(os.getcwd(), "../.temp"))
    print(f"1. Source Directory: {root_dir}")
    
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        print("\n[CRITICAL] OPENAI_API_KEY is missing in .env or environment.")
        print("Cannot proceed with LLM ETL and Vector Embedding.")
        return

    # 1. Fetch
    source = LocalFileSource(root_dir)
    raw_laws = await source.fetch_all_laws()
    print(f">> Fetched {len(raw_laws)} raw documents.")
    
    if not raw_laws:
        return

    # Pick top 3 for testing to save tokens/time
    test_laws = raw_laws[:3]
    print(f">> Selected {len(test_laws)} documents for testing.")

    # 2. ETL
    print("\n2. Running ETL (Structuring)...")
    etl = LawETLProcessor()
    processed_docs = []
    
    for law in test_laws:
        print(f"   - Processing: {law.title}...")
        try:
            processed = await etl.process(law)
            processed_docs.append(processed)
        except Exception as e:
            print(f"   [Error] {e}")
            
    print(f">> Successfully processed {len(processed_docs)} documents.")

    # 3. Vector Storage
    print("\n3. Storing in Vector DB (pgvector)...")
    try:
        vector_service = VectorStoreService()
        await vector_service.add_documents(processed_docs)
        print(">> Success! Documents stored in Vector DB.")
    except Exception as e:
        print(f">> Storage Failed: {e}")
        print("Make sure 'pgvector' extension is enabled in your Postgres DB.")
        print("Run: CREATE EXTENSION IF NOT EXISTS vector;")

if __name__ == "__main__":
    asyncio.run(main())
