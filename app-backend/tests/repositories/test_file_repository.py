"""FileRepository CRUD 테스트."""

import pytest

from app.core import db
from app.models.file import File
from app.repositories.file_repository import FileRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OWNER_TYPE_AK = "actionkit_item"
OWNER_TYPE_GC = "growth_club_post"
OWNER_TYPE_PROFILE = "user_profile"


def _make_file(
    owner_type: str = OWNER_TYPE_AK,
    owner_id: int = 1,
    object_key: str = "test/key.pdf",
    **kwargs,
) -> File:
    defaults = dict(
        owner_type=owner_type,
        owner_id=owner_id,
        object_key=object_key,
        original_filename="file.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
        category="document",
    )
    defaults.update(kwargs)
    return File(**defaults)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_file():
    """File 레코드를 생성하고 ID가 할당된다."""
    async with db.async_session() as session:
        repo = FileRepository(session)
        file = _make_file(object_key="create/test-1.pdf")
        created = await repo.create(file=file)
        await session.commit()

    assert created.id is not None
    assert created.object_key == "create/test-1.pdf"
    assert created.original_filename == "file.pdf"
    assert created.size_bytes == 1024


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_found():
    """ID로 File을 조회한다."""
    async with db.async_session() as session:
        repo = FileRepository(session)
        file = _make_file(object_key="getbyid/found.pdf")
        created = await repo.create(file=file)
        await session.commit()

    async with db.async_session() as session:
        repo = FileRepository(session)
        found = await repo.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.object_key == "getbyid/found.pdf"


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """존재하지 않는 ID로 조회 시 None을 반환한다."""
    async with db.async_session() as session:
        repo = FileRepository(session)
        result = await repo.get_by_id(999999)

    assert result is None


# ---------------------------------------------------------------------------
# get_by_key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_key_found():
    """object_key로 File을 조회한다."""
    key = "getbykey/unique-key.pdf"
    async with db.async_session() as session:
        repo = FileRepository(session)
        await repo.create(file=_make_file(object_key=key))
        await session.commit()

    async with db.async_session() as session:
        repo = FileRepository(session)
        found = await repo.get_by_key(key)

    assert found is not None
    assert found.object_key == key


@pytest.mark.asyncio
async def test_get_by_key_not_found():
    """존재하지 않는 key로 조회 시 None을 반환한다."""
    async with db.async_session() as session:
        repo = FileRepository(session)
        result = await repo.get_by_key("nonexistent/key.pdf")

    assert result is None


# ---------------------------------------------------------------------------
# get_by_owner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_owner():
    """owner_type + owner_id로 파일 목록을 조회한다."""
    owner_id = 9001
    async with db.async_session() as session:
        repo = FileRepository(session)
        await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_GC,
                owner_id=owner_id,
                object_key="getbyowner/a.jpg",
                kind="image",
            )
        )
        await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_GC,
                owner_id=owner_id,
                object_key="getbyowner/b.pdf",
                kind="file",
            )
        )
        # 다른 owner의 파일 — 결과에 포함되지 않아야 함
        await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_GC,
                owner_id=owner_id + 1,
                object_key="getbyowner/other.pdf",
            )
        )
        await session.commit()

    async with db.async_session() as session:
        repo = FileRepository(session)
        files = await repo.get_by_owner(
            owner_type=OWNER_TYPE_GC, owner_id=owner_id
        )

    assert len(files) == 2
    assert all(f.owner_id == owner_id for f in files)


# ---------------------------------------------------------------------------
# delete_by_owner (Cascade Delete 대체)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_by_owner():
    """소유자의 모든 파일을 삭제하고 삭제된 수를 반환한다."""
    owner_id = 9010
    async with db.async_session() as session:
        repo = FileRepository(session)
        for i in range(3):
            await repo.create(
                file=_make_file(
                    owner_type=OWNER_TYPE_GC,
                    owner_id=owner_id,
                    object_key=f"delowner/{owner_id}-{i}.pdf",
                )
            )
        await session.commit()

    async with db.async_session() as session:
        repo = FileRepository(session)
        deleted_count = await repo.delete_by_owner(
            owner_type=OWNER_TYPE_GC, owner_id=owner_id
        )
        await session.commit()

    assert deleted_count == 3

    # 삭제 후 조회 시 빈 리스트
    async with db.async_session() as session:
        repo = FileRepository(session)
        remaining = await repo.get_by_owner(
            owner_type=OWNER_TYPE_GC, owner_id=owner_id
        )

    assert remaining == []


# ---------------------------------------------------------------------------
# ActionKit용: get_current_files
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_files():
    """is_current=True인 파일만 조회한다."""
    owner_id = 9020
    async with db.async_session() as session:
        repo = FileRepository(session)
        # v1 (not current)
        await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_AK,
                owner_id=owner_id,
                object_key=f"current/{owner_id}-v1.pdf",
                version=1,
                is_current=False,
            )
        )
        # v2 (current)
        await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_AK,
                owner_id=owner_id,
                object_key=f"current/{owner_id}-v2.pdf",
                version=2,
                is_current=True,
            )
        )
        await session.commit()

    async with db.async_session() as session:
        repo = FileRepository(session)
        current = await repo.get_current_files(
            owner_type=OWNER_TYPE_AK, owner_ids=[owner_id]
        )

    assert len(current) == 1
    assert current[0].version == 2
    assert current[0].is_current is True


@pytest.mark.asyncio
async def test_get_current_files_empty_ids():
    """빈 owner_ids 리스트로 호출 시 빈 리스트를 반환한다."""
    async with db.async_session() as session:
        repo = FileRepository(session)
        result = await repo.get_current_files(
            owner_type=OWNER_TYPE_AK, owner_ids=[]
        )

    assert result == []


# ---------------------------------------------------------------------------
# ActionKit용: set_current
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_current():
    """set_current 호출 시 지정 파일만 is_current=True가 된다."""
    owner_id = 9030
    async with db.async_session() as session:
        repo = FileRepository(session)
        f1 = await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_AK,
                owner_id=owner_id,
                object_key=f"setcurrent/{owner_id}-v1.pdf",
                version=1,
                is_current=True,
            )
        )
        f2 = await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_AK,
                owner_id=owner_id,
                object_key=f"setcurrent/{owner_id}-v2.pdf",
                version=2,
                is_current=False,
            )
        )
        await session.commit()
        f1_id, f2_id = f1.id, f2.id

    # set f2 as current
    async with db.async_session() as session:
        repo = FileRepository(session)
        await repo.set_current(
            owner_type=OWNER_TYPE_AK, owner_id=owner_id, file_id=f2_id
        )
        await session.commit()

    # verify
    async with db.async_session() as session:
        repo = FileRepository(session)
        old = await repo.get_by_id(f1_id)
        new = await repo.get_by_id(f2_id)

    assert old.is_current is not True  # False or None
    assert new.is_current is True


# ---------------------------------------------------------------------------
# ActionKit용: get_next_version
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_next_version_first():
    """파일이 없으면 다음 버전은 1이다."""
    owner_id = 9040
    async with db.async_session() as session:
        repo = FileRepository(session)
        version = await repo.get_next_version(
            owner_type=OWNER_TYPE_AK, owner_id=owner_id
        )

    assert version == 1


@pytest.mark.asyncio
async def test_get_next_version_increments():
    """기존 최대 버전 + 1을 반환한다."""
    owner_id = 9050
    async with db.async_session() as session:
        repo = FileRepository(session)
        await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_AK,
                owner_id=owner_id,
                object_key=f"nextver/{owner_id}-v1.pdf",
                version=1,
            )
        )
        await repo.create(
            file=_make_file(
                owner_type=OWNER_TYPE_AK,
                owner_id=owner_id,
                object_key=f"nextver/{owner_id}-v3.pdf",
                version=3,
            )
        )
        await session.commit()

    async with db.async_session() as session:
        repo = FileRepository(session)
        version = await repo.get_next_version(
            owner_type=OWNER_TYPE_AK, owner_id=owner_id
        )

    assert version == 4
