from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.law_etl import ProcessedLawData

logger = get_logger(__name__)

# guide_text 용 청킹 설정 (ETL 거친 텍스트)
_DEFAULT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " "],
)


class VectorStoreService:
    def __init__(self, *, chunk_size: int = 600, chunk_overlap: int = 100):
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            message = "OPENAI_API_KEY is not configured; VectorStoreService cannot initialize embeddings."
            if settings.ENVIRONMENT.lower() == "production":
                raise RuntimeError(message)
            logger.warning(message)

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY,
        )
        self.db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        self.collection_name = "law_vectors"

        # 커스텀 청킹 파라미터가 기본값과 동일하면 모듈 수준 인스턴스 재사용
        if chunk_size == 600 and chunk_overlap == 100:
            self.splitter = _DEFAULT_SPLITTER
        else:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ".", " "],
            )

    def _build_content(self, item: ProcessedLawData) -> str:
        """ProcessedLawData → 인덱싱용 텍스트 조합"""
        return f"{item.title}\n\n{item.guide_text}\n\n[Reference]\n{item.law_reference}"

    def _build_base_metadata(self, item: ProcessedLawData) -> dict:
        """ProcessedLawData → 공통 메타데이터 딕셔너리"""
        metadata = item.original_data.metadata.copy()
        metadata.update({
            "source": "law_etl",
            "title": item.title,
            "category": item.category,
            "summary": item.summary,
            "law_reference": str(item.law_reference),
        })
        return metadata

    async def add_documents(self, processed_data_list: List[ProcessedLawData]):
        """ProcessedLawData 목록을 청킹하여 PGVector에 적재한다."""
        from langchain_postgres import PGVector

        documents: list[Document] = []
        for item in processed_data_list:
            content = self._build_content(item)
            chunks = self.splitter.split_text(content)
            base_metadata = self._build_base_metadata(item)

            for i, chunk in enumerate(chunks):
                metadata = {
                    **base_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                documents.append(Document(page_content=chunk, metadata=metadata))

        if not documents:
            return

        logger.info(
            "청킹 완료: 원본 %d건 → 청크 %d건",
            len(processed_data_list),
            len(documents),
        )

        vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.db_url,
            use_jsonb=True,
        )
        # sync add_documents 사용 (_async_engine 미지원 회피)
        vector_store.add_documents(documents)
