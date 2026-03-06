from __future__ import annotations

import mimetypes
import re


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
