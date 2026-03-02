import logging
from uuid import UUID

from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import async_session
from app.features.roadmaps.application.roadmap_generation_service import (
    RoadmapGenerationService,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository

logger = logging.getLogger(__name__)


async def process_roadmap_job(ctx: dict, job_id: str) -> None:
    async with async_session() as session:  # type: AsyncSession
        service = RoadmapGenerationService(session)
        await service.process_job(UUID(job_id))


async def cleanup_expired_refresh_tokens(ctx: dict) -> None:
    """Delete expired/revoked refresh tokens older than 30 days."""
    async with async_session() as session:
        repo = RefreshTokenRepository(session)
        deleted = await repo.delete_expired_and_revoked(older_than_days=30)
        if deleted:
            logger.info("Cleaned up %d expired/revoked refresh tokens", deleted)


class WorkerSettings:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [process_roadmap_job]
    cron_jobs = [
        cron(cleanup_expired_refresh_tokens, hour=3, minute=0),  # daily at 03:00 UTC
    ]
