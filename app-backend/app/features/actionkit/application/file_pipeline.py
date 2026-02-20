from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path

from fastapi import UploadFile


def normalize_filename(filename: str) -> str:
    cleaned = filename.strip().replace(" ", "_")
    cleaned = re.sub(r"[^A-Za-z0-9._\-가-힣]", "", cleaned)
    return cleaned or "file.bin"


def build_object_key(
    *,
    domain: str,
    category_slug: str,
    item_id: int,
    version: int,
    filename: str,
) -> str:
    normalized_filename = normalize_filename(filename)
    return f"{domain}/{category_slug}/{item_id}/v{version}/{normalized_filename}"


def detect_mime_type(filename: str, fallback: str | None = None) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or fallback or "application/octet-stream"


def file_checksum(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


async def save_upload_to_path(upload_file: UploadFile, *, destination: Path) -> tuple[int, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = await upload_file.read()
    destination.write_bytes(data)
    checksum = file_checksum(destination)
    return len(data), checksum

