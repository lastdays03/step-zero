from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.roadmap import RoadmapGenerationJob


class RoadmapJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(
        self,
        *,
        team_id: UUID,
        user_id: int,
        payload: dict,
    ) -> RoadmapGenerationJob:
        job = RoadmapGenerationJob(
            team_id=team_id,
            user_id=user_id,
            input_payload=payload,
            status="QUEUED",
            stage="QUEUED",
            progress=0,
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_for_team(self, *, job_id: UUID, team_id: UUID) -> RoadmapGenerationJob | None:
        stmt = select(RoadmapGenerationJob).where(
            RoadmapGenerationJob.id == job_id,
            RoadmapGenerationJob.team_id == team_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, *, job_id: UUID) -> RoadmapGenerationJob | None:
        stmt = select(RoadmapGenerationJob).where(RoadmapGenerationJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_running(self, job: RoadmapGenerationJob) -> None:
        job.status = "RUNNING"
        job.stage = "MASTER_GENERATING"
        job.progress = 10
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        self.session.add(job)
        await self.session.commit()

    async def set_progress(self, job: RoadmapGenerationJob, *, stage: str, progress: int) -> None:
        job.stage = stage
        job.progress = max(0, min(progress, 100))
        job.updated_at = datetime.utcnow()
        self.session.add(job)
        await self.session.commit()

    async def mark_succeeded(self, job: RoadmapGenerationJob, *, roadmap_id: UUID) -> None:
        now = datetime.utcnow()
        job.status = "SUCCEEDED"
        job.stage = "COMPLETED"
        job.progress = 100
        job.roadmap_id = roadmap_id
        job.completed_at = now
        job.updated_at = now
        self.session.add(job)
        await self.session.commit()

    async def mark_failed(self, job: RoadmapGenerationJob, *, code: str, message: str) -> None:
        now = datetime.utcnow()
        job.status = "FAILED"
        job.stage = "FAILED"
        job.error_code = code
        job.error_message = message[:1000]
        job.completed_at = now
        job.updated_at = now
        self.session.add(job)
        await self.session.commit()
