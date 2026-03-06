"""Redis Pub/Sub for real-time notification delivery via SSE.

Usage (publish side):
    from app.services.notification_pubsub import publish_notification
    await publish_notification(user_id=123, payload={...})

Usage (subscribe side — SSE endpoint):
    from app.services.notification_pubsub import subscribe_notifications
    async for message in subscribe_notifications(user_id=123):
        yield f"data: {message}\\n\\n"
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_pool: aioredis.Redis | None = None


def _channel_name(user_id: int) -> str:
    return f"notifications:{user_id}"


async def _get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_pool


async def publish_notification(user_id: int, payload: dict) -> None:
    """Publish a notification event to the user's Redis channel."""
    try:
        redis = await _get_redis()
        await redis.publish(_channel_name(user_id), json.dumps(payload))
    except Exception:
        logger.warning("Failed to publish notification for user %s", user_id, exc_info=True)


async def subscribe_notifications(user_id: int) -> AsyncIterator[str]:
    """Yield JSON-encoded notification messages for the given user."""
    redis = await _get_redis()
    pubsub = redis.pubsub()
    channel = _channel_name(user_id)
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
