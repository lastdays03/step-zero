from typing import TypedDict, List
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
    await session.refresh(item)
    return item

async def update_item(session: AsyncSession, item_id: int, data: ActionKitItemUpdateRequest) -> ActionKitItem | None:
    item = await get_item_detail(session, item_id)
    if not item:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await session.commit()
    await session.refresh(item)
    return item
