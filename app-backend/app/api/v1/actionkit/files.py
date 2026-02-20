from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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


@router.post("/items/{item_id}/files", response_model=ActionKitFileUploadResponse)
async def upload_actionkit_file(
    item_id: int,
    upload: UploadFile = File(...),
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

