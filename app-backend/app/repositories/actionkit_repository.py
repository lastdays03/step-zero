import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.actionkit import (
    ActionKitCategory,
    ActionKitChecklist,
    ActionKitFile,
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

    async def list_current_files(self, *, item_ids: list[int]) -> list[ActionKitFile]:
        if not item_ids:
            return []
        stmt = (
            select(ActionKitFile)
            .where(
                ActionKitFile.item_id.in_(item_ids),
                ActionKitFile.is_current.is_(True),
            )
            .order_by(ActionKitFile.version.desc(), ActionKitFile.id.desc())
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

    async def get_next_file_version(self, *, item_id: int) -> int:
        stmt = select(sa.func.max(ActionKitFile.version)).where(
            ActionKitFile.item_id == item_id
        )
        result = await self.session.execute(stmt)
        max_version = result.scalar_one_or_none() or 0
        return int(max_version) + 1

    async def clear_current_file_flags(self, *, item_id: int) -> None:
        stmt = (
            sa.update(ActionKitFile)
            .where(ActionKitFile.item_id == item_id, ActionKitFile.is_current.is_(True))
            .values(is_current=False)
        )
        await self.session.execute(stmt)

    async def create_file_record(
        self,
        *,
        item_id: int,
        version: int,
        object_key: str,
        original_filename: str | None,
        mime_type: str | None,
        size_bytes: int | None,
        checksum: str | None,
    ) -> ActionKitFile:
        record = ActionKitFile(
            item_id=item_id,
            version=version,
            object_key=object_key,
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum=checksum,
            is_current=True,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def commit(self) -> None:
        await self.session.commit()
