from uuid import UUID

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_pool: ArqRedis | None = None


async def _get_pool() -> ArqRedis:
    global _pool
    if _pool is None:
        settings = get_settings()
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        _pool = await create_pool(redis_settings)
    return _pool


async def enqueue_roadmap_job(job_id: UUID) -> bool:
    try:
        pool = await _get_pool()
        await pool.enqueue_job("process_roadmap_job", str(job_id))
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue roadmap job: job_id={job_id}, error={e}")
        return False
