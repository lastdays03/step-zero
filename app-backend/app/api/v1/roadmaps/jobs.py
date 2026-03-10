from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
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
from app.core.exceptions import (
    AppException,
    AppValidationError,
    RoadmapJobNotFoundError,
)
from app.features.roadmaps.application.roadmap_generation_service import (
    RoadmapGenerationService,
)
from app.features.roadmaps.application.worker_queue import enqueue_roadmap_job
from app.models.team import Team
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_job_repository import RoadmapJobRepository

router = APIRouter(prefix="/jobs")


@router.post(
    "/validate",
    response_model=RoadmapInputValidateResponse,
    summary="로드맵 입력값 검증",
    description="로드맵 생성 전에 업종/지역 입력값 정규화 및 유효성 검증을 수행합니다.",
    response_description="검증 결과와 정규화 값을 반환합니다.",
)
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


@router.post(
    "",
    response_model=RoadmapJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="로드맵 생성 잡 생성",
    description="비동기 로드맵 생성 작업을 큐에 등록합니다.",
    response_description="생성된 잡 상태 정보를 반환합니다.",
)
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
        raise AppValidationError(
            validation.reason or "Invalid business_type/location input"
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
    repo = RoadmapJobRepository(session)
    job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)

    enqueued = await enqueue_roadmap_job(job_id)
    if not enqueued and job:
        await repo.mark_failed(
            job, code="QUEUE_UNAVAILABLE", message="Failed to enqueue job"
        )
    if not job:
        raise AppException("Job create failed")
    return RoadmapJobResponse(
        job_id=job.id,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        roadmap_id=job.roadmap_id,
        error_code=job.error_code,
        error_message=job.error_message,
    )


@router.get(
    "/{job_id}",
    response_model=RoadmapJobResponse,
    summary="로드맵 생성 잡 조회",
    description="잡 ID로 비동기 로드맵 생성 진행 상태를 조회합니다.",
    response_description="잡 상태 정보를 반환합니다.",
)
async def get_roadmap_job(
    job_id: UUID = Path(..., description="조회할 로드맵 생성 잡 ID"),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> RoadmapJobResponse:
    repo = RoadmapJobRepository(session)
    job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
    if not job:
        raise RoadmapJobNotFoundError()
    return RoadmapJobResponse(
        job_id=job.id,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        roadmap_id=job.roadmap_id,
        error_code=job.error_code,
        error_message=job.error_message,
    )


@router.get(
    "/{job_id}/result",
    response_model=RoadmapJobResultResponse,
    summary="로드맵 생성 결과 조회",
    description="잡 완료 시 생성된 로드맵 ID를 반환합니다.",
    response_description="잡 상태와 생성 결과를 반환합니다.",
)
async def get_roadmap_job_result(
    job_id: UUID = Path(..., description="결과를 조회할 로드맵 생성 잡 ID"),
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> RoadmapJobResultResponse:
    repo = RoadmapJobRepository(session)
    job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
    if not job:
        raise RoadmapJobNotFoundError()
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
