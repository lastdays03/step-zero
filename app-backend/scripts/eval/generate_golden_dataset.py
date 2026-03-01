#!/usr/bin/env python3
"""
골든 데이터셋 자동 생성 스크립트.

현재 벡터 DB에 저장된 문서들을 기반으로 LLM이 Q&A 쌍을 자동 생성합니다.
생성된 데이터셋은 전문가 검수 후 golden_dataset.json에 병합합니다.

사용법:
    cd app-backend
    python -m scripts.eval.generate_golden_dataset --count 50 --output tests/eval/data/generated_qa.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("scripts.generate_golden_dataset")


QUESTION_GENERATION_PROMPT = """당신은 한국 스타트업 창업자를 위한 법률 Q&A 데이터셋을 만드는 전문가입니다.

다음 법률 문서를 읽고, 이 문서에서 답할 수 있는 질문-답변 쌍을 생성하세요.

문서 내용:
{document}

지시사항:
1. 한국어로 자연스러운 질문을 만드세요 (실제 창업자가 물어볼 만한 질문)
2. 답변은 문서 내용에만 근거해야 합니다
3. 다양한 유형의 질문을 포함하세요:
   - factual: 단순 사실 확인 ("~의 기한은?", "~는 몇 명?")
   - procedural: 절차 관련 ("~을 하려면 어떻게?")
   - interpretive: 해석 필요 ("~한 경우에도 적용되나요?")
4. {count}개의 질문-답변 쌍을 생성하세요

JSON 배열로 응답:
[
  {{
    "question": "질문 텍스트",
    "ground_truth": "문서에 근거한 정답",
    "category": "factual|procedural|interpretive",
    "difficulty": "easy|medium|hard",
    "expected_keywords": ["핵심", "키워드"],
    "requires_citation": true/false
  }}
]"""


async def generate_from_documents(count: int, output_path: str) -> None:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY required")
        return

    # 벡터 DB에서 문서 가져오기
    sync_db_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    embeddings = OpenAIEmbeddings(
        model=settings.OPENAI_EMBED_MODEL,
        api_key=settings.OPENAI_API_KEY,
    )

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="law_vectors",
        connection=sync_db_url,
        use_jsonb=True,
    )

    # 모든 문서 가져오기 (다양한 쿼리로 검색)
    seed_queries = [
        # 기존 법률 도메인
        "영업신고 절차",
        "허가 요건",
        "위생 기준",
        "법인 설립",
        "사업자 등록",
        # 세무 도메인
        "부가가치세 과세유형 간이과세",
        "적격증빙 경비처리",
        # 인사 도메인
        "근로계약서 작성 의무",
        "4대보험 성립신고",
        "취업규칙 작성",
        # 공고문 도메인
        "소상공인 정책자금 융자",
        # 행정법 도메인
        "행정심판 청구 절차",
        "행정조사 사전통지",
    ]

    all_docs = []
    seen_contents = set()

    for query in seed_queries:
        docs = vector_store.similarity_search(query, k=5)
        for doc in docs:
            content_hash = hash(doc.page_content[:200])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                all_docs.append(doc)

    logger.info(f"Retrieved {len(all_docs)} unique documents")

    if not all_docs:
        logger.error("No documents found in vector store")
        return

    # LLM으로 Q&A 생성
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )

    questions_per_doc = max(1, count // len(all_docs))
    all_qa_pairs = []

    for i, doc in enumerate(all_docs):
        logger.info(f"Generating Q&A for doc {i + 1}/{len(all_docs)}")

        prompt = QUESTION_GENERATION_PROMPT.format(
            document=doc.page_content[:3000],
            count=questions_per_doc,
        )

        try:
            response = llm.invoke(prompt)
            qa_pairs = json.loads(response.content.strip())

            # ID 부여 및 메타데이터 추가
            for j, qa in enumerate(qa_pairs):
                qa["id"] = f"gen-{i:03d}-{j:02d}"
                qa["expected_source"] = "legal_rag"
                qa["source_doc_title"] = doc.metadata.get("title", "unknown")

            all_qa_pairs.extend(qa_pairs)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to generate Q&A for doc {i}: {e}")
            continue

    # 저장
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_qa_pairs[:count], f, ensure_ascii=False, indent=2)

    logger.info(f"Generated {len(all_qa_pairs[:count])} Q&A pairs → {output}")
    print(f"\nGenerated {len(all_qa_pairs[:count])} Q&A pairs")
    print(f"Output: {output}")
    print("\nNext steps:")
    print("1. Review generated Q&A pairs for quality")
    print("2. Merge approved entries into tests/eval/data/golden_dataset.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="골든 데이터셋 자동 생성")
    parser.add_argument("--count", type=int, default=50, help="생성할 Q&A 쌍 수")
    parser.add_argument(
        "--output",
        default="tests/eval/data/generated_qa.json",
        help="출력 파일 경로",
    )
    args = parser.parse_args()

    asyncio.run(generate_from_documents(args.count, args.output))


if __name__ == "__main__":
    main()
