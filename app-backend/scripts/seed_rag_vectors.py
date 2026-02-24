#!/usr/bin/env python3
"""law_vectors 통합 인제스트 스크립트.

두 가지 데이터 소스를 하나의 law_vectors 컬렉션에 적재한다:
  Step 1: LocalFileSource → LawETLProcessor → 청킹 → law_vectors
  Step 2: ActionKitDataSource → ActionKitETLBridge → 청킹 → law_vectors

Usage:
    cd app-backend

    # 법률 문서만 시딩
    python -m scripts.seed_rag_vectors --source-dir .temp/rag

    # ActionKit만 시딩
    python -m scripts.seed_rag_vectors --actionkit-only

    # 전체 재인덱싱 (삭제 후 법률 + ActionKit 모두 적재)
    python -m scripts.seed_rag_vectors --source-dir .temp/rag --include-actionkit --clean

    # ActionKit만 추가 (기존 법률 데이터 유지)
    python -m scripts.seed_rag_vectors --actionkit-only
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.vector_store import VectorStoreService

logger = get_logger("scripts.seed_rag_vectors")


def parse_args() -> argparse.Namespace:
    backend_root = Path(__file__).resolve().parents[1]
    default_source = backend_root / ".temp" / "rag"

    parser = argparse.ArgumentParser(
        description="RAG 벡터 컬렉션 통합 인제스트 (법률 + ActionKit)."
    )
    parser.add_argument(
        "--source-dir",
        default=str(default_source),
        help="법률 문서 루트 디렉토리 (pdf/md).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="법률 문서 최대 인제스트 수 (0 = 전체).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="기존 law_vectors 컬렉션을 삭제하고 재인덱싱.",
    )
    parser.add_argument(
        "--include-actionkit",
        action="store_true",
        help="ActionKit 데이터도 함께 인제스트.",
    )
    parser.add_argument(
        "--actionkit-only",
        action="store_true",
        help="ActionKit 데이터만 인제스트 (법률 문서 건너뜀).",
    )
    return parser.parse_args()


def _delete_collection(db_url: str, collection_name: str) -> int:
    """기존 컬렉션의 임베딩을 삭제한다. 반환: 삭제된 레코드 수."""
    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
            {"name": collection_name},
        ).fetchone()

        if not row:
            logger.warning("컬렉션 '%s'이 존재하지 않습니다. 건너뜀.", collection_name)
            return 0

        collection_id = str(row[0])

        result = conn.execute(
            text("DELETE FROM langchain_pg_embedding WHERE collection_id = :cid"),
            {"cid": collection_id},
        )
        deleted = result.rowcount

        conn.execute(
            text("DELETE FROM langchain_pg_collection WHERE uuid = :uuid"),
            {"uuid": collection_id},
        )

        logger.info(
            "컬렉션 삭제 완료: name=%s, uuid=%s, 삭제 벡터=%d",
            collection_name,
            collection_id,
            deleted,
        )
        return deleted


async def _ingest_laws(source_dir: Path, limit: int, vector_store: VectorStoreService) -> int:
    """Step 1: LocalFileSource → LawETLProcessor → VectorStore."""
    from app.services.law_etl import LawETLProcessor
    from app.services.law_fetcher import LocalFileSource

    source = LocalFileSource(str(source_dir))
    raw_laws = await source.fetch_all_laws()
    if not raw_laws:
        logger.warning("법률 문서 없음: %s", source_dir)
        return 0

    selected = raw_laws[:limit] if limit and limit > 0 else raw_laws
    logger.info(
        "[Step 1] 법률 ETL 시작: total=%d, selected=%d",
        len(raw_laws),
        len(selected),
    )

    etl = LawETLProcessor()
    processed = []
    for idx, law in enumerate(selected, start=1):
        logger.info("  법률 ETL %d/%d: %s", idx, len(selected), law.title)
        processed.append(await etl.process(law))

    await vector_store.add_documents(processed)
    logger.info("[Step 1] 법률 인제스트 완료: %d건 (청킹 적용)", len(processed))
    return len(processed)


async def _ingest_actionkit(vector_store: VectorStoreService) -> int:
    """Step 2: ActionKitDataSource → ActionKitETLBridge → VectorStore."""
    from app.services.actionkit_data_source import ActionKitDataSource
    from app.services.actionkit_etl import ActionKitETLBridge

    source = ActionKitDataSource()
    law_data_list = await source.fetch_all_laws()
    if not law_data_list:
        logger.warning("ActionKit 데이터 없음")
        return 0

    logger.info("[Step 2] ActionKit ETL 시작: %d건", len(law_data_list))

    bridge = ActionKitETLBridge()
    processed = await bridge.process_batch(law_data_list)

    await vector_store.add_documents(processed)
    logger.info("[Step 2] ActionKit 인제스트 완료: %d건 (청킹 적용)", len(processed))
    return len(processed)


async def run() -> int:
    args = parse_args()
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is required for RAG vector seeding")
        return 1

    # --clean: 기존 컬렉션 삭제
    if args.clean:
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        deleted = _delete_collection(sync_url, "law_vectors")
        logger.info("기존 벡터 %d건 삭제 완료", deleted)

    vector_store = VectorStoreService()
    total_ingested = 0

    # Step 1: 법률 문서 (--actionkit-only가 아닌 경우)
    if not args.actionkit_only:
        source_dir = Path(args.source_dir).expanduser().resolve()
        if source_dir.exists():
            total_ingested += await _ingest_laws(source_dir, args.limit, vector_store)
        else:
            logger.warning("법률 소스 디렉토리 없음: %s", source_dir)

    # Step 2: ActionKit (--include-actionkit 또는 --actionkit-only)
    if args.include_actionkit or args.actionkit_only:
        total_ingested += await _ingest_actionkit(vector_store)

    if total_ingested == 0:
        logger.error("인제스트된 문서가 없습니다. 소스 확인 필요.")
        return 1

    logger.info("=== 통합 인제스트 완료: 총 %d건 ===", total_ingested)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
