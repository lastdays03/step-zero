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
    get_file_by_id
)
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
