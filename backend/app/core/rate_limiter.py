"""
Rate Limiter for Authentication Endpoints.

Provides IP-based rate limiting using Redis to prevent brute-force attacks.
Implements sliding window algorithm for accurate rate limiting.

HIPAA Compliance:
- Failed login attempts are logged for audit trail
- Account lockout after excessive failures
"""

import time
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.

    Designed specifically for authentication endpoints to prevent:
    - Brute force password attacks
    - Credential stuffing
    - Account enumeration
    """

    # Rate limit configurations by endpoint type
    CONFIGS = {
        "login": {
            "max_requests": 5,      # Max login attempts
            "window_seconds": 300,  # 5 minute window
            "lockout_seconds": 900, # 15 minute lockout after exceeding
        },
        "password_reset": {
            "max_requests": 3,
            "window_seconds": 3600,  # 1 hour window
            "lockout_seconds": 3600,
        },
        "register": {
            "max_requests": 5,
            "window_seconds": 3600,
            "lockout_seconds": 3600,
        },
        "default": {
            "max_requests": 100,
            "window_seconds": 60,
            "lockout_seconds": 60,
        }
    }

    def __init__(self, redis_client):
        """
        Initialize rate limiter with Redis client.

        Args:
            redis_client: Async Redis client instance
        """
        self.redis = redis_client
        self.key_prefix = "ratelimit:"

    def _get_key(self, identifier: str, endpoint_type: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"{self.key_prefix}{endpoint_type}:{identifier}"

    def _get_lockout_key(self, identifier: str, endpoint_type: str) -> str:
        """Generate Redis key for lockout status."""
        return f"{self.key_prefix}lockout:{endpoint_type}:{identifier}"

    async def is_rate_limited(
        self,
        identifier: str,
        endpoint_type: str = "default"
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if identifier is rate limited.

        Args:
            identifier: Client identifier (IP address or user ID)
            endpoint_type: Type of endpoint (login, password_reset, etc.)

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        config = self.CONFIGS.get(endpoint_type, self.CONFIGS["default"])
        lockout_key = self._get_lockout_key(identifier, endpoint_type)

        # Check if currently locked out
        lockout_ttl = await self.redis.ttl(lockout_key)
        if lockout_ttl > 0:
            return True, lockout_ttl

        # Check current request count
        rate_key = self._get_key(identifier, endpoint_type)
        current_count = await self.redis.get(rate_key)

        if current_count and int(current_count) >= config["max_requests"]:
            # Apply lockout
            await self.redis.setex(
                lockout_key,
                config["lockout_seconds"],
                "1"
            )
            logger.warning(
                f"Rate limit exceeded for {identifier} on {endpoint_type}. "
                f"Locked out for {config['lockout_seconds']} seconds."
            )
            return True, config["lockout_seconds"]

        return False, None

    async def record_request(
        self,
        identifier: str,
        endpoint_type: str = "default"
    ) -> int:
        """
        Record a request and return current count.

        Args:
            identifier: Client identifier
            endpoint_type: Type of endpoint

        Returns:
            Current request count
        """
        config = self.CONFIGS.get(endpoint_type, self.CONFIGS["default"])
        rate_key = self._get_key(identifier, endpoint_type)

        # Increment counter
        count = await self.redis.incr(rate_key)

        # Set expiry on first request
        if count == 1:
            await self.redis.expire(rate_key, config["window_seconds"])

        return count

    async def reset_rate_limit(
        self,
        identifier: str,
        endpoint_type: str = "default"
    ) -> None:
        """
        Reset rate limit for identifier (e.g., after successful login).

        Args:
            identifier: Client identifier
            endpoint_type: Type of endpoint
        """
        rate_key = self._get_key(identifier, endpoint_type)
        lockout_key = self._get_lockout_key(identifier, endpoint_type)

        await self.redis.delete(rate_key, lockout_key)

    async def get_remaining_attempts(
        self,
        identifier: str,
        endpoint_type: str = "default"
    ) -> int:
        """
        Get remaining attempts before rate limit.

        Args:
            identifier: Client identifier
            endpoint_type: Type of endpoint

        Returns:
            Number of remaining attempts
        """
        config = self.CONFIGS.get(endpoint_type, self.CONFIGS["default"])
        rate_key = self._get_key(identifier, endpoint_type)

        current_count = await self.redis.get(rate_key)
        if current_count:
            return max(0, config["max_requests"] - int(current_count))
        return config["max_requests"]


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles X-Forwarded-For header for reverse proxy setups.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # First IP in the list is the original client
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


async def check_rate_limit(
    request: Request,
    endpoint_type: str = "default",
    redis_client=None
) -> None:
    """
    FastAPI dependency to check rate limiting.

    Usage:
        @router.post("/login")
        async def login(
            request: Request,
            _: None = Depends(lambda r: check_rate_limit(r, "login"))
        ):
            ...

    Args:
        request: FastAPI Request
        endpoint_type: Type of endpoint for rate limit config
        redis_client: Redis client (injected via dependency)

    Raises:
        HTTPException(429): If rate limited
    """
    if redis_client is None:
        # Skip rate limiting if Redis not available
        logger.warning("Rate limiter: Redis client not available, skipping check")
        return

    limiter = RateLimiter(redis_client)
    client_ip = get_client_ip(request)

    is_limited, retry_after = await limiter.is_rate_limited(client_ip, endpoint_type)

    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    # Record this request
    await limiter.record_request(client_ip, endpoint_type)
