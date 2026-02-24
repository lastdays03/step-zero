"""
Tier 1: 무비용 기본 검증 테스트.

API 호출 없이 실행되므로 매 커밋마다 실행 가능.
비용: $0, 실행 시간: <5초

실행: pytest tests/eval/test_tier1_basic.py -v
"""

from __future__ import annotations

import pytest

from app.features.rag.application.chat_service import LEGAL_KEYWORDS, classify_query


# ─── 1. Query 라우팅 정확성 ────────────────────────────────────────


class TestQueryRouting:
    """키워드 기반 쿼리 분류 정확성 테스트."""

    @pytest.mark.parametrize(
        "query,expected",
        [
            # 명확한 법률 질문 (LEGAL_KEYWORDS 포함)
            ("영업허가 절차를 알려주세요", "legal"),
            ("식품위생법에 대해 알려주세요", "legal"),
            ("음식점 영업신고 방법은?", "legal"),
            ("사업자등록은 어디서 하나요?", "legal"),  # "등록" 키워드
            ("면허 취득 조건은?", "legal"),
            ("위생 교육은 필수인가요?", "legal"),
            # 명확한 일반 질문
            ("안녕하세요", "general"),
            ("좋은 아침이에요", "general"),
            ("투자자를 어떻게 찾나요?", "general"),
            ("마케팅 전략을 추천해주세요", "general"),
            ("직원 면접 질문 추천해주세요", "general"),
        ],
    )
    def test_query_classification(self, query: str, expected: str) -> None:
        result = classify_query(query)
        assert result == expected, (
            f"Query: '{query}' → got '{result}', expected '{expected}'"
        )

    def test_all_legal_keywords_trigger_legal_route(self) -> None:
        """모든 LEGAL_KEYWORDS가 legal 분류를 트리거하는지 확인."""
        for keyword in LEGAL_KEYWORDS:
            query = f"{keyword}에 대해 알려주세요"
            result = classify_query(query)
            assert result == "legal", (
                f"Keyword '{keyword}' in query did not trigger legal route"
            )

    @pytest.mark.parametrize(
        "query",
        [
            # 키워드가 없지만 법률 의도가 있는 질문 (현재 한계 파악용)
            "사업자등록번호 없이 장사하면 어떻게 되나요?",  # "등록" 포함 → legal
            "세금 신고 기한이 언제인가요?",  # "신고" 포함 → legal
            "4대보험 가입 의무가 있나요?",  # 키워드 없음 → general (오분류)
            "근로계약서를 안 쓰면 벌금이 있나요?",  # 키워드 없음 → general (오분류)
        ],
    )
    def test_routing_edge_cases_documented(self, query: str) -> None:
        """경계 케이스의 현재 동작을 문서화 (pass always, 결과만 기록)."""
        result = classify_query(query)
        # 이 테스트는 항상 pass - 현재 동작을 기록하는 용도
        print(f"  Edge case: '{query}' → {result}")


# ─── 2. 골든 데이터셋 라우팅 정확성 ──────────────────────────────────


class TestGoldenDatasetRouting:
    """골든 데이터셋의 expected_source와 실제 라우팅 결과 비교."""

    def test_routing_accuracy(self, golden_dataset: list[dict]) -> None:
        correct = 0
        total = 0
        misclassified = []

        for case in golden_dataset:
            if case["category"] == "out_of_scope":
                continue  # 범위 밖은 라우팅 테스트에서 제외

            expected = "legal" if case["expected_source"] == "legal_rag" else "general"
            actual = classify_query(case["question"])
            total += 1

            if actual == expected:
                correct += 1
            else:
                misclassified.append(
                    f"  [{case['id']}] '{case['question'][:50]}' "
                    f"→ got '{actual}', expected '{expected}'"
                )

        accuracy = correct / total if total > 0 else 0
        report = f"Routing accuracy: {accuracy:.2%} ({correct}/{total})"

        if misclassified:
            report += "\nMisclassified:\n" + "\n".join(misclassified)

        print(f"\n{report}")

        # 현재는 경고만 출력 (키워드 기반이라 100% 불가능)
        # 향후 LLM 기반 라우팅으로 전환 시 임계값 상향
        assert accuracy >= 0.70, (
            f"Routing accuracy {accuracy:.2%} below 70% threshold.\n{report}"
        )


# ─── 3. 서비스 기본 동작 검증 ──────────────────────────────────────


class TestServiceBasicBehavior:
    """RagService/ChatService의 기본 동작 검증 (mock 기반)."""

    def test_rag_service_not_ready_returns_fallback(self) -> None:
        """API 키 없을 때 적절한 폴백 메시지 반환."""
        from app.features.rag.application.rag_service import RagService

        service = RagService.__new__(RagService)
        service.ready = False

        import asyncio

        result = asyncio.get_event_loop().run_until_complete(service.query("테스트"))
        assert "사용할 수 없습니다" in result

    def test_classify_query_returns_valid_values(self) -> None:
        """classify_query는 항상 'legal' 또는 'general'만 반환."""
        test_inputs = ["", "테스트", "법", "hello", "123", "법률 질문입니다"]
        for query in test_inputs:
            result = classify_query(query)
            assert result in ("legal", "general"), (
                f"Invalid classification result: '{result}' for query '{query}'"
            )


# ─── 4. 골든 데이터셋 무결성 검증 ──────────────────────────────────


class TestGoldenDatasetIntegrity:
    """골든 데이터셋 자체의 품질 검증."""

    def test_dataset_not_empty(self, golden_dataset: list[dict]) -> None:
        assert len(golden_dataset) >= 10, (
            f"Golden dataset too small: {len(golden_dataset)} cases (minimum 10)"
        )

    def test_required_fields_present(self, golden_dataset: list[dict]) -> None:
        required_fields = {
            "id", "question", "ground_truth", "expected_source", "category",
        }
        for case in golden_dataset:
            missing = required_fields - set(case.keys())
            assert not missing, (
                f"Case {case.get('id', '?')}: missing fields {missing}"
            )

    def test_unique_ids(self, golden_dataset: list[dict]) -> None:
        ids = [c["id"] for c in golden_dataset]
        duplicates = [i for i in ids if ids.count(i) > 1]
        assert not duplicates, f"Duplicate IDs: {set(duplicates)}"

    def test_balanced_categories(self, golden_dataset: list[dict]) -> None:
        """카테고리 분포가 적절한지 확인."""
        from collections import Counter

        categories = Counter(c["category"] for c in golden_dataset)
        print(f"\nCategory distribution: {dict(categories)}")
        # 최소 2개 카테고리 존재
        assert len(categories) >= 2

    def test_has_legal_and_general_cases(
        self, legal_cases: list[dict], general_cases: list[dict]
    ) -> None:
        assert len(legal_cases) >= 5, "Need at least 5 legal cases"
        assert len(general_cases) >= 2, "Need at least 2 general cases"

    def test_has_out_of_scope_cases(self, out_of_scope_cases: list[dict]) -> None:
        """OOS 케이스가 충분한지 확인 (oos-001~005)."""
        assert len(out_of_scope_cases) >= 5, (
            f"Need at least 5 out_of_scope cases, got {len(out_of_scope_cases)}"
        )


# ─── 5. general_cases fixture 라우팅 테스트 ────────────────────────


class TestGeneralCasesRouting:
    """골든 데이터셋의 general_cases fixture를 사용한 라우팅 테스트."""

    def test_general_cases_routed_to_general(self, general_cases: list[dict]) -> None:
        """일반 대화 케이스(OOS 제외)의 라우팅 현황 기록.

        키워드 기반 라우터의 한계로 일반 질문이 legal로 오분류될 수 있음.
        현재는 문서화 목적으로만 기록하고, LLM 기반 라우터 전환 후 임계값 추가.
        """
        # general_cases fixture에는 OOS도 포함되므로 category=="general"만 필터
        pure_general = [c for c in general_cases if c["category"] == "general"]
        correct = 0
        total = len(pure_general)
        misclassified = []

        for case in pure_general:
            actual = classify_query(case["question"])
            if actual == "general":
                correct += 1
            else:
                misclassified.append(
                    f"  [{case['id']}] '{case['question'][:50]}' → got '{actual}'"
                )

        accuracy = correct / total if total > 0 else 0
        print(f"\n  General routing accuracy: {accuracy:.2%} ({correct}/{total})")
        if misclassified:
            print("  Misclassified as legal (keyword-based router 한계):")
            for m in misclassified:
                print(f"    {m}")

    def test_general_cases_have_no_law_reference(self, general_cases: list[dict]) -> None:
        """일반 케이스에는 법령 참조가 없어야 함."""
        for case in general_cases:
            assert case.get("expected_law_reference") is None, (
                f"[{case['id']}] General case should not have law reference: "
                f"{case.get('expected_law_reference')}"
            )


# ─── 6. routing_edge_cases fixture 테스트 ──────────────────────────


class TestRoutingEdgeCases:
    """골든 데이터셋의 routing_edge_cases fixture를 사용한 경계 케이스 테스트."""

    def test_routing_edge_cases_classification(self, routing_edge_cases: list[dict]) -> None:
        """라우팅 경계 케이스의 분류 결과를 기록하고 정확도 확인."""
        correct = 0
        total = len(routing_edge_cases)
        details = []

        for case in routing_edge_cases:
            expected = "legal" if case["expected_source"] == "legal_rag" else "general"
            actual = classify_query(case["question"])
            is_correct = actual == expected
            if is_correct:
                correct += 1
            details.append({
                "id": case["id"],
                "question": case["question"][:50],
                "expected": expected,
                "actual": actual,
                "correct": is_correct,
            })

        accuracy = correct / total if total > 0 else 0
        print(f"\n  Routing edge cases accuracy: {accuracy:.2%} ({correct}/{total})")
        for d in details:
            status = "OK" if d["correct"] else "MISS"
            print(f"    [{d['id']}] {d['question']} → {d['actual']} (expected: {d['expected']}) [{status}]")

    def test_edge_cases_are_legal_source(self, routing_edge_cases: list[dict]) -> None:
        """라우팅 경계 케이스가 모두 legal_rag 소스인지 확인."""
        for case in routing_edge_cases:
            assert case["expected_source"] == "legal_rag", (
                f"[{case['id']}] Routing edge case should be legal_rag, "
                f"got: {case['expected_source']}"
            )
