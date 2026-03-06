from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.core import db
from app.models.file import File
from app.models.user import User


async def _get_admin_token(client: AsyncClient) -> str:
    async with db.async_session() as session:
        user = (
            await session.execute(select(User).where(User.email == "test@example.com"))
        ).scalar_one()
        user.is_superuser = True
        user.is_active = True
        session.add(user)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _get_normal_token(client: AsyncClient) -> str:
    async with db.async_session() as session:
        user = (
            await session.execute(select(User).where(User.email == "test@example.com"))
        ).scalar_one()
        user.is_superuser = False
        user.is_active = True
        session.add(user)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _seed_files() -> list[int]:
    async with db.async_session() as session:
        files = [
            File(
                owner_type="actionkit_item",
                owner_id=1,
                category="document",
                object_key="ak/doc1.pdf",
                original_filename="invoice.pdf",
                mime_type="application/pdf",
                size_bytes=2_100_000,
            ),
            File(
                owner_type="growth_club_post",
                owner_id=2,
                category="image",
                object_key="gc/img1.jpg",
                original_filename="photo.jpg",
                mime_type="image/jpeg",
                size_bytes=340_000,
            ),
            File(
                owner_type="user_profile",
                owner_id=1,
                category="profile_image",
                object_key="pr/avatar.png",
                original_filename="avatar.png",
                mime_type="image/png",
                size_bytes=150_000,
            ),
        ]
        for f in files:
            session.add(f)
        await session.flush()
        ids = [f.id for f in files]
        await session.commit()
    return ids


async def _cleanup_files():
    async with db.async_session() as session:
        await session.execute(
            File.__table__.delete().where(
                File.object_key.in_(["ak/doc1.pdf", "gc/img1.jpg", "pr/avatar.png"])
            )
        )
        await session.commit()


@pytest.fixture(autouse=True)
async def cleanup():
    yield
    await _cleanup_files()


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_list_files(mock_storage, client: AsyncClient):
    mock_backend = AsyncMock()
    mock_backend.get_public_url = lambda key: f"https://cdn.test/{key}"
    mock_storage.return_value = mock_backend

    file_ids = await _seed_files()
    token = await _get_admin_token(client)

    response = await client.get(
        "/api/v1/ops/files/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert len(body["data"]) >= 3


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_list_files_filter_owner_type(mock_storage, client: AsyncClient):
    mock_backend = AsyncMock()
    mock_backend.get_public_url = lambda key: f"https://cdn.test/{key}"
    mock_storage.return_value = mock_backend

    await _seed_files()
    token = await _get_admin_token(client)

    response = await client.get(
        "/api/v1/ops/files/",
        params={"owner_type": "actionkit_item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    for item in body["data"]:
        assert item["owner_type"] == "actionkit_item"


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_list_files_filter_mime_group(mock_storage, client: AsyncClient):
    mock_backend = AsyncMock()
    mock_backend.get_public_url = lambda key: f"https://cdn.test/{key}"
    mock_storage.return_value = mock_backend

    await _seed_files()
    token = await _get_admin_token(client)

    response = await client.get(
        "/api/v1/ops/files/",
        params={"mime_group": "image"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    for item in body["data"]:
        assert item["mime_type"].startswith("image/")


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_list_files_search(mock_storage, client: AsyncClient):
    mock_backend = AsyncMock()
    mock_backend.get_public_url = lambda key: f"https://cdn.test/{key}"
    mock_storage.return_value = mock_backend

    await _seed_files()
    token = await _get_admin_token(client)

    response = await client.get(
        "/api/v1/ops/files/",
        params={"search": "invoice"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any("invoice" in item["original_filename"] for item in body["data"])


@pytest.mark.asyncio
async def test_get_stats(client: AsyncClient):
    await _seed_files()
    token = await _get_admin_token(client)

    response = await client.get(
        "/api/v1/ops/files/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_files"] >= 3
    assert body["total_bytes"] >= 2_590_000
    assert isinstance(body["by_owner_type"], list)
    assert isinstance(body["by_mime_group"], list)


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_delete_file(mock_storage, client: AsyncClient):
    mock_backend = AsyncMock()
    mock_backend.delete = AsyncMock(return_value=True)
    mock_storage.return_value = mock_backend

    file_ids = await _seed_files()
    token = await _get_admin_token(client)

    response = await client.delete(
        f"/api/v1/ops/files/{file_ids[0]}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True

    # Verify file is gone
    async with db.async_session() as session:
        file = (
            await session.execute(select(File).where(File.id == file_ids[0]))
        ).scalar_one_or_none()
        assert file is None


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_delete_file_not_found(mock_storage, client: AsyncClient):
    mock_backend = AsyncMock()
    mock_storage.return_value = mock_backend

    token = await _get_admin_token(client)

    response = await client.delete(
        "/api/v1/ops/files/999999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_batch_delete_files(mock_storage, client: AsyncClient):
    mock_backend = AsyncMock()
    mock_backend.delete = AsyncMock(return_value=True)
    mock_storage.return_value = mock_backend

    file_ids = await _seed_files()
    token = await _get_admin_token(client)

    response = await client.request(
        "DELETE",
        "/api/v1/ops/files/batch",
        json={"ids": file_ids[:2]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] == 2
    assert body["failed"] == 0


@pytest.mark.asyncio
@patch("app.features.ops.application.files.service.get_storage_backend")
async def test_batch_delete_partial_failure(mock_storage, client: AsyncClient):
    call_count = 0

    async def mock_delete(key):
        nonlocal call_count
        call_count += 1
        return call_count != 2  # Second call fails

    mock_backend = AsyncMock()
    mock_backend.delete = mock_delete
    mock_storage.return_value = mock_backend

    file_ids = await _seed_files()
    token = await _get_admin_token(client)

    response = await client.request(
        "DELETE",
        "/api/v1/ops/files/batch",
        json={"ids": file_ids},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] == 2
    assert body["failed"] == 1


@pytest.mark.asyncio
async def test_non_admin_forbidden(client: AsyncClient):
    token = await _get_normal_token(client)

    response = await client.get(
        "/api/v1/ops/files/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
