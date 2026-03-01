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

    # 백업 JSON으로부터 법률 벡터 복원 (기존 314 벡터 유지하며 추가)
    python -m scripts.seed_rag_vectors --restore-backup
    python -m scripts.seed_rag_vectors --restore-backup --backup-file .temp/backups/law_vectors_20260224_153755.json

    # 큐레이션된 법률 문서 적재 (LLM ETL 없이 직접 청킹)
    python -m scripts.seed_rag_vectors --curated
    python -m scripts.seed_rag_vectors --curated --curated-dir .temp/rag
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
from pathlib import Path

from sqlmodel import select

from app.core.config import get_settings
from app.core.db import async_session
from app.core.logging import get_logger
from app.models.actionkit import (
    ActionKitCategory,
    ActionKitFile,
    ActionKitItem,
    ActionKitItemHighlight,
)
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

    backend_root_for_backup = Path(__file__).resolve().parents[1]
    default_backup = (
        backend_root_for_backup
        / ".temp"
        / "backups"
        / "law_vectors_20260224_153755.json"
    )
    parser.add_argument(
        "--restore-backup",
        action="store_true",
        help="백업 JSON 파일의 법률 벡터를 law_vectors 컬렉션에 추가 적재 (기존 벡터 삭제 없음).",
    )
    parser.add_argument(
        "--backup-file",
        default=str(default_backup),
        help=f"복원할 백업 JSON 파일 경로 (기본값: {default_backup}).",
    )

    parser.add_argument(
        "--curated",
        action="store_true",
        help="큐레이션된 _curated.md 파일을 직접 청킹하여 적재 + ActionKitItem 자동 생성.",
    )
    parser.add_argument(
        "--curated-dir",
        default=str(default_source),
        help="큐레이션 파일이 있는 루트 디렉토리 (기본값: .temp/rag).",
    )
    parser.add_argument(
        "--sync-actionkit",
        action="store_true",
        help="curated 파일 기반 ActionKitItem만 생성 (벡터 적재 없음, 기존 보강용).",
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


async def _ingest_laws(
    source_dir: Path, limit: int, vector_store: VectorStoreService
) -> int:
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


async def _restore_from_backup(
    backup_file: Path, vector_store: VectorStoreService
) -> int:
    """백업 JSON 파일로부터 법률 벡터를 복원하여 law_vectors 컬렉션에 추가한다.

    기존 벡터(ActionKit 314건 등)는 삭제하지 않고, 백업의 3건만 청킹 후 추가한다.
    chunk_size=600, overlap=100, RecursiveCharacterTextSplitter 적용.

    반환: 추가된 문서 수.
    """
    if not backup_file.exists():
        logger.warning(
            "--restore-backup: 백업 파일을 찾을 수 없습니다. 건너뜀. (경로: %s)",
            backup_file,
        )
        return 0

    with open(backup_file, encoding="utf-8") as f:
        backup = json.load(f)

    records = backup.get("records", [])
    if not records:
        logger.warning("--restore-backup: 백업 파일에 records가 없습니다. 건너뜀.")
        return 0

    logger.info(
        "--restore-backup: 백업 파일 로드 완료 (collection=%s, records=%d, backed_up_at=%s)",
        backup.get("collection_name", "unknown"),
        len(records),
        backup.get("backed_up_at", "unknown"),
    )

    # RecursiveCharacterTextSplitter로 청킹 적용
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        length_function=len,
    )

    chunked_docs: list[Document] = []
    for record in records:
        raw_text = record.get("document", "")
        metadata = record.get("cmetadata", {})
        if not raw_text:
            continue
        chunks = splitter.split_text(raw_text)
        for chunk in chunks:
            chunked_docs.append(Document(page_content=chunk, metadata=metadata))

    if not chunked_docs:
        logger.warning("--restore-backup: 청킹 후 문서가 없습니다. 건너뜀.")
        return 0

    logger.info(
        "--restore-backup: 청킹 완료 (원본 %d건 → 청크 %d건), law_vectors에 추가 중...",
        len(records),
        len(chunked_docs),
    )

    # 이미 청킹된 Document이므로 PGVector에 직접 적재
    from langchain_postgres import PGVector

    pg_vector = PGVector(
        embeddings=vector_store.embeddings,
        collection_name=vector_store.collection_name,
        connection=vector_store.db_url,
        use_jsonb=True,
    )
    pg_vector.add_documents(chunked_docs)
    logger.info(
        "--restore-backup: 복원 완료. %d 청크를 law_vectors에 추가했습니다.",
        len(chunked_docs),
    )
    return len(records)


def _detect_law_hierarchy(filename: str) -> str:
    """파일명으로부터 법령 위계를 판별한다."""
    if "시행규칙" in filename:
        return "시행규칙"
    if "시행령" in filename:
        return "시행령"
    return "법률"


def _detect_law_name(filename: str) -> str:
    """파일명에서 _curated.md 접미사를 제거하여 법령명을 추출한다."""
    return filename.replace("_curated.md", "").strip()


def _extract_summary_from_curated(content: str, law_name: str) -> str:
    """큐레이션 파일 내용에서 1줄 요약을 추출한다."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("> 큐레이션 기준:"):
            return stripped.lstrip("> 큐레이션 기준:").strip()
        if stripped.startswith("> "):
            return stripped.lstrip("> ").strip()
    return f"{law_name} 관련 큐레이션 조문"


def _extract_highlights_from_curated(content: str, max_count: int = 5) -> list[str]:
    """큐레이션 파일에서 ## 제목(조문명)을 highlights로 추출한다."""
    highlights: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and len(stripped) > 3:
            highlights.append(stripped[3:].strip())
            if len(highlights) >= max_count:
                break
    return highlights


# 업종 → 챕터 슬러그 매핑 (기존 1~6은 시드 데이터가 차지)
_BUSINESS_TYPE_TO_CHAPTER: dict[str, tuple[str, str]] = {
    "식품제조가공업": ("7", "Ⅶ. 식품제조가공업 관련법"),
    "통신판매업": ("8", "Ⅷ. 통신판매업 관련법"),
    "미용업": ("9", "Ⅸ. 미용업 관련법"),
    "일반소매업": ("10", "Ⅹ. 일반소매업 관련법"),
    "학원업": ("11", "ⅩⅠ. 학원업 관련법"),
    "숙박업": ("12", "ⅩⅡ. 숙박업 관련법"),
}


def _normalize_filename(filename: str) -> str:
    """파일명에서 특수 문자를 제거하고 공백을 _로 치환한다."""
    cleaned = filename.strip().replace(" ", "_")
    cleaned = re.sub(r"[^A-Za-z0-9._\-가-힣]", "", cleaned)
    return cleaned or "file.bin"


def _copy_file_to_storage(
    source: Path,
    *,
    item_id: int,
    chapter_slug: str,
) -> tuple[str, int, str]:
    """큐레이션 파일을 ActionKit 스토리지에 복사한다.

    반환: (object_key, size_bytes, checksum)
    """
    settings = get_settings()
    storage_root = settings.ACTIONKIT_STORAGE_PATH

    normalized = _normalize_filename(source.name)
    object_key = f"laws/chapter-{chapter_slug}/{item_id}/v1/{normalized}"
    dest = storage_root / object_key
    dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, dest)

    size_bytes = dest.stat().st_size
    sha = hashlib.sha256()
    with dest.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    checksum = sha.hexdigest()

    return object_key, size_bytes, checksum


async def _ensure_actionkit_items(
    curated_files: list[Path],
) -> int:
    """큐레이션 파일 목록으로부터 ActionKitCategory/Item/Highlight/File을 생성한다.

    이미 동일 name의 Item이 존재하면 건너뛴다 (멱등).
    파일이 없는 기존 Item에 대해서는 ActionKitFile을 보강한다.
    반환: 새로 생성된 ActionKitItem 수.
    """
    created_count = 0

    async with async_session() as session:
        # 기존 아이템 이름+카테고리 로드 (중복 체크용)
        existing_result = await session.execute(
            select(ActionKitItem.id, ActionKitItem.name, ActionKitItem.category_id)
        )
        existing_rows = existing_result.fetchall()
        # (name, category_id) 튜플로 중복 체크 (같은 법령이 다른 업종에 존재 가능)
        existing_name_cat: set[tuple[str, int]] = {
            (row[1], row[2]) for row in existing_rows
        }
        name_cat_to_item_id: dict[tuple[str, int], int] = {
            (row[1], row[2]): row[0] for row in existing_rows
        }

        # 기존 파일 레코드 로드 (item_id → 존재 여부)
        file_result = await session.execute(
            select(ActionKitFile.item_id).where(ActionKitFile.is_current.is_(True))
        )
        items_with_files: set[int] = {row[0] for row in file_result.fetchall()}

        # 기존 카테고리 로드
        cat_result = await session.execute(
            select(ActionKitCategory).where(ActionKitCategory.domain == "laws")
        )
        slug_to_category: dict[str, ActionKitCategory] = {
            c.slug: c for c in cat_result.scalars().all()
        }

        # 업종별로 그룹핑
        business_files: dict[str, list[Path]] = {}
        for fpath in curated_files:
            category_name = fpath.parent.name
            business_files.setdefault(category_name, []).append(fpath)

        for business_type, files in business_files.items():
            mapping = _BUSINESS_TYPE_TO_CHAPTER.get(business_type)
            if not mapping:
                logger.warning(
                    "[ActionKit] 업종 '%s'의 챕터 매핑이 없습니다. 건너뜀.",
                    business_type,
                )
                continue

            chapter_slug, chapter_title = mapping

            # 카테고리 생성 or 조회
            if chapter_slug not in slug_to_category:
                max_sort = max(
                    (c.sort_order for c in slug_to_category.values()), default=0
                )
                cat = ActionKitCategory(
                    domain="laws",
                    slug=chapter_slug,
                    title=chapter_title,
                    sort_order=max_sort + 1,
                    is_active=True,
                )
                session.add(cat)
                await session.flush()
                slug_to_category[chapter_slug] = cat
                logger.info(
                    "[ActionKit] 카테고리 생성: slug=%s, title=%s",
                    chapter_slug,
                    chapter_title,
                )

            category = slug_to_category[chapter_slug]

            # 아이템 생성 + 파일 등록
            for sort_idx, fpath in enumerate(sorted(files), start=1):
                law_name = _detect_law_name(fpath.name)

                dedup_key = (law_name, category.id)
                if dedup_key in existing_name_cat:
                    # 기존 Item에 파일이 없으면 보강
                    item_id = name_cat_to_item_id.get(dedup_key)
                    if item_id and item_id not in items_with_files:
                        object_key, size_bytes, checksum = _copy_file_to_storage(
                            fpath,
                            item_id=item_id,
                            chapter_slug=chapter_slug,
                        )
                        session.add(
                            ActionKitFile(
                                item_id=item_id,
                                version=1,
                                object_key=object_key,
                                original_filename=fpath.name,
                                mime_type="text/markdown",
                                size_bytes=size_bytes,
                                checksum=checksum,
                                is_current=True,
                            )
                        )
                        items_with_files.add(item_id)
                        logger.info(
                            "[ActionKit] 기존 아이템 파일 보강: id=%d, name=%s",
                            item_id,
                            law_name,
                        )
                    else:
                        logger.info("[ActionKit] 이미 존재, 건너뜀: %s", law_name)
                    continue

                content = fpath.read_text(encoding="utf-8")
                summary = _extract_summary_from_curated(content, law_name)
                highlights = _extract_highlights_from_curated(content)

                item = ActionKitItem(
                    domain="laws",
                    category_id=category.id,
                    name=law_name,
                    summary=summary,
                    tag=f"[{business_type}]",
                    ext=".md",
                    file_type="MD",
                    sort_order=sort_idx,
                    is_active=True,
                )
                session.add(item)
                await session.flush()

                for h_idx, highlight_text in enumerate(highlights, start=1):
                    session.add(
                        ActionKitItemHighlight(
                            item_id=item.id,
                            content=highlight_text,
                            sort_order=h_idx,
                        )
                    )

                # 파일 복사 + ActionKitFile 레코드 생성
                object_key, size_bytes, checksum = _copy_file_to_storage(
                    fpath,
                    item_id=item.id,
                    chapter_slug=chapter_slug,
                )
                session.add(
                    ActionKitFile(
                        item_id=item.id,
                        version=1,
                        object_key=object_key,
                        original_filename=fpath.name,
                        mime_type="text/markdown",
                        size_bytes=size_bytes,
                        checksum=checksum,
                        is_current=True,
                    )
                )

                existing_name_cat.add(dedup_key)
                name_cat_to_item_id[dedup_key] = item.id
                items_with_files.add(item.id)
                created_count += 1
                logger.info(
                    "[ActionKit] 아이템+파일 생성: id=%d, name=%s, highlights=%d, file=%s",
                    item.id,
                    law_name,
                    len(highlights),
                    object_key,
                )

        await session.commit()

    return created_count


async def _ingest_curated(curated_dir: Path, vector_store: VectorStoreService) -> int:
    """큐레이션된 _curated.md 파일을 직접 청킹하여 벡터 적재 + ActionKitItem 자동 생성.

    디렉토리 구조: {curated_dir}/{업종명}/{법령명}_curated.md

    1단계: ActionKitItem/Category/Highlight 자동 생성 (멱등)
    2단계: 벡터 청킹 후 law_vectors에 추가 적재

    반환: 적재된 청크 수.
    """
    from langchain_core.documents import Document
    from langchain_postgres import PGVector
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    curated_files = sorted(curated_dir.rglob("*_curated.md"))
    if not curated_files:
        logger.warning("큐레이션 파일 없음: %s", curated_dir)
        return 0

    logger.info("[Curated] %d개 큐레이션 파일 발견", len(curated_files))

    # 1단계: ActionKitItem 자동 생성
    created = await _ensure_actionkit_items(curated_files)
    logger.info("[Curated] ActionKitItem 생성: %d건 (새로 추가)", created)

    # 2단계: 벡터 청킹 + 적재
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "],
    )

    all_docs: list[Document] = []
    for fpath in curated_files:
        category = fpath.parent.name  # 업종 디렉토리명
        law_name = _detect_law_name(fpath.name)
        law_hierarchy = _detect_law_hierarchy(fpath.name)

        content = fpath.read_text(encoding="utf-8")
        if not content.strip():
            logger.warning("  빈 파일 건너뜀: %s", fpath)
            continue

        chunks = splitter.split_text(content)
        logger.info(
            "  %s / %s (%s): %d자 → %d 청크",
            category,
            law_name,
            law_hierarchy,
            len(content),
            len(chunks),
        )

        target_business_types = [category]

        for i, chunk in enumerate(chunks):
            metadata = {
                "source_type": "law_curated",
                "source": "law_curated",
                "target_business_types": target_business_types,
                "law_name": law_name,
                "law_hierarchy": law_hierarchy,
                "category": category,
                "title": law_name,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            all_docs.append(Document(page_content=chunk, metadata=metadata))

    if not all_docs:
        logger.warning("[Curated] 청킹 후 문서가 없습니다.")
        return 0

    logger.info(
        "[Curated] 총 %d 청크 적재 시작 (%d개 파일)",
        len(all_docs),
        len(curated_files),
    )

    pg_vector = PGVector(
        embeddings=vector_store.embeddings,
        collection_name=vector_store.collection_name,
        connection=vector_store.db_url,
        use_jsonb=True,
    )
    pg_vector.add_documents(all_docs)
    logger.info(
        "[Curated] 적재 완료: %d 청크 + ActionKitItem %d건", len(all_docs), created
    )
    return len(all_docs)


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

    # --sync-actionkit: ActionKitItem만 생성 (벡터 적재 없음, OPENAI_API_KEY 불필요)
    if args.sync_actionkit:
        curated_dir = Path(args.curated_dir).expanduser().resolve()
        curated_files = sorted(curated_dir.rglob("*_curated.md"))
        if not curated_files:
            logger.error("큐레이션 파일 없음: %s", curated_dir)
            return 1
        created = await _ensure_actionkit_items(curated_files)
        logger.info("=== ActionKitItem 동기화 완료: %d건 생성 ===", created)
        return 0

    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is required for RAG vector seeding")
        return 1

    # --clean: 기존 컬렉션 삭제
    if args.clean:
        sync_url = settings.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        deleted = _delete_collection(sync_url, "law_vectors")
        logger.info("기존 벡터 %d건 삭제 완료", deleted)

    vector_store = VectorStoreService()
    total_ingested = 0

    # --curated: 큐레이션된 법률 문서 직접 적재
    if args.curated:
        curated_dir = Path(args.curated_dir).expanduser().resolve()
        if curated_dir.exists():
            total_ingested += await _ingest_curated(curated_dir, vector_store)
        else:
            logger.warning("큐레이션 디렉토리 없음: %s", curated_dir)
        if total_ingested == 0:
            logger.error("인제스트된 큐레이션 문서가 없습니다.")
            return 1
        logger.info("=== 큐레이션 인제스트 완료: 총 %d 청크 ===", total_ingested)
        return 0

    # --restore-backup: 백업 JSON으로부터 복원 (단독 실행 또는 다른 옵션과 병행 가능)
    if args.restore_backup:
        backup_file = Path(args.backup_file).expanduser().resolve()
        total_ingested += await _restore_from_backup(backup_file, vector_store)
        if not args.actionkit_only and not args.include_actionkit:
            # restore-backup 단독 실행인 경우 여기서 종료
            if total_ingested == 0:
                logger.error("--restore-backup: 복원된 문서가 없습니다.")
                return 1
            logger.info("=== 백업 복원 완료: 총 %d건 ===", total_ingested)
            return 0

    # Step 1: 법률 문서 (--actionkit-only 및 --restore-backup 단독이 아닌 경우)
    if not args.actionkit_only and not args.restore_backup:
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
