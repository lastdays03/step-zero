from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.schemas import DashboardResponse
from app.core.db import get_session
from app.features.dashboard.application.dashboard_service import DashboardService
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_repository import RoadmapRepository

router = APIRouter()


@router.get(
    "",
    response_model=DashboardResponse,
    summary="대시보드 지표 조회",
    description="현재 사용자(또는 게스트) 기준 대시보드 요약 지표를 조회합니다.",
    response_description="대시보드 카드/진행률 데이터를 반환합니다.",
)
async def get_dashboard_stats(
    current_user: AuthenticatedUser | None = Depends(deps.get_optional_current_user),
    session: AsyncSession = Depends(get_session),
    x_team_id: str | None = Header(
        default=None,
        alias="X-Team-Id",
        description="조회 대상 팀 ID. 생략 시 현재 사용자 기본 팀을 사용합니다.",
    ),
) -> Any:
    service = DashboardService(roadmap_repo=RoadmapRepository(session))
    if not current_user:
        result = await service.get_dashboard(
            team_id=UUID("00000000-0000-0000-0000-000000000000"),
            user_name="Guest",
            is_guest=True,
        )
        return result.__dict__

    current_team = await deps.get_current_team(
        current_user=current_user,
        session=session,
        x_team_id=x_team_id,
    )
    result = await service.get_dashboard(
        team_id=current_team.id,
        user_name=current_user.full_name or current_user.email.split("@")[0],
        is_guest=False,
    )
    return result.__dict__
