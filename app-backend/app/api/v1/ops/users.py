from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.features.ops.application.users import OpsUserRead, list_users

router = APIRouter(prefix="/users")


@router.get(
    "",
    response_model=list[OpsUserRead],
    summary="운영 사용자 목록 조회",
    description="최근 생성된 사용자 목록(최대 50건)을 운영자 화면용으로 조회합니다.",
    response_description="운영 사용자 목록을 반환합니다.",
)
async def list_ops_users(
    offset: int = Query(default=0, ge=0, description="조회 시작 오프셋"),
    limit: int = Query(default=50, ge=1, le=200, description="조회 개수"),
    session: AsyncSession = Depends(get_session),
) -> list[OpsUserRead]:
    return await list_users(session, offset=offset, limit=limit)
