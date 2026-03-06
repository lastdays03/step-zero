from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings

from .base import StorageBackend


@lru_cache(maxsize=1)
def get_storage_backend() -> StorageBackend:
    settings = get_settings()
    backend = getattr(settings, "STORAGE_BACKEND", "local")

    if backend == "r2":
        from .r2 import R2StorageBackend

        return R2StorageBackend()

    from .local import LocalStorageBackend

    return LocalStorageBackend()
