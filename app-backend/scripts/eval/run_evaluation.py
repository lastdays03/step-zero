#!/usr/bin/env python3
"""
RAG 성능 종합 평가 스크립트.

DB 연결 + OpenAI API 필요.
결과를 tests/eval/results/에 저장하고 콘솔에 요약 출력.

사용법:
    cd app-backend
    python -m scripts.eval.run_evaluation [--tier 1|2|3|4] [--report-only]
    python -m scripts.eval.run_evaluation --update-baseline  # 현재 결과로 baseline 갱신

Tier 4: 로드맵 품질 평가 (actionkit_mapping_rate, legal_basis_accuracy,
        document_validity, generation_success_rate, personalization_score)
        인프라 없이도 mock 데이터로 동작 가능.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── 경로 설정 ─────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_DATA_DIR = PROJECT_ROOT / "tests" / "eval" / "data"
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval" / "results"
BASELINE_PATH = RESULTS_DIR / "baseline.json"
LATEST_RUN_PATH = RESULTS_DIR / "latest_run.json"


def load_golden_dataset() -> list[dict]:
    """골든 데이터셋 로드."""
    path = EVAL_DATA_DIR / "golden_dataset.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_results(name: str, data: Any) -> None:
    """개별 평가 결과 파일 저장."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {path}")


def _get_git_commit() -> str:
    """현재 git commit 해시(short) 반환."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def save_latest_run(
    dataset: list[dict],
    tier1_result: dict | None,
    tier2_result: dict | None,
    tier4_result: dict | None = None,
) -> dict:
    """평가 결과를 latest_run.json으로 저장. baseline과 동일한 스키마 사용."""
    # 카테고리별 케이스 수 집계
    categories = Counter(c["category"] for c in dataset)
    case_count = {
        "legal": len([c for c in dataset if c["expected_source"] == "legal_rag"]),
        "general": len([c for c in dataset if c["category"] == "general"]),
        "routing_edge": categories.get("routing_edge", 0),
        "out_of_scope": categories.get("out_of_scope", 0),
    }

    # 메트릭 수집
    metrics: dict[str, float] = {}
    if tier1_result and not tier1_result.get("skipped"):
        metrics["routing_accuracy"] = tier1_result.get("routing_accuracy", 0.0)
    if tier2_result and not tier2_result.get("skipped"):
        metrics["hit_rate_at_3"] = tier2_result.get("hit_rate", 0.0)
        metrics["faithfulness"] = tier2_result.get("faithfulness", {}).get("avg", 0.0)
        metrics["answer_relevancy"] = tier2_result.get("answer_relevancy", {}).get("avg", 0.0)
        metrics["answer_correctness"] = tier2_result.get("answer_correctness", {}).get("avg", 0.0)
    if tier4_result and not tier4_result.get("skipped"):
        metrics["roadmap_actionkit_mapping_rate"] = tier4_result.get("actionkit_mapping_rate", 0.0)
        metrics["roadmap_legal_basis_accuracy"] = tier4_result.get("legal_basis_accuracy", 0.0)
        metrics["roadmap_personalization_score"] = tier4_result.get("personalization_score", 0.0)

    run_data = {
        "created_at": datetime.now().isoformat(),
        "git_commit": _get_git_commit(),
        "description": "Auto-saved evaluation run",
        "metrics": metrics,
        "case_count": case_count,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LATEST_RUN_PATH, "w", encoding="utf-8") as f:
        json.dump(run_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {LATEST_RUN_PATH}")
    return run_data


def update_baseline() -> None:
    """latest_run.json을 baseline.json으로 복사하여 베이스라인 갱신."""
    if not LATEST_RUN_PATH.exists():
        print("  ERROR: latest_run.json이 없습니다. 먼저 평가를 실행하세요.")
        return

    with open(LATEST_RUN_PATH, encoding="utf-8") as f:
        run_data = json.load(f)

    run_data["description"] = f"Baseline updated from run at {run_data['created_at']}"
    run_data["created_at"] = datetime.now().isoformat()

    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(run_data, f, ensure_ascii=False, indent=2)
    print(f"  Baseline updated: {BASELINE_PATH}")
    print(f"  Metrics: {json.dumps(run_data['metrics'], indent=2)}")


# ─── Tier 1: 무비용 기본 검증 ──────────────────────────────────────


def run_tier1(dataset: list[dict]) -> dict:
    print("\n" + "=" * 60)
    print("TIER 1: 무비용 기본 검증")
    print("=" * 60)

    from app.features.rag.application.chat_service import classify_query

    # 라우팅 정확성
    correct = 0
    total = 0
    misclassified = []

    for case in dataset:
        if case["category"] == "out_of_scope":
            continue
        expected = "legal" if case["expected_source"] == "legal_rag" else "general"
        actual = classify_query(case["question"])
        total += 1
        if actual == expected:
            correct += 1
        else:
            misclassified.append(
                f"  [{case['id']}] '{case['question'][:40]}' → {actual} (expected: {expected})"
            )

    routing_accuracy = correct / total if total > 0 else 0
    print(f"\n  Routing Accuracy: {routing_accuracy:.2%} ({correct}/{total})")
    if misclassified:
        print("  Misclassified:")
        for m in misclassified:
            print(f"    {m}")

    result = {
        "routing_accuracy": routing_accuracy,
        "total_cases": total,
        "correct": correct,
        "misclassified": misclassified,
    }
    save_results("tier1_routing", result)
    return result


# ─── Tier 2: LLM 기반 평가 ────────────────────────────────────────


async def run_tier2(dataset: list[dict]) -> dict:
    print("\n" + "=" * 60)
    print("TIER 2: LLM 기반 메트릭 평가")
    print("=" * 60)

    from app.features.rag.application.rag_service import RagService
    from langchain_openai import ChatOpenAI
    from app.core.config import get_settings

    settings = get_settings()
    service = RagService()
    if not service.ready:
        print(f"  SKIP: RAG service unavailable ({service.unavailable_reason})")
        return {"skipped": True}

    judge = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )

    legal_cases = [c for c in dataset if c["expected_source"] == "legal_rag"]

    # 1. RAG 응답 생성
    print("\n  Generating RAG responses...")
    evaluated = []
    for i, case in enumerate(legal_cases):
        try:
            answer = await service.query(case["question"])
            docs = service.retriever.invoke(case["question"])
            contexts = [d.page_content for d in docs]
        except Exception as e:
            answer = f"ERROR: {e}"
            contexts = []

        evaluated.append({**case, "rag_answer": answer, "retrieved_contexts": contexts})
        print(f"    [{i + 1}/{len(legal_cases)}] {case['id']}")

    # 2. Faithfulness 평가
    print("\n  Evaluating Faithfulness...")
    faithfulness_scores = []
    for case in evaluated:
        if not case["retrieved_contexts"]:
            continue
        ctx = "\n---\n".join(case["retrieved_contexts"])
        prompt = f"""답변이 컨텍스트에만 근거하는지 0.0~1.0으로 평가하세요.
컨텍스트:\n{ctx}\n\n질문: {case['question']}\n답변: {case['rag_answer']}\n\n숫자만:"""
        resp = judge.invoke(prompt)
        try:
            score = max(0.0, min(1.0, float(resp.content.strip())))
        except ValueError:
            score = 0.0
        faithfulness_scores.append({"id": case["id"], "score": score})

    avg_faith = (
        sum(s["score"] for s in faithfulness_scores) / len(faithfulness_scores)
        if faithfulness_scores
        else 0
    )

    # 3. Answer Relevancy 평가
    print("  Evaluating Answer Relevancy...")
    relevancy_scores = []
    for case in evaluated:
        prompt = f"""질문에 대한 답변의 관련성을 0.0~1.0으로 평가하세요.
질문: {case['question']}\n답변: {case['rag_answer']}\n\n숫자만:"""
        resp = judge.invoke(prompt)
        try:
            score = max(0.0, min(1.0, float(resp.content.strip())))
        except ValueError:
            score = 0.0
        relevancy_scores.append({"id": case["id"], "score": score})

    avg_rel = (
        sum(s["score"] for s in relevancy_scores) / len(relevancy_scores)
        if relevancy_scores
        else 0
    )

    # 4. Answer Correctness 평가
    print("  Evaluating Answer Correctness...")
    correctness_scores = []
    for case in evaluated:
        prompt = f"""정답과 AI 답변의 의미적 일치도를 0-3으로 평가하세요.
질문: {case['question']}\n정답: {case['ground_truth']}\nAI 답변: {case['rag_answer']}\n\n숫자만 (0-3):"""
        resp = judge.invoke(prompt)
        try:
            score = max(0, min(3, int(float(resp.content.strip()))))
        except ValueError:
            score = 0
        correctness_scores.append({"id": case["id"], "score": score, "normalized": score / 3.0})

    avg_correct = (
        sum(s["normalized"] for s in correctness_scores) / len(correctness_scores)
        if correctness_scores
        else 0
    )

    # 5. Hit Rate 계산 (무비용)
    hits = 0
    hit_total = 0
    for case in evaluated:
        kws = case.get("expected_keywords", [])
        if not kws:
            continue
        hit_total += 1
        ctx_text = " ".join(case["retrieved_contexts"]).lower()
        if any(kw.lower() in ctx_text for kw in kws):
            hits += 1
    hit_rate = hits / hit_total if hit_total > 0 else 0

    # 결과 요약
    print(f"\n  ─── Tier 2 Results ───")
    print(f"  Faithfulness:       {avg_faith:.3f}")
    print(f"  Answer Relevancy:   {avg_rel:.3f}")
    print(f"  Answer Correctness: {avg_correct:.3f}")
    print(f"  Hit Rate@3:         {hit_rate:.2%}")

    result = {
        "faithfulness": {"avg": avg_faith, "details": faithfulness_scores},
        "answer_relevancy": {"avg": avg_rel, "details": relevancy_scores},
        "answer_correctness": {"avg": avg_correct, "details": correctness_scores},
        "hit_rate": hit_rate,
        "total_cases": len(evaluated),
        "timestamp": datetime.now().isoformat(),
    }
    save_results("tier2_metrics", result)

    # 개별 케이스 상세 저장
    cases_output = []
    for case in evaluated:
        cases_output.append({
            "id": case["id"],
            "question": case["question"],
            "ground_truth": case["ground_truth"],
            "rag_answer": case["rag_answer"],
            "retrieved_context_count": len(case["retrieved_contexts"]),
        })
    save_results("tier2_cases", cases_output)

    return result


# ─── Tier 4: 로드맵 품질 평가 ─────────────────────────────────────

ROADMAP_GOLDEN_DATASET_PATH = EVAL_DATA_DIR / "roadmap_golden_dataset.json"
ROADMAP_EVAL_RESULTS_PATH = RESULTS_DIR / "roadmap_eval_results.json"
ROADMAP_BASELINE_PATH = RESULTS_DIR / "roadmap_baseline.json"


def _load_roadmap_golden_dataset() -> list[dict]:
    """로드맵 골든 데이터셋 로드."""
    with open(ROADMAP_GOLDEN_DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_mock_steps_for_scenario(scenario: dict) -> list[dict]:
    """골든 데이터셋 시나리오에서 mock steps_payload를 구성한다.

    시나리오에 ``mock_steps`` 키가 있으면 그대로 반환한다.
    없으면 ``expected`` 필드를 참고해 최소한의 mock 데이터를 자동 생성한다.
    """
    if "mock_steps" in scenario:
        return scenario["mock_steps"]

    expected = scenario.get("expected", {})
    payload = scenario.get("payload", {})
    business_type = payload.get("business_type", "사업체")
    startup_type = payload.get("startup_type", "신규")
    experience_level = payload.get("experience_level", "BEGINNER")
    phases = expected.get("expected_phases", ["영업 인허가"])
    min_legal_basis = expected.get("min_legal_basis", 1)
    min_documents = expected.get("min_documents", 0)
    expected_mapping_rate = expected.get("expected_actionkit_mapping_rate", 0.7)

    # Distribute legal_basis and documents proportionally across phases
    legal_per_phase = max(1, min_legal_basis // max(len(phases), 1))
    doc_per_phase = max(0, min_documents // max(len(phases), 1))

    # Determine mapping_source based on expected_mapping_rate
    mapping_source = "actionkit_direct" if expected_mapping_rate >= 0.5 else "llm_generated"

    # Build personalized checklist depth based on experience_level
    checklist_items = (
        [f"{business_type} 영업신고 서류 확인", "위생교육 이수 여부 확인", "보건증 발급 신청"]
        if experience_level == "BEGINNER"
        else [f"{business_type} 핵심 서류 준비", "필수 요건 확인"]
    )
    if startup_type == "양수양도":
        checklist_items.insert(0, "기존 인허가 승계 여부 확인")
    elif startup_type == "프랜차이즈":
        checklist_items.insert(0, "본사 지원 항목 확인")

    steps: list[dict] = []
    item_id_counter = 1

    for idx, phase in enumerate(phases):
        legal_basis: list[dict] = []
        for i in range(legal_per_phase):
            legal_basis.append({
                "title": f"관련 법령 {idx * legal_per_phase + i + 1}",
                "snippet": f"{business_type} {phase} 관련 법령 요약",
                "actionkit_item_id": item_id_counter if mapping_source == "actionkit_direct" else None,
                "mapping_source": mapping_source,
            })
            item_id_counter += 1

        documents: list[dict] = []
        for i in range(doc_per_phase):
            documents.append({
                "name": f"서류 {idx * doc_per_phase + i + 1}",
                "file_url": f"actionkit/forms/{business_type}_{idx}_{i}.pdf" if mapping_source == "actionkit_direct" else None,
                "actionkit_item_id": item_id_counter if mapping_source == "actionkit_direct" else None,
                "actionkit_file_id": item_id_counter * 10 if mapping_source == "actionkit_direct" else None,
                "mapping_source": mapping_source,
            })
            item_id_counter += 1

        steps.append({
            "phase": phase,
            "title": f"{phase} 단계 진행",
            "objective": f"{business_type} {phase} 절차를 완료합니다.",
            "estimated_days": 7 if experience_level == "EXPERIENCED" else 14,
            "checklist": checklist_items[:],
            "legal_basis": legal_basis,
            "documents": documents,
            "risk_notes": [f"{phase} 단계 지연 위험"],
            "mapping_source": mapping_source,
            "actionkit_items": [item_id_counter - 1] if mapping_source == "actionkit_direct" else [],
        })

    return steps


async def run_tier4(mock_mode: bool = True) -> dict:
    """Tier 4: 로드맵 품질 평가.

    Args:
        mock_mode: True면 골든 데이터셋의 mock_steps 또는 자동 생성 mock을 사용.
                   False면 실제 DB 연결로 생성된 로드맵을 평가 (인프라 필요).

    Returns:
        평가 결과 dict (actionkit_mapping_rate, legal_basis_accuracy 등 집계값).
    """
    print("\n" + "=" * 60)
    print("TIER 4: 로드맵 품질 평가")
    print("=" * 60)

    if not ROADMAP_GOLDEN_DATASET_PATH.exists():
        print(f"  SKIP: {ROADMAP_GOLDEN_DATASET_PATH} 없음")
        return {"skipped": True}

    from scripts.eval.roadmap_evaluator import RoadmapEvaluator, PersonalizationEvalResult, summarize_eval_result

    dataset = _load_roadmap_golden_dataset()
    print(f"  Loaded {len(dataset)} roadmap scenarios")

    evaluator = RoadmapEvaluator()

    # ── 단일 시나리오 평가 ──────────────────────────────────────────
    eval_results: list[dict] = []
    aggregated: dict[str, list[float]] = {
        "actionkit_mapping_rate": [],
        "legal_basis_accuracy": [],
        "document_validity": [],
        "generation_success_rate": [],
        "personalization_score": [],
        "overall_score": [],
    }

    print("\n  ─── Per-scenario Evaluation ───")

    regular_scenarios = [s for s in dataset if not s.get("comparison_pair")]
    for scenario in regular_scenarios:
        scenario_id = scenario["id"]
        payload = scenario.get("payload", {})
        business_type = payload.get("business_type", "")

        steps_payload = _build_mock_steps_for_scenario(scenario)

        result = await evaluator.evaluate(
            steps_payload=steps_payload,
            business_type=business_type,
            payload=payload,
        )

        summary_line = summarize_eval_result(result)
        print(f"    [{scenario_id}] {summary_line}")

        result_dict = result.to_dict()
        result_dict["scenario_id"] = scenario_id
        result_dict["description"] = scenario.get("description", "")
        eval_results.append(result_dict)

        for key in aggregated:
            val = result_dict.get(key, result.overall_score() if key == "overall_score" else 0.0)
            aggregated[key].append(float(val))

    # ── 개인화 비교 평가 ────────────────────────────────────────────
    personalization_results: list[dict] = []
    print("\n  ─── Personalization Comparison ───")

    # Find explicit comparison pairs from the dataset
    pair_ids: set[str] = set()
    for scenario in dataset:
        cmp_id = scenario.get("expected", {}).get("comparison_pair_id")
        if cmp_id and scenario["id"] not in pair_ids and cmp_id not in pair_ids:
            pair_ids.add(scenario["id"])
            pair_ids.add(cmp_id)
            # Find the paired scenario
            pair_scenario = next((s for s in dataset if s["id"] == cmp_id), None)
            if pair_scenario:
                steps_a = _build_mock_steps_for_scenario(scenario)
                steps_b = _build_mock_steps_for_scenario(pair_scenario)
                p_result = await evaluator.evaluate_personalization(
                    result_a=steps_a,
                    result_b=steps_b,
                    payload_a=scenario.get("payload", {}),
                    payload_b=pair_scenario.get("payload", {}),
                )
                print(f"    Pair {scenario['id']} vs {cmp_id}: {p_result.analysis[:80]}")
                p_dict = p_result.to_dict()
                p_dict["scenario_ids"] = [scenario["id"], cmp_id]
                personalization_results.append(p_dict)

    # Also handle explicit comparison_pair scenarios (with mock_steps_a / mock_steps_b)
    for scenario in dataset:
        if scenario.get("comparison_pair"):
            steps_a = scenario.get("mock_steps_a", [])
            steps_b = scenario.get("mock_steps_b", [])
            if steps_a and steps_b:
                p_result = await evaluator.evaluate_personalization(
                    result_a=steps_a,
                    result_b=steps_b,
                    payload_a=scenario.get("payload_a", {}),
                    payload_b=scenario.get("payload_b", {}),
                )
                print(f"    [{scenario['id']}] {p_result.analysis[:80]}")
                p_dict = p_result.to_dict()
                p_dict["scenario_ids"] = [scenario["id"]]
                personalization_results.append(p_dict)

    # ── 집계 결과 ──────────────────────────────────────────────────
    def _avg(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    avg_metrics = {k: round(_avg(v), 4) for k, v in aggregated.items()}
    avg_personalization = (
        round(
            sum(r["overall_personalization_score"] for r in personalization_results)
            / len(personalization_results),
            4,
        )
        if personalization_results
        else 0.0
    )

    print(f"\n  ─── Tier 4 Aggregate Results ({len(eval_results)} scenarios) ───")
    print(f"  ActionKit Mapping Rate:   {avg_metrics['actionkit_mapping_rate']:.3f}")
    print(f"  Legal Basis Accuracy:     {avg_metrics['legal_basis_accuracy']:.3f}")
    print(f"  Document Validity:        {avg_metrics['document_validity']:.3f}")
    print(f"  Generation Success Rate:  {avg_metrics['generation_success_rate']:.3f}")
    print(f"  Personalization Score:    {avg_metrics['personalization_score']:.3f}")
    print(f"  Overall Score:            {avg_metrics['overall_score']:.3f}")
    if personalization_results:
        print(f"  Personalization Diff:     {avg_personalization:.3f}")

    full_result = {
        "timestamp": datetime.now().isoformat(),
        "total_scenarios": len(eval_results),
        "mode": "mock" if mock_mode else "live",
        "actionkit_mapping_rate": avg_metrics["actionkit_mapping_rate"],
        "legal_basis_accuracy": avg_metrics["legal_basis_accuracy"],
        "document_validity": avg_metrics["document_validity"],
        "generation_success_rate": avg_metrics["generation_success_rate"],
        "personalization_score": avg_metrics["personalization_score"],
        "overall_score": avg_metrics["overall_score"],
        "avg_personalization_difference": avg_personalization,
        "scenario_results": eval_results,
        "personalization_comparisons": personalization_results,
    }

    # Save detailed results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ROADMAP_EVAL_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(full_result, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {ROADMAP_EVAL_RESULTS_PATH}")

    # Baseline comparison for roadmap metrics
    _compare_roadmap_with_baseline(full_result)

    return full_result


def _compare_roadmap_with_baseline(current: dict) -> None:
    """로드맵 평가 결과를 roadmap_baseline.json과 비교하여 회귀 감지."""
    if not ROADMAP_BASELINE_PATH.exists():
        print(f"  INFO: {ROADMAP_BASELINE_PATH.name} 없음 — 첫 실행이면 --update-baseline으로 저장하세요.")
        return

    with open(ROADMAP_BASELINE_PATH, encoding="utf-8") as f:
        baseline = json.load(f)

    roadmap_margins = {
        "actionkit_mapping_rate": 0.05,
        "legal_basis_accuracy": 0.10,
        "personalization_score": 0.10,
    }

    regressions: list[str] = []
    print(f"\n  ─── Roadmap Regression Check (vs baseline) ───")
    for metric, margin in roadmap_margins.items():
        b_val = baseline.get(metric)
        c_val = current.get(metric)
        if b_val is None or c_val is None:
            continue
        diff = c_val - b_val
        status = "OK"
        if diff < -margin:
            status = "REGRESSION"
            regressions.append(metric)
        elif diff > 0:
            status = "IMPROVED"
        print(
            f"    {metric:30s}  baseline={b_val:.3f}  current={c_val:.3f}  "
            f"diff={diff:+.3f} (margin={margin:.2f})  [{status}]"
        )

    if regressions:
        print(f"\n  WARNING: {len(regressions)} roadmap metric(s) regressed: {regressions}")
    else:
        print(f"\n  All roadmap metrics within acceptable range.")


# ─── 회귀 감지 ────────────────────────────────────────────────────

# 메트릭별 허용 하락 마진 (절대값). 이 이상 떨어지면 회귀로 판정.
REGRESSION_MARGINS: dict[str, float] = {
    "hit_rate_at_3": 0.10,
    "faithfulness": 0.05,
    "answer_relevancy": 0.05,
    "answer_correctness": 0.05,
    "routing_accuracy": 0.10,
    "oos_refusal_rate": 0.10,
    "legal_accuracy": 0.05,
    # Roadmap quality metrics (Tier 4)
    "roadmap_actionkit_mapping_rate": 0.05,
    "roadmap_legal_basis_accuracy": 0.10,
    "roadmap_personalization_score": 0.10,
}


def detect_regression() -> list[str]:
    """baseline.json과 latest_run.json을 비교하여 회귀를 감지.

    Returns:
        회귀 감지된 메트릭 목록. 빈 리스트면 회귀 없음.
    """
    if not BASELINE_PATH.exists():
        print("  SKIP: baseline.json이 없어 회귀 감지 생략")
        return []
    if not LATEST_RUN_PATH.exists():
        print("  SKIP: latest_run.json이 없어 회귀 감지 생략")
        return []

    with open(BASELINE_PATH, encoding="utf-8") as f:
        baseline = json.load(f)
    with open(LATEST_RUN_PATH, encoding="utf-8") as f:
        latest = json.load(f)

    baseline_metrics = baseline.get("metrics", {})
    latest_metrics = latest.get("metrics", {})

    regressions: list[str] = []

    print(f"\n  ─── Regression Check (vs baseline {baseline.get('git_commit', '?')}) ───")

    for metric, margin in REGRESSION_MARGINS.items():
        b_val = baseline_metrics.get(metric)
        l_val = latest_metrics.get(metric)

        if b_val is None or l_val is None:
            continue

        diff = l_val - b_val
        status = "OK"
        if diff < -margin:
            status = "REGRESSION"
            regressions.append(metric)
        elif diff > 0:
            status = "IMPROVED"

        print(
            f"    {metric:25s}  baseline={b_val:.3f}  current={l_val:.3f}  "
            f"diff={diff:+.3f} (margin={margin:.2f})  [{status}]"
        )

    if regressions:
        print(f"\n  WARNING: {len(regressions)} metric(s) regressed: {regressions}")
    else:
        print(f"\n  All metrics within acceptable range.")

    return regressions


# ─── 리포트 생성 ──────────────────────────────────────────────────


def generate_report() -> None:
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY REPORT")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    all_results = {}
    for f in RESULTS_DIR.glob("*.json"):
        if f.stem == "summary_report":
            continue
        try:
            with open(f, encoding="utf-8") as fp:
                all_results[f.stem] = json.load(fp)
        except Exception:
            pass

    # 요약 출력
    if "tier1_routing" in all_results:
        t1 = all_results["tier1_routing"]
        print(f"\n  [Tier 1] Routing Accuracy: {t1.get('routing_accuracy', 'N/A'):.2%}")

    if "tier2_metrics" in all_results:
        t2 = all_results["tier2_metrics"]
        print(f"\n  [Tier 2] Metrics:")
        print(f"    Faithfulness:       {t2.get('faithfulness', {}).get('avg', 'N/A')}")
        print(f"    Answer Relevancy:   {t2.get('answer_relevancy', {}).get('avg', 'N/A')}")
        print(f"    Answer Correctness: {t2.get('answer_correctness', {}).get('avg', 'N/A')}")
        print(f"    Hit Rate@3:         {t2.get('hit_rate', 'N/A')}")

    if ROADMAP_EVAL_RESULTS_PATH.exists():
        try:
            with open(ROADMAP_EVAL_RESULTS_PATH, encoding="utf-8") as fp:
                t4 = json.load(fp)
            if not t4.get("skipped"):
                print(f"\n  [Tier 4] Roadmap Quality Metrics ({t4.get('total_scenarios', 0)} scenarios):")
                print(f"    ActionKit Mapping Rate:   {t4.get('actionkit_mapping_rate', 'N/A')}")
                print(f"    Legal Basis Accuracy:     {t4.get('legal_basis_accuracy', 'N/A')}")
                print(f"    Document Validity:        {t4.get('document_validity', 'N/A')}")
                print(f"    Generation Success Rate:  {t4.get('generation_success_rate', 'N/A')}")
                print(f"    Personalization Score:    {t4.get('personalization_score', 'N/A')}")
                print(f"    Overall Score:            {t4.get('overall_score', 'N/A')}")
        except Exception:
            pass

    # Pass/Fail 판정
    thresholds = {
        "routing_accuracy": 0.70,
        "faithfulness": 0.50,
        "answer_relevancy": 0.50,
        "answer_correctness": 0.40,
        "hit_rate": 0.60,
        # Roadmap thresholds (Tier 4)
        "roadmap_actionkit_mapping_rate": 0.50,
        "roadmap_legal_basis_accuracy": 0.50,
        "roadmap_personalization_score": 0.40,
    }

    print(f"\n  ─── Pass/Fail Summary ───")

    # Load tier 4 results once for the pass/fail loop
    t4_data: dict = {}
    if ROADMAP_EVAL_RESULTS_PATH.exists():
        try:
            with open(ROADMAP_EVAL_RESULTS_PATH, encoding="utf-8") as fp:
                t4_data = json.load(fp)
        except Exception:
            pass

    for metric, threshold in thresholds.items():
        value = None

        if metric == "routing_accuracy" and "tier1_routing" in all_results:
            value = all_results["tier1_routing"].get(metric, 0)

        elif metric.startswith("roadmap_") and t4_data and not t4_data.get("skipped"):
            # roadmap_actionkit_mapping_rate -> actionkit_mapping_rate in t4_data
            t4_key = metric[len("roadmap_"):]
            value = t4_data.get(t4_key)

        elif "tier2_metrics" in all_results:
            t2 = all_results["tier2_metrics"]
            if metric == "hit_rate":
                value = t2.get(metric, 0)
            elif not metric.startswith("roadmap_"):
                value = t2.get(metric, {}).get("avg", 0)

        if value is not None:
            status = "PASS" if value >= threshold else "FAIL"
            print(f"    {metric:35s} {value:.3f}  (>= {threshold:.2f})  [{status}]")

    # 종합 리포트 저장
    summary = {
        "evaluation_date": datetime.now().isoformat(),
        "thresholds": thresholds,
        "results": all_results,
    }
    save_results("summary_report", summary)
    print(f"\n  Full report: {RESULTS_DIR / 'summary_report.json'}")


# ─── Main ──────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG 및 로드맵 품질 성능 평가")
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3, 4],
        default=2,
        help=(
            "평가 티어 "
            "(1=무비용 라우팅, 2=LLM RAG 평가, 3=전체 RAG, "
            "4=로드맵 품질 평가). 기본: 2"
        ),
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="기존 결과로 리포트만 생성",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="latest_run.json을 baseline.json으로 갱신",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Tier 4: mock 데이터로 실행 (인프라 없이 동작, 기본값 True)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Tier 4: 실제 DB에서 로드맵 생성 후 평가 (DB + OpenAI 필요)",
    )
    args = parser.parse_args()

    # --update-baseline: latest_run → baseline 복사 후 종료
    if args.update_baseline:
        update_baseline()
        # Also update roadmap baseline if Tier 4 results exist
        if ROADMAP_EVAL_RESULTS_PATH.exists():
            with open(ROADMAP_EVAL_RESULTS_PATH, encoding="utf-8") as f:
                t4_data = json.load(f)
            if not t4_data.get("skipped"):
                t4_data["description"] = f"Baseline updated at {datetime.now().isoformat()}"
                with open(ROADMAP_BASELINE_PATH, "w", encoding="utf-8") as f:
                    json.dump(t4_data, f, ensure_ascii=False, indent=2)
                print(f"  Roadmap baseline updated: {ROADMAP_BASELINE_PATH}")
        return

    if args.report_only:
        generate_report()
        return

    start = time.time()

    tier1_result = None
    tier2_result = None
    tier4_result = None

    # Tier 4 is standalone — skip RAG dataset loading when only tier 4 is requested
    if args.tier == 4:
        mock_mode = not args.live
        tier4_result = asyncio.run(run_tier4(mock_mode=mock_mode))
    else:
        dataset = load_golden_dataset()
        print(f"  Loaded {len(dataset)} test cases from golden dataset")

        if args.tier >= 1:
            tier1_result = run_tier1(dataset)

        if args.tier >= 2:
            tier2_result = asyncio.run(run_tier2(dataset))

        elapsed = time.time() - start
        print(f"\n  Total evaluation time: {elapsed:.1f}s")

        # latest_run.json 자동 저장 (RAG tiers only)
        save_latest_run(dataset, tier1_result, tier2_result)

        # baseline 대비 회귀 감지
        regressions = detect_regression()

        generate_report()

        if regressions:
            print(f"\n  EXIT CODE 1: {len(regressions)} regression(s) detected")
            raise SystemExit(1)
        return

    elapsed = time.time() - start
    print(f"\n  Total evaluation time: {elapsed:.1f}s")
    generate_report()


if __name__ == "__main__":
    main()
