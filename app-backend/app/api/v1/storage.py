from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AppValidationError
from app.models.user import AuthenticatedUser
from app.services.storage import get_storage_backend

router = APIRouter()

ALLOWED_KINDS = {"growth-club/image", "growth-club/file", "profile", "actionkit"}


class PresignRequest(BaseModel):
    filename: str
    content_type: str
    kind: str

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        if not re.match(r"^[\w\-]+/[\w\-\+\.]+(\;.+)?$", v):
            raise ValueError("Invalid MIME type format")
        return v


class PresignResponse(BaseModel):
    upload_url: str
    key: str
    public_url: str


def _build_key(kind: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1]
    now = datetime.now(timezone.utc)

    if kind == "growth-club/image":
        return f"growth-club/image/{now.year}/{now.month:02d}/{uuid4().hex}_image{ext}"
    elif kind == "growth-club/file":
        return f"growth-club/file/{now.year}/{now.month:02d}/{uuid4().hex}_file{ext}"
    elif kind == "actionkit":
        return f"actionkit/{uuid4().hex}{ext}"
    else:  # profile
        return f"profile/{uuid4()}{ext}"


@router.post(
    "/presign",
    response_model=PresignResponse,
    summary="Presigned URL 발급",
    description="R2 다이렉트 업로드용 presigned PUT URL을 생성합니다.",
)
async def create_presigned_url(
    body: PresignRequest,
    _: AuthenticatedUser = Depends(get_current_user),
):
    settings = get_settings()
    if settings.STORAGE_BACKEND != "r2":
        raise AppValidationError("Presigned URL은 R2 모드에서만 지원됩니다")

    if body.kind not in ALLOWED_KINDS:
        raise AppValidationError(
            f"Invalid kind: {body.kind}. Allowed: {sorted(ALLOWED_KINDS)}"
        )

    storage = get_storage_backend()
    key = _build_key(body.kind, body.filename)
    upload_url = storage.create_presigned_put_url(key, body.content_type)
    public_url = storage.get_public_url(key)

    return PresignResponse(upload_url=upload_url, key=key, public_url=public_url)
