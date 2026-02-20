from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import get_settings


async def enqueue_roadmap_job(job_id: UUID) -> bool:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    try:
        pool = await create_pool(redis_settings)
        await pool.enqueue_job("process_roadmap_job", str(job_id))
        await pool.close()
        return True
    except Exception:
        return False
