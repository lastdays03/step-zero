"""ActionKit Matcher: Fact layer for roadmap generation.

Matches a business type + location to relevant ActionKit items using
hybrid search (vector similarity + relational DB JOIN).

Multi-query strategy:
  1. Base query: "{business_type} {location} 창업 인허가"
  2. Business-specific queries from BUSINESS_QUERY_TEMPLATES
  3. All queries executed in parallel via asyncio.gather
  4. Results merged with dedup + best-score retention
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.logging import get_logger
from app.features.rag.application.rag_service import RagService
from app.models.actionkit import (
    ActionKitCategory,
    ActionKitItem,
    ActionKitItemHighlight,
    ActionKitRelatedLaw,
)
from app.models.file import File

logger = get_logger(__name__)

# Minimum vector similarity score to keep a match.
# Scores below this are considered noise and filtered out.
_MIN_RELEVANCE_SCORE: float = 0.2

# ActionKit category slug -> roadmap phase name mapping
CATEGORY_TO_PHASE: dict[str, str] = {
    # LAW_DATA chapter keys (domain=laws, slug="1".."6")
    "1": "입지 검토",
    "2": "영업 인허가",
    "3": "안전·소방",
    "4": "영업 준수사항",
    "5": "위반 대응",
    "6": "행정처분 구제",
    # Business-specific law chapters (domain=laws, slug="7".."12")
    "7": "영업 인허가",  # 식품제조가공업
    "8": "영업 인허가",  # 통신판매업
    "9": "영업 인허가",  # 미용업
    "10": "영업 인허가",  # 일반소매업
    "11": "영업 인허가",  # 학원업
    "12": "영업 인허가",  # 숙박업
    # ACTION_KIT_DATA category slugs (domain=kits)
    "legal": "법률 준비",
    "tax": "세무 설정",
    "hr": "인사·노무",
    "grant": "정책자금 신청",
}

# Business type -> specialized search keyword templates
BUSINESS_QUERY_TEMPLATES: dict[str, list[str]] = {
    "휴게음식점": ["위생 허가", "식품 안전", "영업 신고"],
    "카페": ["위생 허가", "식품 안전", "영업 신고"],
    "일반음식점": ["위생 허가", "식품 안전", "영업 허가"],
    "식품제조가공업": ["식품 제조 허가", "HACCP", "위생 관리", "식품위생법"],
    "통신판매업": ["통신판매업 신고", "전자상거래", "소비자 보호", "청약철회"],
    "미용실": ["공중위생 신고", "미용업 면허", "위생 관리"],
    "미용업": ["공중위생 신고", "미용업 면허", "위생 관리"],
    "학원": ["학원 등록", "교육청 신고", "소방 안전"],
    "숙박업": ["숙박업 허가", "소방 안전", "위생 관리"],
    "소매업": ["영업 신고", "통신판매업", "사업자 등록"],
    "일반소매업": ["영업 신고", "통신판매업", "사업자 등록"],
}

DEFAULT_QUERY_KEYWORDS: list[str] = ["창업 인허가", "영업 신고", "사업자 등록"]


@dataclass
class MatchedActionKit:
    """Structured fact data from ActionKit matching."""

    item: ActionKitItem
    highlights: list[ActionKitItemHighlight] = field(default_factory=list)
    related_laws: list[ActionKitRelatedLaw] = field(default_factory=list)
    files: list[File] = field(default_factory=list)
    phase_group: str = ""
    relevance_score: float = 0.0


class ActionKitMatcher:
    """Matches business type to relevant ActionKit items using hybrid search.

    Search strategy:
      1. Vector similarity search via RagService's vector_store
      2. Extract item titles from document metadata
      3. Relational DB JOIN for full data (highlights, related_laws, files)
      4. Group by category -> phase mapping
      5. Deduplicate by item id
    """

    def __init__(self, rag_service: RagService):
        self.rag_service = rag_service

    async def match(
        self,
        business_type: str,
        location: str,
        session: AsyncSession,
    ) -> list[MatchedActionKit]:
        """Find relevant ActionKit items for a business type via multi-query hybrid search."""
        if not self.rag_service.ready:
            logger.warning("RagService not ready; returning empty match list")
            return []

        # 1. Build multiple queries for broader recall
        queries = self._build_queries(business_type, location)
        logger.info(
            "Multi-query search: business_type=%s, queries=%d, queries=%s",
            business_type,
            len(queries),
            queries,
        )

        # 2. Execute all queries in parallel via asyncio.gather
        try:
            docs = await self._multi_query_search(queries, k_per_query=6)
        except Exception:
            logger.exception(
                "Multi-query search failed for business_type=%s", business_type
            )
            return []

        if not docs:
            logger.info(
                "Multi-query search returned no results for business_type=%s",
                business_type,
            )
            return []

        # 3. Extract unique item titles from metadata
        item_titles = self._extract_item_titles(docs)
        if not item_titles:
            logger.info("No actionkit item titles found in vector results metadata")
            return []

        # 4. Query DB for full ActionKit data
        matched = await self._load_full_items(item_titles, session)

        # 5. Assign relevance scores based on vector result ordering
        title_to_score = self._build_score_map(docs)
        for m in matched:
            m.relevance_score = title_to_score.get(m.item.name, 0.0)

        # 6. Filter out low-relevance matches
        pre_filter_count = len(matched)
        matched = [m for m in matched if m.relevance_score >= _MIN_RELEVANCE_SCORE]

        # 7. Sort by relevance (highest first)
        matched.sort(key=lambda m: m.relevance_score, reverse=True)

        logger.info(
            "ActionKit match complete: business_type=%s, queries=%d, "
            "db_items=%d, after_score_filter=%d (min_score=%.2f), "
            "scores=%s",
            business_type,
            len(queries),
            pre_filter_count,
            len(matched),
            _MIN_RELEVANCE_SCORE,
            [(m.item.name[:30], f"{m.relevance_score:.3f}") for m in matched[:10]],
        )
        return matched

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_queries(business_type: str, location: str) -> list[str]:
        """Build multiple search queries for broader recall.

        Strategy:
          - Base query: "{business_type} {location} 창업 인허가"
          - Business-specific queries: "{business_type} {keyword}" per template
          - Falls back to DEFAULT_QUERY_KEYWORDS if no template match
        """
        queries: list[str] = []

        # Base query (always included)
        queries.append(f"{business_type} {location} 창업 인허가")

        # Business-specific keyword queries
        keywords = BUSINESS_QUERY_TEMPLATES.get(business_type, DEFAULT_QUERY_KEYWORDS)
        for kw in keywords:
            queries.append(f"{business_type} {kw}")

        return queries

    async def _multi_query_search(
        self, queries: list[str], k_per_query: int = 6
    ) -> list:
        """Execute multiple vector searches in parallel and merge results.

        Returns a deduplicated list of (Document, score) tuples, keeping the
        highest score when the same document (by page_content) appears in
        multiple query results.
        """
        tasks = [self._vector_search(q, k=k_per_query) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge all results, dedup by page_content keeping best score
        seen: dict[str, tuple] = {}  # page_content -> (Document, score)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "Query %d failed: %s (query=%s)",
                    i,
                    result,
                    queries[i],
                )
                continue

            logger.debug(
                "Query %d returned %d results (query=%s)",
                i,
                len(result),
                queries[i],
            )

            for doc_or_tuple in result:
                if isinstance(doc_or_tuple, tuple):
                    doc, score = doc_or_tuple
                else:
                    doc, score = doc_or_tuple, 1.0

                content_key = doc.page_content
                existing = seen.get(content_key)
                if existing is None or score > existing[1]:
                    seen[content_key] = (doc, score)

        merged = list(seen.values())
        logger.info(
            "Multi-query merge: total_unique=%d from %d queries",
            len(merged),
            len(queries),
        )
        return merged

    async def _vector_search(self, query: str, k: int = 10) -> list:
        """Execute vector similarity search using the RagService's vector_store."""
        from fastapi.concurrency import run_in_threadpool

        vector_store = self.rag_service.vector_store
        docs = await run_in_threadpool(
            vector_store.similarity_search_with_relevance_scores,
            query,
            k=k,
        )
        return docs  # list of (Document, score) tuples

    @staticmethod
    def _extract_item_titles(docs: list) -> list[str]:
        """Extract unique item titles from vector search result metadata.

        The vector store metadata contains a ``title`` field that maps to
        ``ActionKitItem.name``.  Results from both ``laws`` and ``kits``
        domains carry this field.
        """
        seen: set[str] = set()
        titles: list[str] = []
        for doc_or_tuple in docs:
            # similarity_search_with_relevance_scores returns (Document, score)
            doc = doc_or_tuple[0] if isinstance(doc_or_tuple, tuple) else doc_or_tuple
            title = doc.metadata.get("title")
            if title and title not in seen:
                seen.add(title)
                titles.append(title)
        return titles

    @staticmethod
    def _build_score_map(docs: list) -> dict[str, float]:
        """Build title -> best relevance score mapping."""
        scores: dict[str, float] = {}
        for doc_or_tuple in docs:
            if isinstance(doc_or_tuple, tuple):
                doc, score = doc_or_tuple
            else:
                doc, score = doc_or_tuple, 1.0
            title = doc.metadata.get("title", "")
            if title and (title not in scores or score > scores[title]):
                scores[title] = float(score)
        return scores

    async def _load_full_items(
        self,
        item_titles: list[str],
        session: AsyncSession,
    ) -> list[MatchedActionKit]:
        """Load full ActionKit data for the given item titles."""
        # Query items by name
        stmt = select(ActionKitItem).where(
            ActionKitItem.name.in_(item_titles),
            ActionKitItem.is_active.is_(True),
        )
        result = await session.execute(stmt)
        items: Sequence[ActionKitItem] = result.scalars().all()

        if not items:
            return []

        item_ids = [item.id for item in items]
        item_map: dict[int, ActionKitItem] = {item.id: item for item in items}

        # Load highlights
        highlight_stmt = (
            select(ActionKitItemHighlight)
            .where(ActionKitItemHighlight.item_id.in_(item_ids))
            .order_by(ActionKitItemHighlight.sort_order.asc())
        )
        highlight_result = await session.execute(highlight_stmt)
        highlights_by_item: dict[int, list[ActionKitItemHighlight]] = {}
        for h in highlight_result.scalars().all():
            highlights_by_item.setdefault(h.item_id, []).append(h)

        # Load related laws
        law_stmt = (
            select(ActionKitRelatedLaw)
            .where(ActionKitRelatedLaw.item_id.in_(item_ids))
            .order_by(ActionKitRelatedLaw.sort_order.asc())
        )
        law_result = await session.execute(law_stmt)
        laws_by_item: dict[int, list[ActionKitRelatedLaw]] = {}
        for law in law_result.scalars().all():
            laws_by_item.setdefault(law.item_id, []).append(law)

        # Load files from unified files table
        file_stmt = select(File).where(
            File.owner_type == "actionkit_item",
            File.owner_id.in_(item_ids),
            File.is_current.is_(True),
        )
        file_result = await session.execute(file_stmt)
        files_by_item: dict[int, list[File]] = {}
        for f in file_result.scalars().all():
            files_by_item.setdefault(f.owner_id, []).append(f)

        # Load categories for phase mapping
        category_ids = list({item.category_id for item in items})
        cat_stmt = select(ActionKitCategory).where(
            ActionKitCategory.id.in_(category_ids)
        )
        cat_result = await session.execute(cat_stmt)
        category_map: dict[int, ActionKitCategory] = {
            c.id: c for c in cat_result.scalars().all()
        }

        # Assemble MatchedActionKit objects
        matched: list[MatchedActionKit] = []
        seen_ids: set[int] = set()
        for item in items:
            if item.id in seen_ids:
                continue
            seen_ids.add(item.id)

            cat = category_map.get(item.category_id)
            phase = ""
            if cat:
                phase = CATEGORY_TO_PHASE.get(cat.slug, cat.title)

            matched.append(
                MatchedActionKit(
                    item=item,
                    highlights=highlights_by_item.get(item.id, []),
                    related_laws=laws_by_item.get(item.id, []),
                    files=files_by_item.get(item.id, []),
                    phase_group=phase,
                )
            )

        return matched
