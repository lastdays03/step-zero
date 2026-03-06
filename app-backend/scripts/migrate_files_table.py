"""
기존 파일 모델 → 통합 files 테이블 데이터 마이그레이션

사용법:
  uv run python scripts/migrate_files_table.py --dry-run
  uv run python scripts/migrate_files_table.py
  uv run python scripts/migrate_files_table.py --verify
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


async def get_engine():
    settings = get_settings()
    return create_async_engine(settings.DATABASE_URL)


async def migrate_actionkit_files(session: AsyncSession, dry_run: bool) -> int:
    """actionkit_files → files"""
    count_result = await session.execute(text("SELECT COUNT(*) FROM actionkit_files"))
    total = count_result.scalar()
    print(f"  ActionKit files: {total}건")

    if dry_run or total == 0:
        return total

    await session.execute(
        text("""
        INSERT INTO files (owner_type, owner_id, category, object_key, original_filename,
                          mime_type, size_bytes, checksum, version, is_current, kind,
                          metadata_extra, uploaded_at, created_at)
        SELECT
            'actionkit_item',
            item_id,
            'document',
            object_key,
            original_filename,
            mime_type,
            size_bytes,
            checksum,
            version,
            is_current,
            NULL,
            '{}',
            uploaded_at,
            created_at
        FROM actionkit_files
        WHERE object_key NOT IN (SELECT object_key FROM files WHERE owner_type = 'actionkit_item')
    """)
    )
    return total


async def migrate_growth_club_attachments(session: AsyncSession, dry_run: bool) -> int:
    """growthclubpostattachment → files"""
    count_result = await session.execute(
        text("SELECT COUNT(*) FROM growthclubpostattachment")
    )
    total = count_result.scalar()
    print(f"  Growth Club attachments: {total}건")

    if dry_run or total == 0:
        return total

    await session.execute(
        text("""
        INSERT INTO files (owner_type, owner_id, category, object_key, original_filename,
                          mime_type, size_bytes, checksum, version, is_current, kind,
                          metadata_extra, uploaded_at, created_at)
        SELECT
            'growth_club_post',
            post_id,
            CASE WHEN kind = 'image' THEN 'image' ELSE 'file' END,
            object_key,
            original_filename,
            mime_type,
            size_bytes,
            NULL,
            NULL,
            NULL,
            kind,
            '{}',
            created_at,
            created_at
        FROM growthclubpostattachment
        WHERE object_key NOT IN (SELECT object_key FROM files WHERE owner_type = 'growth_club_post')
    """)
    )
    return total


async def migrate_profile_images(session: AsyncSession, dry_run: bool) -> int:
    """userprofile.profile_img → files"""
    count_result = await session.execute(
        text("""
        SELECT COUNT(*) FROM userprofile
        WHERE profile_img IS NOT NULL
          AND profile_img != ''
          AND profile_img != 'default.png'
    """)
    )
    total = count_result.scalar()
    print(f"  Profile images: {total}건")

    if dry_run or total == 0:
        return total

    await session.execute(
        text("""
        INSERT INTO files (owner_type, owner_id, category, object_key, original_filename,
                          mime_type, size_bytes, checksum, version, is_current, kind,
                          metadata_extra, uploaded_at, created_at)
        SELECT
            'user_profile',
            user_id,
            'profile_image',
            profile_img,
            profile_img,
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
            '{}',
            updated_at,
            updated_at
        FROM userprofile
        WHERE profile_img IS NOT NULL
          AND profile_img != ''
          AND profile_img != 'default.png'
          AND profile_img NOT IN (SELECT object_key FROM files WHERE owner_type = 'user_profile')
    """)
    )
    return total


async def build_id_mapping(session: AsyncSession, dry_run: bool) -> None:
    """actionkit_files.id → files.id 매핑 생성 (FK 재매핑용)"""
    if dry_run:
        print("  [dry-run] ID 매핑 생성 스킵")
        return

    # 매핑 테이블 생성 (이미 있으면 drop)
    await session.execute(text("DROP TABLE IF EXISTS _file_id_mapping"))
    await session.execute(
        text("""
        CREATE TABLE _file_id_mapping AS
        SELECT af.id AS old_id, f.id AS new_id
        FROM actionkit_files af
        JOIN files f ON f.object_key = af.object_key AND f.owner_type = 'actionkit_item'
    """)
    )

    count = await session.execute(text("SELECT COUNT(*) FROM _file_id_mapping"))
    print(f"  ID 매핑 생성: {count.scalar()}건")


async def remap_fk(session: AsyncSession, dry_run: bool) -> None:
    """RoadmapTemplateAction.actionkit_file_id FK 재매핑"""
    count_result = await session.execute(
        text("""
        SELECT COUNT(*) FROM roadmap_template_actions
        WHERE actionkit_file_id IS NOT NULL
    """)
    )
    total = count_result.scalar()
    print(f"  FK 재매핑 대상: {total}건")

    if dry_run or total == 0:
        return

    await session.execute(
        text("""
        UPDATE roadmap_template_actions rta
        SET actionkit_file_id = m.new_id
        FROM _file_id_mapping m
        WHERE rta.actionkit_file_id = m.old_id
    """)
    )
    print("  FK 재매핑 완료")


async def verify(session: AsyncSession) -> bool:
    """마이그레이션 검증"""
    ok = True

    # ActionKit 수 비교
    old = (
        await session.execute(text("SELECT COUNT(*) FROM actionkit_files"))
    ).scalar()
    new = (
        await session.execute(
            text("SELECT COUNT(*) FROM files WHERE owner_type = 'actionkit_item'")
        )
    ).scalar()
    status = "OK" if old == new else "FAIL"
    print(f"  [{status}] ActionKit: {old} -> {new}")
    if old != new:
        ok = False

    # GrowthClub 수 비교
    old = (
        await session.execute(text("SELECT COUNT(*) FROM growthclubpostattachment"))
    ).scalar()
    new = (
        await session.execute(
            text("SELECT COUNT(*) FROM files WHERE owner_type = 'growth_club_post'")
        )
    ).scalar()
    status = "OK" if old == new else "FAIL"
    print(f"  [{status}] GrowthClub: {old} -> {new}")
    if old != new:
        ok = False

    # Profile 수 비교
    old = (
        await session.execute(
            text("""
        SELECT COUNT(*) FROM userprofile
        WHERE profile_img IS NOT NULL AND profile_img != '' AND profile_img != 'default.png'
    """)
        )
    ).scalar()
    new = (
        await session.execute(
            text("SELECT COUNT(*) FROM files WHERE owner_type = 'user_profile'")
        )
    ).scalar()
    status = "OK" if old == new else "FAIL"
    print(f"  [{status}] Profile: {old} -> {new}")
    if old != new:
        ok = False

    # FK 재매핑 검증
    orphan = (
        await session.execute(
            text("""
        SELECT COUNT(*) FROM roadmap_template_actions rta
        WHERE rta.actionkit_file_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM files WHERE id = rta.actionkit_file_id)
    """)
        )
    ).scalar()
    status = "OK" if orphan == 0 else "FAIL"
    print(f"  [{status}] FK orphan: {orphan}건")
    if orphan > 0:
        ok = False

    return ok


async def main():
    parser = argparse.ArgumentParser(description="파일 테이블 데이터 마이그레이션")
    parser.add_argument(
        "--dry-run", action="store_true", help="실행하지 않고 대상만 확인"
    )
    parser.add_argument(
        "--migrate-only",
        action="store_true",
        help="데이터 복사만 실행 (FK 재매핑 스킵)",
    )
    parser.add_argument(
        "--verify", action="store_true", help="마이그레이션 결과 검증"
    )
    args = parser.parse_args()

    engine = await get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        if args.verify:
            print("=== 마이그레이션 검증 ===")
            ok = await verify(session)
            result = "PASS" if ok else "FAIL"
            print(f"\n결과: {result}")
            return

        mode = "[dry-run] " if args.dry_run else ""
        print(f"=== {mode}데이터 마이그레이션 시작 ===")

        total = 0
        total += await migrate_actionkit_files(session, args.dry_run)
        total += await migrate_growth_club_attachments(session, args.dry_run)
        total += await migrate_profile_images(session, args.dry_run)

        print(f"\n총 {total}건 대상")

        if not args.dry_run:
            if not args.migrate_only:
                print("\n=== ID 매핑 + FK 재매핑 ===")
                await build_id_mapping(session, args.dry_run)
                await remap_fk(session, args.dry_run)
            else:
                print("\n[migrate-only] FK 재매핑 스킵")
            await session.commit()
            print("\n마이그레이션 완료!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
