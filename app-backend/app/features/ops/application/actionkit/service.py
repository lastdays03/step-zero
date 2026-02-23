from typing import TypedDict, List
from fastapi import UploadFile
import os
import shutil
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.actionkit import ActionKitCategory, ActionKitItem, ActionKitFile, ActionKitRelatedLaw, ActionKitItemHighlight
from app.api.v1.ops.schemas import ActionKitItemCreateRequest, ActionKitItemUpdateRequest

class ActionKitOpsSummary(TypedDict):
    total_items: int
    pending_reviews: int


async def get_summary(session: AsyncSession) -> ActionKitOpsSummary:
    stmt = select(ActionKitItem)
    result = await session.execute(stmt)
    total = len(list(result.scalars().all()))
    return {"total_items": total, "pending_reviews": 0}

async def get_all_categories(session: AsyncSession) -> List[ActionKitCategory]:
    stmt = select(ActionKitCategory).order_by(ActionKitCategory.sort_order)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_items_by_category(session: AsyncSession, category_id: int) -> List[ActionKitItem]:
    stmt = select(ActionKitItem).where(ActionKitItem.category_id == category_id).options(
        selectinload(ActionKitItem.files),
        selectinload(ActionKitItem.highlights),
        selectinload(ActionKitItem.related_laws)
    ).order_by(ActionKitItem.sort_order)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_item_detail(session: AsyncSession, item_id: int) -> ActionKitItem | None:
    stmt = select(ActionKitItem).where(ActionKitItem.id == item_id).options(
        selectinload(ActionKitItem.files),
        selectinload(ActionKitItem.highlights),
        selectinload(ActionKitItem.related_laws)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_item(session: AsyncSession, data: ActionKitItemCreateRequest) -> ActionKitItem:
    item = ActionKitItem(**data.model_dump())
    session.add(item)
    await session.commit()
    return await get_item_detail(session, item.id)

async def update_item(session: AsyncSession, item_id: int, data: ActionKitItemUpdateRequest) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await session.commit()
    await session.refresh(item)
    return item

async def upload_file_for_item(session: AsyncSession, item_id: int, file: UploadFile) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None

    next_version = len(item.files) + 1 if item.files else 1
    upload_dir = "data/uploads/actionkit"
    os.makedirs(upload_dir, exist_ok=True)
    
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    for f in item.files:
        f.is_current = False

    new_file = ActionKitFile(
        item_id=item.id,
        version=next_version,
        object_key=file_path,
        original_filename=file.filename,
        mime_type=file.content_type,
        size_bytes=os.path.getsize(file_path),
        is_current=True
    )
    session.add(new_file)
    
    ext = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else None
    item.file_type = file.content_type
    item.ext = ext
    
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    item.size_label = f"{size_mb:.1f}MB" if size_mb >= 0.1 else f"{os.path.getsize(file_path) / 1024:.0f}KB"

    await session.commit()
    return await get_item_detail(session, item.id)

async def delete_item(session: AsyncSession, item_id: int) -> bool:
    item = await get_item_detail(session, item_id)
    if not item:
        return False
    await session.delete(item)
    await session.commit()
    return True
