"""
Session Management Service
Redis-based session storage and management
"""
import json
from typing import Optional
from redis.asyncio import Redis
from app.models.session import Session
from app.core.config import settings


class SessionService:
    """Service for managing user sessions in Redis."""

    def __init__(self):
        """Initialize Redis connection."""
        # Redis connection will be created on first use
        self._redis: Optional[Redis] = None

    async def get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                str(settings.REDIS_URL),
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def create_session(self, session: Session) -> None:
        """
        Store session in Redis with TTL.

        Args:
            session: Session object to store
        """
        redis = await self.get_redis()
        key = session.to_redis_key()
        value = session.model_dump_json()
        ttl = session.ttl_seconds()

        await redis.setex(key, ttl, value)

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve session from Redis.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session object if found, None otherwise
        """
        redis = await self.get_redis()
        key = f"session:{session_id}"
        value = await redis.get(key)

        if value is None:
            return None

        return Session.model_validate_json(value)

    async def delete_session(self, session_id: str) -> None:
        """
        Delete session from Redis (logout).

        Args:
            session_id: Session ID to delete
        """
        redis = await self.get_redis()
        key = f"session:{session_id}"
        await redis.delete(key)

    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions deleted
        """
        redis = await self.get_redis()
        pattern = "session:*"
        deleted = 0

        async for key in redis.scan_iter(match=pattern):
            value = await redis.get(key)
            if value:
                session = Session.model_validate_json(value)
                if session.user_id == user_id:
                    await redis.delete(key)
                    deleted += 1

        return deleted


# Global session service instance
session_service = SessionService()
