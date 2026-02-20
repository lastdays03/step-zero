from fastapi import APIRouter, Depends
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.actionkit.schemas import LawChapter, ActionKitCategory
from app.core.db import get_session
from app.features.actionkit.application import ActionKitService
from app.repositories.actionkit_repository import ActionKitRepository

router = APIRouter()


def _service(session: AsyncSession) -> ActionKitService:
    return ActionKitService(ActionKitRepository(session))


@router.get("/laws", response_model=Dict[str, LawChapter])
async def list_laws(
    session: AsyncSession = Depends(get_session),
):
    """List all law chapters."""
    return await _service(session).list_laws()

@router.get("/kits", response_model=Dict[str, ActionKitCategory])
async def list_kits(
    session: AsyncSession = Depends(get_session),
):
    """List all action kit categories."""
    return await _service(session).list_kits()
