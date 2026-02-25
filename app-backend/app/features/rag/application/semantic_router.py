"""Semantic routing for classifying user queries using embedding similarity."""

from __future__ import annotations

import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.core.logging import get_logger

logger = get_logger(__name__)

# Keyword fallback (expanded set from T-1.3)
LEGAL_KEYWORDS = frozenset(
    {
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
    }
)


class SemanticRouter:
    """Embedding-based semantic classifier with keyword fallback."""

    def __init__(self, embeddings: OpenAIEmbeddings):
        self.embeddings = embeddings
        self.anchors: dict[str, list[str]] = {
            "legal": [
                "창업 시 필요한 인허가 절차",
                "영업신고 방법과 서류",
                "법인 설립 등록",
                "세금 신고 및 납부",
                "4대보험 가입 절차",
                "행정심판 및 행정처분",
                "근로계약서 작성 의무",
                "소방 안전 기준",
            ],
            "general": [
                "카페 인테리어 추천",
                "마케팅 전략",
                "사업계획서 작성",
                "투자 유치 방법",
            ],
        }
        self._anchor_embeddings: dict[str, np.ndarray] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Pre-compute anchor embeddings (call once at app startup)."""
        for category, texts in self.anchors.items():
            embeddings = await self.embeddings.aembed_documents(texts)
            self._anchor_embeddings[category] = np.array(embeddings)
        self._initialized = True
        logger.info(
            "SemanticRouter initialized with %d categories", len(self.anchors)
        )

    async def classify(self, query: str, threshold: float = 0.7) -> str:
        """Classify query using cosine similarity + keyword fallback."""
        if not self._initialized:
            await self.initialize()

        # Get query embedding
        query_embedding = await self.embeddings.aembed_query(query)
        query_vec = np.array(query_embedding)

        # Compute cosine similarity with legal anchors
        legal_anchors = self._anchor_embeddings.get("legal")
        if legal_anchors is not None:
            similarities = self._cosine_similarity(query_vec, legal_anchors)
            max_sim = float(np.max(similarities))
            if max_sim >= threshold:
                logger.debug("Semantic route: legal (sim=%.3f)", max_sim)
                return "legal"

        # Keyword fallback
        if self._keyword_match(query):
            logger.debug("Keyword fallback route: legal")
            return "legal"

        logger.debug("Route: general")
        return "general"

    @staticmethod
    def _cosine_similarity(
        query_vec: np.ndarray, anchor_vecs: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarity between query and anchor vectors."""
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        anchor_norms = anchor_vecs / (
            np.linalg.norm(anchor_vecs, axis=1, keepdims=True) + 1e-10
        )
        return anchor_norms @ query_norm

    @staticmethod
    def _keyword_match(query: str) -> bool:
        """Check if query contains any legal keywords."""
        return any(kw in query for kw in LEGAL_KEYWORDS)
