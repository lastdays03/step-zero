#!/usr/bin/env python3
"""
RAG 성능 종합 평가 스크립트.

DB 연결 + OpenAI API 필요.
결과를 tests/eval/results/에 저장하고 콘솔에 요약 출력.

사용법:
    cd app-backend
    python -m scripts.eval.run_evaluation [--tier 1|2|3] [--report-only]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── 경로 설정 ─────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_DATA_DIR = PROJECT_ROOT / "tests" / "eval" / "data"
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval" / "results"


def load_golden_dataset() -> list[dict]:
    path = EVAL_DATA_DIR / "golden_dataset.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_results(name: str, data: Any) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {path}")


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

    # Pass/Fail 판정
    thresholds = {
        "routing_accuracy": 0.70,
        "faithfulness": 0.50,
        "answer_relevancy": 0.50,
        "answer_correctness": 0.40,
        "hit_rate": 0.60,
    }

    print(f"\n  ─── Pass/Fail Summary ───")
    for metric, threshold in thresholds.items():
        if metric == "routing_accuracy" and "tier1_routing" in all_results:
            value = all_results["tier1_routing"].get(metric, 0)
        elif "tier2_metrics" in all_results:
            t2 = all_results["tier2_metrics"]
            if metric == "hit_rate":
                value = t2.get(metric, 0)
            else:
                value = t2.get(metric, {}).get("avg", 0)
        else:
            value = None

        if value is not None:
            status = "PASS" if value >= threshold else "FAIL"
            print(f"    {metric:25s} {value:.3f}  (>= {threshold:.2f})  [{status}]")

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
    parser = argparse.ArgumentParser(description="RAG 성능 평가")
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3],
        default=2,
        help="평가 티어 (1=무비용, 2=LLM 평가, 3=전체). 기본: 2",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="기존 결과로 리포트만 생성",
    )
    args = parser.parse_args()

    if args.report_only:
        generate_report()
        return

    dataset = load_golden_dataset()
    print(f"  Loaded {len(dataset)} test cases from golden dataset")

    start = time.time()

    if args.tier >= 1:
        run_tier1(dataset)

    if args.tier >= 2:
        asyncio.run(run_tier2(dataset))

    elapsed = time.time() - start
    print(f"\n  Total evaluation time: {elapsed:.1f}s")

    generate_report()


if __name__ == "__main__":
    main()
