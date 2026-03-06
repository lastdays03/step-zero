from __future__ import annotations

import asyncio
import hashlib

import boto3

from app.core.config import get_settings

from .base import StorageBackend, StorageResult


class R2StorageBackend(StorageBackend):
    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.R2_BUCKET_NAME
        self._public_url = (settings.R2_PUBLIC_URL or "").rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )

    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> StorageResult:
        checksum = hashlib.sha256(data).hexdigest()

        def _upload() -> None:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        await asyncio.to_thread(_upload)
        return StorageResult(
            key=key,
            size_bytes=len(data),
            checksum=checksum,
            content_type=content_type,
        )

    async def get(self, key: str) -> bytes:
        def _download() -> bytes:
            resp = self._client.get_object(Bucket=self._bucket, Key=key)
            return resp["Body"].read()

        return await asyncio.to_thread(_download)

    async def delete(self, key: str) -> bool:
        def _delete() -> bool:
            self._client.delete_object(Bucket=self._bucket, Key=key)
            return True

        return await asyncio.to_thread(_delete)

    def get_public_url(self, key: str) -> str:
        return f"{self._public_url}/{key}"

    def create_presigned_put_url(
        self, key: str, content_type: str, expires_in: int = 3600
    ) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
