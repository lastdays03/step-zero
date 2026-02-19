from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.schemas import (
    RoadmapDetailResponse,
    RoadmapDetailStepResponse,
    RoadmapResponse,
    RoadmapStepActionUpdateRequest,
    RoadmapStepActionResponse,
    RoadmapStepDetailResponse,
    RoadmapStepResponse,
    RoadmapStepStatusUpdateRequest,
)
from app.core.db import get_session
from app.features.roadmaps.application.roadmap_progress_service import (
    InvalidRoadmapStepStatusError,
    RoadmapProgressService,
)
from app.models.team import Team
from app.models.roadmap import Roadmap
from app.repositories.roadmap_repository import RoadmapRepository

router = APIRouter()


async def _serialize_roadmap_detail(
    *,
    repo: RoadmapRepository,
    roadmap: Roadmap,
) -> RoadmapDetailResponse:
    steps = await repo.list_steps(roadmap.id)
    step_ids = [s.id for s in steps if s.id is not None]
    details = await repo.list_step_details(step_ids)
    actions = await repo.list_step_actions(step_ids)

    detail_map = {d.roadmap_step_id: d for d in details}
    action_map: dict[int, list[RoadmapStepActionResponse]] = {}
    for action in actions:
        action_map.setdefault(action.roadmap_step_id, []).append(
            RoadmapStepActionResponse(
                id=action.id,
                action_type=action.action_type,
                title=action.title,
                description=action.description,
                source_url=action.source_url,
                metadata_json=action.metadata_json,
            )
        )

    output_steps: list[RoadmapDetailStepResponse] = []
    for step in steps:
        if step.id is None:
            continue
        detail = detail_map.get(step.id)
        detail_model = None
        if detail:
            detail_model = RoadmapStepDetailResponse(
                id=detail.id,
                phase=detail.phase,
                objective=detail.objective,
                estimated_days=detail.estimated_days,
                risk_notes=detail.risk_notes,
                generation_mode=detail.generation_mode,
                actions=action_map.get(step.id, []),
            )
        output_steps.append(
            RoadmapDetailStepResponse(
                id=int(step.id),
                title=step.title,
                status=step.status,
                detail=detail_model,
            )
        )

    return RoadmapDetailResponse(
        roadmap_id=roadmap.id,
        title=roadmap.title,
        steps=output_steps,
    )


@router.get("/latest/detail", response_model=RoadmapDetailResponse)
async def get_latest_roadmap_detail(
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    repo = RoadmapRepository(session)
    roadmap = await repo.get_latest_for_team(current_team.id)
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    return await _serialize_roadmap_detail(repo=repo, roadmap=roadmap)


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: UUID,
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    repo = RoadmapRepository(session)
    roadmap = await repo.get_by_id_for_team(roadmap_id, current_team.id)
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    steps = await repo.list_steps(roadmap.id)
    return {
        "roadmap_id": roadmap.id,
        "title": roadmap.title,
        "steps": [{"id": step.id, "title": step.title, "status": step.status} for step in steps],
    }


@router.get("/{roadmap_id}/detail", response_model=RoadmapDetailResponse)
async def get_roadmap_detail(
    roadmap_id: UUID,
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    repo = RoadmapRepository(session)
    roadmap = await repo.get_by_id_for_team(roadmap_id, current_team.id)
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    return await _serialize_roadmap_detail(repo=repo, roadmap=roadmap)


@router.patch("/tasks/{step_id}", response_model=RoadmapStepResponse)
async def update_roadmap_step_status(
    step_id: int,
    request: RoadmapStepStatusUpdateRequest,
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    repo = RoadmapRepository(session)
    service = RoadmapProgressService(repo)
    try:
        step = await service.update_step_status(
            team_id=current_team.id,
            step_id=step_id,
            new_status=request.status,
        )
    except InvalidRoadmapStepStatusError as exc:
        message = str(exc)
        if message == "Roadmap step not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    if step.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Roadmap step update failed",
        )
    return RoadmapStepResponse(id=step.id, title=step.title, status=step.status)


@router.patch("/tasks/{step_id}/actions/{action_id}", response_model=RoadmapStepActionResponse)
async def update_roadmap_step_action(
    step_id: int,
    action_id: int,
    request: RoadmapStepActionUpdateRequest,
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    repo = RoadmapRepository(session)
    service = RoadmapProgressService(repo)
    try:
        action = await service.update_action_completion(
            team_id=current_team.id,
            step_id=step_id,
            action_id=action_id,
            completed=request.completed,
        )
    except InvalidRoadmapStepStatusError as exc:
        message = str(exc)
        if message == "Roadmap step action not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return RoadmapStepActionResponse(
        id=action.id,
        action_type=action.action_type,
        title=action.title,
        description=action.description,
        source_url=action.source_url,
        metadata_json=action.metadata_json,
    )
