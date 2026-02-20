from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.schemas import (
    RoadmapInputValidateRequest,
    RoadmapInputValidateResponse,
    RoadmapJobCreateRequest,
    RoadmapJobResponse,
    RoadmapJobResultResponse,
)
from app.core.db import get_session
from app.features.roadmaps.application.roadmap_generation_service import RoadmapGenerationService
from app.features.roadmaps.application.worker_queue import enqueue_roadmap_job
from app.models.team import Team
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_job_repository import RoadmapJobRepository

router = APIRouter(prefix="/jobs")


@router.post("/validate", response_model=RoadmapInputValidateResponse)
async def validate_roadmap_job_input(
    request: RoadmapInputValidateRequest,
    _: AuthenticatedUser = Depends(deps.get_current_user),
    __: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> RoadmapInputValidateResponse:
    service = RoadmapGenerationService(session)
    result = await service.validate_generation_input(
        business_type=request.business_type,
        location=request.location,
        description=request.description,
    )
    return RoadmapInputValidateResponse(
        valid=result.valid,
        normalized_business_type=result.normalized_business_type,
        normalized_location=result.normalized_location,
        reason=result.reason,
        confidence=result.confidence,
    )


@router.post("", response_model=RoadmapJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_roadmap_job(
    request: RoadmapJobCreateRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> RoadmapJobResponse:
    service = RoadmapGenerationService(session)
    validation = await service.validate_generation_input(
        business_type=request.business_type,
        location=request.location,
        description=request.description,
    )
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=validation.reason or "Invalid business_type/location input",
        )

    normalized_payload = request.model_dump()
    normalized_payload["business_type"] = (
        validation.normalized_business_type or request.business_type
    )
    normalized_payload["location"] = validation.normalized_location or request.location

    job_id = await service.submit_job(
        team_id=current_team.id,
        user_id=current_user.id,
        payload=normalized_payload,
    )
    enqueued = await enqueue_roadmap_job(job_id)
    if not enqueued:
        repo = RoadmapJobRepository(session)
        job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
        if job:
            await repo.mark_failed(job, code="QUEUE_UNAVAILABLE", message="Failed to enqueue job")

    repo = RoadmapJobRepository(session)
    job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
    if not job:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Job create failed")
    return RoadmapJobResponse(
        job_id=job.id,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        roadmap_id=job.roadmap_id,
        error_code=job.error_code,
        error_message=job.error_message,
    )


@router.get("/{job_id}", response_model=RoadmapJobResponse)
async def get_roadmap_job(
    job_id: UUID,
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> RoadmapJobResponse:
    repo = RoadmapJobRepository(session)
    job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return RoadmapJobResponse(
        job_id=job.id,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        roadmap_id=job.roadmap_id,
        error_code=job.error_code,
        error_message=job.error_message,
    )


@router.get("/{job_id}/result", response_model=RoadmapJobResultResponse)
async def get_roadmap_job_result(
    job_id: UUID,
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> RoadmapJobResultResponse:
    repo = RoadmapJobRepository(session)
    job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != "SUCCEEDED":
        return RoadmapJobResultResponse(
            job_id=job.id,
            status=job.status,
            roadmap_id=None,
        )
    return RoadmapJobResultResponse(
        job_id=job.id,
        status=job.status,
        roadmap_id=job.roadmap_id,
    )
