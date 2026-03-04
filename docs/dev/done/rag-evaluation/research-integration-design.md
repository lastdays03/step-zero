# ActionKit-RAG 통합 아키텍처 및 자동 생성 스크립트 설계

> 작성일: 2026-02-24
> 작성자: rag-architect agent

---

## 1. 기존 RAG 파이프라인 분석

### 1.1 전체 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                     현재 RAG 파이프라인                               │
│                                                                     │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐   │
│  │ LawDataSource│───▶│ LawETLProcessor │───▶│ VectorStoreService│  │
│  │   (ABC)      │    │  (LLM 구조화)    │    │   (PGVector)     │   │
│  └──────────────┘    └─────────────────┘    └──────────────────┘   │
│        │                                            │               │
│        │                                            ▼               │
│  ┌──────────────┐                          ┌──────────────────┐    │
│  │LocalFileSource│                          │   RagService     │    │
│  │ (.pdf, .md)  │                          │ (Retriever+LLM)  │    │
│  └──────────────┘                          └──────────────────┘    │
│                                                     │               │
│                                                     ▼               │
│                                              질의 응답 (SSE)         │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 핵심 인터페이스

| 컴포넌트 | 파일 위치 | 역할 |
|---------|----------|------|
| `LawDataSource` (ABC) | `app/services/law_fetcher.py` | 데이터 소스 추상화. `fetch_all_laws() -> List[LawData]` |
| `LawData` (Pydantic) | `app/services/law_fetcher.py` | 통합 데이터 모델: title, category, content_body, source_type, metadata |
| `LocalFileSource` | `app/services/law_fetcher.py` | `.temp/` 디렉토리의 PDF/MD 파일 읽기 |
| `LawETLProcessor` | `app/services/law_etl.py` | LLM(GPT-4-turbo)으로 raw text → `ProcessedLawData` 구조화 |
| `ProcessedLawData` | `app/services/law_etl.py` | title, summary, guide_text, law_reference, category |
| `VectorStoreService` | `app/services/vector_store.py` | `ProcessedLawData` → LangChain `Document` → PGVector("law_vectors") |
| `RagService` | `app/features/rag/.../rag_service.py` | PGVector retriever(k=3) + LLM 체인 → 질의응답 |

### 1.3 확장 포인트 (Extension Points)

1. **`LawDataSource` ABC**: 새로운 구현체를 추가하여 데이터 소스 확장 가능
   - 현재: `LocalFileSource` (파일시스템)
   - 확장: `ActionKitDataSource` (DB 기반)

2. **`LawETLProcessor.process()`**: LawData를 받아 ProcessedLawData로 변환
   - ActionKit 데이터는 이미 구조화되어 있어 ETL 단순화 가능

3. **`VectorStoreService.add_documents()`**: ProcessedLawData 리스트를 받아 벡터 저장
   - 컬렉션명으로 데이터 소스 구분 가능 (e.g., "actionkit_vectors")

4. **`RagService`**: retriever의 collection_name 변경 또는 다중 retriever 조합 가능

### 1.4 현재 파이프라인의 한계

| 한계 | 상세 |
|------|------|
| 단일 데이터소스 | LocalFileSource만 존재, DB 기반 소스 없음 |
| 단일 컬렉션 | "law_vectors" 하드코딩, 멀티소스 구분 불가 |
| ETL 비효율 | ActionKit은 이미 구조화된 메타데이터를 보유하나, 현재 ETL은 raw text 전용 |
| 평가 데이터 수동 관리 | golden_dataset.json이 수작업 생성, ActionKit 데이터와 연동 없음 |

---

## 2. ActionKit 데이터 모델 분석

### 2.1 DB 스키마 (5개 테이블)

```
┌──────────────────────┐     ┌──────────────────────┐
│ actionkit_categories │     │   actionkit_items     │
│──────────────────────│     │──────────────────────│
│ id (PK)             │◀────│ category_id (FK)      │
│ domain (laws|kits)  │     │ id (PK)              │
│ slug                │     │ domain (laws|kits)    │
│ title               │     │ name                  │
│ sort_order          │     │ summary               │
│ is_active           │     │ tag                   │
└──────────────────────┘     │ ext, size_label       │
                             │ file_type, dday       │
                             │ is_active             │
                             └───────┬──────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                 ▼
          ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
          │ item_highlights │ │ related_laws │ │ actionkit_files│
          │─────────────────│ │──────────────│ │──────────────│
          │ item_id (FK)    │ │ item_id (FK) │ │ item_id (FK) │
          │ content         │ │ law_name     │ │ version      │
          │ sort_order      │ │ law_summary  │ │ object_key   │
          └─────────────────┘ └──────────────┘ │ mime_type    │
                                                │ is_current   │
                                                └──────────────┘
```

### 2.2 Seed 데이터 분석 결과

| 도메인 | 카테고리 수 | 아이템 수 | 하이라이트 | 관련법률 |
|--------|-----------|----------|-----------|---------|
| **laws** (LAW_DATA) | 6개 장 | 20개 법령 | 42개 | - |
| **kits** (ACTION_KIT_DATA) | 4개 카테고리 (legal, tax, hr, grant) | 22개 키트 | - | 32개 |

### 2.3 ActionKit의 RAG 활용 가능한 정보

**Laws 도메인 (법령)**:
- `item.name`: 법령명 (예: "건축법 제2조 (용도 분류)")
- `item.summary`: 법령 요약 (예: "건축물의 용도를 29개 군으로 분류...")
- `highlight.content`: 핵심 포인트 (예: "일반음식점은 '제2종 근린생활시설'군에 해당")
- `category.title`: 장 제목 (예: "Ⅰ. 입지 적법성")
- `file.object_key`: 실제 PDF 파일 경로

**Kits 도메인 (액션키트)**:
- `item.name`: 키트명 (예: "식품위생법 영업신고 실무 패키지")
- `item.summary`: 키트 설명
- `item.tag`: 분류 태그 (예: "[영업 신고]")
- `related_law.law_name`: 관련 법률명
- `related_law.law_summary`: 관련 법률 요약
- `file.object_key`: 실제 파일 경로

---

## 3. ActionKitDataSource 설계

### 3.1 클래스 다이어그램

```
                    LawDataSource (ABC)
                    ├── fetch_all_laws() -> List[LawData]
                    │
          ┌─────────┴──────────┐
          │                    │
  LocalFileSource      ActionKitDataSource (NEW)
  (.pdf/.md 파일)      (DB 메타데이터 + PDF 텍스트)
```

### 3.2 ActionKitDataSource 인터페이스

```python
# app/services/actionkit_data_source.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.law_fetcher import LawDataSource, LawData, SourceType
from app.repositories.actionkit_repository import ActionKitRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class ActionKitDataSource(LawDataSource):
    """
    ActionKit DB에서 법령/키트 데이터를 읽어 LawData로 변환하는 데이터소스.

    두 가지 모드를 지원:
    1. metadata_only=True: DB 메타데이터(name, summary, highlights, related_laws)만 활용
    2. metadata_only=False: 메타데이터 + PDF 파일 텍스트 추출 (풍부한 컨텍스트)
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        domains: list[str] | None = None,     # ["laws", "kits"] 또는 특정 도메인
        include_file_content: bool = False,    # PDF 본문 텍스트 추출 여부
        storage_base_path: str = "",           # 파일 저장 경로 (uploads/actionkit/)
    ):
        self.repository = ActionKitRepository(session)
        self.domains = domains or ["laws", "kits"]
        self.include_file_content = include_file_content
        self.storage_base_path = storage_base_path

    async def fetch_all_laws(self) -> List[LawData]:
        """
        ActionKit DB의 모든 활성 아이템을 LawData 리스트로 변환.

        Returns:
            List[LawData]: 각 ActionKitItem이 하나의 LawData로 매핑됨
        """
        results: list[LawData] = []

        for domain in self.domains:
            domain_results = await self._fetch_domain(domain)
            results.extend(domain_results)

        logger.info(f"ActionKit에서 데이터 로드 완료: count={len(results)}, domains={self.domains}")
        return results

    async def _fetch_domain(self, domain: str) -> list[LawData]:
        """단일 도메인의 모든 아이템을 가져옴."""
        categories = await self.repository.list_categories(domain=domain)
        if not categories:
            return []

        category_ids = [c.id for c in categories if c.id is not None]
        category_map = {c.id: c for c in categories}

        items = await self.repository.list_items_for_categories(
            domain=domain, category_ids=category_ids
        )
        if not items:
            return []

        item_ids = [i.id for i in items if i.id is not None]

        # 관련 데이터 일괄 로드
        highlights = await self.repository.list_item_highlights(item_ids=item_ids)
        related_laws = await self.repository.list_related_laws(item_ids=item_ids)
        files = await self.repository.list_current_files(item_ids=item_ids)

        # 맵 구성
        highlights_map: dict[int, list[str]] = {}
        for h in highlights:
            highlights_map.setdefault(h.item_id, []).append(h.content)

        related_map: dict[int, list[dict]] = {}
        for r in related_laws:
            related_map.setdefault(r.item_id, []).append({
                "law_name": r.law_name,
                "law_summary": r.law_summary or "",
            })

        file_map = {f.item_id: f for f in files}

        # LawData 변환
        results: list[LawData] = []
        for item in items:
            if item.id is None:
                continue

            category = category_map.get(item.category_id)
            category_title = category.title if category else "Uncategorized"

            # content_body 구성: 메타데이터 기반 풍부한 텍스트
            content_body = self._build_content_body(
                item=item,
                category_title=category_title,
                highlights=highlights_map.get(item.id, []),
                related_laws=related_map.get(item.id, []),
            )

            # PDF 본문 추가 (옵션)
            file_content = ""
            current_file = file_map.get(item.id)
            if self.include_file_content and current_file:
                file_content = await self._extract_file_text(current_file.object_key)
                if file_content:
                    content_body += f"\n\n---\n[문서 본문]\n{file_content}"

            law_data = LawData(
                title=item.name,
                category=category_title,
                content_body=content_body,
                source_type=SourceType.LOCAL,  # DB이지만 로컬 데이터
                file_path=current_file.object_key if current_file else None,
                metadata={
                    "actionkit_item_id": item.id,
                    "actionkit_domain": domain,
                    "actionkit_category_slug": category.slug if category else "",
                    "tag": item.tag or "",
                    "summary": item.summary,
                    "highlights": highlights_map.get(item.id, []),
                    "related_laws": related_map.get(item.id, []),
                    "file_type": item.file_type or item.ext or "",
                    "dday": item.dday or "",
                },
            )
            results.append(law_data)

        return results

    @staticmethod
    def _build_content_body(
        *,
        item,              # ActionKitItem
        category_title: str,
        highlights: list[str],
        related_laws: list[dict],
    ) -> str:
        """메타데이터를 기반으로 검색 가능한 텍스트 본문 구성."""
        parts = [
            f"# {item.name}",
            f"분류: {category_title}",
            f"요약: {item.summary}",
        ]

        if item.tag:
            parts.append(f"태그: {item.tag}")

        if highlights:
            parts.append("\n## 핵심 포인트")
            for h in highlights:
                parts.append(f"- {h}")

        if related_laws:
            parts.append("\n## 관련 법령")
            for law in related_laws:
                parts.append(f"- {law['law_name']}: {law['law_summary']}")

        return "\n".join(parts)

    async def _extract_file_text(self, object_key: str) -> str:
        """파일에서 텍스트 추출 (PDF 지원). Phase 2에서 구현."""
        # TODO: Phase 2 - pdfplumber를 활용한 PDF 텍스트 추출
        # file_path = Path(self.storage_base_path) / object_key
        # if file_path.suffix.lower() == ".pdf":
        #     return extract_text_from_pdf(file_path)
        return ""
```

### 3.3 ETL 우회 전략 (ActionKit 전용)

ActionKit 데이터는 이미 구조화(name, summary, highlights, related_laws)되어 있으므로,
`LawETLProcessor`의 LLM 호출 없이 직접 `ProcessedLawData`로 변환 가능:

```python
# app/services/actionkit_etl.py

from app.services.law_etl import ProcessedLawData
from app.services.law_fetcher import LawData


class ActionKitETLProcessor:
    """
    ActionKit 데이터 전용 ETL.
    이미 구조화된 메타데이터를 활용하여 LLM 호출 없이 ProcessedLawData로 변환.
    """

    async def process(self, law_data: LawData) -> ProcessedLawData:
        metadata = law_data.metadata

        # highlights를 guide_text로 변환
        highlights = metadata.get("highlights", [])
        guide_text_parts = [law_data.content_body]
        if highlights:
            guide_text_parts.append("\n핵심 확인사항:")
            for h in highlights:
                guide_text_parts.append(f"  - {h}")

        # related_laws를 law_reference로 변환
        related_laws = metadata.get("related_laws", [])
        law_refs = []
        for law in related_laws:
            law_refs.append(f"[{law['law_name']}] {law['law_summary']}")

        return ProcessedLawData(
            title=law_data.title,
            summary=metadata.get("summary", ""),
            guide_text="\n".join(guide_text_parts),
            law_reference="\n".join(law_refs) if law_refs else "N/A",
            category=law_data.category,
            original_data=law_data,
        )
```

---

## 4. generate_golden_dataset.py 설계안

### 4.1 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                  Q&A 자동 생성 파이프라인                          │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ ActionKit DB │───▶│ Context 구성  │───▶│ LLM Q&A 생성     │  │
│  │ (메타데이터)   │    │ (아이템별)     │    │ (GPT-4-turbo)   │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│                                                   │             │
│                                                   ▼             │
│                                          ┌──────────────────┐  │
│                                          │ golden_dataset.json│ │
│                                          │  (호환 형식 출력)   │  │
│                                          └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 스크립트 설계

```python
# scripts/generate_golden_dataset.py
"""
ActionKit 메타데이터 기반 RAG 평가 골든 데이터셋 자동 생성 스크립트.

Usage:
    python -m scripts.generate_golden_dataset \
        --output tests/eval/data/golden_dataset_actionkit.json \
        --questions-per-item 2 \
        --domains laws,kits
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


# ──────────────────────────────────────
# 1. 출력 스키마 (golden_dataset.json 호환)
# ──────────────────────────────────────

class GoldenQA(BaseModel):
    """golden_dataset.json의 단일 항목과 동일한 스키마."""
    id: str = Field(..., description="고유 ID (예: actionkit-laws-001)")
    question: str = Field(..., description="사용자 질문")
    ground_truth: str = Field(..., description="정답 (2~3문장)")
    expected_source: str = Field(default="legal_rag", description="예상 응답 소스")
    category: str = Field(..., description="질문 유형: factual|procedural|interpretive")
    difficulty: str = Field(..., description="난이도: easy|medium|hard")
    expected_keywords: list[str] = Field(..., description="응답에 포함되어야 할 키워드")
    expected_law_reference: str | None = Field(None, description="참조 법령명")
    requires_citation: bool = Field(default=True, description="인용 필요 여부")


# ──────────────────────────────────────
# 2. LLM 프롬프트 전략
# ──────────────────────────────────────

QA_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 한국 창업 법률 전문가입니다.
주어진 법령/키트 메타데이터를 기반으로 스타트업 창업자가 실제로 물어볼 법한 Q&A 쌍을 생성합니다.

## 생성 규칙
1. 질문은 실제 창업자의 관점에서 자연스러운 한국어로 작성
2. 정답(ground_truth)은 메타데이터에 포함된 정보만으로 구성 (환각 금지)
3. 질문 유형을 다양하게 분배:
   - factual: 사실 확인 질문 ("~은 무엇인가요?")
   - procedural: 절차 질문 ("~하려면 어떻게 해야 하나요?")
   - interpretive: 해석/판단 질문 ("~한 경우에도 적용되나요?")
4. 난이도 분배: easy(직접적 답변), medium(추론 필요), hard(복합 조건 해석)
5. expected_keywords는 정답에 반드시 포함되는 핵심 용어 2~4개
6. expected_law_reference는 관련 법령명 (없으면 null)

## 출력 형식
JSON 배열로 {questions_per_item}개의 Q&A를 생성하세요.
각 항목은 다음 필드를 포함: question, ground_truth, category, difficulty, expected_keywords, expected_law_reference, requires_citation
"""),
    ("human", """## 법령/키트 정보

제목: {title}
분류: {category_title}
요약: {summary}
태그: {tag}

### 핵심 포인트 (Highlights)
{highlights_text}

### 관련 법령
{related_laws_text}

위 정보를 기반으로 {questions_per_item}개의 Q&A 쌍을 생성하세요."""),
])


# ──────────────────────────────────────
# 3. 메인 생성 로직
# ──────────────────────────────────────

class GoldenDatasetGenerator:
    """ActionKit 메타데이터 → Golden Dataset 변환기."""

    def __init__(
        self,
        *,
        openai_api_key: str,
        model: str = "gpt-4-turbo-preview",
        questions_per_item: int = 2,
    ):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.7,  # 질문 다양성을 위해 약간 높게
            api_key=openai_api_key,
        )
        self.questions_per_item = questions_per_item
        self.parser = JsonOutputParser()
        self.chain = QA_GENERATION_PROMPT | self.llm | self.parser

    async def generate_for_item(
        self,
        *,
        item_id: int,
        domain: str,
        title: str,
        category_title: str,
        summary: str,
        tag: str,
        highlights: list[str],
        related_laws: list[dict],
        seq: int,
    ) -> list[GoldenQA]:
        """단일 ActionKitItem에 대한 Q&A 생성."""

        highlights_text = "\n".join(f"- {h}" for h in highlights) if highlights else "(없음)"
        related_laws_text = "\n".join(
            f"- {law['law_name']}: {law.get('law_summary', '')}"
            for law in related_laws
        ) if related_laws else "(없음)"

        result = await self.chain.ainvoke({
            "title": title,
            "category_title": category_title,
            "summary": summary,
            "tag": tag or "",
            "highlights_text": highlights_text,
            "related_laws_text": related_laws_text,
            "questions_per_item": self.questions_per_item,
        })

        # 결과를 GoldenQA로 변환
        qa_list: list[GoldenQA] = []
        items = result if isinstance(result, list) else [result]

        for i, qa_raw in enumerate(items):
            qa = GoldenQA(
                id=f"actionkit-{domain}-{seq:03d}-{i+1}",
                question=qa_raw["question"],
                ground_truth=qa_raw["ground_truth"],
                expected_source="legal_rag",
                category=qa_raw.get("category", "factual"),
                difficulty=qa_raw.get("difficulty", "medium"),
                expected_keywords=qa_raw.get("expected_keywords", []),
                expected_law_reference=qa_raw.get("expected_law_reference"),
                requires_citation=qa_raw.get("requires_citation", True),
            )
            qa_list.append(qa)

        return qa_list

    async def generate_from_seed_data(
        self,
        *,
        law_data: dict[str, dict],
        kit_data: dict[str, dict],
    ) -> list[dict[str, Any]]:
        """Seed 데이터에서 직접 생성 (DB 없이 테스트용)."""
        all_qa: list[GoldenQA] = []
        seq = 1

        # Laws 도메인
        for chapter_id, chapter in law_data.items():
            for item in chapter.get("items", []):
                qa_list = await self.generate_for_item(
                    item_id=seq,
                    domain="laws",
                    title=item["name"],
                    category_title=chapter["title"],
                    summary=item.get("summary", ""),
                    tag="",
                    highlights=item.get("highlights", []),
                    related_laws=[],
                    seq=seq,
                )
                all_qa.extend(qa_list)
                seq += 1

        # Kits 도메인
        for cat_id, category in kit_data.items():
            if cat_id == "all":
                continue
            for item in category.get("items", []):
                qa_list = await self.generate_for_item(
                    item_id=seq,
                    domain="kits",
                    title=item["name"],
                    category_title=category["title"],
                    summary=item.get("summary", ""),
                    tag=item.get("tag", ""),
                    highlights=[],
                    related_laws=item.get("relatedLaws", []) or [],
                    seq=seq,
                )
                all_qa.extend(qa_list)
                seq += 1

        return [qa.model_dump() for qa in all_qa]


# ──────────────────────────────────────
# 4. CLI 엔트리포인트
# ──────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="ActionKit 기반 골든 데이터셋 생성")
    parser.add_argument("--output", type=str, default="tests/eval/data/golden_dataset_actionkit.json")
    parser.add_argument("--questions-per-item", type=int, default=2)
    parser.add_argument("--domains", type=str, default="laws,kits")
    parser.add_argument("--mode", choices=["seed", "db"], default="seed",
                       help="seed: seed 파일 사용, db: 실제 DB 조회")
    args = parser.parse_args()

    from app.core.config import get_settings
    settings = get_settings()

    generator = GoldenDatasetGenerator(
        openai_api_key=settings.OPENAI_API_KEY,
        questions_per_item=args.questions_per_item,
    )

    if args.mode == "seed":
        from scripts.seeds.actionkit_seed_source import LAW_DATA, ACTION_KIT_DATA
        results = await generator.generate_from_seed_data(
            law_data=LAW_DATA,
            kit_data=ACTION_KIT_DATA,
        )
    else:
        # DB 모드: 실제 DB에서 조회
        # TODO: Phase 2 구현
        raise NotImplementedError("DB 모드는 Phase 2에서 구현 예정")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"생성 완료: {len(results)}개 Q&A → {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 프롬프트 전략 상세

| 전략 | 설명 | 근거 |
|------|------|------|
| **메타데이터 기반 생성** | DB의 name, summary, highlights, related_laws만 활용 | PDF 파싱 없이 즉시 생성 가능 |
| **다양성 확보** | temperature=0.7, 유형/난이도 분배 지시 | 평가 커버리지 확보 |
| **환각 방지** | "메타데이터에 포함된 정보만으로 구성" 명시 | ground_truth 신뢰성 |
| **ID 체계** | `actionkit-{domain}-{seq}-{sub}` | 기존 `legal-001` 체계와 구분, 추적 용이 |
| **호환 형식** | GoldenQA 스키마 = golden_dataset.json과 동일 | 기존 평가 프레임워크 즉시 활용 |

### 4.4 예상 생성 결과 (Seed 데이터 기준)

| 도메인 | 아이템 수 | Q&A/아이템 | 예상 총 Q&A |
|--------|----------|-----------|------------|
| laws | 20 | 2 | 40 |
| kits (all 제외) | 22 | 2 | 44 |
| **합계** | **42** | **2** | **84** |

기존 golden_dataset.json의 20개와 합치면 **총 104개**의 평가 데이터셋 확보.

---

## 5. 평가 프레임워크 확장 방안

### 5.1 기존 3-Tier 평가 시스템

```
Tier 1: 단위 테스트 (키워드, 인용, 포맷)
Tier 2: LLM 기반 메트릭 (의미적 유사도, 충실도, 관련성)
Tier 3: 전체 통합 테스트 (E2E 품질)
```

### 5.2 확장된 conftest.py 설계

```python
# tests/eval/conftest.py (확장안)

@pytest.fixture(scope="session")
def actionkit_dataset() -> list[dict[str, Any]]:
    """ActionKit 기반 골든 데이터셋 로드."""
    path = EVAL_DATA_DIR / "golden_dataset_actionkit.json"
    if not path.exists():
        pytest.skip("ActionKit 골든 데이터셋 미생성")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def combined_dataset(golden_dataset, actionkit_dataset) -> list[dict[str, Any]]:
    """기존 + ActionKit 통합 데이터셋."""
    return golden_dataset + actionkit_dataset

@pytest.fixture(scope="session")
def actionkit_law_cases(actionkit_dataset) -> list[dict]:
    """ActionKit laws 도메인 케이스."""
    return [c for c in actionkit_dataset if "actionkit-laws" in c["id"]]

@pytest.fixture(scope="session")
def actionkit_kit_cases(actionkit_dataset) -> list[dict]:
    """ActionKit kits 도메인 케이스."""
    return [c for c in actionkit_dataset if "actionkit-kits" in c["id"]]
```

### 5.3 새로운 평가 차원

| 평가 항목 | Tier | 설명 |
|----------|------|------|
| ActionKit 소스 정확도 | T1 | 응답이 올바른 ActionKit 아이템을 참조하는지 |
| 하이라이트 커버리지 | T1 | 핵심 포인트(highlights)가 응답에 반영되는 비율 |
| 관련 법령 인용 정확도 | T1 | related_laws의 법령명이 정확히 인용되는지 |
| 메타데이터 충실도 | T2 | LLM 판정: 응답이 ActionKit 메타데이터와 일관적인지 |
| 도메인 간 라우팅 정확도 | T2 | laws vs kits 질문을 올바른 소스로 라우팅하는지 |

---

## 6. 통합 아키텍처 (목표 상태)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    확장된 RAG 파이프라인 (목표 상태)                       │
│                                                                         │
│  ┌──────────────────┐                                                   │
│  │  LawDataSource   │ (ABC)                                             │
│  │  ├─ LocalFileSource ──── .temp/ (PDF, MD)                            │
│  │  └─ ActionKitDataSource ──── ActionKit DB ──── PDF Files             │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐    ┌──────────────────┐                           │
│  │ ETL Processor    │    │ ActionKit ETL    │ (LLM 불필요)               │
│  │ (LLM 구조화)     │    │ (메타데이터 직접) │                            │
│  └────────┬─────────┘    └────────┬─────────┘                           │
│           │                       │                                     │
│           ▼                       ▼                                     │
│  ┌─────────────────────────────────────────┐                            │
│  │        VectorStoreService               │                            │
│  │  ├─ collection: "law_vectors"           │ (기존 법령)                 │
│  │  └─ collection: "actionkit_vectors"     │ (ActionKit)                │
│  └────────────────────┬────────────────────┘                            │
│                       │                                                 │
│                       ▼                                                 │
│  ┌─────────────────────────────────────────┐                            │
│  │          RagService (확장)               │                            │
│  │  ├─ retriever: EnsembleRetriever        │                            │
│  │  │   ├─ law_vectors retriever           │                            │
│  │  │   └─ actionkit_vectors retriever     │                            │
│  │  └─ chain: retriever → prompt → LLM    │                            │
│  └─────────────────────────────────────────┘                            │
│                       │                                                 │
│                       ▼                                                 │
│               사용자 질의 응답 (SSE)                                      │
│                                                                         │
│  ┌─────────────────────────────────────────┐                            │
│  │      평가 프레임워크 (3-Tier)              │                          │
│  │  ├─ golden_dataset.json (기존 20개)      │                           │
│  │  ├─ golden_dataset_actionkit.json (84개) │ ← generate_golden_dataset │
│  │  └─ conftest.py (확장 fixtures)          │                           │
│  └─────────────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 단계별 구현 로드맵

### Phase 1: 평가 데이터 생성 (1~2일)

**목표**: ActionKit 메타데이터 기반 골든 데이터셋 자동 생성

| 단계 | 작업 | 산출물 |
|------|------|--------|
| 1-1 | `scripts/generate_golden_dataset.py` 구현 (seed 모드) | 스크립트 파일 |
| 1-2 | Seed 데이터 기반 84개 Q&A 생성 | `golden_dataset_actionkit.json` |
| 1-3 | 생성된 Q&A 품질 검증 (수동 샘플링) | 품질 리포트 |
| 1-4 | `conftest.py` 확장 (actionkit fixtures) | 확장된 테스트 설정 |

**의존성**: 없음 (seed 데이터만 활용)
**리스크**: LLM 생성 Q&A 품질 불균일 → 수동 검수 필요

### Phase 2: ActionKitDataSource 통합 (2~3일)

**목표**: ActionKit DB → RAG 벡터 스토어 연결

| 단계 | 작업 | 산출물 |
|------|------|--------|
| 2-1 | `ActionKitDataSource` 클래스 구현 | `app/services/actionkit_data_source.py` |
| 2-2 | `ActionKitETLProcessor` 구현 | `app/services/actionkit_etl.py` |
| 2-3 | `VectorStoreService` 확장 (멀티 컬렉션) | collection_name 파라미터화 |
| 2-4 | 인제스트 스크립트 작성 | `scripts/ingest_actionkit.py` |
| 2-5 | Phase 1 데이터셋으로 Tier 1~2 평가 실행 | 평가 결과 리포트 |

**의존성**: Phase 1 완료
**리스크**: PDF 파싱 품질 → `include_file_content=False`로 시작, 점진적 활성화

### Phase 3: RagService 멀티소스 확장 (1~2일)

**목표**: 다중 벡터 컬렉션을 통합하는 RAG 서비스

| 단계 | 작업 | 산출물 |
|------|------|--------|
| 3-1 | `RagService`에 `EnsembleRetriever` 적용 | 확장된 RAG 서비스 |
| 3-2 | 소스별 가중치 설정 (law_vectors: 0.5, actionkit: 0.5) | 설정 파라미터 |
| 3-3 | 응답에 소스 메타데이터 포함 (어떤 ActionKit에서 왔는지) | 응답 형식 확장 |
| 3-4 | Tier 3 전체 통합 평가 | 최종 평가 리포트 |

**의존성**: Phase 2 완료
**리스크**: 검색 정확도 저하 가능 → A/B 테스트로 가중치 최적화

### 전체 타임라인

```
Phase 1 (Day 1~2)     Phase 2 (Day 3~5)      Phase 3 (Day 6~7)
├── 스크립트 구현        ├── DataSource 구현      ├── EnsembleRetriever
├── Q&A 생성            ├── ETL 구현             ├── 가중치 최적화
├── 품질 검증            ├── 벡터 저장             ├── 소스 메타 포함
└── conftest 확장       ├── 인제스트 스크립트       └── 최종 평가
                        └── Tier 1~2 평가
```

---

## 8. 핵심 설계 결정 요약

| 결정 사항 | 선택 | 근거 |
|----------|------|------|
| 데이터소스 패턴 | `LawDataSource` ABC 확장 | 기존 인터페이스 재활용, OCP 준수 |
| ETL 전략 | LLM 우회 (메타데이터 직접 변환) | ActionKit은 이미 구조화, 비용/시간 절약 |
| 벡터 컬렉션 | 별도 컬렉션 "actionkit_vectors" | 데이터 소스 추적, 독립적 업데이트 가능 |
| Q&A 생성 | Seed 데이터 우선 (DB 모드는 Phase 2) | 즉시 시작 가능, DB 의존성 제거 |
| 평가 통합 | 기존 conftest.py 확장 | 3-Tier 평가 체계 재활용 |
| 검색 통합 | EnsembleRetriever (Phase 3) | 기존 검색과 공존, 가중치 조정 가능 |

---

## 부록: 파일 경로 매핑

| 설계 산출물 | 목표 경로 |
|------------|----------|
| ActionKitDataSource | `app-backend/app/services/actionkit_data_source.py` |
| ActionKitETLProcessor | `app-backend/app/services/actionkit_etl.py` |
| 골든 데이터셋 생성기 | `app-backend/scripts/generate_golden_dataset.py` |
| ActionKit 골든 데이터셋 | `app-backend/tests/eval/data/golden_dataset_actionkit.json` |
| 확장된 conftest | `app-backend/tests/eval/conftest.py` |
| 인제스트 스크립트 | `app-backend/scripts/ingest_actionkit.py` |
