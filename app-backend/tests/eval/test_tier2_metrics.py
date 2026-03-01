"""
Tier 2: LLM 기반 평가 메트릭 테스트.

OpenAI API 호출이 필요하며, 실제 RAG 파이프라인을 통해 응답을 생성하고 평가합니다.
비용: ~$2-5, 실행 시간: ~5분

실행: pytest tests/eval/test_tier2_metrics.py -v -s
환경변수: OPENAI_API_KEY, DATABASE_URL 필요

의존성: pip install ragas datasets
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .conftest import ensure_results_dir

# ─── 마커 설정 ─────────────────────────────────────────────────────

pytestmark = [
    pytest.mark.eval,
    pytest.mark.slow,
]


# ─── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def rag_service():
    """실제 RagService 인스턴스 (DB + OpenAI 연결 필요).

    pytest-asyncio (asyncio_mode=auto) 환경에서 PGVector의 sync 초기화가
    greenlet 충돌을 일으키므로, psycopg 드라이버를 명시적으로 사용한다.
    """
    from pathlib import Path

    from dotenv import dotenv_values
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_postgres import PGVector

    # tests/conftest.py가 DATABASE_URL을 sqlite로 덮어쓰므로
    # .env + .env.local 파일에서 실제 설정을 직접 읽는다
    backend_root = Path(__file__).resolve().parents[2]
    env_vars: dict[str, str] = {}
    for env_file in (".env", ".env.local"):
        p = backend_root / env_file
        if p.exists():
            env_vars.update({k: v for k, v in dotenv_values(p).items() if v})
    db_url = env_vars.get("DATABASE_URL", "")
    api_key = env_vars.get("OPENAI_API_KEY", "")
    chat_model = env_vars.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    embed_model = env_vars.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    if not api_key:
        pytest.skip("OPENAI_API_KEY required for RAG evaluation")
    if "postgresql" not in db_url:
        pytest.skip(f"PostgreSQL DATABASE_URL required, got: {db_url[:30]}")

    # async 드라이버 → sync 드라이버로 변환
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

    try:
        embeddings = OpenAIEmbeddings(model=embed_model, api_key=api_key)
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name="law_vectors",
            connection=sync_url,
            use_jsonb=True,
            create_extension=False,
        )

        class _TestRagService:
            """테스트 전용 RagService 래퍼."""

            def __init__(self):
                self.ready = True
                self.unavailable_reason = ""
                self.embeddings = embeddings
                self.vector_store = vector_store
                self.retriever = vector_store.as_retriever(search_kwargs={"k": 3})
                self.llm = ChatOpenAI(
                    model=chat_model,
                    api_key=api_key,
                    timeout=20,
                    max_retries=2,
                )
                self.prompt = ChatPromptTemplate.from_template("""
                You are an AI assistant for startup founders in Korea.
                Answer the question based ONLY on the following context.
                If the answer is not in the context, say "제공된 법령 문서에서는 해당 정보를 찾을 수 없습니다."

                Context:
                {context}

                Question: {question}

                Answer (in Korean):
                """)

                def format_docs(docs):
                    if not docs:
                        return "No relevant legal documents found."
                    return "\n\n".join(doc.page_content for doc in docs)

                self.chain = (
                    {
                        "context": self.retriever | format_docs,
                        "question": RunnablePassthrough(),
                    }
                    | self.prompt
                    | self.llm
                    | StrOutputParser()
                )

            async def query(self, question: str) -> str:
                from fastapi.concurrency import run_in_threadpool

                return await run_in_threadpool(self.chain.invoke, question)

        return _TestRagService()

    except Exception as exc:
        pytest.skip(f"RAG service init failed: {exc}")


@pytest.fixture(scope="session")
def chat_service(rag_service):
    """실제 ChatService 인스턴스."""
    from app.features.rag.application.chat_service import ChatService

    return ChatService(rag_service)


@pytest.fixture(scope="session")
def evaluated_cases(rag_service, legal_cases: list[dict]) -> list[dict[str, Any]]:
    """골든 데이터셋의 법률 케이스에 대해 RAG 응답을 미리 생성."""
    results = []
    loop = asyncio.new_event_loop()

    for case in legal_cases:
        try:
            answer = loop.run_until_complete(rag_service.query(case["question"]))
            # retriever를 직접 호출하여 검색된 문서도 수집
            retrieved_docs = rag_service.retriever.invoke(case["question"])
            contexts = [doc.page_content for doc in retrieved_docs]
        except Exception as e:
            answer = f"ERROR: {e}"
            contexts = []

        results.append(
            {
                "id": case["id"],
                "question": case["question"],
                "ground_truth": case["ground_truth"],
                "rag_answer": answer,
                "retrieved_contexts": contexts,
                "expected_keywords": case.get("expected_keywords", []),
                "expected_law_reference": case.get("expected_law_reference"),
                "requires_citation": case.get("requires_citation", False),
                "category": case["category"],
                "difficulty": case["difficulty"],
            }
        )

    loop.close()
    return results


@pytest.fixture(scope="session")
def llm_judge():
    """평가용 LLM (GPT-4o-mini)."""
    from pathlib import Path

    from dotenv import dotenv_values
    from langchain_openai import ChatOpenAI

    backend_root = Path(__file__).resolve().parents[2]
    env_vars: dict[str, str] = {}
    for env_file in (".env", ".env.local"):
        p = backend_root / env_file
        if p.exists():
            env_vars.update({k: v for k, v in dotenv_values(p).items() if v})
    api_key = env_vars.get("OPENAI_API_KEY", "")
    if not api_key:
        pytest.skip("OPENAI_API_KEY required for LLM judge")

    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        temperature=0,
    )


# ─── 1. Retrieval 품질 테스트 ──────────────────────────────────────


class TestRetrievalQuality:
    """검색 단계의 품질 평가."""

    def test_hit_rate(self, evaluated_cases: list[dict]) -> None:
        """Top-3 검색 결과에 관련 문서가 1개 이상 포함되는 비율."""
        hits = 0
        total = 0

        for case in evaluated_cases:
            if not case["expected_keywords"]:
                continue
            total += 1

            contexts_text = " ".join(case["retrieved_contexts"]).lower()
            # 기대 키워드 중 하나라도 검색 결과에 포함되면 hit
            if any(kw.lower() in contexts_text for kw in case["expected_keywords"]):
                hits += 1

        hit_rate = hits / total if total > 0 else 0
        print(f"\n  Hit Rate@3: {hit_rate:.2%} ({hits}/{total})")

        # 베이스라인(2026-02-24): 41.18% → 회귀 감지 임계값: 30%
        assert (
            hit_rate >= 0.30
        ), f"Hit Rate@3 = {hit_rate:.2%} (threshold: 30%, baseline: 41%)"

    def test_context_not_empty(self, evaluated_cases: list[dict]) -> None:
        """모든 법률 질문에 대해 최소 1개 컨텍스트가 검색되는지 확인."""
        empty_count = 0
        for case in evaluated_cases:
            if not case["retrieved_contexts"]:
                empty_count += 1
                print(f"  No context for: [{case['id']}] {case['question'][:50]}")

        empty_rate = empty_count / len(evaluated_cases) if evaluated_cases else 0
        assert (
            empty_rate <= 0.10
        ), f"Too many empty retrievals: {empty_count}/{len(evaluated_cases)}"

    def test_context_relevance_keyword_check(self, evaluated_cases: list[dict]) -> None:
        """검색된 컨텍스트에 관련 법령 키워드가 포함되는 비율."""
        relevant = 0
        total = 0

        for case in evaluated_cases:
            ref = case.get("expected_law_reference")
            if not ref:
                continue
            total += 1

            contexts_text = " ".join(case["retrieved_contexts"])
            if ref in contexts_text:
                relevant += 1

        relevance = relevant / total if total > 0 else 0
        print(f"\n  Law reference match rate: {relevance:.2%} ({relevant}/{total})")


# ─── 2. Generation 품질 테스트 ─────────────────────────────────────


class TestGenerationQuality:
    """생성 답변의 품질 평가 (LLM-as-Judge)."""

    def test_faithfulness_batch(self, evaluated_cases: list[dict], llm_judge) -> None:
        """답변이 검색된 컨텍스트에 근거하는지 LLM으로 평가."""
        scores = []
        details = []

        for case in evaluated_cases[:10]:  # 비용 절약: 상위 10개만
            if not case["retrieved_contexts"]:
                continue

            context_text = "\n---\n".join(case["retrieved_contexts"])
            prompt = f"""다음 답변이 제공된 컨텍스트에만 근거하는지 평가하세요.

컨텍스트:
{context_text}

질문: {case['question']}
답변: {case['rag_answer']}

평가 기준:
- 1.0: 답변의 모든 주장이 컨텍스트에 의해 뒷받침됨
- 0.7: 대부분 뒷받침되나 일부 추론 포함
- 0.3: 일부만 뒷받침되고 상당 부분 컨텍스트에 없는 내용
- 0.0: 컨텍스트와 무관한 답변

숫자만 응답하세요 (예: 0.7):"""

            response = llm_judge.invoke(prompt)
            try:
                score = float(response.content.strip())
                score = max(0.0, min(1.0, score))
            except ValueError:
                score = 0.0

            scores.append(score)
            details.append(
                {"id": case["id"], "score": score, "question": case["question"][:50]}
            )

        avg_faithfulness = sum(scores) / len(scores) if scores else 0
        print(f"\n  Avg Faithfulness: {avg_faithfulness:.3f} (n={len(scores)})")
        for d in details:
            print(f"    [{d['id']}] {d['score']:.2f} - {d['question']}")

        # 결과 저장
        results_dir = ensure_results_dir()
        with open(results_dir / "faithfulness.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "avg": avg_faithfulness,
                    "details": details,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # 베이스라인(2026-02-24): 0.150 → 회귀 감지 임계값: 0.05
        assert (
            avg_faithfulness >= 0.05
        ), f"Avg faithfulness {avg_faithfulness:.3f} below 0.05 threshold (baseline: 0.15)"

    def test_answer_relevancy_batch(
        self, evaluated_cases: list[dict], llm_judge
    ) -> None:
        """답변이 질문에 적절히 응답하는지 LLM으로 평가."""
        scores = []

        for case in evaluated_cases[:10]:
            prompt = f"""질문에 대한 답변이 얼마나 관련성이 있는지 평가하세요.

질문: {case['question']}
답변: {case['rag_answer']}

평가 기준:
- 1.0: 질문에 정확히 답함
- 0.7: 대체로 관련있으나 일부 불필요한 내용 포함
- 0.3: 부분적으로만 관련
- 0.0: 질문과 무관

숫자만 응답하세요:"""

            response = llm_judge.invoke(prompt)
            try:
                score = float(response.content.strip())
                score = max(0.0, min(1.0, score))
            except ValueError:
                score = 0.0
            scores.append(score)

        avg_relevancy = sum(scores) / len(scores) if scores else 0
        print(f"\n  Avg Answer Relevancy: {avg_relevancy:.3f} (n={len(scores)})")

        # 베이스라인(2026-02-24): 0.240 → 회귀 감지 임계값: 0.14
        assert (
            avg_relevancy >= 0.14
        ), f"Avg relevancy {avg_relevancy:.3f} below 0.14 threshold (baseline: 0.24)"

    def test_keyword_presence_in_answers(self, evaluated_cases: list[dict]) -> None:
        """기대 키워드가 답변에 포함되는 비율 (무비용 체크)."""
        matches = 0
        total = 0

        for case in evaluated_cases:
            if not case["expected_keywords"]:
                continue
            total += 1

            answer_lower = case["rag_answer"].lower()
            if any(kw.lower() in answer_lower for kw in case["expected_keywords"]):
                matches += 1

        match_rate = matches / total if total > 0 else 0
        print(f"\n  Keyword match rate: {match_rate:.2%} ({matches}/{total})")

    def test_no_english_only_responses(self, evaluated_cases: list[dict]) -> None:
        """한국어 질문에 대해 영어로만 답변하지 않는지 확인."""
        korean_pattern = re.compile(r"[가-힣]")

        for case in evaluated_cases:
            answer = case["rag_answer"]
            if len(answer) > 20:  # 에러 메시지가 아닌 실제 답변만
                has_korean = bool(korean_pattern.search(answer))
                assert has_korean, f"[{case['id']}] No Korean in answer: {answer[:100]}"


# ─── 3. End-to-End 품질 테스트 ─────────────────────────────────────


class TestEndToEndQuality:
    """전체 파이프라인 품질 평가."""

    def test_answer_correctness_batch(
        self, evaluated_cases: list[dict], llm_judge
    ) -> None:
        """정답과 RAG 답변의 의미적 일치도 평가."""
        scores = []
        details = []

        for case in evaluated_cases[:10]:
            prompt = f"""정답과 AI 답변의 핵심 의미가 일치하는지 평가하세요.
정확한 어휘 일치는 불필요하며, 핵심 사실과 개념의 일치만 평가합니다.

질문: {case['question']}
정답: {case['ground_truth']}
AI 답변: {case['rag_answer']}

점수 (0-3):
0: 핵심 사실이 틀리거나 완전히 무관
1: 부분적으로 정확하나 핵심 정보 누락
2: 대체로 정확하나 사소한 차이
3: 핵심 의미 완전 일치

JSON으로 응답: {{"score": <0-3>, "reasoning": "<한줄 설명>"}}"""

            response = llm_judge.invoke(prompt)
            try:
                result = json.loads(response.content.strip())
                score = result.get("score", 0)
                reasoning = result.get("reasoning", "")
            except (json.JSONDecodeError, KeyError):
                score = 0
                reasoning = "parse error"

            normalized = score / 3.0
            scores.append(normalized)
            details.append(
                {
                    "id": case["id"],
                    "score": score,
                    "normalized": normalized,
                    "reasoning": reasoning,
                }
            )

        avg_correctness = sum(scores) / len(scores) if scores else 0
        print(f"\n  Avg Answer Correctness: {avg_correctness:.3f} (n={len(scores)})")
        for d in details:
            print(f"    [{d['id']}] {d['score']}/3 - {d['reasoning'][:60]}")

        # 결과 저장
        results_dir = ensure_results_dir()
        with open(results_dir / "correctness.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "avg": avg_correctness,
                    "details": details,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # 베이스라인(2026-02-24): 0.000 → 회귀 감지 비활성 (개선 필요)
        # assert avg_correctness >= 0.00  # 현재 0%이므로 회귀 감지 불가
        print(f"  [BASELINE] Correctness = {avg_correctness:.3f} (target: >= 0.40)")

    def test_chat_routing_e2e(self, chat_service, golden_dataset: list[dict]) -> None:
        """ChatService를 통한 실제 라우팅 결과 확인."""
        loop = asyncio.new_event_loop()
        correct = 0
        total = 0

        for case in golden_dataset[:5]:
            if case["category"] == "out_of_scope":
                continue
            total += 1

            answer, source = loop.run_until_complete(
                chat_service.chat(case["question"])
            )
            expected = case["expected_source"]

            if source == expected:
                correct += 1
            else:
                print(
                    f"  [{case['id']}] source mismatch: "
                    f"got '{source}', expected '{expected}'"
                )

        loop.close()
        accuracy = correct / total if total > 0 else 0
        print(f"\n  E2E Routing accuracy: {accuracy:.2%} ({correct}/{total})")


# ─── 4. RAGAS 프레임워크 평가 (선택적) ─────────────────────────────


class TestRAGASMetrics:
    """RAGAS 프레임워크를 활용한 표준 메트릭 평가.

    의존성: pip install ragas datasets
    """

    def test_ragas_evaluation(self, evaluated_cases: list[dict]) -> None:
        """RAGAS 메트릭으로 종합 평가."""
        try:
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import (
                answer_relevancy,
                context_precision,
                context_recall,
                faithfulness,
            )
        except ImportError:
            pytest.skip("ragas/datasets not installed: pip install ragas datasets")

        # RAGAS 형식으로 변환
        ragas_data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": [],
        }

        for case in evaluated_cases:
            if not case["retrieved_contexts"]:
                continue
            ragas_data["question"].append(case["question"])
            ragas_data["answer"].append(case["rag_answer"])
            ragas_data["contexts"].append(case["retrieved_contexts"])
            ragas_data["ground_truth"].append(case["ground_truth"])

        if not ragas_data["question"]:
            pytest.skip("No evaluated cases with contexts available")

        dataset = Dataset.from_dict(ragas_data)

        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
        )

        df = result.to_pandas()

        # 결과 출력 및 저장
        print("\n  === RAGAS Evaluation Results ===")
        for col in [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ]:
            if col in df.columns:
                mean_val = df[col].mean()
                print(f"    {col}: {mean_val:.3f}")

        results_dir = ensure_results_dir()
        df.to_csv(results_dir / "ragas_results.csv", index=False)

        # 최소 임계값 (초기 베이스라인이므로 낮게 설정)
        if "faithfulness" in df.columns:
            assert df["faithfulness"].mean() >= 0.40, "Faithfulness below threshold"
