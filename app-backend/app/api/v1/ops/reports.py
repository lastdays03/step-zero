from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.features.ops.application.reports import OpsReportsService

router = APIRouter(prefix="/reports")


@router.get(
    "/summary",
    summary="운영 리포트 요약 조회",
    description="운영 콘솔 카드에서 사용하는 핵심 지표 요약을 조회합니다.",
    response_description="선택 기간 기준 운영 지표 요약을 반환합니다.",
)
async def get_ops_summary(
    range: str = Query("7d", pattern="^(7d|30d)$"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    range_days = 7 if range == "7d" else 30
    service = OpsReportsService(session)
    return await service.get_summary(range_days)
