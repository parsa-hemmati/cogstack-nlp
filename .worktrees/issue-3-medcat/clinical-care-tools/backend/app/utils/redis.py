"""Redis caching utilities."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis connection pool
_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool."""
    global _pool

    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_MAX_SIZE,
            decode_responses=True,
        )
        logger.info("Redis connection pool created")

    return _pool


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)


class RedisCache:
    """Redis cache wrapper with JSON serialization."""

    def __init__(self):
        """Initialize Redis cache."""
        self.redis: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis = await get_redis()
        logger.info("Connected to Redis")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.redis:
            await self.connect()

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds

        Returns:
            True if successful
        """
        if not self.redis:
            await self.connect()

        try:
            serialized = json.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.redis:
            await self.connect()

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self.redis:
            await self.connect()

        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            await self.connect()

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis CLEAR error: {e}")
            return 0


# Global cache instance
cache = RedisCache()
