"""Meditech OAuth 2.0 Client for FHIR API Authentication.

Implements OAuth 2.0 client credentials flow for Meditech Expanse FHIR API.
Tokens are cached in Redis to avoid repeated authentication requests.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx
from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class MeditechOAuthClient:
    """OAuth 2.0 client for Meditech FHIR API authentication.

    Implements client credentials flow with token caching in Redis.
    Automatically refreshes tokens on expiry.
    """

    def __init__(self):
        """Initialize OAuth client with Meditech credentials."""
        self.client_id = settings.MEDITECH_CLIENT_ID
        self.client_secret = settings.MEDITECH_CLIENT_SECRET
        self.token_url = settings.MEDITECH_TOKEN_URL
        self.cache_key = "meditech:oauth:token"
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def get_access_token(self) -> str:
        """Get valid access token (from cache or fetch new).

        Returns:
            Access token string

        Raises:
            HTTPException: If OAuth authentication fails
        """
        # Check cache first
        cached_token = await self._get_cached_token()
        if cached_token:
            logger.debug("Using cached Meditech OAuth token")
            return cached_token

        # Fetch new token
        logger.info("Fetching new Meditech OAuth token")
        token = await self._fetch_token()

        # Cache token
        await self._cache_token(token)

        return token

    async def _fetch_token(self) -> str:
        """Fetch new access token from Meditech OAuth endpoint.

        Returns:
            Access token string

        Raises:
            HTTPException: If authentication fails
        """
        try:
            response = await self.http_client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "system/Patient.read system/Condition.read system/Observation.read system/MedicationRequest.read"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour

            if not access_token:
                raise ValueError("No access_token in OAuth response")

            logger.info(f"OAuth token fetched successfully (expires in {expires_in}s)")

            # Store expiry time for cache TTL
            self._token_expires_in = expires_in

            return access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"OAuth authentication failed: HTTP {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"OAuth token fetch error: {str(e)}")
            raise

    async def _get_cached_token(self) -> Optional[str]:
        """Get access token from Redis cache.

        Returns:
            Cached token if valid, None if expired or not found
        """
        try:
            token = await redis_client.get(self.cache_key)
            return token.decode() if token else None
        except Exception as e:
            logger.warning(f"Failed to get cached token: {str(e)}")
            return None

    async def _cache_token(self, token: str) -> None:
        """Cache access token in Redis with TTL.

        Args:
            token: Access token to cache
        """
        try:
            # Cache for 90% of expiry time (safety buffer for token refresh)
            ttl = int(self._token_expires_in * 0.9)
            await redis_client.setex(self.cache_key, ttl, token)
            logger.debug(f"Cached OAuth token (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Failed to cache token: {str(e)}")

    async def invalidate_token(self) -> None:
        """Invalidate cached token (force re-fetch on next request)."""
        try:
            await redis_client.delete(self.cache_key)
            logger.info("Meditech OAuth token invalidated")
        except Exception as e:
            logger.warning(f"Failed to invalidate token: {str(e)}")

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.http_client.aclose()


# Global OAuth client instance
_oauth_client: Optional[MeditechOAuthClient] = None


async def get_oauth_client() -> MeditechOAuthClient:
    """Get global OAuth client instance (singleton pattern).

    Returns:
        MeditechOAuthClient instance
    """
    global _oauth_client
    if _oauth_client is None:
        _oauth_client = MeditechOAuthClient()
    return _oauth_client
