from fastapi import APIRouter, HTTPException
from app.api.v1.actionkit.schemas import LawChapter, ActionKitCategory
from app.features.actionkit.domain.data import LAW_DATA, ACTION_KIT_DATA

router = APIRouter()

@router.get("/laws/{chapter_id}", response_model=LawChapter)
async def get_law_chapter(chapter_id: str):
    """Get a specific law chapter."""
    chapter = LAW_DATA.get(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Law chapter not found")
    return chapter

@router.get("/kits/{category_id}", response_model=ActionKitCategory)
async def get_kit_category(category_id: str):
    """Get a specific action kit category."""
    category = ACTION_KIT_DATA.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Action kit category not found")
    return category
