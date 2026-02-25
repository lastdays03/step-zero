"""ActionKit Matcher: Fact layer for roadmap generation.

Matches a business type + location to relevant ActionKit items using
hybrid search (vector similarity + relational DB JOIN).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.logging import get_logger
from app.features.rag.application.rag_service import RagService
from app.models.actionkit import (
    ActionKitCategory,
    ActionKitFile,
    ActionKitItem,
    ActionKitItemHighlight,
    ActionKitRelatedLaw,
)

logger = get_logger(__name__)

# ActionKit category slug -> roadmap phase name mapping
CATEGORY_TO_PHASE: dict[str, str] = {
    # LAW_DATA chapter keys (domain=laws, slug="1".."6")
    "1": "입지 검토",
    "2": "영업 인허가",
    "3": "안전·소방",
    "4": "영업 준수사항",
    "5": "위반 대응",
    "6": "행정처분 구제",
    # ACTION_KIT_DATA category slugs (domain=kits)
    "legal": "법률 준비",
    "tax": "세무 설정",
    "hr": "인사·노무",
    "grant": "정책자금 신청",
}


@dataclass
class MatchedActionKit:
    """Structured fact data from ActionKit matching."""

    item: ActionKitItem
    highlights: list[ActionKitItemHighlight] = field(default_factory=list)
    related_laws: list[ActionKitRelatedLaw] = field(default_factory=list)
    files: list[ActionKitFile] = field(default_factory=list)
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
        """Find relevant ActionKit items for a business type via hybrid search."""
        if not self.rag_service.ready:
            logger.warning("RagService not ready; returning empty match list")
            return []

        # 1. Vector similarity search
        search_query = f"{business_type} {location} 창업 인허가"
        try:
            docs = await self._vector_search(search_query, k=10)
        except Exception:
            logger.exception("Vector search failed for query=%s", search_query)
            return []

        if not docs:
            logger.info("Vector search returned no results for query=%s", search_query)
            return []

        # 2. Extract unique item titles from metadata
        item_titles = self._extract_item_titles(docs)
        if not item_titles:
            logger.info("No actionkit item titles found in vector results metadata")
            return []

        # 3. Query DB for full ActionKit data
        matched = await self._load_full_items(item_titles, session)

        # 4. Assign relevance scores based on vector result ordering
        title_to_score = self._build_score_map(docs)
        for m in matched:
            m.relevance_score = title_to_score.get(m.item.name, 0.0)

        # 5. Sort by relevance (highest first)
        matched.sort(key=lambda m: m.relevance_score, reverse=True)

        logger.info(
            "ActionKit match complete: query=%s, matched_items=%d",
            search_query,
            len(matched),
        )
        return matched

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

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

        # Load files
        file_stmt = (
            select(ActionKitFile)
            .where(
                ActionKitFile.item_id.in_(item_ids),
                ActionKitFile.is_current.is_(True),
            )
        )
        file_result = await session.execute(file_stmt)
        files_by_item: dict[int, list[ActionKitFile]] = {}
        for f in file_result.scalars().all():
            files_by_item.setdefault(f.item_id, []).append(f)

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
