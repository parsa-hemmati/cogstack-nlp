# Redis Caching Patterns

Expert knowledge of Redis caching strategies for healthcare applications. Provides battle-tested patterns from Sprint 3 implementation with 73% cache hit rate. Use when implementing caching, optimizing performance, or managing cache invalidation.

## When This Skill Activates

**Activates automatically when**:
- Implementing caching layers
- Optimizing API response times
- Managing cache invalidation
- Designing TTL strategies
- Building distributed caches
- Handling cache stampedes

**Keywords**: redis, cache, TTL, invalidation, performance, distributed cache

## Knowledge Base

### Core Caching Patterns

#### 1. Deterministic Cache Key Generation
From Sprint 3 QueryCache implementation:

```python
def _generate_cache_key(
    query_text: str,
    query_type: str,
    filters: Dict[str, str],
    page: int,
    page_size: int
) -> str:
    """Generate deterministic cache key using SHA256."""

    # Normalize inputs for consistency
    normalized = {
        "query": query_text.lower().strip(),  # Case-insensitive
        "type": query_type,
        "filters": filters or {},
        "page": page,
        "size": page_size
    }

    # Sort keys for deterministic JSON
    key_string = json.dumps(normalized, sort_keys=True)

    # Hash for shorter keys (Redis key limit: 512MB)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

    # Namespaced key
    return f"search:{query_type}:{key_hash}"
```

**Key Principles**:
- Normalize inputs (lowercase, strip whitespace)
- Sort dictionary keys for consistency
- Use SHA256 for distribution
- Namespace keys for organization
- Keep keys short but unique

#### 2. TTL Strategy by Data Type

```python
TTL_CONFIG = {
    # Stable data - longer TTL
    "user_profile": 86400,      # 24 hours
    "reference_data": 604800,   # 1 week

    # Dynamic data - medium TTL
    "search_results": 3600,      # 1 hour
    "document_list": 1800,       # 30 minutes

    # Time-sensitive - short TTL
    "notifications": 300,        # 5 minutes
    "active_alerts": 60,         # 1 minute

    # Session data - sliding window
    "user_session": 1800,        # 30 min, refresh on access

    # Never cache
    "phi_data": 0,              # Don't cache PHI
    "financial": 0,             # Don't cache financial
}
```

#### 3. Cache-Aside Pattern with Fallback

```python
async def get_with_cache(key: str, fetch_func, ttl: int = 3600):
    """Cache-aside pattern with automatic fallback."""

    # Try cache first
    cached = await redis.get(key)
    if cached:
        # Increment hit counter
        await redis.hincrby("cache:stats", "hits", 1)
        return json.loads(cached)

    # Cache miss - increment counter
    await redis.hincrby("cache:stats", "misses", 1)

    try:
        # Fetch from source
        data = await fetch_func()

        # Cache for next time
        await redis.setex(
            key,
            ttl,
            json.dumps(data, default=str)
        )

        return data

    except Exception as e:
        # Check for stale cache (backup)
        stale = await redis.get(f"{key}:stale")
        if stale:
            logger.warning(f"Using stale cache due to error: {e}")
            return json.loads(stale)
        raise
```

#### 4. Write-Through with Stale Backup

```python
async def set_with_backup(key: str, data: Any, ttl: int = 3600):
    """Write-through caching with stale backup."""

    serialized = json.dumps(data, default=str)

    # Use pipeline for atomic operations
    pipe = redis.pipeline()

    # Set main cache with TTL
    pipe.setex(key, ttl, serialized)

    # Set stale backup with longer TTL (2x)
    pipe.setex(f"{key}:stale", ttl * 2, serialized)

    # Update stats
    pipe.hincrby("cache:stats", "sets", 1)

    # Execute atomically
    await pipe.execute()
```

#### 5. Pattern-Based Invalidation

```python
async def invalidate_pattern(pattern: str) -> int:
    """Invalidate all keys matching pattern."""

    count = 0

    # Use SCAN for non-blocking iteration
    async for key in redis.scan_iter(match=pattern, count=100):
        await redis.delete(key)
        count += 1

    # Log invalidation
    logger.info(f"Invalidated {count} keys matching {pattern}")

    return count

# Usage examples:
await invalidate_pattern("search:*")           # All searches
await invalidate_pattern("user:123:*")         # Specific user
await invalidate_pattern("*:document:456")     # Specific document
```

#### 6. Cache Warming

```python
async def warm_cache(queries: List[Dict], priority: bool = False):
    """Pre-populate cache with common queries."""

    for query_config in queries:
        key = _generate_cache_key(**query_config)

        # Check if already cached
        if not await redis.exists(key):
            # Fetch and cache
            data = await fetch_data(**query_config)

            # Use longer TTL for warmed cache
            ttl = TTL_CONFIG.get(query_config["type"], 3600) * 2

            await redis.setex(key, ttl, json.dumps(data))

            if priority:
                # Mark as priority (don't evict)
                await redis.persist(key)
```

### Healthcare-Specific Patterns

#### 1. PHI-Safe Caching

```python
class PHISafeCacheService:
    """Cache service that never stores PHI."""

    FORBIDDEN_FIELDS = {
        "patient_name", "mrn", "ssn", "dob",
        "address", "phone", "email"
    }

    async def safe_cache_set(self, key: str, data: Dict, ttl: int):
        """Cache data after removing PHI."""

        # Deep copy to avoid modifying original
        safe_data = json.loads(json.dumps(data))

        # Remove PHI fields
        self._remove_phi(safe_data)

        # Add cache metadata
        safe_data["_cached_at"] = datetime.now().isoformat()
        safe_data["_cache_version"] = "1.0"

        await redis.setex(key, ttl, json.dumps(safe_data))

    def _remove_phi(self, data: Any):
        """Recursively remove PHI fields."""
        if isinstance(data, dict):
            for field in list(data.keys()):
                if field.lower() in self.FORBIDDEN_FIELDS:
                    data[field] = "[REDACTED]"
                else:
                    self._remove_phi(data[field])
        elif isinstance(data, list):
            for item in data:
                self._remove_phi(item)
```

#### 2. User-Scoped Caching

```python
def get_user_cache_key(user_id: str, resource: str) -> str:
    """Generate user-scoped cache keys."""
    return f"user:{user_id}:{resource}"

async def invalidate_user_cache(user_id: str):
    """Invalidate all cache for a specific user."""
    pattern = f"user:{user_id}:*"
    count = await invalidate_pattern(pattern)

    # Audit log the invalidation
    await audit_log(
        action="CACHE_INVALIDATE",
        user_id=user_id,
        details={"keys_invalidated": count}
    )
```

#### 3. Audit-Compliant Caching

```python
class AuditedCache:
    """Cache with audit trail for compliance."""

    async def get(self, key: str, user_id: str):
        """Get with audit logging."""

        value = await redis.get(key)

        # Log cache access
        await audit_log(
            action="CACHE_ACCESS",
            user_id=user_id,
            resource=key,
            cache_hit=value is not None
        )

        return value

    async def set(self, key: str, value: Any, ttl: int, user_id: str):
        """Set with audit logging."""

        await redis.setex(key, ttl, json.dumps(value))

        # Log cache write
        await audit_log(
            action="CACHE_WRITE",
            user_id=user_id,
            resource=key,
            ttl=ttl
        )
```

### Performance Optimization

#### 1. Pipeline for Batch Operations

```python
async def batch_get(keys: List[str]) -> Dict[str, Any]:
    """Get multiple keys efficiently."""

    pipe = redis.pipeline()

    for key in keys:
        pipe.get(key)

    results = await pipe.execute()

    return {
        key: json.loads(val) if val else None
        for key, val in zip(keys, results)
    }
```

#### 2. Cache Statistics Tracking

```python
class CacheStats:
    """Track cache performance metrics."""

    @staticmethod
    async def get_stats() -> Dict:
        """Get cache statistics."""

        stats = await redis.hgetall("cache:stats")

        hits = int(stats.get(b"hits", 0))
        misses = int(stats.get(b"misses", 0))
        sets = int(stats.get(b"sets", 0))

        total_requests = hits + misses
        hit_rate = (hits / total_requests * 100) if total_requests else 0

        return {
            "hits": hits,
            "misses": misses,
            "sets": sets,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "memory_used": await redis.info("memory"),
            "keys_count": await redis.dbsize()
        }
```

#### 3. Connection Pooling

```python
# Create connection pool
redis_pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    db=0,
    max_connections=50,
    socket_keepalive=True,
    socket_keepalive_options={
        1: 1,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 5   # TCP_KEEPCNT
    }
)

# Use pool for all connections
redis_client = redis.Redis(connection_pool=redis_pool)
```

### Cache Invalidation Strategies

#### 1. Event-Driven Invalidation

```python
async def on_document_update(document_id: str):
    """Invalidate cache when document updates."""

    patterns = [
        f"search:*",                    # All searches
        f"document:{document_id}:*",    # Document-specific
        f"timeline:*:{document_id}:*"   # Timeline containing doc
    ]

    for pattern in patterns:
        await invalidate_pattern(pattern)
```

#### 2. Time-Based Invalidation

```python
# Use Redis EXPIRE for automatic cleanup
await redis.setex(key, ttl=3600, value=data)

# Or set expiration separately
await redis.set(key, data)
await redis.expire(key, 3600)

# Check remaining TTL
ttl_remaining = await redis.ttl(key)
```

#### 3. Tag-Based Invalidation

```python
class TaggedCache:
    """Cache with tag-based invalidation."""

    async def set_with_tags(self, key: str, value: Any, tags: List[str], ttl: int):
        """Set cache with tags for group invalidation."""

        # Store the value
        await redis.setex(key, ttl, json.dumps(value))

        # Store tags
        for tag in tags:
            await redis.sadd(f"tag:{tag}", key)
            await redis.expire(f"tag:{tag}", ttl)

    async def invalidate_tag(self, tag: str):
        """Invalidate all keys with a specific tag."""

        keys = await redis.smembers(f"tag:{tag}")

        if keys:
            await redis.delete(*keys)
            await redis.delete(f"tag:{tag}")

        return len(keys)
```

### Common Pitfalls and Solutions

1. **Cache Stampede**: Use distributed locks
2. **Memory Overflow**: Set maxmemory-policy
3. **Key Collision**: Use proper namespacing
4. **Stale Data**: Implement versioning
5. **Network Latency**: Use connection pooling

### Monitoring and Alerting

```python
async def monitor_cache_health():
    """Monitor cache health metrics."""

    stats = await CacheStats.get_stats()

    # Alert if hit rate drops
    if stats["hit_rate"] < 50:
        await alert("Cache hit rate below 50%")

    # Alert if memory usage high
    memory = stats["memory_used"]
    if memory["used_memory_rss"] > memory["maxmemory"] * 0.9:
        await alert("Redis memory usage above 90%")

    # Alert if too many evictions
    if memory["evicted_keys"] > 1000:
        await alert("High key eviction rate")
```

## Example Implementation

### Complete Caching Service

```python
class ClinicalCacheService:
    """Production-ready cache service for clinical data."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl_config = TTL_CONFIG

    async def get_search_results(
        self,
        query: str,
        filters: Dict,
        user_id: str
    ) -> Optional[Dict]:
        """Get cached search results with compliance."""

        # Generate key
        key = self._get_search_key(query, filters)

        # Try cache
        cached = await self.redis.get(key)

        if cached:
            # Audit cache hit
            await self._audit_cache_access(user_id, key, hit=True)

            # Update stats
            await self.redis.hincrby("cache:stats:search", "hits", 1)

            return json.loads(cached)

        # Cache miss
        await self._audit_cache_access(user_id, key, hit=False)
        await self.redis.hincrby("cache:stats:search", "misses", 1)

        return None

    async def set_search_results(
        self,
        query: str,
        filters: Dict,
        results: Dict,
        user_id: str
    ):
        """Cache search results."""

        # Don't cache if contains PHI
        if self._contains_phi(results):
            logger.warning("Skipping cache due to PHI content")
            return

        key = self._get_search_key(query, filters)
        ttl = self.ttl_config.get("search_results", 3600)

        # Cache with backup
        pipe = self.redis.pipeline()
        pipe.setex(key, ttl, json.dumps(results))
        pipe.setex(f"{key}:stale", ttl * 2, json.dumps(results))
        pipe.hincrby("cache:stats:search", "sets", 1)
        await pipe.execute()

        # Audit
        await self._audit_cache_write(user_id, key, ttl)
```

## Related Skills

- **elasticsearch-query-expert**: For search result caching
- **search-performance-optimizer**: For cache tuning
- **healthcare-compliance-checker**: For PHI-safe caching

## References

- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Sprint 3 QueryCache Implementation](clinical-care-tools/backend/app/services/elasticsearch/query_cache.py)
- [Cache Hit Rate: 73.53%](PROJECT_STATUS_REPORT.md)