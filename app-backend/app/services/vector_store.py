from typing import List, Optional
import os
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.core.config import get_settings
from app.services.law_etl import ProcessedLawData

class VectorStoreService:
    def __init__(self):
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
             # In production, we might want to log this but for now it's critical
             pass
             
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY
        )
        
        # Supabase Logic
        # We need SUPABASE_URL and SUPABASE_KEY if we use supabase-py client
        # BUT, since we have a local postgres with pgvector, we can use PGVector directly
        # or use SupabaseVectorStore if we were connecting to cloud Supabase.
        # Given docker-compose has local db, we should use PGVector from langchain-postgres 
        # OR use the 'connection_string' approach if SupabaseVectorStore supports it (it usually needs client).
        
        # Let's check if we are using Real Supabase or Local DB acting as Supabase.
        # The docker-compose uses 'pgvector/pgvector'. This is standard Postgres.
        # So we should use 'langchain_postgres.PGVector' (or 'langchain_community.vectorstores.PGVector').
        # I will use standard PGVector for local compatibility.
        
        self.db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        self.collection_name = "law_vectors"

    async def add_documents(self, processed_data_list: List[ProcessedLawData]):
        from langchain_postgres import PGVector
        
        documents = []
        for item in processed_data_list:
            # Create Document for retrieval
            # We index the 'guide_text' and 'law_reference' primarily
            # But maybe we want to retrieve by question matching guide text.
            
            # Metadata flattening
            metadata = item.original_data.metadata.copy()
            metadata.update({
                "title": item.title,
                "category": item.category,
                "summary": item.summary,
                "law_reference": str(item.law_reference)
            })
            
            doc = Document(
                page_content=f"{item.title}\n\n{item.guide_text}\n\n[Reference]\n{item.law_reference}",
                metadata=metadata
            )
            documents.append(doc)
            
        if not documents:
            return

        # Initialize PGVector
        # Note: We need to ensure the extension is created.
        vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.db_url,
            use_jsonb=True,
        )
        
        # Use sync add_documents to avoid _async_engine missing error
        vector_store.add_documents(documents)
