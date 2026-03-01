#!/usr/bin/env python3
"""로드맵 품질 Baseline 평가 스크립트.

DB에 저장된 기존 로드맵 데이터를 분석하여 정량적 품질 baseline을
JSON 리포트로 출력한다.

5개 핵심 지표:
  1. fallback_rate          - 업종별 LEGAL_BASIS 액션 중 source_url 없는 비율
  2. source_url_coverage    - 업종별 전체 액션의 source_url 보유율
  3. generation_mode_distribution - RAG vs ACTIONKIT_RAG 생성 모드 분포
  4. avg_actions_per_step   - 단계별 평균 액션 수
  5. retrieval_precision_at_3 - 상위 3건 검색 정밀도 (source_url 유효성 기반 근사)

Usage:
    cd app-backend
    python -m scripts.eval_roadmap_quality              # 전체 분석 (콘솔 + JSON)
    python -m scripts.eval_roadmap_quality --json        # JSON만 stdout
    python -m scripts.eval_roadmap_quality --output results/baseline.json  # 파일 저장
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import get_settings
from app.core.db import async_session
from app.core.logging import get_logger, setup_logging
from app.models.roadmap import (
    Roadmap,
    RoadmapStep,
    RoadmapStepAction,
    RoadmapStepDetail,
)

logger = get_logger("scripts.eval_roadmap_quality")


# ─── Data structures ─────────────────────────────────────────────────


class RoadmapSnapshot:
    """In-memory representation of a single roadmap with related data."""

    def __init__(
        self,
        roadmap: Roadmap,
        steps: list[RoadmapStep],
        details: dict[int, RoadmapStepDetail],
        actions: dict[int, list[RoadmapStepAction]],
    ) -> None:
        self.roadmap = roadmap
        self.steps = steps
        self.details = details  # step_id -> detail
        self.actions = actions  # step_id -> [actions]


# ─── DB queries ───────────────────────────────────────────────────────


async def load_all_roadmaps(session: AsyncSession) -> list[RoadmapSnapshot]:
    """Load all non-deleted roadmaps with steps, details, and actions."""
    # 1. Load roadmaps
    stmt = (
        select(Roadmap).where(Roadmap.deleted_at.is_(None)).order_by(Roadmap.created_at)
    )
    result = await session.execute(stmt)
    roadmaps: list[Roadmap] = list(result.scalars().all())

    if not roadmaps:
        return []

    roadmap_ids = [r.id for r in roadmaps]

    # 2. Load steps
    step_stmt = (
        select(RoadmapStep)
        .where(RoadmapStep.roadmap_id.in_(roadmap_ids))
        .order_by(RoadmapStep.roadmap_id, RoadmapStep.step_order)
    )
    step_result = await session.execute(step_stmt)
    all_steps: list[RoadmapStep] = list(step_result.scalars().all())

    steps_by_roadmap: dict[Any, list[RoadmapStep]] = defaultdict(list)
    all_step_ids: list[int] = []
    for s in all_steps:
        steps_by_roadmap[s.roadmap_id].append(s)
        if s.id is not None:
            all_step_ids.append(s.id)

    # 3. Load details
    details_by_step: dict[int, RoadmapStepDetail] = {}
    if all_step_ids:
        detail_stmt = select(RoadmapStepDetail).where(
            RoadmapStepDetail.roadmap_step_id.in_(all_step_ids)
        )
        detail_result = await session.execute(detail_stmt)
        for d in detail_result.scalars().all():
            details_by_step[d.roadmap_step_id] = d

    # 4. Load actions
    actions_by_step: dict[int, list[RoadmapStepAction]] = defaultdict(list)
    if all_step_ids:
        action_stmt = (
            select(RoadmapStepAction)
            .where(RoadmapStepAction.roadmap_step_id.in_(all_step_ids))
            .order_by(RoadmapStepAction.roadmap_step_id, RoadmapStepAction.id)
        )
        action_result = await session.execute(action_stmt)
        for a in action_result.scalars().all():
            actions_by_step[a.roadmap_step_id].append(a)

    # 5. Assemble snapshots
    snapshots: list[RoadmapSnapshot] = []
    for rm in roadmaps:
        rm_steps = steps_by_roadmap.get(rm.id, [])
        rm_details: dict[int, RoadmapStepDetail] = {}
        rm_actions: dict[int, list[RoadmapStepAction]] = {}
        for st in rm_steps:
            if st.id is not None:
                if st.id in details_by_step:
                    rm_details[st.id] = details_by_step[st.id]
                rm_actions[st.id] = actions_by_step.get(st.id, [])

        snapshots.append(RoadmapSnapshot(rm, rm_steps, rm_details, rm_actions))

    return snapshots


# ─── Metric computations ─────────────────────────────────────────────


def compute_fallback_rate(snapshot: RoadmapSnapshot) -> dict[str, Any]:
    """LEGAL_BASIS 액션 중 source_url이 없는 비율 (법률/비법률 분리).

    Returns:
        dict with keys: total_legal_basis, fallback_count, fallback_rate,
        legal_fallback_count, non_legal_fallback_count
    """
    total = 0
    fallback = 0
    legal_fallback = 0
    non_legal_fallback = 0

    for step_id, actions in snapshot.actions.items():
        for action in actions:
            if action.action_type != "LEGAL_BASIS":
                continue
            total += 1
            if not action.source_url:
                fallback += 1
                # Check if phase is a legal phase (chapters 1-6)
                detail = snapshot.details.get(step_id)
                phase = detail.phase if detail else ""
                legal_phases = {
                    "입지 검토",
                    "영업 인허가",
                    "안전·소방",
                    "영업 준수사항",
                    "위반 대응",
                    "행정처분 구제",
                }
                if phase in legal_phases:
                    legal_fallback += 1
                else:
                    non_legal_fallback += 1

    return {
        "total_legal_basis": total,
        "fallback_count": fallback,
        "fallback_rate": round(fallback / total, 4) if total > 0 else 0.0,
        "legal_fallback_count": legal_fallback,
        "non_legal_fallback_count": non_legal_fallback,
    }


def compute_source_url_coverage(snapshot: RoadmapSnapshot) -> dict[str, Any]:
    """전체 액션의 source_url 보유율.

    Returns:
        dict with keys: total_actions, with_source_url, coverage
    """
    total = 0
    with_url = 0

    for actions in snapshot.actions.values():
        for action in actions:
            total += 1
            if action.source_url:
                with_url += 1

    return {
        "total_actions": total,
        "with_source_url": with_url,
        "coverage": round(with_url / total, 4) if total > 0 else 0.0,
    }


def compute_generation_mode_distribution(
    snapshot: RoadmapSnapshot,
) -> dict[str, Any]:
    """RAG vs ACTIONKIT_RAG 생성 모드 분포.

    Returns:
        dict with keys: total_steps_with_detail, mode_counts (dict)
    """
    mode_counts: dict[str, int] = defaultdict(int)
    total = 0

    for detail in snapshot.details.values():
        total += 1
        mode_counts[detail.generation_mode] += 1

    return {
        "total_steps_with_detail": total,
        "mode_counts": dict(mode_counts),
    }


def compute_avg_actions_per_step(snapshot: RoadmapSnapshot) -> dict[str, Any]:
    """단계별 평균 액션 수.

    Returns:
        dict with keys: total_steps, total_actions, avg_actions_per_step,
        by_action_type (dict of type -> avg)
    """
    total_steps = len(snapshot.steps)
    total_actions = sum(len(acts) for acts in snapshot.actions.values())

    type_counts: dict[str, int] = defaultdict(int)
    for actions in snapshot.actions.values():
        for action in actions:
            type_counts[action.action_type] += 1

    by_type: dict[str, float] = {}
    for atype, count in type_counts.items():
        by_type[atype] = round(count / total_steps, 2) if total_steps > 0 else 0.0

    return {
        "total_steps": total_steps,
        "total_actions": total_actions,
        "avg_actions_per_step": (
            round(total_actions / total_steps, 2) if total_steps > 0 else 0.0
        ),
        "by_action_type": by_type,
    }


def compute_retrieval_precision_at_3(snapshot: RoadmapSnapshot) -> dict[str, Any]:
    """상위 3건 검색 정밀도 (source_url 유효성 기반 근사).

    각 step의 LEGAL_BASIS 액션을 순서대로 최대 3건까지 검사하여
    source_url이 있으면 '유효 검색'으로 간주한다.

    Returns:
        dict with keys: total_steps_evaluated, precision_at_3
    """
    step_precisions: list[float] = []

    for step in snapshot.steps:
        if step.id is None:
            continue
        actions = snapshot.actions.get(step.id, [])
        legal_actions = [a for a in actions if a.action_type == "LEGAL_BASIS"]

        if not legal_actions:
            continue

        top_3 = legal_actions[:3]
        hits = sum(1 for a in top_3 if a.source_url)
        step_precisions.append(hits / len(top_3))

    avg_precision = (
        round(sum(step_precisions) / len(step_precisions), 4)
        if step_precisions
        else 0.0
    )

    return {
        "total_steps_evaluated": len(step_precisions),
        "precision_at_3": avg_precision,
    }


# ─── Aggregation ──────────────────────────────────────────────────────


def analyze_snapshots(snapshots: list[RoadmapSnapshot]) -> dict[str, Any]:
    """Analyze all roadmap snapshots and produce the full report dict."""
    by_business_type: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "fallback_rates": [],
            "source_url_coverages": [],
            "generation_modes": defaultdict(int),
            "avg_actions_per_step_list": [],
            "retrieval_precisions": [],
        }
    )

    overall_fallback_rates: list[float] = []
    overall_coverages: list[float] = []
    overall_gen_modes: dict[str, int] = defaultdict(int)
    overall_actions_per_step: list[float] = []
    overall_precisions: list[float] = []

    for snap in snapshots:
        bt = snap.roadmap.business_type
        entry = by_business_type[bt]
        entry["count"] += 1

        fb = compute_fallback_rate(snap)
        entry["fallback_rates"].append(fb["fallback_rate"])
        overall_fallback_rates.append(fb["fallback_rate"])

        cov = compute_source_url_coverage(snap)
        entry["source_url_coverages"].append(cov["coverage"])
        overall_coverages.append(cov["coverage"])

        gen = compute_generation_mode_distribution(snap)
        for mode, cnt in gen["mode_counts"].items():
            entry["generation_modes"][mode] += cnt
            overall_gen_modes[mode] += cnt

        act = compute_avg_actions_per_step(snap)
        entry["avg_actions_per_step_list"].append(act["avg_actions_per_step"])
        overall_actions_per_step.append(act["avg_actions_per_step"])

        prec = compute_retrieval_precision_at_3(snap)
        if prec["total_steps_evaluated"] > 0:
            entry["retrieval_precisions"].append(prec["precision_at_3"])
            overall_precisions.append(prec["precision_at_3"])

    def _avg(vals: list[float]) -> float:
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    # Build per-business-type summary
    bt_summary: dict[str, dict[str, Any]] = {}
    for bt, entry in by_business_type.items():
        bt_summary[bt] = {
            "count": entry["count"],
            "fallback_rate": _avg(entry["fallback_rates"]),
            "source_url_coverage": _avg(entry["source_url_coverages"]),
            "generation_mode": dict(entry["generation_modes"]),
            "avg_actions_per_step": _avg(entry["avg_actions_per_step_list"]),
            "retrieval_precision_at_3": _avg(entry["retrieval_precisions"]),
        }

    # Build overall summary
    overall: dict[str, Any] = {
        "fallback_rate": _avg(overall_fallback_rates),
        "source_url_coverage": _avg(overall_coverages),
        "generation_mode": dict(overall_gen_modes),
        "avg_actions_per_step": _avg(overall_actions_per_step),
        "retrieval_precision_at_3": _avg(overall_precisions),
    }

    report: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "total_roadmaps": len(snapshots),
        "by_business_type": bt_summary,
        "overall": overall,
    }

    return report


# ─── Console output ───────────────────────────────────────────────────


def print_report(report: dict[str, Any]) -> None:
    """Print a human-readable summary to stderr."""
    print("=" * 60, file=sys.stderr)
    print("  로드맵 품질 Baseline 리포트", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"  생성 시각: {report['generated_at']}", file=sys.stderr)
    print(f"  총 로드맵: {report['total_roadmaps']}", file=sys.stderr)

    if report["total_roadmaps"] == 0:
        print("\n  DB에 로드맵 데이터가 없습니다.", file=sys.stderr)
        return

    print("\n  ─── 업종별 요약 ───", file=sys.stderr)
    for bt, data in report["by_business_type"].items():
        print(f"\n  [{bt}] (count={data['count']})", file=sys.stderr)
        print(
            f"    fallback_rate:            {data['fallback_rate']:.4f}",
            file=sys.stderr,
        )
        print(
            f"    source_url_coverage:      {data['source_url_coverage']:.4f}",
            file=sys.stderr,
        )
        print(
            f"    generation_mode:          {data['generation_mode']}", file=sys.stderr
        )
        print(
            f"    avg_actions_per_step:     {data['avg_actions_per_step']:.2f}",
            file=sys.stderr,
        )
        print(
            f"    retrieval_precision@3:    {data['retrieval_precision_at_3']:.4f}",
            file=sys.stderr,
        )

    overall = report["overall"]
    print("\n  ─── 전체 요약 ───", file=sys.stderr)
    print(
        f"    fallback_rate:            {overall['fallback_rate']:.4f}", file=sys.stderr
    )
    print(
        f"    source_url_coverage:      {overall['source_url_coverage']:.4f}",
        file=sys.stderr,
    )
    print(
        f"    generation_mode:          {overall['generation_mode']}", file=sys.stderr
    )
    print(
        f"    avg_actions_per_step:     {overall['avg_actions_per_step']:.2f}",
        file=sys.stderr,
    )
    print(
        f"    retrieval_precision@3:    {overall['retrieval_precision_at_3']:.4f}",
        file=sys.stderr,
    )
    print("=" * 60, file=sys.stderr)


# ─── CLI ──────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="DB의 로드맵 데이터를 분석하여 정량적 품질 baseline 리포트를 생성합니다.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 리포트만 stdout으로 출력 (콘솔 요약 생략).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="리포트를 저장할 파일 경로 (예: results/baseline.json).",
    )
    return parser.parse_args()


async def run() -> int:
    """Main async entry point."""
    args = parse_args()

    logger.info("로드맵 품질 baseline 분석 시작")

    async with async_session() as session:
        snapshots = await load_all_roadmaps(session)

    logger.info("로드맵 %d건 로드 완료", len(snapshots))

    report = analyze_snapshots(snapshots)

    # Output
    json_str = json.dumps(report, ensure_ascii=False, indent=2)

    if args.json:
        # JSON only to stdout
        print(json_str)
    else:
        # Console summary + JSON
        print_report(report)
        print(json_str)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str, encoding="utf-8")
        logger.info("리포트 저장 완료: %s", output_path)

    logger.info("로드맵 품질 baseline 분석 완료")
    return 0


def main() -> None:
    """Sync entry point."""
    setup_logging()
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
