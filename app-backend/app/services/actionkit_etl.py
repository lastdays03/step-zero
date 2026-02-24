"""ActionKit 데이터 → ProcessedLawData 직접 매핑 브릿지.

LLM 호출 없이 구조화된 ActionKit 시드 데이터를
VectorStoreService가 소비할 수 있는 ProcessedLawData 형태로 변환한다.

두 가지 사용 방식:
    # 1. ActionKitDataSource와 함께 (권장: PDF 파싱 포함)
    source = ActionKitDataSource()
    bridge = ActionKitETLBridge()
    law_data_list = await source.fetch_all_laws()
    processed = [await bridge.process(ld) for ld in law_data_list]

    # 2. 독립 사용 (seed 메타데이터만, PDF 파싱 없음)
    bridge = ActionKitETLBridge()
    processed = bridge.convert_all()
"""

from __future__ import annotations

from typing import Any, List

from app.core.logging import get_logger
from app.services.law_etl import ProcessedLawData
from app.services.law_fetcher import LawData, SourceType

logger = get_logger(__name__)


class ActionKitETLBridge:
    """ActionKit 시드 데이터를 ProcessedLawData로 직접 변환.

    LawETLProcessor와 달리 LLM을 사용하지 않고,
    ActionKit의 구조화된 필드(highlights, relatedLaws)를
    그대로 매핑하여 ProcessedLawData를 생성한다.
    """

    # ── ActionKitDataSource 연동 인터페이스 ──

    async def process(self, law_data: LawData) -> ProcessedLawData:
        """LawData(ActionKitDataSource 출력)를 ProcessedLawData로 변환.

        LawETLProcessor.process()와 동일한 시그니처로,
        통합 스크립트에서 교체 가능하다.
        """
        metadata = law_data.metadata or {}

        # guide_text: ActionKitDataSource가 조합한 content_body를 그대로 사용
        guide_text = law_data.content_body

        # summary: content_body 둘째 줄 (첫 줄은 title)
        summary = self._extract_summary(law_data)

        # law_reference: 제목을 대표 참조로 사용
        law_reference = law_data.title

        # category
        category = metadata.get("category", law_data.category)

        return ProcessedLawData(
            title=law_data.title,
            summary=summary,
            guide_text=guide_text,
            law_reference=law_reference,
            category=category,
            original_data=law_data,
        )

    async def process_batch(self, items: List[LawData]) -> List[ProcessedLawData]:
        """배치 변환. LLM 호출이 없으므로 순차 처리해도 빠르다."""
        results = []
        for item in items:
            results.append(await self.process(item))

        logger.info(
            "ActionKit ETL 배치 완료: %d건 변환 (LLM 호출 0회)",
            len(results),
        )
        return results

    @staticmethod
    def _extract_summary(law_data: LawData) -> str:
        """content_body에서 summary를 추출한다."""
        lines = law_data.content_body.strip().split("\n")
        # 첫 줄: title, 둘째 줄: summary
        if len(lines) >= 2:
            candidate = lines[1].strip()
            if candidate and not candidate.startswith("#"):
                return candidate
        return law_data.title

    # ── 독립 사용 인터페이스 (seed 데이터 직접 참조) ──

    def convert_law_item(
        self,
        item: dict[str, Any],
        chapter_key: str,
        chapter_title: str,
    ) -> ProcessedLawData:
        """LAW_DATA 아이템을 ProcessedLawData로 변환."""
        title = item["name"]
        summary = item.get("summary", "")
        highlights = item.get("highlights", [])

        # guide_text: highlights → 불릿 포인트
        guide_parts: list[str] = []
        if highlights:
            guide_parts.append("## 핵심 포인트")
            for h in highlights:
                guide_parts.append(f"- {h}")
        if summary:
            guide_parts.append(f"\n## 요약\n{summary}")

        guide_text = "\n".join(guide_parts) if guide_parts else summary

        law_reference = title
        category = f"actionkit/laws/{chapter_key}"

        original = LawData(
            title=title,
            category=category,
            content_body=guide_text,
            source_type=SourceType.LOCAL,
            file_path=item.get("path"),
            metadata={
                "source": "actionkit",
                "domain": "laws",
                "chapter_key": chapter_key,
                "chapter_title": chapter_title,
            },
        )

        return ProcessedLawData(
            title=title,
            summary=summary,
            guide_text=guide_text,
            law_reference=law_reference,
            category=category,
            original_data=original,
        )

    def convert_kit_item(
        self,
        item: dict[str, Any],
        category_slug: str,
        category_title: str,
    ) -> ProcessedLawData:
        """ACTION_KIT_DATA 아이템을 ProcessedLawData로 변환."""
        title = item["name"]
        summary = item.get("summary", "")
        related_laws = item.get("relatedLaws", [])
        tag = item.get("tag", "")

        guide_parts: list[str] = []
        if tag:
            guide_parts.append(f"## {tag.strip('[]')} 가이드")
        if summary:
            guide_parts.append(summary)

        if related_laws:
            guide_parts.append("\n## 관련 법령")
            for law in related_laws:
                law_name = law.get("name", "")
                law_summary = law.get("summary", "")
                if law_summary:
                    guide_parts.append(f"- **{law_name}**: {law_summary}")
                else:
                    guide_parts.append(f"- **{law_name}**")

        guide_text = "\n".join(guide_parts) if guide_parts else summary

        if related_laws:
            law_reference = related_laws[0].get("name", title)
        else:
            law_reference = title

        category = f"actionkit/kits/{category_slug}"

        original = LawData(
            title=title,
            category=category,
            content_body=guide_text,
            source_type=SourceType.LOCAL,
            file_path=item.get("path"),
            metadata={
                "source": "actionkit",
                "domain": "kits",
                "category_slug": category_slug,
                "category_title": category_title,
                "tag": tag,
                "dday": item.get("dday"),
            },
        )

        return ProcessedLawData(
            title=title,
            summary=summary,
            guide_text=guide_text,
            law_reference=law_reference,
            category=category,
            original_data=original,
        )

    def convert_all(self) -> list[ProcessedLawData]:
        """전체 ActionKit 시드 데이터(46개)를 ProcessedLawData로 변환.

        LAW_DATA(21개) + ACTION_KIT_DATA(25개, "all" 제외) = 46개.
        LLM 호출 0회.
        """
        from scripts.seeds.actionkit_seed_source import ACTION_KIT_DATA, LAW_DATA

        results: list[ProcessedLawData] = []

        # 1. LAW_DATA 변환 (21개)
        for chapter_key, chapter in LAW_DATA.items():
            chapter_title = chapter["title"]
            for item in chapter["items"]:
                processed = self.convert_law_item(item, chapter_key, chapter_title)
                results.append(processed)

        law_count = len(results)

        # 2. ACTION_KIT_DATA 변환 (25개, "all" 제외)
        for category_slug, category_data in ACTION_KIT_DATA.items():
            if category_slug == "all":
                continue
            category_title = category_data["title"]
            for item in category_data["items"]:
                processed = self.convert_kit_item(item, category_slug, category_title)
                results.append(processed)

        kit_count = len(results) - law_count

        logger.info(
            "ActionKit ETL 완료: laws=%d, kits=%d, total=%d (LLM 호출: 0)",
            law_count,
            kit_count,
            len(results),
        )
        return results
