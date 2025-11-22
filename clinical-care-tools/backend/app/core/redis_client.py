"""
Redis client for caching and session management.

Web environment: Native Redis connection.
Production: Docker-based Redis with persistence.
"""

import json
from typing import Optional, Any
from redis import asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    """
    Async Redis client wrapper.

    Provides caching and session management functionality.
    """

    def __init__(self):
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
        )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    # Session Management

    async def set_session(
        self, session_id: str, data: dict[str, Any], ttl: int = 3600
    ) -> None:
        """
        Store session data.

        Args:
            session_id: Session identifier
            data: Session data dictionary
            ttl: Time to live in seconds (default 1 hour)
        """
        await self.client.setex(
            f"session:{session_id}", ttl, json.dumps(data)
        )

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data dictionary or None if not found
        """
        data = await self.client.get(f"session:{session_id}")
        return json.loads(data) if data else None

    async def delete_session(self, session_id: str) -> None:
        """
        Delete session.

        Args:
            session_id: Session identifier
        """
        await self.client.delete(f"session:{session_id}")

    async def extend_session(self, session_id: str, ttl: int = 3600) -> bool:
        """
        Extend session TTL.

        Args:
            session_id: Session identifier
            ttl: New TTL in seconds

        Returns:
            True if session exists and was extended, False otherwise
        """
        return bool(await self.client.expire(f"session:{session_id}", ttl))

    # Caching

    async def set_cache(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        """
        Store cached value.

        Args:
            key: Cache key
            value: Value to cache (will be JSON-serialized)
            ttl: Optional TTL in seconds
        """
        serialized = json.dumps(value)
        if ttl:
            await self.client.setex(f"cache:{key}", ttl, serialized)
        else:
            await self.client.set(f"cache:{key}", serialized)

    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Retrieve cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        data = await self.client.get(f"cache:{key}")
        return json.loads(data) if data else None

    async def delete_cache(self, key: str) -> None:
        """
        Delete cached value.

        Args:
            key: Cache key
        """
        await self.client.delete(f"cache:{key}")

    async def clear_cache_pattern(self, pattern: str) -> int:
        """
        Delete all cache keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        keys = await self.client.keys(f"cache:{pattern}")
        if keys:
            return await self.client.delete(*keys)
        return 0

    # Health Check

    async def ping(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is responsive
        """
        try:
            return await self.client.ping()
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> Redis:
    """
    Dependency for getting Redis client.

    Usage:
        @app.get("/endpoint")
        async def endpoint(redis: Redis = Depends(get_redis)):
            ...
    """
    return redis_client.client
