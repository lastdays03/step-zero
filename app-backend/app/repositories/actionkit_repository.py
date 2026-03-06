from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.actionkit import (
    ActionKitCategory,
    ActionKitChecklist,
    ActionKitItem,
    ActionKitItemHighlight,
    ActionKitRelatedLaw,
)


class ActionKitRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_categories(self, *, domain: str) -> list[ActionKitCategory]:
        stmt = (
            select(ActionKitCategory)
            .where(
                ActionKitCategory.domain == domain,
                ActionKitCategory.is_active.is_(True),
            )
            .order_by(ActionKitCategory.sort_order.asc(), ActionKitCategory.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_category(self, *, domain: str, slug: str) -> ActionKitCategory | None:
        stmt = select(ActionKitCategory).where(
            ActionKitCategory.domain == domain,
            ActionKitCategory.slug == slug,
            ActionKitCategory.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_items_for_categories(
        self, *, domain: str, category_ids: list[int]
    ) -> list[ActionKitItem]:
        if not category_ids:
            return []
        stmt = (
            select(ActionKitItem)
            .where(
                ActionKitItem.domain == domain,
                ActionKitItem.category_id.in_(category_ids),
                ActionKitItem.is_active.is_(True),
            )
            .order_by(ActionKitItem.sort_order.asc(), ActionKitItem.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_item_highlights(
        self, *, item_ids: list[int]
    ) -> list[ActionKitItemHighlight]:
        if not item_ids:
            return []
        stmt = (
            select(ActionKitItemHighlight)
            .where(ActionKitItemHighlight.item_id.in_(item_ids))
            .order_by(
                ActionKitItemHighlight.sort_order.asc(), ActionKitItemHighlight.id.asc()
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_checklists(self, *, item_ids: list[int]) -> list[ActionKitChecklist]:
        if not item_ids:
            return []
        stmt = (
            select(ActionKitChecklist)
            .where(ActionKitChecklist.item_id.in_(item_ids))
            .order_by(ActionKitChecklist.sort_order.asc(), ActionKitChecklist.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_related_laws(
        self, *, item_ids: list[int]
    ) -> list[ActionKitRelatedLaw]:
        if not item_ids:
            return []
        stmt = (
            select(ActionKitRelatedLaw)
            .where(ActionKitRelatedLaw.item_id.in_(item_ids))
            .order_by(
                ActionKitRelatedLaw.sort_order.asc(), ActionKitRelatedLaw.id.asc()
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_item_with_category(
        self, *, item_id: int
    ) -> tuple[ActionKitItem, ActionKitCategory] | None:
        stmt = (
            select(ActionKitItem, ActionKitCategory)
            .join(ActionKitCategory, ActionKitCategory.id == ActionKitItem.category_id)
            .where(ActionKitItem.id == item_id, ActionKitItem.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None
        return row[0], row[1]

    async def commit(self) -> None:
        await self.session.commit()
