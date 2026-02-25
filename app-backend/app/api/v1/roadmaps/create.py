from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.schemas import (
    RoadmapCreateRequest,
    RoadmapListResponse,
    RoadmapResponse,
    RoadmapSummaryItem,
)
from app.core.db import get_session
from app.features.roadmaps.application.roadmap_service import RoadmapService
from app.models.team import Team
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_repository import RoadmapRepository

router = APIRouter()


@router.get(
    "",
    response_model=RoadmapListResponse,
    summary="로드맵 목록 조회",
    description="현재 팀의 로드맵 목록을 최신순으로 조회합니다.",
    response_description="로드맵 요약 목록과 전체 건수를 반환합니다.",
)
async def list_roadmaps(
    offset: int = Query(0, ge=0, description="페이징 오프셋"),
    limit: int = Query(20, ge=1, le=100, description="페이징 제한"),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    repo = RoadmapRepository(session)
    roadmaps, total = await repo.list_for_team(current_team.id, offset=offset, limit=limit)

    items: list[RoadmapSummaryItem] = []
    for roadmap in roadmaps:
        steps = await repo.list_steps(roadmap.id)
        total_steps = len(steps)
        completed_steps = sum(1 for s in steps if s.status == "COMPLETED")
        progress = int(completed_steps / total_steps * 100) if total_steps > 0 else 0
        items.append(
            RoadmapSummaryItem(
                roadmap_id=roadmap.id,
                title=roadmap.title,
                business_type=roadmap.business_type,
                location=roadmap.location,
                created_at=roadmap.created_at.isoformat(),
                progress=progress,
                total_steps=total_steps,
                completed_steps=completed_steps,
            )
        )

    return RoadmapListResponse(items=items, total=total)


@router.post(
    "",
    response_model=RoadmapResponse,
    summary="로드맵 생성",
    description="입력된 업종/지역/메모를 기반으로 로드맵을 생성합니다.",
    response_description="생성된 로드맵 ID, 제목, 단계 목록을 반환합니다.",
)
async def create_roadmap(
    request: RoadmapCreateRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = RoadmapService(roadmap_repo=RoadmapRepository(session))
    result = await service.create_roadmap(
        team_id=current_team.id,
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
