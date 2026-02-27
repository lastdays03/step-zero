from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.features.actionkit.models import ActionKitItem, ActionKitCategory

async def get_all_items(session: AsyncSession) -> List[ActionKitItem]:
    """Retrieve all action kit items"""
    stmt = select(ActionKitItem)
    result = await session.execute(stmt)
    return list(result.scalars().all())

