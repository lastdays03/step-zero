from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.storage.base import StorageResult


# ---------------------------------------------------------------------------
# Local backend tests
# ---------------------------------------------------------------------------


@pytest.fixture
def local_backend(tmp_path, monkeypatch):
    """Create a LocalStorageBackend with a temporary root directory."""
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite://")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt-signing-0123456789")

    # Clear cached settings and backend
    from app.core.config import get_settings
    from app.services.storage.factory import get_storage_backend

    get_settings.cache_clear()
    get_storage_backend.cache_clear()

    from app.services.storage.local import LocalStorageBackend

    backend = LocalStorageBackend()
    yield backend

    get_settings.cache_clear()
    get_storage_backend.cache_clear()


async def test_local_put_get_delete(local_backend):
    data = b"hello world"
    result = await local_backend.put("test/hello.txt", data, "text/plain")

    assert isinstance(result, StorageResult)
    assert result.key == "test/hello.txt"
    assert result.size_bytes == len(data)
    assert result.content_type == "text/plain"
    assert len(result.checksum) == 64  # sha256 hex

    fetched = await local_backend.get("test/hello.txt")
    assert fetched == data

    deleted = await local_backend.delete("test/hello.txt")
    assert deleted is True

    deleted_again = await local_backend.delete("test/hello.txt")
    assert deleted_again is False


async def test_local_get_nonexistent(local_backend):
    with pytest.raises(FileNotFoundError):
        await local_backend.get("nonexistent/file.txt")


async def test_local_public_url(local_backend):
    url = local_backend.get_public_url("profile/avatar.png")
    assert url == "/api/uploads/profile/avatar.png"


# ---------------------------------------------------------------------------
# R2 backend tests (mocked)
# ---------------------------------------------------------------------------


def _make_r2_backend():
    """Create an R2StorageBackend with mocked settings and boto3 client."""
    from app.services.storage.r2 import R2StorageBackend

    with patch("app.services.storage.r2.get_settings") as mock_settings, patch(
        "app.services.storage.r2.boto3"
    ) as mock_boto3:
        settings = MagicMock()
        settings.R2_ACCOUNT_ID = "test-account-id"
        settings.R2_ACCESS_KEY_ID = "test-access-key"
        settings.R2_SECRET_ACCESS_KEY = "test-secret-key"
        settings.R2_BUCKET_NAME = "test-bucket"
        settings.R2_PUBLIC_URL = "https://cdn.example.com"
        mock_settings.return_value = settings

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        backend = R2StorageBackend()
        return backend, mock_client


async def test_r2_put():
    backend, mock_client = _make_r2_backend()
    data = b"test data for r2"

    result = await backend.put("uploads/test.txt", data, "text/plain")

    assert isinstance(result, StorageResult)
    assert result.key == "uploads/test.txt"
    assert result.size_bytes == len(data)
    assert result.content_type == "text/plain"
    mock_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="uploads/test.txt",
        Body=data,
        ContentType="text/plain",
    )


async def test_r2_get():
    backend, mock_client = _make_r2_backend()
    body_mock = MagicMock()
    body_mock.read.return_value = b"file content from r2"
    mock_client.get_object.return_value = {"Body": body_mock}

    content = await backend.get("uploads/test.txt")

    assert content == b"file content from r2"
    mock_client.get_object.assert_called_once_with(
        Bucket="test-bucket", Key="uploads/test.txt"
    )


async def test_r2_delete():
    backend, mock_client = _make_r2_backend()

    result = await backend.delete("uploads/test.txt")

    assert result is True
    mock_client.delete_object.assert_called_once_with(
        Bucket="test-bucket", Key="uploads/test.txt"
    )


async def test_r2_public_url():
    backend, _ = _make_r2_backend()

    url = backend.get_public_url("profile/avatar.png")
    assert url == "https://cdn.example.com/profile/avatar.png"


async def test_r2_presigned_url():
    backend, mock_client = _make_r2_backend()
    mock_client.generate_presigned_url.return_value = "https://presigned.example.com/upload"

    url = backend.create_presigned_put_url("uploads/file.pdf", "application/pdf", 600)

    assert url == "https://presigned.example.com/upload"
    mock_client.generate_presigned_url.assert_called_once_with(
        "put_object",
        Params={
            "Bucket": "test-bucket",
            "Key": "uploads/file.pdf",
            "ContentType": "application/pdf",
        },
        ExpiresIn=600,
    )


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


async def test_factory_local(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite://")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt-signing-0123456789")

    from app.core.config import get_settings
    from app.services.storage.factory import get_storage_backend
    from app.services.storage.local import LocalStorageBackend

    get_settings.cache_clear()
    get_storage_backend.cache_clear()

    try:
        backend = get_storage_backend()
        assert isinstance(backend, LocalStorageBackend)
    finally:
        get_settings.cache_clear()
        get_storage_backend.cache_clear()


async def test_factory_r2(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "r2")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite://")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt-signing-0123456789")
    monkeypatch.setenv("R2_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("R2_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("R2_PUBLIC_URL", "https://cdn.example.com")

    from app.core.config import get_settings
    from app.services.storage.factory import get_storage_backend
    from app.services.storage.r2 import R2StorageBackend

    get_settings.cache_clear()
    get_storage_backend.cache_clear()

    try:
        with patch("app.services.storage.r2.boto3"):
            backend = get_storage_backend()
            assert isinstance(backend, R2StorageBackend)
    finally:
        get_settings.cache_clear()
        get_storage_backend.cache_clear()
