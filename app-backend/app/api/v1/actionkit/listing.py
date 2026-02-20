from fastapi import APIRouter, Depends
from typing import Dict
from app.api.v1.actionkit.schemas import LawChapter, ActionKitCategory
from app.features.actionkit.domain.data import LAW_DATA, ACTION_KIT_DATA

router = APIRouter()

@router.get("/laws", response_model=Dict[str, LawChapter])
async def list_laws():
    """List all law chapters."""
    return LAW_DATA

@router.get("/kits", response_model=Dict[str, ActionKitCategory])
async def list_kits():
    """List all action kit categories."""
    return ACTION_KIT_DATA
