from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StorageResult:
    key: str
    size_bytes: int
    checksum: str
    content_type: str


class StorageBackend(ABC):
    @abstractmethod
    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> StorageResult: ...

    @abstractmethod
    async def get(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> bool: ...

    @abstractmethod
    def get_public_url(self, key: str) -> str: ...

    def create_presigned_put_url(
        self, key: str, content_type: str, expires_in: int = 3600
    ) -> str:
        raise NotImplementedError("Presigned URLs not supported by this backend")
