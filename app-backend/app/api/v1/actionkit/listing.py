from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.actionkit.schemas import ActionKitCategory, LawChapter
from app.core.db import get_session
from app.features.actionkit.application import ActionKitService
from app.repositories.actionkit_repository import ActionKitRepository

router = APIRouter()


def _service(session: AsyncSession) -> ActionKitService:
    return ActionKitService(ActionKitRepository(session))


@router.get(
    "/laws",
    response_model=Dict[str, LawChapter],
    summary="법령 챕터 목록 조회",
    description="액션키트에서 사용하는 법령 챕터 전체 목록을 조회합니다.",
    response_description="법령 챕터 맵을 반환합니다.",
)
async def list_laws(
    session: AsyncSession = Depends(get_session),
):
    """List all law chapters."""
    return await _service(session).list_laws()


@router.get(
    "/kits",
    response_model=Dict[str, ActionKitCategory],
    summary="액션키트 카테고리 목록 조회",
    description="액션키트 카테고리와 각 아이템 목록을 조회합니다.",
    response_description="카테고리 맵을 반환합니다.",
)
async def list_kits(
    session: AsyncSession = Depends(get_session),
):
    """List all action kit categories."""
    return await _service(session).list_kits()
