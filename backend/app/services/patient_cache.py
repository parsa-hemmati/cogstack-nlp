"""Patient Data Caching Service.

Caches FHIR patient data in Redis to reduce Meditech API calls and improve performance.
"""

import logging
import json
from typing import Optional, Dict, Any
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class PatientDataCache:
    """Redis-based cache for patient FHIR data.

    Caches complete patient bundles (Patient + Conditions + Observations + Medications)
    with 5-minute TTL to reduce Meditech API load.
    """

    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL.

        Args:
            ttl_seconds: Time to live for cached data (default 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self.key_prefix = "patient:fhir:"

    def _make_key(self, nhs_number: str) -> str:
        """Create Redis cache key for patient.

        Args:
            nhs_number: Patient NHS number

        Returns:
            Redis key string
        """
        return f"{self.key_prefix}{nhs_number}"

    async def get(self, nhs_number: str) -> Optional[Dict[str, Any]]:
        """Get cached patient data.

        Args:
            nhs_number: Patient NHS number

        Returns:
            Cached patient bundle dict if found, None if cache miss
        """
        key = self._make_key(nhs_number)
        try:
            cached_data = await redis_client.get(key)
            if cached_data:
                logger.debug(f"Cache hit for patient: {nhs_number}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache miss for patient: {nhs_number}")
                return None
        except Exception as e:
            logger.warning(f"Failed to get cached patient data: {str(e)}")
            return None

    async def set(self, nhs_number: str, patient_data: Dict[str, Any]) -> None:
        """Cache patient data with TTL.

        Args:
            nhs_number: Patient NHS number
            patient_data: Patient bundle dict (patient, conditions, observations, medications)
        """
        key = self._make_key(nhs_number)
        try:
            cached_json = json.dumps(patient_data, default=str)  # default=str handles datetime serialization
            await redis_client.setex(key, self.ttl_seconds, cached_json)
            logger.debug(f"Cached patient data: {nhs_number} (TTL: {self.ttl_seconds}s)")
        except Exception as e:
            logger.warning(f"Failed to cache patient data: {str(e)}")

    async def invalidate(self, nhs_number: str) -> None:
        """Invalidate cached patient data (force refresh on next request).

        Args:
            nhs_number: Patient NHS number
        """
        key = self._make_key(nhs_number)
        try:
            await redis_client.delete(key)
            logger.info(f"Invalidated cache for patient: {nhs_number}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {str(e)}")

    async def clear_all(self) -> None:
        """Clear all cached patient data (use for testing or data refresh)."""
        try:
            # Scan for all keys matching pattern
            keys = []
            async for key in redis_client.scan_iter(match=f"{self.key_prefix}*"):
                keys.append(key)

            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached patient records")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {str(e)}")


# Global cache instance
_patient_cache: Optional[PatientDataCache] = None


def get_patient_cache() -> PatientDataCache:
    """Get global patient cache instance (singleton pattern).

    Returns:
        PatientDataCache instance
    """
    global _patient_cache
    if _patient_cache is None:
        _patient_cache = PatientDataCache()
    return _patient_cache
