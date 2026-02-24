#!/usr/bin/env python3
"""
RAG 성능 종합 평가 스크립트.

DB 연결 + OpenAI API 필요.
결과를 tests/eval/results/에 저장하고 콘솔에 요약 출력.

사용법:
    cd app-backend
    python -m scripts.eval.run_evaluation [--tier 1|2|3] [--report-only]
    python -m scripts.eval.run_evaluation --update-baseline  # 현재 결과로 baseline 갱신
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


def save_latest_run(dataset: list[dict], tier1_result: dict | None, tier2_result: dict | None) -> dict:
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
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="latest_run.json을 baseline.json으로 갱신",
    )
    args = parser.parse_args()

    # --update-baseline: latest_run → baseline 복사 후 종료
    if args.update_baseline:
        update_baseline()
        return

    if args.report_only:
        generate_report()
        return

    dataset = load_golden_dataset()
    print(f"  Loaded {len(dataset)} test cases from golden dataset")

    start = time.time()

    tier1_result = None
    tier2_result = None

    if args.tier >= 1:
        tier1_result = run_tier1(dataset)

    if args.tier >= 2:
        tier2_result = asyncio.run(run_tier2(dataset))

    elapsed = time.time() - start
    print(f"\n  Total evaluation time: {elapsed:.1f}s")

    # latest_run.json 자동 저장
    save_latest_run(dataset, tier1_result, tier2_result)

    # baseline 대비 회귀 감지
    regressions = detect_regression()

    generate_report()

    if regressions:
        print(f"\n  EXIT CODE 1: {len(regressions)} regression(s) detected")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
