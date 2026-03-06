"""
로컬 파일 -> R2 마이그레이션 스크립트

files 테이블 기반으로 로컬 uploads/ 디렉토리의 파일을 R2에 업로드합니다.

사용법:
  uv run python scripts/migrate_to_r2.py --dry-run
  uv run python scripts/migrate_to_r2.py
  uv run python scripts/migrate_to_r2.py --verify
"""
from __future__ import annotations

import argparse
import asyncio
import mimetypes
import os
import sys
from pathlib import Path

# app 패키지를 import 할 수 있도록 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


async def get_engine_and_session():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, async_session


async def get_r2_backend():
    """R2 스토리지 백엔드 인스턴스 생성 (no-arg constructor, reads settings internally)"""
    from app.services.storage.r2 import R2StorageBackend

    return R2StorageBackend()


def resolve_local_path(object_key: str, owner_type: str, uploads_root: str) -> str | None:
    """object_key에서 로컬 파일 경로를 해석.

    owner_type에 따라 파일 위치가 다름:
    - actionkit_item: uploads/actionkit/{object_key}
    - growth_club_post: uploads/{object_key}
    - user_profile: uploads/{object_key}
    """
    # actionkit 파일은 별도 하위 디렉토리에 저장됨
    if owner_type == "actionkit_item":
        candidate = os.path.join(uploads_root, "actionkit", object_key)
        if os.path.exists(candidate):
            return candidate

    # 그 외는 object_key가 직접 매핑
    candidate = os.path.join(uploads_root, object_key)
    if os.path.exists(candidate):
        return candidate

    return None


def to_r2_key(object_key: str, owner_type: str) -> str:
    """owner_type에 따라 R2 object key를 결정.

    - actionkit_item: actionkit/{object_key} prefix 추가
    - 나머지: object_key 그대로
    """
    if owner_type == "actionkit_item":
        return f"actionkit/{object_key}"
    return object_key


def detect_mime(filepath: str) -> str:
    mime, _ = mimetypes.guess_type(filepath)
    return mime or "application/octet-stream"


async def migrate(dry_run: bool) -> None:
    settings = get_settings()
    uploads_root = str(settings.STORAGE_ROOT_PATH)

    print(f"Uploads root: {uploads_root}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    r2 = None
    if not dry_run:
        r2 = await get_r2_backend()

    engine, async_session_factory = await get_engine_and_session()

    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT id, owner_type, object_key FROM files ORDER BY id")
        )
        rows = result.fetchall()

        total = len(rows)
        uploaded = 0
        missing = 0
        errors = 0

        print(f"Total files: {total}")
        print("-" * 60)

        for i, row in enumerate(rows, 1):
            file_id, owner_type, object_key = row

            local_path = resolve_local_path(object_key, owner_type, uploads_root)

            if not local_path:
                print(f"  [{i}/{total}] MISSING: {object_key} (owner={owner_type})")
                missing += 1
                continue

            r2_key = to_r2_key(object_key, owner_type)

            if dry_run:
                size = os.path.getsize(local_path)
                print(f"  [{i}/{total}] WOULD UPLOAD: {r2_key} ({size:,} bytes)")
                uploaded += 1
                continue

            try:
                mime = detect_mime(local_path)
                with open(local_path, "rb") as f:
                    data = f.read()

                assert r2 is not None
                await r2.put(r2_key, data, content_type=mime)
                uploaded += 1

                if i % 10 == 0 or i == total:
                    print(f"  [{i}/{total}] uploaded: {r2_key}")
            except Exception as e:
                print(f"  [{i}/{total}] ERROR: {r2_key} - {e}")
                errors += 1

        print()
        print(f"Result: total={total}, uploaded={uploaded}, missing={missing}, errors={errors}")

    await engine.dispose()


async def verify() -> None:
    r2 = await get_r2_backend()
    engine, async_session_factory = await get_engine_and_session()

    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT id, owner_type, object_key, size_bytes FROM files ORDER BY id")
        )
        rows = result.fetchall()

        total = len(rows)
        ok = 0
        fail = 0

        print(f"Verifying {total} files in R2...")
        print("-" * 60)

        for i, row in enumerate(rows, 1):
            file_id, owner_type, object_key, db_size = row

            r2_key = to_r2_key(object_key, owner_type)

            try:
                data = await r2.get(r2_key)
                r2_size = len(data)

                if db_size and r2_size != db_size:
                    print(
                        f"  [{i}/{total}] SIZE MISMATCH: {r2_key} "
                        f"(DB={db_size}, R2={r2_size})"
                    )
                    fail += 1
                else:
                    ok += 1
            except Exception:
                print(f"  [{i}/{total}] NOT FOUND: {r2_key}")
                fail += 1

        print()
        print(f"Verify result: total={total}, ok={ok}, fail={fail}")
        print("PASS" if fail == 0 else "FAIL")

    await engine.dispose()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Local uploads -> R2 migration")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be uploaded without actually uploading",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify all files exist in R2 with correct sizes",
    )
    args = parser.parse_args()

    if args.verify:
        await verify()
    else:
        await migrate(args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
