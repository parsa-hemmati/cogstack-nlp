"""Query result caching service for performance optimization.

Provides:
- Redis-based query result caching
- Cache key generation with query normalization
- TTL management for different query types
- Cache invalidation strategies
"""

import hashlib
import json
import pickle
from typing import Optional, Dict, Any
import redis.asyncio as redis
import logging
from datetime import timedelta

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
        "suggestions": 7200    # 2 hours for autocomplete suggestions
    }

    def __init__(self, redis_client: redis.Redis):
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
            ttl: Optional TTL override in seconds

        Returns:
            True if cached successfully
        """
        try:
            cache_key = self._generate_cache_key(
                query_text, query_type, filters, page, page_size
            )

            # Serialize data
            serialized = pickle.dumps(results)

            # Determine TTL
            if ttl is None:
                ttl = self.TTL_CONFIG.get(query_type, 3600)

            # Set in Redis with TTL
            await self.redis.setex(
                cache_key,
                ttl,
                serialized
            )

            # Update statistics
            await self._update_stats("set", query_type)
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Redis pattern to match keys

        Returns:
            Number of keys invalidated
        """
        try:
            # Find matching keys
            keys = []
            async for key in self.redis.scan_iter(f"{self.cache_prefix}{pattern}"):
                keys.append(key)

            # Delete keys if found
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    async def invalidate_all(self) -> int:
        """
        Clear all cached queries.

        Returns:
            Number of keys cleared
        """
        return await self.invalidate_pattern("*")

    async def _update_stats(self, stat_type: str, query_type: str):
        """
        Update cache statistics.

        Args:
            stat_type: Type of statistic (hit, miss, set)
            query_type: Type of query
        """
        try:
            stat_key = f"{self.stats_prefix}{query_type}:{stat_type}"
            await self.redis.incr(stat_key)

            # Update daily stats
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"{self.stats_prefix}daily:{today}:{query_type}:{stat_type}"
            await self.redis.incr(daily_key)

            # Set TTL for daily stats (7 days)
            await self.redis.expire(daily_key, 604800)

        except Exception as e:
            logger.error(f"Stats update error: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        try:
            stats = {}

            # Get stats for each query type
            for query_type in self.TTL_CONFIG.keys():
                hits = await self.redis.get(f"{self.stats_prefix}{query_type}:hit")
                misses = await self.redis.get(f"{self.stats_prefix}{query_type}:miss")
                sets = await self.redis.get(f"{self.stats_prefix}{query_type}:set")

                hits = int(hits) if hits else 0
                misses = int(misses) if misses else 0
                sets = int(sets) if sets else 0

                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else 0

                stats[query_type] = {
                    "hits": hits,
                    "misses": misses,
                    "sets": sets,
                    "total_requests": total,
                    "hit_rate": round(hit_rate, 2),
                    "ttl_seconds": self.TTL_CONFIG[query_type]
                }

            # Get total cache size
            cache_size = 0
            async for _ in self.redis.scan_iter(f"{self.cache_prefix}*"):
                cache_size += 1

            stats["total_cached_queries"] = cache_size
            stats["cache_prefix"] = self.cache_prefix

            return stats

        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return {}

    async def warm_cache(self, common_queries: list):
        """
        Pre-warm cache with common queries.

        Args:
            common_queries: List of common query dictionaries
        """
        logger.info(f"Warming cache with {len(common_queries)} queries")

        # This would be called during startup or maintenance
        # Implementation would execute queries and cache results
        pass