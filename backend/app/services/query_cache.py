"""
Query result caching service for search performance optimization.

Provides:
- Redis-based query result caching
- Cache key generation with query normalization
- TTL management for different query types
- Cache invalidation strategies
- Cache statistics tracking

Ported from: origin/development:clinical-care-tools/backend/app/services/elasticsearch/query_cache.py
"""

import hashlib
import json
import pickle
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryCache:
    """Redis-based cache for search query results."""

    # Cache TTL configuration by query type (in seconds)
    TTL_CONFIG = {
        "standard": 3600,      # 1 hour for standard queries
        "boolean": 3600,       # 1 hour for boolean queries
        "wildcard": 1800,      # 30 minutes for wildcard (more dynamic)
        "fuzzy": 3600,         # 1 hour for fuzzy
        "proximity": 3600,     # 1 hour for proximity
        "range": 600,          # 10 minutes for range (time-sensitive)
        "regex": 1800,         # 30 minutes for regex
        "suggestions": 7200,   # 2 hours for autocomplete suggestions
        "patient_search": 1800 # 30 minutes for patient search
    }

    def __init__(self, redis_client):
        """
        Initialize query cache.

        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client
        self.cache_prefix = "search:cache:"
        self.stats_prefix = "search:stats:"

    def _generate_cache_key(
        self,
        query_text: str,
        query_type: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> str:
        """
        Generate deterministic cache key for query.

        Args:
            query_text: Search query text
            query_type: Type of query
            filters: Additional filters
            page: Page number
            page_size: Results per page

        Returns:
            SHA256 hash as cache key
        """
        # Normalize and sort parameters for consistent key generation
        key_data = {
            "query": query_text.lower().strip(),
            "type": query_type,
            "filters": filters or {},
            "page": page,
            "size": page_size
        }

        # Sort filters for consistent ordering
        if key_data["filters"]:
            key_data["filters"] = dict(sorted(key_data["filters"].items()))

        # Generate SHA256 hash
        key_string = json.dumps(key_data, sort_keys=True)
        hash_key = hashlib.sha256(key_string.encode()).hexdigest()

        return f"{self.cache_prefix}{query_type}:{hash_key}"

    async def get(
        self,
        query_text: str,
        query_type: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached query results.

        Args:
            query_text: Search query text
            query_type: Type of query
            filters: Additional filters
            page: Page number
            page_size: Results per page

        Returns:
            Cached results or None if not found
        """
        try:
            cache_key = self._generate_cache_key(
                query_text, query_type, filters, page, page_size
            )

            # Get from Redis
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                # Update cache hit statistics
                await self._update_stats("hit", query_type)

                # Deserialize and return
                return pickle.loads(cached_data)

            # Update cache miss statistics
            await self._update_stats("miss", query_type)
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        query_text: str,
        query_type: str,
        results: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache query results.

        Args:
            query_text: Search query text
            query_type: Type of query
            results: Query results to cache
            filters: Additional filters
            page: Page number
            page_size: Results per page
            ttl: Optional custom TTL (seconds)

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(
                query_text, query_type, filters, page, page_size
            )

            # Use custom TTL or default for query type
            cache_ttl = ttl or self.TTL_CONFIG.get(query_type, 3600)

            # Serialize results
            serialized = pickle.dumps(results)

            # Store in Redis with TTL
            await self.redis.setex(cache_key, cache_ttl, serialized)

            logger.debug(f"Cached query: {query_type}, TTL: {cache_ttl}s")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def invalidate(
        self,
        query_type: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> int:
        """
        Invalidate cached queries.

        Args:
            query_type: Optional query type to invalidate
            pattern: Optional pattern to match keys

        Returns:
            Number of keys invalidated
        """
        try:
            if pattern:
                # Custom pattern
                search_pattern = f"{self.cache_prefix}{pattern}"
            elif query_type:
                # Invalidate specific query type
                search_pattern = f"{self.cache_prefix}{query_type}:*"
            else:
                # Invalidate all search cache
                search_pattern = f"{self.cache_prefix}*"

            # Find and delete matching keys
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=search_pattern,
                    count=100
                )
                if keys:
                    deleted += await self.redis.delete(*keys)
                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted} cache entries for pattern: {search_pattern}")
            return deleted

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = {
                "hits": {},
                "misses": {},
                "hit_rate": {},
                "total_keys": 0
            }

            # Get stats for each query type
            for query_type in self.TTL_CONFIG.keys():
                hits_key = f"{self.stats_prefix}hits:{query_type}"
                misses_key = f"{self.stats_prefix}misses:{query_type}"

                hits = int(await self.redis.get(hits_key) or 0)
                misses = int(await self.redis.get(misses_key) or 0)

                stats["hits"][query_type] = hits
                stats["misses"][query_type] = misses

                total = hits + misses
                stats["hit_rate"][query_type] = hits / total if total > 0 else 0

            # Count total cached keys
            cursor = 0
            count = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=f"{self.cache_prefix}*",
                    count=100
                )
                count += len(keys)
                if cursor == 0:
                    break

            stats["total_keys"] = count
            stats["timestamp"] = datetime.utcnow().isoformat()

            return stats

        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {"error": str(e)}

    async def _update_stats(self, stat_type: str, query_type: str) -> None:
        """
        Update cache statistics.

        Args:
            stat_type: 'hit' or 'miss'
            query_type: Query type
        """
        try:
            stat_key = f"{self.stats_prefix}{stat_type}s:{query_type}"
            await self.redis.incr(stat_key)
        except Exception as e:
            logger.warning(f"Failed to update stats: {e}")
