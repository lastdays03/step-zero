from uuid import UUID

import sentry_sdk
import structlog
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import async_session
from app.core.exceptions import AppException
from app.features.roadmaps.application.roadmap_generation_service import (
    RoadmapGenerationService,
)
from app.models.actionkit_event import ActionKitEvent
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.roadmap_job_repository import RoadmapJobRepository

logger = structlog.get_logger("app.worker")


async def process_roadmap_job(ctx: dict, job_id: str) -> None:
    log = logger.bind(job_id=job_id, worker="roadmap")
    sentry_sdk.set_tag("job_id", job_id)

    try:
        parsed_id = UUID(job_id)
    except ValueError:
        await log.aerror("invalid_job_id", job_id=job_id)
        return

    try:
        async with async_session() as session:  # type: AsyncSession
            service = RoadmapGenerationService(session)
            await service.process_job(parsed_id)
        await log.ainfo("job_completed")
    except AppException as exc:
        await log.aerror(
            "job_domain_error",
            error_code=exc.error_code,
            error=str(exc),
        )
        sentry_sdk.capture_exception(exc)
        await _mark_job_failed(parsed_id, exc.error_code, str(exc))
    except Exception as exc:
        await log.aerror("job_unexpected_error", error=str(exc), exc_info=True)
        sentry_sdk.capture_exception(exc)
        await _mark_job_failed(parsed_id, "UNEXPECTED_ERROR", str(exc))


async def _mark_job_failed(job_id: UUID, code: str, message: str) -> None:
    """실패 시 새 세션으로 job 상태를 FAILED로 마킹한다."""
    try:
        async with async_session() as session:
            repo = RoadmapJobRepository(session)
            job = await repo.get(job_id)
            if job:
                await repo.mark_failed(job, code=code, message=message)
    except Exception:
        await logger.aerror("mark_failed_error", job_id=str(job_id), exc_info=True)


async def cleanup_expired_refresh_tokens(ctx: dict) -> None:
    """Delete expired/revoked refresh tokens older than 30 days."""
    async with async_session() as session:
        repo = RefreshTokenRepository(session)
        deleted = await repo.delete_expired_and_revoked(older_than_days=30)
        if deleted:
            await logger.ainfo(
                "cleanup_refresh_tokens", deleted=deleted
            )


async def cleanup_old_actionkit_events(ctx: dict) -> None:
    """Delete actionkit events older than 90 days."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import delete

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=90)
    async with async_session() as session:
        stmt = delete(ActionKitEvent).where(ActionKitEvent.created_at < cutoff)
        result = await session.execute(stmt)
        await session.commit()
        if result.rowcount:
            await logger.ainfo(
                "cleanup_actionkit_events", deleted=result.rowcount
            )


class WorkerSettings:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [process_roadmap_job]
    max_tries = 3
    retry_delay = 30
    job_timeout = 300
    cron_jobs = [
        cron(cleanup_expired_refresh_tokens, hour=3, minute=0),  # daily at 03:00 UTC
        cron(cleanup_old_actionkit_events, hour=4, minute=0),  # daily at 04:00 UTC
    ]
