#!/usr/bin/env python3
"""법률 데이터 수집 CLI 스크립트.

국가법령정보센터 Open API를 통해 업종별 법령을 수집하고
.temp/rag/{업종}/{법령명}.md + {법령명}_meta.json 으로 저장한다.

Usage:
    cd app-backend

    # Wave 1 전체 수집
    python -m scripts.fetch_laws --wave 1

    # 단일 법률 수집
    python -m scripts.fetch_laws --law 식품위생법

    # 수집 대상 목록 출력
    python -m scripts.fetch_laws --list

    # 수집 현황 출력
    python -m scripts.fetch_laws --status

    # 시뮬레이션 (실제 API 호출 없음)
    python -m scripts.fetch_laws --wave 1 --dry-run

    # 기존 파일 덮어쓰기
    python -m scripts.fetch_laws --wave 1 --force
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.core.logging import get_logger
from app.services.law_api_client import LawApiClient, LawApiError, LawFullText

from scripts.fetch_laws_config import (
    WAVE_CONFIG,
    get_wave_targets,
    list_all_queries,
)

logger = get_logger("scripts.fetch_laws")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_OUTPUT_ROOT = _BACKEND_ROOT / ".temp" / "rag"

_LAW_TYPE_MAP = {
    "법률": "법률",
    "시행령": "대통령령",
    "시행규칙": "총리령,부령",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거한다."""
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()


def _format_articles_to_markdown(law: LawFullText) -> str:
    """LawFullText를 Markdown 문자열로 변환한다."""
    lines: list[str] = []
    lines.append(f"# {law.law_name}")
    lines.append("")
    lines.append(f"- 법령ID: {law.law_id}")
    lines.append(f"- 법령MST: {law.mst}")
    lines.append(f"- 시행일자: {law.enforcement_date}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for article in law.articles:
        title_part = f" {article.article_title}" if article.article_title else ""
        lines.append(f"## 제{article.article_no}조{title_part}")
        lines.append("")
        if article.article_content:
            lines.append(article.article_content.strip())
        lines.append("")

    return "\n".join(lines)


def _build_metadata(
    law: LawFullText,
    biz_types: list[str],
    hierarchy: str,
) -> dict:
    """메타데이터 dict를 생성한다."""
    return {
        "law_id": str(law.law_id),
        "law_name": law.law_name,
        "effective_date": law.enforcement_date,
        "target_business_types": biz_types,
        "law_hierarchy": hierarchy,
        "source_url": f"https://www.law.go.kr/법령/{law.law_name}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _save_law(
    biz_type: str,
    law: LawFullText,
    hierarchy: str,
    biz_types: list[str],
    force: bool = False,
) -> bool:
    """법령을 .md + _meta.json 파일로 저장한다. 반환: 저장 성공 여부."""
    safe_name = _sanitize_filename(law.law_name)
    out_dir = _OUTPUT_ROOT / biz_type
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"{safe_name}.md"
    meta_path = out_dir / f"{safe_name}_meta.json"

    if md_path.exists() and not force:
        logger.info("  -> 이미 존재, 건너뜀: %s (--force 로 덮어쓰기)", md_path)
        return False

    # Markdown
    md_content = _format_articles_to_markdown(law)
    md_path.write_text(md_content, encoding="utf-8")

    # Metadata JSON
    meta = _build_metadata(law, biz_types, hierarchy)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("  -> 저장 완료: %s (%d조)", md_path.relative_to(_BACKEND_ROOT), len(law.articles))
    return True


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------


async def _fetch_and_save_law(
    client: LawApiClient,
    query: str,
    hierarchy_filters: list[str],
    biz_type: str,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, str]:
    """단일 쿼리에 대해 법령 검색 → 본문 조회 → 저장.

    Returns: {"query": ..., "status": "saved" | "skipped" | "not_found" | "error"}
    """
    result = {"query": query, "biz_type": biz_type, "status": "unknown", "laws": []}

    if dry_run:
        logger.info("[DRY-RUN] 검색: query='%s', hierarchy=%s, 업종=%s", query, hierarchy_filters, biz_type)
        result["status"] = "dry_run"
        return result

    try:
        search_results = await client.search_laws(query, display=20)
    except LawApiError as e:
        logger.error("검색 실패: query='%s', error=%s", query, e)
        result["status"] = "error"
        return result

    if not search_results:
        logger.warning("검색 결과 없음: query='%s'", query)
        result["status"] = "not_found"
        return result

    # hierarchy 필터링: "법률" → law_type 에서 "법률" 포함,
    # "시행령" → "대통령령", "시행규칙" → "총리령" 또는 "부령"
    saved_count = 0
    for sr in search_results:
        matched_hierarchy = None
        for h in hierarchy_filters:
            target_types = _LAW_TYPE_MAP.get(h, h)
            for tt in target_types.split(","):
                if tt in sr.law_type:
                    matched_hierarchy = h
                    break
            if matched_hierarchy:
                break

        if not matched_hierarchy:
            continue

        logger.info("  본문 조회: %s (MST=%s, type=%s)", sr.law_name, sr.law_mst, sr.law_type)
        try:
            full_text = await client.get_law_full_text(str(sr.law_mst))
        except LawApiError as e:
            logger.error("  본문 조회 실패: %s, error=%s", sr.law_name, e)
            continue

        if not full_text.law_name:
            full_text.law_name = sr.law_name
        if not full_text.law_id:
            full_text.law_id = int(sr.law_id) if sr.law_id else 0
        if not full_text.enforcement_date:
            full_text.enforcement_date = sr.enforcement_date

        was_saved = _save_law(biz_type, full_text, matched_hierarchy, [biz_type], force)
        if was_saved:
            saved_count += 1
        result["laws"].append(sr.law_name)

    result["status"] = "saved" if saved_count > 0 else "skipped"
    return result


async def fetch_wave(wave: int, force: bool = False, dry_run: bool = False) -> list[dict]:
    """Wave 단위로 법률을 수집한다."""
    targets = get_wave_targets(wave)
    all_results = []

    async with LawApiClient() as client:
        for biz_type, queries in targets.items():
            logger.info("=== 업종: %s ===", biz_type)
            for q in queries:
                logger.info("  검색: query='%s', hierarchy=%s", q["query"], q["hierarchy"])
                result = await _fetch_and_save_law(
                    client,
                    q["query"],
                    q["hierarchy"],
                    biz_type,
                    force=force,
                    dry_run=dry_run,
                )
                all_results.append(result)

    return all_results


async def fetch_single_law(law_name: str, force: bool = False) -> list[dict]:
    """단일 법률명으로 검색하여 수집한다."""
    # WAVE_CONFIG에서 해당 법률이 속한 업종 찾기
    biz_type = "기타"
    hierarchy = ["법률", "시행령", "시행규칙"]
    for _wave, biz_map in WAVE_CONFIG.items():
        for bt, queries in biz_map.items():
            for q in queries:
                if law_name in q["query"] or q["query"] in law_name:
                    biz_type = bt
                    hierarchy = q["hierarchy"]
                    break

    async with LawApiClient() as client:
        result = await _fetch_and_save_law(
            client, law_name, hierarchy, biz_type, force=force,
        )
    return [result]


# ---------------------------------------------------------------------------
# CLI subcommands
# ---------------------------------------------------------------------------


def cmd_list() -> None:
    """수집 대상 목록 출력."""
    queries = list_all_queries()
    print(f"\n{'Wave':>5}  {'업종':<15}  {'검색 쿼리':<40}  {'계층'}")
    print("-" * 90)
    for wave, biz_type, query, hierarchy in queries:
        h_str = ", ".join(hierarchy)
        print(f"{wave:>5}  {biz_type:<15}  {query:<40}  {h_str}")
    print(f"\n총 {len(queries)}건의 검색 쿼리")


def cmd_status() -> None:
    """수집 현황 출력."""
    print(f"\n수집 디렉토리: {_OUTPUT_ROOT}")
    if not _OUTPUT_ROOT.exists():
        print("  -> 디렉토리가 존재하지 않습니다.")
        return

    total_md = 0
    total_meta = 0
    for biz_dir in sorted(_OUTPUT_ROOT.iterdir()):
        if not biz_dir.is_dir():
            continue
        md_files = list(biz_dir.glob("*.md"))
        meta_files = list(biz_dir.glob("*_meta.json"))
        total_md += len(md_files)
        total_meta += len(meta_files)
        print(f"  {biz_dir.name}: {len(md_files)} md, {len(meta_files)} meta")
        for md in sorted(md_files):
            print(f"    - {md.name}")

    print(f"\n총 {total_md}개 법령 문서, {total_meta}개 메타데이터")


def _print_results(results: list[dict]) -> None:
    """수집 결과 리포트 출력."""
    print(f"\n{'업종':<15}  {'쿼리':<35}  {'상태':<10}  {'수집 법령'}")
    print("-" * 100)
    for r in results:
        laws = ", ".join(r.get("laws", []))[:40]
        print(f"{r['biz_type']:<15}  {r['query']:<35}  {r['status']:<10}  {laws}")

    saved = sum(1 for r in results if r["status"] == "saved")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")
    not_found = sum(1 for r in results if r["status"] == "not_found")
    print(f"\n결과: 저장={saved}, 건너뜀={skipped}, 미발견={not_found}, 에러={errors}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="국가법령정보센터 API를 통한 업종별 법률 수집 CLI."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--wave", type=int, choices=[1, 2, 3], help="수집할 Wave 번호 (1-3)")
    group.add_argument("--law", type=str, help="단일 법률명으로 검색하여 수집")
    group.add_argument("--list", action="store_true", help="수집 대상 목록 출력")
    group.add_argument("--status", action="store_true", help="수집 현황 출력")

    parser.add_argument("--dry-run", action="store_true", help="시뮬레이션 (실제 API 호출 없음)")
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    return parser.parse_args()


async def run() -> int:
    args = parse_args()

    if args.list:
        cmd_list()
        return 0

    if args.status:
        cmd_status()
        return 0

    if args.wave:
        logger.info("Wave %d 수집 시작 (dry_run=%s, force=%s)", args.wave, args.dry_run, args.force)
        results = await fetch_wave(args.wave, force=args.force, dry_run=args.dry_run)
        _print_results(results)
        return 0

    if args.law:
        logger.info("단일 법률 수집: '%s' (force=%s)", args.law, args.force)
        results = await fetch_single_law(args.law, force=args.force)
        _print_results(results)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
