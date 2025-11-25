"""
Redis Client
Global Redis connection management
"""
from redis.asyncio import Redis
from app.core.config import settings

_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """
    Get or create Redis client (singleton pattern).

    Returns:
        Redis: Async Redis client

    Example:
        >>> redis = await get_redis()
        >>> await redis.set("key", "value")
        >>> value = await redis.get("key")
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


async def close_redis() -> None:
    """
    Close Redis connection (for application shutdown).

    Example:
        >>> await close_redis()
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
