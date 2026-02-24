from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.api.deps import require_platform_admin
from app.api.v1.actionkit.schemas import ActionKitFileUploadResponse
from app.core.db import get_session
from app.core.config import get_settings
from app.features.actionkit.application import ActionKitService
from app.models.user import AuthenticatedUser
from app.repositories.actionkit_repository import ActionKitRepository

router = APIRouter()


def _service(session: AsyncSession) -> ActionKitService:
    return ActionKitService(ActionKitRepository(session))


@router.post(
    "/items/{item_id}/files",
    response_model=ActionKitFileUploadResponse,
    summary="액션키트 파일 업로드",
    description="운영자가 액션키트 아이템에 파일을 업로드합니다.",
    response_description="업로드된 파일의 메타데이터를 반환합니다.",
)
async def upload_actionkit_file(
    item_id: int = Path(description="파일을 업로드할 액션키트 아이템 ID"),
    upload: UploadFile = File(..., description="업로드할 원본 파일"),
    _: AuthenticatedUser = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_session),
):
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        payload = await _service(session).upload_item_file(
            item_id=item_id,
            upload_file=upload,
        )
        return ActionKitFileUploadResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/items/{item_id}/download",
    summary="액션키트 아이템 최신 파일 다운로드",
    description="해당 아이템의 최신 버전 파일을 다운로드합니다.",
)
async def download_item_current_file(
    item_id: int = Path(description="다운로드할 아이템 ID"),
    session: AsyncSession = Depends(get_session),
):
    repo = ActionKitRepository(session)
    files = await repo.list_current_files(item_ids=[item_id])
    if not files:
        raise HTTPException(status_code=404, detail="No file found for this item")

    current_file = files[0]
    settings = get_settings()
    file_path = os.path.join(settings.ACTIONKIT_STORAGE_PATH, current_file.object_key)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=current_file.original_filename or "download",
        media_type=current_file.mime_type or "application/octet-stream",
    )

