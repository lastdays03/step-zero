from datetime import datetime

from app.core.security import utc_now
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api import deps
from app.api.v1.ops.schemas import (
    ActionKitCategoryCreateRequest,
    ActionKitCategoryResponse,
    ActionKitCategoryUpdateRequest,
    ActionKitItemCreateRequest,
    ActionKitItemReorderRequest,
    ActionKitItemResponse,
    ActionKitItemUpdateRequest,
)
from app.core.db import get_session
from app.features.ops.application.actionkit import (
    add_checklist,
    add_highlight,
    add_related_law,
    create_category,
    create_item,
    delete_category,
    delete_checklist,
    delete_highlight,
    delete_item,
    delete_related_law,
    get_all_categories,
    get_file_by_id,
    get_item_detail,
    get_items_by_category,
    get_summary,
    update_category,
    update_item,
    update_item_orders,
    upload_file_for_item,
)
from app.features.ops.application.audit_logs import (
    AuditAction,
    AuditTargetType,
    record_admin_audit_log,
)
from app.models.actionkit import ActionKitItem
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/actionkit", tags=["ops-actionkit"])


@router.get(
    "/summary",
    summary="액션키트 운영 요약 조회",
    description="액션키트 운영 화면에서 사용하는 기본 요약을 조회합니다.",
)
async def get_actionkit_summary(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    return await get_summary(session)


@router.get(
    "/categories",
    response_model=List[ActionKitCategoryResponse],
    summary="액션키트 카테고리 목록 조회",
)
async def get_categories(session: AsyncSession = Depends(get_session)):
    return await get_all_categories(session)


@router.post(
    "/categories",
    response_model=ActionKitCategoryResponse,
    summary="새로운 액션키트 카테고리 생성",
)
async def post_category(
    data: ActionKitCategoryCreateRequest, session: AsyncSession = Depends(get_session)
):
    return await create_category(session, data)


@router.patch(
    "/categories/{category_id}",
    response_model=ActionKitCategoryResponse,
    summary="액션키트 카테고리 정보 수정",
)
async def patch_category(
    category_id: int,
    data: ActionKitCategoryUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    category = await update_category(session, category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete(
    "/categories/{category_id}",
    summary="액션키트 카테고리 삭제",
)
async def remove_category(
    category_id: int, session: AsyncSession = Depends(get_session)
):
    success = await delete_category(session, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


@router.get(
    "/categories/{category_id}/items",
    response_model=List[ActionKitItemResponse],
    summary="카테고리별 액션키트 아이템 목록 조회",
)
async def get_category_items(
    category_id: int, session: AsyncSession = Depends(get_session)
):
    return await get_items_by_category(session, category_id)


@router.post(
    "/items",
    response_model=ActionKitItemResponse,
    summary="새로운 액션키트 아이템 생성",
)
async def create_actionkit_item(
    data: ActionKitItemCreateRequest, session: AsyncSession = Depends(get_session)
):
    return await create_item(session, data)


@router.patch(
    "/items/reorder",
    summary="액션키트 아이템 일괄 순서 변경",
)
async def patch_actionkit_item_orders(
    data: ActionKitItemReorderRequest, session: AsyncSession = Depends(get_session)
):
    await update_item_orders(session, data.model_dump()["items"])
    return {"message": "Success"}


@router.get(
    "/items/{item_id}",
    response_model=ActionKitItemResponse,
    summary="액션키트 아이템 상세 조회",
)
async def get_actionkit_item(
    item_id: int, session: AsyncSession = Depends(get_session)
):
    item = await get_item_detail(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch(
    "/items/{item_id}",
    response_model=ActionKitItemResponse,
    summary="액션키트 아이템 정보 수정",
)
async def patch_actionkit_item(
    item_id: int,
    data: ActionKitItemUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    item = await update_item(session, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


class OpsActionKitItemStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: str | None = None


@router.patch(
    "/items/{item_id}/status",
    summary="운영 액션키트 아이템 상태 변경",
    description="액션키트 아이템 활성/비활성 상태를 변경하고 감사로그를 남깁니다.",
    response_description="변경 결과를 반환합니다.",
)
async def update_actionkit_item_status(
    payload: OpsActionKitItemStatusUpdateRequest,
    item_id: int = Path(description="상태를 변경할 아이템 ID"),
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
) -> dict[str, object]:
    stmt = select(ActionKitItem).where(ActionKitItem.id == item_id)
    item = (await session.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="ActionKit item not found")

    before_is_active = bool(item.is_active)
    after_is_active = bool(payload.is_active)
    if before_is_active == after_is_active:
        return {
            "status": "no_change",
            "item_id": item.id,
            "is_active": before_is_active,
        }

    item.is_active = after_is_active
    item.updated_at = utc_now()
    session.add(item)

    await record_admin_audit_log(
        session,
        admin_id=admin_user.id,
        action=AuditAction.ACTIONKIT_ITEM_STATUS_UPDATED,
        target_type=AuditTargetType.ACTIONKIT_ITEM,
        target_id=str(item.id),
        reason=payload.reason,
        meta={
            "before": {"is_active": before_is_active},
            "after": {"is_active": after_is_active},
        },
    )
    await session.commit()

    return {"status": "success", "item_id": item.id, "is_active": item.is_active}


@router.post(
    "/items/{item_id}/files",
    response_model=ActionKitItemResponse,
    summary="액션키트 아이템 연관 파일 업로드",
)
async def upload_actionkit_item_file(
    item_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    item = await upload_file_for_item(session, item_id, file)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete(
    "/items/{item_id}",
    summary="액션키트 아이템 삭제",
)
async def delete_actionkit_item(
    item_id: int, session: AsyncSession = Depends(get_session)
):
    success = await delete_item(session, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}


@router.get(
    "/files/{file_id}/download",
    summary="액션키트 파일 다운로드",
)
async def download_actionkit_file(
    file_id: int, session: AsyncSession = Depends(get_session)
):
    file_record = await get_file_by_id(session, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    import os

    if not os.path.exists(file_record.object_key):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_record.object_key,
        filename=file_record.original_filename or "download",
        media_type=file_record.mime_type or "application/octet-stream",
    )


class RelatedLawRequest(PydanticBaseModel):
    law_name: str
    law_summary: str | None = None


class HighlightRequest(PydanticBaseModel):
    content: str


@router.post(
    "/items/{item_id}/related-laws",
    response_model=ActionKitItemResponse,
    summary="액션키트 관련 법령 추가",
)
async def add_actionkit_related_law(
    item_id: int, data: RelatedLawRequest, session: AsyncSession = Depends(get_session)
):
    item = await add_related_law(session, item_id, data.law_name, data.law_summary)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete(
    "/related-laws/{law_id}",
    summary="액션키트 관련 법령 삭제",
)
async def remove_actionkit_related_law(
    law_id: int, session: AsyncSession = Depends(get_session)
):
    success = await delete_related_law(session, law_id)
    if not success:
        raise HTTPException(status_code=404, detail="Law not found")
    return {"ok": True}


@router.post(
    "/items/{item_id}/highlights",
    response_model=ActionKitItemResponse,
    summary="액션키트 하이라이트 추가",
)
async def add_actionkit_highlight(
    item_id: int, data: HighlightRequest, session: AsyncSession = Depends(get_session)
):
    item = await add_highlight(session, item_id, data.content)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete(
    "/highlights/{highlight_id}",
    summary="액션키트 하이라이트 삭제",
)
async def remove_actionkit_highlight(
    highlight_id: int, session: AsyncSession = Depends(get_session)
):
    success = await delete_highlight(session, highlight_id)
    if not success:
        raise HTTPException(status_code=404, detail="Highlight not found")
    return {"ok": True}


class ChecklistRequest(PydanticBaseModel):
    content: str


@router.post(
    "/items/{item_id}/checklists",
    response_model=ActionKitItemResponse,
    summary="액션키트 체크리스트 추가",
)
async def add_actionkit_checklist(
    item_id: int, data: ChecklistRequest, session: AsyncSession = Depends(get_session)
):
    item = await add_checklist(session, item_id, data.content)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete(
    "/checklists/{checklist_id}",
    summary="액션키트 체크리스트 삭제",
)
async def remove_actionkit_checklist(
    checklist_id: int, session: AsyncSession = Depends(get_session)
):
    success = await delete_checklist(session, checklist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return {"ok": True}
