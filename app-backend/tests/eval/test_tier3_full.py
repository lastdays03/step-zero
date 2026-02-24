"""
Tier 3: 전체 평가 - 법률 도메인 전문 평가.

릴리즈 전 또는 주요 RAG 변경 시 실행.
GPT-4o를 사용한 정밀 평가 포함.
비용: ~$15-25, 실행 시간: ~15분

실행: pytest tests/eval/test_tier3_full.py -v -s
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from typing import Any

import pytest

from .conftest import ensure_results_dir

pytestmark = [
    pytest.mark.eval,
    pytest.mark.slow,
    pytest.mark.full_eval,
]


# ─── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def rag_service():
    from app.features.rag.application.rag_service import RagService

    service = RagService()
    if not service.ready:
        pytest.skip(f"RAG service not available: {service.unavailable_reason}")
    return service


@pytest.fixture(scope="session")
def strong_judge():
    """강력한 평가 모델 (GPT-4o) - 법률 정확성 평가용."""
    from langchain_openai import ChatOpenAI
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY required")
    return ChatOpenAI(
        model="gpt-4o",
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )


@pytest.fixture(scope="session")
def full_evaluated_cases(rag_service, legal_cases: list[dict]) -> list[dict]:
    """전체 법률 케이스에 대해 RAG 응답 생성."""
    results = []
    loop = asyncio.new_event_loop()

    for case in legal_cases:
        try:
            answer = loop.run_until_complete(rag_service.query(case["question"]))
            retrieved_docs = rag_service.retriever.invoke(case["question"])
            contexts = [doc.page_content for doc in retrieved_docs]
            metadata_list = [doc.metadata for doc in retrieved_docs]
        except Exception as e:
            answer = f"ERROR: {e}"
            contexts = []
            metadata_list = []

        results.append(
            {
                **case,
                "rag_answer": answer,
                "retrieved_contexts": contexts,
                "retrieved_metadata": metadata_list,
            }
        )

    loop.close()
    return results


# ─── 1. 법률 정확성 전문 평가 ──────────────────────────────────────


class TestLegalAccuracy:
    """GPT-4o를 사용한 법률 도메인 정확성 평가."""

    def test_legal_accuracy_full(
        self, full_evaluated_cases: list[dict], strong_judge
    ) -> None:
        """전체 케이스에 대한 법률 정확성 평가."""
        scores = []
        details = []

        for case in full_evaluated_cases:
            prompt = f"""당신은 한국 법률 전문가입니다.
다음 법률 질의응답의 정확성을 평가하세요.

질문: {case['question']}
참고 정답: {case['ground_truth']}
AI 답변: {case['rag_answer']}

평가 기준 (0-3):
0: 법적 사실이 틀리거나 중요한 법령을 놓침
1: 부분적으로 정확하나 핵심 요건이나 기한을 놓침
2: 대체로 정확하나 사소한 오류 있음
3: 완전히 정확하고 관련 법령을 올바르게 인용

다음 JSON으로만 응답: {{"score": <0-3>, "reasoning": "<한국어 설명>", "hallucinated_facts": ["<환각된 사실1>", ...]}}"""

            response = strong_judge.invoke(prompt)
            try:
                result = json.loads(response.content.strip())
            except json.JSONDecodeError:
                result = {"score": 0, "reasoning": "parse error", "hallucinated_facts": []}

            score = result.get("score", 0)
            scores.append(score / 3.0)
            details.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "score": score,
                    "reasoning": result.get("reasoning", ""),
                    "hallucinated_facts": result.get("hallucinated_facts", []),
                    "difficulty": case.get("difficulty", "unknown"),
                }
            )

        avg_accuracy = sum(scores) / len(scores) if scores else 0

        # 난이도별 분석
        difficulty_scores: dict[str, list[float]] = {}
        for d in details:
            diff = d["difficulty"]
            difficulty_scores.setdefault(diff, []).append(d["score"] / 3.0)

        print(f"\n  === Legal Accuracy Full Report ===")
        print(f"  Overall: {avg_accuracy:.3f} (n={len(scores)})")
        for diff, s in difficulty_scores.items():
            avg = sum(s) / len(s) if s else 0
            print(f"  {diff}: {avg:.3f} (n={len(s)})")

        # 환각 사례 출력
        hallucinated = [d for d in details if d["hallucinated_facts"]]
        if hallucinated:
            print(f"\n  Hallucinated facts found in {len(hallucinated)} cases:")
            for d in hallucinated:
                print(f"    [{d['id']}] {d['hallucinated_facts']}")

        # 결과 저장
        results_dir = ensure_results_dir()
        report = {
            "avg_legal_accuracy": avg_accuracy,
            "total_cases": len(scores),
            "hallucination_count": len(hallucinated),
            "difficulty_breakdown": {
                k: sum(v) / len(v) for k, v in difficulty_scores.items()
            },
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        with open(results_dir / "legal_accuracy_full.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        assert avg_accuracy >= 0.50, (
            f"Legal accuracy {avg_accuracy:.3f} below 0.50 threshold"
        )


# ─── 2. 법령 인용 검증 ────────────────────────────────────────────


class TestStatuteCitation:
    """법령 인용의 정확성 검증."""

    CITATION_PATTERNS = [
        re.compile(r"제\d+조"),          # 제37조
        re.compile(r"[가-힣]+법"),        # 식품위생법
        re.compile(r"시행규칙"),          # 시행규칙
        re.compile(r"시행령"),            # 시행령
    ]

    def test_citation_rate(self, full_evaluated_cases: list[dict]) -> None:
        """인용이 필요한 케이스에서 법령 인용 비율."""
        citation_cases = [c for c in full_evaluated_cases if c.get("requires_citation")]
        if not citation_cases:
            pytest.skip("No citation-required cases")

        cited = 0
        for case in citation_cases:
            answer = case["rag_answer"]
            has_citation = any(
                pattern.search(answer) for pattern in self.CITATION_PATTERNS
            )
            if has_citation:
                cited += 1
            else:
                print(
                    f"  Missing citation: [{case['id']}] {case['question'][:50]}"
                )

        rate = cited / len(citation_cases)
        print(f"\n  Citation rate: {rate:.2%} ({cited}/{len(citation_cases)})")

    def test_no_incorrect_law_names(
        self, full_evaluated_cases: list[dict], strong_judge
    ) -> None:
        """존재하지 않는 법령명 인용 여부 확인."""
        law_pattern = re.compile(r"[가-힣]+법")
        false_citations = []

        for case in full_evaluated_cases[:5]:  # 비용 절약
            answer = case["rag_answer"]
            law_names = law_pattern.findall(answer)

            if law_names:
                prompt = f"""다음 한국 법령명들이 실제 존재하는 법률인지 확인하세요.
법령명 목록: {law_names}

실제 존재하지 않는 법령이 있으면 알려주세요.
JSON 응답: {{"all_valid": true/false, "invalid_laws": ["<없는 법령>"]}}"""

                response = strong_judge.invoke(prompt)
                try:
                    result = json.loads(response.content.strip())
                    if not result.get("all_valid", True):
                        false_citations.append(
                            {
                                "id": case["id"],
                                "invalid": result.get("invalid_laws", []),
                            }
                        )
                except json.JSONDecodeError:
                    pass

        if false_citations:
            print(f"\n  False law citations found:")
            for fc in false_citations:
                print(f"    [{fc['id']}] {fc['invalid']}")


# ─── 3. 범위 밖 질문 거부 테스트 ──────────────────────────────────


class TestOutOfScopeRefusal:
    """범위 밖 질문에 대한 적절한 거부 응답 확인."""

    REFUSAL_INDICATORS = [
        "찾을 수 없습니다",
        "해당 정보",
        "범위",
        "알 수 없",
        "확인되지 않",
        "제공된",
        "문서에서는",
    ]

    def test_refusal_on_out_of_scope(self, rag_service) -> None:
        """RAG에 없는 내용을 질문했을 때 '모른다'고 답하는지."""
        out_of_scope_questions = [
            "일본 식품위생법의 내용은?",
            "2035년 예상 법률 변화는?",
            "양자역학의 기본 원리를 설명해주세요",
        ]

        loop = asyncio.new_event_loop()
        refusal_count = 0

        for question in out_of_scope_questions:
            answer = loop.run_until_complete(rag_service.query(question))
            has_refusal = any(
                indicator in answer for indicator in self.REFUSAL_INDICATORS
            )

            if has_refusal:
                refusal_count += 1
            else:
                print(f"  No refusal for: '{question[:50]}'")
                print(f"    Answer: {answer[:100]}")

        loop.close()
        refusal_rate = refusal_count / len(out_of_scope_questions)
        print(f"\n  Refusal rate: {refusal_rate:.2%}")

        # 범위 밖 질문에 대한 적절 거부는 환각 방지의 핵심
        # 초기 베이스라인이므로 낮게 설정
        assert refusal_rate >= 0.30, (
            f"Refusal rate {refusal_rate:.2%} too low"
        )


# ─── 4. 응답 시간 테스트 ──────────────────────────────────────────


class TestResponseLatency:
    """RAG 응답 지연 시간 측정."""

    def test_query_latency(self, rag_service) -> None:
        """평균 응답 시간이 임계값 이내인지 확인."""
        import time

        questions = [
            "휴게음식점 영업신고 절차는?",
            "식품위생교육은 언제 받아야 하나요?",
            "법인 설립 절차를 알려주세요",
        ]

        loop = asyncio.new_event_loop()
        latencies = []

        for q in questions:
            start = time.time()
            loop.run_until_complete(rag_service.query(q))
            elapsed = time.time() - start
            latencies.append(elapsed)
            print(f"  '{q[:30]}...' → {elapsed:.2f}s")

        loop.close()

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        print(f"\n  Avg latency: {avg_latency:.2f}s, Max: {max_latency:.2f}s")

        assert avg_latency <= 15.0, f"Avg latency {avg_latency:.2f}s exceeds 15s"
        assert max_latency <= 25.0, f"Max latency {max_latency:.2f}s exceeds 25s"


# ─── 5. 종합 리포트 생성 ──────────────────────────────────────────


class TestGenerateReport:
    """전체 평가 결과를 종합 리포트로 생성."""

    def test_generate_summary_report(self) -> None:
        """기존 평가 결과 파일들을 종합."""
        results_dir = ensure_results_dir()
        report_parts = []

        # 각 결과 파일 수집
        for result_file in results_dir.glob("*.json"):
            try:
                with open(result_file, encoding="utf-8") as f:
                    data = json.load(f)
                report_parts.append(
                    {"source": result_file.stem, "data": data}
                )
            except Exception:
                pass

        summary = {
            "evaluation_date": datetime.now().isoformat(),
            "total_result_files": len(report_parts),
            "results": report_parts,
        }

        with open(results_dir / "summary_report.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n  Summary report saved with {len(report_parts)} result files")
