from uuid import UUID

from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import async_session
from app.features.roadmaps.application.roadmap_generation_service import (
    RoadmapGenerationService,
)


async def process_roadmap_job(ctx: dict, job_id: str) -> None:
    async with async_session() as session:  # type: AsyncSession
        service = RoadmapGenerationService(session)
        await service.process_job(UUID(job_id))


class WorkerSettings:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [process_roadmap_job]
