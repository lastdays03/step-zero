from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, TypedDict

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from app.api.v1.ops.schemas import (
        ActionKitCategoryCreateRequest,
        ActionKitCategoryUpdateRequest,
        ActionKitItemCreateRequest,
        ActionKitItemUpdateRequest,
    )

from app.models.actionkit import (
    ActionKitCategory,
    ActionKitChecklist,
    ActionKitFile,
    ActionKitItem,
    ActionKitItemHighlight,
    ActionKitRelatedLaw,
)
from app.repositories.file_repository import FileRepository


class ActionKitOpsSummary(TypedDict):
    total_items: int
    items_with_files: int
    inactive_items: int
    total_related_laws: int
    total_highlights: int


async def get_summary(session: AsyncSession) -> ActionKitOpsSummary:
    # Total items
    result = await session.execute(select(ActionKitItem))
    all_items = list(result.scalars().all())
    total = len(all_items)
    inactive = sum(1 for i in all_items if not i.is_active)

    # Items with at least one file
    file_stmt = select(ActionKitFile.item_id).distinct()
    file_result = await session.execute(file_stmt)
    items_with_files = len(list(file_result.scalars().all()))

    # Total related laws
    law_result = await session.execute(select(ActionKitRelatedLaw))
    total_laws = len(list(law_result.scalars().all()))

    # Total highlights
    hl_result = await session.execute(select(ActionKitItemHighlight))
    total_highlights = len(list(hl_result.scalars().all()))

    return {
        "total_items": total,
        "items_with_files": items_with_files,
        "inactive_items": inactive,
        "total_related_laws": total_laws,
        "total_highlights": total_highlights,
    }


async def get_all_categories(session: AsyncSession) -> List[ActionKitCategory]:
    stmt = select(ActionKitCategory).order_by(ActionKitCategory.sort_order)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_category(
    session: AsyncSession, data: ActionKitCategoryCreateRequest
) -> ActionKitCategory:
    category = ActionKitCategory(**data.model_dump())
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def get_category_detail(
    session: AsyncSession, category_id: int
) -> ActionKitCategory | None:
    stmt = select(ActionKitCategory).where(ActionKitCategory.id == category_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def update_category(
    session: AsyncSession, category_id: int, data: ActionKitCategoryUpdateRequest
) -> ActionKitCategory | None:
    category = await get_category_detail(session, category_id)
    if not category:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    category = await get_category_detail(session, category_id)
    if not category:
        return False
    await session.delete(category)
    await session.commit()
    return True


async def get_items_by_category(
    session: AsyncSession, category_id: int
) -> List[ActionKitItem]:
    stmt = (
        select(ActionKitItem)
        .where(ActionKitItem.category_id == category_id)
        .options(
            selectinload(ActionKitItem.files),
            selectinload(ActionKitItem.highlights),
            selectinload(ActionKitItem.related_laws),
            selectinload(ActionKitItem.checklists),
        )
        .order_by(ActionKitItem.sort_order)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_item_detail(session: AsyncSession, item_id: int) -> ActionKitItem | None:
    stmt = (
        select(ActionKitItem)
        .where(ActionKitItem.id == item_id)
        .options(
            selectinload(ActionKitItem.files),
            selectinload(ActionKitItem.highlights),
            selectinload(ActionKitItem.related_laws),
            selectinload(ActionKitItem.checklists),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_item(
    session: AsyncSession, data: ActionKitItemCreateRequest
) -> ActionKitItem:
    item = ActionKitItem(**data.model_dump())
    session.add(item)
    await session.commit()
    return await get_item_detail(session, item.id)


async def update_item(
    session: AsyncSession, item_id: int, data: ActionKitItemUpdateRequest
) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await session.commit()
    return await get_item_detail(session, item.id)


async def update_item_orders(session: AsyncSession, item_orders: List[dict]):
    for order_data in item_orders:
        item_id = order_data["id"]
        sort_order = order_data["sort_order"]
        stmt = select(ActionKitItem).where(ActionKitItem.id == item_id)
        result = await session.execute(stmt)
        item = result.scalars().first()
        if item:
            item.sort_order = sort_order
    await session.commit()
    return True


async def upload_file_for_item(
    session: AsyncSession, item_id: int, file: UploadFile
) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None

    from app.services.storage import get_storage_backend

    next_version = len(item.files) + 1 if item.files else 1

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    object_key = unique_name

    storage = get_storage_backend()
    data = await file.read()
    await storage.put(
        f"actionkit/{object_key}",
        data,
        content_type=file.content_type or "application/octet-stream",
    )
    size_bytes = len(data)

    for f in item.files:
        f.is_current = False

    new_file = ActionKitFile(
        item_id=item.id,
        version=next_version,
        object_key=object_key,
        original_filename=file.filename,
        mime_type=file.content_type,
        size_bytes=size_bytes,
        is_current=True,
    )
    session.add(new_file)

    ext = (
        file.filename.split(".")[-1].lower()
        if file.filename and "." in file.filename
        else None
    )
    item.file_type = file.content_type
    item.ext = ext

    size_mb = size_bytes / (1024 * 1024)
    item.size_label = (
        f"{size_mb:.1f}MB" if size_mb >= 0.1 else f"{size_bytes / 1024:.0f}KB"
    )

    await session.commit()
    return await get_item_detail(session, item.id)


async def delete_item(session: AsyncSession, item_id: int) -> bool:
    item = await get_item_detail(session, item_id)
    if not item:
        return False
    file_repo = FileRepository(session)
    await file_repo.delete_by_owner(
        owner_type="actionkit_item", owner_id=item_id
    )
    await session.delete(item)
    await session.commit()
    return True


async def get_file_by_id(session: AsyncSession, file_id: int) -> ActionKitFile | None:
    stmt = select(ActionKitFile).where(ActionKitFile.id == file_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_related_law(
    session: AsyncSession, item_id: int, law_name: str, law_summary: str | None = None
) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None
    next_order = len(item.related_laws) + 1 if item.related_laws else 1
    law = ActionKitRelatedLaw(
        item_id=item_id,
        law_name=law_name,
        law_summary=law_summary,
        sort_order=next_order,
    )
    session.add(law)
    await session.commit()
    return await get_item_detail(session, item_id)


async def delete_related_law(session: AsyncSession, law_id: int) -> bool:
    stmt = select(ActionKitRelatedLaw).where(ActionKitRelatedLaw.id == law_id)
    result = await session.execute(stmt)
    law = result.scalar_one_or_none()
    if not law:
        return False
    await session.delete(law)
    await session.commit()
    return True


async def add_highlight(
    session: AsyncSession, item_id: int, content: str
) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None
    next_order = len(item.highlights) + 1 if item.highlights else 1
    hl = ActionKitItemHighlight(item_id=item_id, content=content, sort_order=next_order)
    session.add(hl)
    await session.commit()
    return await get_item_detail(session, item_id)


async def delete_highlight(session: AsyncSession, highlight_id: int) -> bool:
    stmt = select(ActionKitItemHighlight).where(
        ActionKitItemHighlight.id == highlight_id
    )
    result = await session.execute(stmt)
    hl = result.scalar_one_or_none()
    if not hl:
        return False
    await session.delete(hl)
    await session.commit()
    return True


async def add_checklist(
    session: AsyncSession, item_id: int, content: str
) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None
    next_order = len(item.checklists) + 1 if item.checklists else 1
    cl = ActionKitChecklist(item_id=item_id, content=content, sort_order=next_order)
    session.add(cl)
    await session.commit()
    return await get_item_detail(session, item_id)


async def delete_checklist(session: AsyncSession, checklist_id: int) -> bool:
    stmt = select(ActionKitChecklist).where(ActionKitChecklist.id == checklist_id)
    result = await session.execute(stmt)
    cl = result.scalar_one_or_none()
    if not cl:
        return False
    await session.delete(cl)
    await session.commit()
    return True
