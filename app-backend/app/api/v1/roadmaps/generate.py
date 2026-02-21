from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.db import get_session
from app.features.roadmaps.application.roadmap_service import RoadmapService
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_repository import RoadmapRepository

router = APIRouter()


class GenerationRequest(BaseModel):
    business_type: str
    location: str
    description: str = ""
    startup_type: str | None = None
    open_timeline: str | None = None
    budget_range: str | None = None
    additional_notes: str = ""


class RoadmapStepResponse(BaseModel):
    id: int
    title: str
    status: str


class GenerationResponse(BaseModel):
    roadmap_id: UUID
    title: str
    steps: list[RoadmapStepResponse]


@router.post(
    "",
    response_model=GenerationResponse,
    summary="로드맵 생성(레거시 엔드포인트)",
    description="기존 클라이언트 호환을 위해 유지되는 로드맵 즉시 생성 API입니다.",
    response_description="생성된 로드맵 ID, 제목, 단계 목록을 반환합니다.",
)
async def generate_roadmap(
    request: GenerationRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    team = await deps.get_current_team(current_user=current_user, session=session)
    if not team:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No team context")
    service = RoadmapService(roadmap_repo=RoadmapRepository(session))
    result = await service.create_roadmap(
        team_id=team.id,
        user_id=current_user.id,
        business_type=request.business_type,
        location=request.location,
        description=request.description,
        startup_type=request.startup_type,
        open_timeline=request.open_timeline,
        budget_range=request.budget_range,
        additional_notes=request.additional_notes,
    )
    return result.__dict__
