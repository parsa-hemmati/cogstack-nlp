"""
Rate Limiting Middleware

Provides rate limiting for API endpoints using Redis.
Implements sliding window rate limiting with configurable limits per user.
"""
import logging
from typing import Callable
from fastapi import HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from app.core.config import settings
from app.models.user import User
from app.core.security import get_current_user as _get_current_user

logger = logging.getLogger(__name__)

# Redis connection (reuse from session management)
redis_client: redis.Redis = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client for rate limiting."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


def create_rate_limiter(limit: int, window: int = 60) -> Callable:
    """
    Create a rate limiter with custom limit and window.

    Args:
        limit: Maximum requests allowed in window
        window: Time window in seconds (default 60)

    Returns:
        Rate limiting dependency function

    Example:
        # Rate limit to 10 requests per minute
        rate_limit_10_per_min = create_rate_limiter(limit=10, window=60)

        @router.post("/expensive-endpoint", dependencies=[Depends(rate_limit_10_per_min)])
        async def expensive_operation(...):
            pass
    """
    async def rate_limiter(
        request: Request,
        current_user: User = Depends(_get_current_user)
    ) -> None:
        # Inline the rate limiting logic to avoid closure issues
        try:
            # Get Redis client
            redis_conn = await get_redis_client()

            # Create rate limit key: rate_limit:search:{user_id}
            key = f"rate_limit:search:{current_user.id}"

            # Get current count
            count = await redis_conn.get(key)

            if count is None:
                # First request in window - set key with TTL
                await redis_conn.setex(key, window, 1)
                count = 1
            else:
                count = int(count)

                if count >= limit:
                    # Rate limit exceeded
                    ttl = await redis_conn.ttl(key)
                    logger.warning(
                        f"Rate limit exceeded: user={current_user.username}, "
                        f"count={count}, limit={limit}, reset_in={ttl}s"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Maximum {limit} searches per {window} seconds. "
                               f"Try again in {ttl} seconds.",
                        headers={"Retry-After": str(ttl)}
                    )

                # Increment count
                await redis_conn.incr(key)
                count += 1

            # Log successful rate limit check
            logger.debug(
                f"Rate limit check: user={current_user.username}, "
                f"count={count}/{limit}"
            )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log error but don't block request if Redis is down
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            # Fallback: allow request (graceful degradation)
            pass

    return rate_limiter


# Default rate limiter for search endpoints (60 requests per minute)
rate_limit_search_dependency = create_rate_limiter(limit=60, window=60)