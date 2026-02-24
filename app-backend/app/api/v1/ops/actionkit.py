from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.features.ops.application.actionkit import (
    get_summary,
    get_all_categories,
    get_items_by_category,
    get_item_detail,
    update_item,
    create_item,
    upload_file_for_item,
    delete_item,
    get_file_by_id,
    add_related_law,
    delete_related_law,
    add_highlight,
    delete_highlight
)
from pydantic import BaseModel as PydanticBaseModel
from app.api.v1.ops.schemas import (
    ActionKitCategoryResponse,
    ActionKitItemResponse,
    ActionKitItemCreateRequest,
    ActionKitItemUpdateRequest
)
from app.core.db import get_session

router = APIRouter(prefix="/actionkit", tags=["ops-actionkit"])


@router.get(
    "/summary",
    summary="액션키트 운영 요약 조회",
    description="액션키트 운영 화면에서 사용하는 기본 요약을 조회합니다.",
)
async def get_actionkit_summary(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    return await get_summary(session)


@router.get(
    "/categories",
    response_model=List[ActionKitCategoryResponse],
    summary="액션키트 카테고리 목록 조회",
)
async def get_categories(session: AsyncSession = Depends(get_session)):
    return await get_all_categories(session)


@router.get(
    "/categories/{category_id}/items",
    response_model=List[ActionKitItemResponse],
    summary="카테고리별 액션키트 아이템 목록 조회",
)
async def get_category_items(category_id: int, session: AsyncSession = Depends(get_session)):
    return await get_items_by_category(session, category_id)


@router.post(
    "/items",
    response_model=ActionKitItemResponse,
    summary="새로운 액션키트 아이템 생성",
)
async def create_actionkit_item(
    data: ActionKitItemCreateRequest, 
    session: AsyncSession = Depends(get_session)
):
    return await create_item(session, data)


@router.get(
    "/items/{item_id}",
    response_model=ActionKitItemResponse,
    summary="액션키트 아이템 상세 조회",
)
async def get_actionkit_item(item_id: int, session: AsyncSession = Depends(get_session)):
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
    session: AsyncSession = Depends(get_session)
):
    item = await update_item(session, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post(
    "/items/{item_id}/files",
    response_model=ActionKitItemResponse,
    summary="액션키트 아이템 연관 파일 업로드",
)
async def upload_actionkit_item_file(
    item_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
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
    item_id: int,
    session: AsyncSession = Depends(get_session)
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
    file_id: int,
    session: AsyncSession = Depends(get_session)
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
        media_type=file_record.mime_type or "application/octet-stream"
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
    item_id: int,
    data: RelatedLawRequest,
    session: AsyncSession = Depends(get_session)
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
    law_id: int,
    session: AsyncSession = Depends(get_session)
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
    item_id: int,
    data: HighlightRequest,
    session: AsyncSession = Depends(get_session)
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
    highlight_id: int,
    session: AsyncSession = Depends(get_session)
):
    success = await delete_highlight(session, highlight_id)
    if not success:
        raise HTTPException(status_code=404, detail="Highlight not found")
    return {"ok": True}
