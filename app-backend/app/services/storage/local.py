from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import get_settings

from .base import StorageBackend, StorageResult


class LocalStorageBackend(StorageBackend):
    def __init__(self) -> None:
        settings = get_settings()
        self._root = settings.STORAGE_ROOT_PATH
        self._root.mkdir(parents=True, exist_ok=True)

    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> StorageResult:
        dest = self._root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        return StorageResult(
            key=key,
            size_bytes=len(data),
            checksum=checksum,
            content_type=content_type,
        )

    async def get(self, key: str) -> bytes:
        path = self._root / key
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> bool:
        path = self._root / key
        if path.exists():
            path.unlink()
            return True
        return False

    def get_public_url(self, key: str) -> str:
        return f"/api/uploads/{key}"

    def get_local_path(self, key: str) -> Path:
        return self._root / key
