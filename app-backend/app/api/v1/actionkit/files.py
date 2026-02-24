from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_platform_admin
from app.api.v1.actionkit.schemas import ActionKitFileUploadResponse
from app.core.db import get_session
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
    item_id: int = Path(..., description="파일을 업로드할 액션키트 아이템 ID"),
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
