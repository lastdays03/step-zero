#!/usr/bin/env python3
"""Seed PGVector collection from local law documents."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.law_etl import LawETLProcessor
from app.services.law_fetcher import LocalFileSource
from app.services.vector_store import VectorStoreService

logger = get_logger("scripts.seed_rag_vectors")


def parse_args() -> argparse.Namespace:
    backend_root = Path(__file__).resolve().parents[1]
    default_source = backend_root / ".temp" / "rag"

    parser = argparse.ArgumentParser(
        description="Seed RAG vector collection from local .pdf/.md documents."
    )
    parser.add_argument(
        "--source-dir",
        default=str(default_source),
        help="Root directory containing law documents (pdf/md).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max documents to ingest (0 means all).",
    )
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    settings = get_settings()

    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.exists():
        logger.error("source directory does not exist: %s", source_dir)
        return 1

    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is required for RAG vector seeding")
        return 1

    source = LocalFileSource(str(source_dir))
    raw_laws = await source.fetch_all_laws()
    if not raw_laws:
        logger.error("no source documents found under: %s", source_dir)
        return 1

    selected = raw_laws[: args.limit] if args.limit and args.limit > 0 else raw_laws
    logger.info(
        "starting RAG ETL: source=%s total=%d selected=%d",
        source_dir,
        len(raw_laws),
        len(selected),
    )

    etl = LawETLProcessor()
    processed_docs = []
    for idx, law in enumerate(selected, start=1):
        logger.info("etl %d/%d: %s", idx, len(selected), law.title)
        processed_docs.append(await etl.process(law))

    vector_store = VectorStoreService()
    await vector_store.add_documents(processed_docs)
    logger.info("RAG vector seeding complete: inserted=%d", len(processed_docs))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
