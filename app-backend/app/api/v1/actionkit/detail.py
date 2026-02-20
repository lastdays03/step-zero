from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.db import get_session
from app.api.v1.actionkit.schemas import LawChapter, ActionKitCategory
from app.features.actionkit.application import ActionKitService
from app.repositories.actionkit_repository import ActionKitRepository

router = APIRouter()


def _service(session: AsyncSession) -> ActionKitService:
    return ActionKitService(ActionKitRepository(session))


@router.get("/laws/{chapter_id}", response_model=LawChapter)
async def get_law_chapter(
    chapter_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific law chapter."""
    chapter = await _service(session).get_law_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Law chapter not found")
    return chapter

@router.get("/kits/{category_id}", response_model=ActionKitCategory)
async def get_kit_category(
    category_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific action kit category."""
    category = await _service(session).get_kit_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Action kit category not found")
    return category
