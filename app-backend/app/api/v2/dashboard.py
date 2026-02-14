from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v2.schemas import DashboardResponse
from app.application.dashboard_service import DashboardService
from app.core.db import get_session
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_repository import RoadmapRepository

router = APIRouter()


@router.get("", response_model=DashboardResponse)
async def get_dashboard_stats(
    current_user: AuthenticatedUser | None = Depends(deps.get_optional_current_user),
    session: AsyncSession = Depends(get_session),
    x_team_id: str | None = Header(default=None, alias="X-Team-Id"),
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
