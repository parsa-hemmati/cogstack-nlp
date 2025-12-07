# Search Performance Optimizer

Expert knowledge of search query optimization and performance tuning for clinical document search. Based on Sprint 3 implementation achieving <500ms response times with 40% performance gains through optimization. Use when diagnosing slow queries, optimizing search performance, or implementing new query types.

## When This Skill Activates

**Activates automatically when**:
- Queries are running slowly
- Implementing new search features
- Analyzing query performance
- Optimizing Elasticsearch queries
- Debugging timeout issues
- Scaling search infrastructure

**Keywords**: performance, optimization, slow query, timeout, profiling, scaling

## Knowledge Base

### Query Optimization Rules (40% Performance Gain)

From Sprint 3 QueryOptimizer implementation:

#### 1. Wildcard Optimization

```python
# SLOW: Leading wildcards cause full index scan
{"wildcard": {"content": "*diabetes"}}  # ❌ Avoid

# BETTER: Trailing wildcards can use prefix
{"wildcard": {"content": "diabet*"}}

# BEST: Convert to prefix query (40% faster)
{"prefix": {"content": "diabet"}}

# For substring matching, use ngram analyzer instead:
{
    "match": {
        "content.ngram": "abet"  # Uses ngram field
    }
}
```

#### 2. Boolean Query Optimization

```python
# SLOW: Everything in 'must' clause (all scored)
{
    "bool": {
        "must": [
            {"match": {"content": "diabetes"}},      # Needs scoring
            {"term": {"document_type": "note"}},     # No scoring needed
            {"range": {"date": {"gte": "2023-01-01"}}} # No scoring needed
        ]
    }
}

# FAST: Non-scoring queries in 'filter' (cached)
{
    "bool": {
        "must": [
            {"match": {"content": "diabetes"}}  # Only scoring query
        ],
        "filter": [  # These get cached!
            {"term": {"document_type": "note"}},
            {"range": {"date": {"gte": "2023-01-01"}}}
        ]
    }
}
# Result: 25% faster due to filter caching
```

#### 3. Fuzzy Query Safety

```python
# DANGEROUS: Unbounded fuzzy expansion
{"fuzzy": {"content": {"value": "diabetes"}}}  # Can explode

# SAFE: With limits (prevents explosion)
{
    "fuzzy": {
        "content": {
            "value": "diabetes",
            "fuzziness": 2,            # Max edit distance
            "prefix_length": 2,        # First 2 chars must match
            "max_expansions": 50,      # Limit term expansion
            "transpositions": true     # Allow transpositions
        }
    }
}
```

#### 4. Regex Query Limits

```python
# DANGEROUS: Can cause stack overflow
{"regexp": {"content": ".*very.*long.*pattern.*"}}

# SAFE: With limits
{
    "regexp": {
        "content": {
            "value": "diabet.*",
            "max_determinized_states": 10000,  # Prevent ReDoS
            "flags": "INTERSECTION|COMPLEMENT",
            "rewrite": "constant_score"        # Don't compute scores
        }
    }
}
```

### Performance Benchmarks Achieved

From Sprint 3 implementation:

| Query Type | Unoptimized | Optimized | Improvement |
|------------|-------------|-----------|-------------|
| Standard | 450ms | 280ms | 38% |
| Boolean | 520ms | 320ms | 38% |
| Wildcard | 750ms | 450ms | 40% |
| Fuzzy | 650ms | 400ms | 38% |
| Cached | N/A | 150ms | 73% hit rate |

### Query Complexity Analysis

```python
class QueryComplexityAnalyzer:
    """Analyze and score query complexity."""

    COMPLEXITY_WEIGHTS = {
        "match": 1,
        "match_phrase": 2,
        "wildcard": 5,
        "fuzzy": 3,
        "regexp": 10,
        "range": 2,
        "span_near": 4,
        "bool": 1  # Multiplier for nested queries
    }

    MAX_COMPLEXITY = 100  # Queries above this are too complex

    def analyze(self, query: Dict) -> Dict:
        """Score query complexity."""

        score = self._calculate_score(query)

        return {
            "total_score": score,
            "is_complex": score > self.MAX_COMPLEXITY,
            "recommendations": self._get_recommendations(score)
        }

    def _get_recommendations(self, score: int) -> List[str]:
        if score > 150:
            return ["Query too complex - split into multiple queries"]
        elif score > 100:
            return ["Consider simplifying query", "Add filters to reduce scope"]
        elif score > 50:
            return ["Query is moderately complex", "Consider caching results"]
        else:
            return ["Query complexity is acceptable"]
```

### Performance Optimization Techniques

#### 1. Source Filtering

```python
# SLOW: Fetching entire documents
{
    "query": {...},
    "_source": true  # Returns everything
}

# FAST: Only fetch needed fields
{
    "query": {...},
    "_source": ["title", "date", "author"],  # Only these fields
    "size": 20
}
# Result: 50-70% reduction in network transfer
```

#### 2. Aggregation Optimization

```python
# SLOW: Large aggregation buckets
{
    "aggs": {
        "departments": {
            "terms": {
                "field": "department",
                "size": 10000  # Too many buckets
            }
        }
    }
}

# FAST: Limited buckets with sampling
{
    "aggs": {
        "sample": {
            "sampler": {
                "shard_size": 100  # Sample for performance
            },
            "aggs": {
                "departments": {
                    "terms": {
                        "field": "department",
                        "size": 10,  # Top 10 only
                        "min_doc_count": 5  # Skip rare terms
                    }
                }
            }
        }
    }
}
```

#### 3. Pagination Strategies

```python
# SLOW for deep pagination: from + size
{"from": 10000, "size": 20}  # Gets slower as from increases

# FAST: search_after for deep pagination
{
    "size": 20,
    "sort": [
        {"date": "desc"},
        {"_id": "asc"}  # Tiebreaker
    ],
    "search_after": ["2023-01-15", "doc-12345"]  # Last result from previous page
}

# FASTEST: Scroll API for exports (not real-time)
# POST /_search/scroll
{
    "scroll": "1m",
    "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAD4WYm9laVYtZndUQlNs..."
}
```

#### 4. Query Profiling

```python
async def profile_query(es_client, query: Dict) -> Dict:
    """Profile query execution."""

    # Add profiling flag
    query["profile"] = True

    response = await es_client.search(
        index="clinical_documents",
        body=query
    )

    profile = response.get("profile", {})

    # Analyze profile data
    slow_operations = []
    for shard in profile.get("shards", []):
        for search in shard.get("searches", []):
            for collector in search.get("collector", []):
                if collector.get("time_in_nanos", 0) > 100_000_000:  # >100ms
                    slow_operations.append({
                        "name": collector.get("name"),
                        "time_ms": collector.get("time_in_nanos") / 1_000_000,
                        "breakdown": collector.get("breakdown", {})
                    })

    return {
        "took_ms": response.get("took"),
        "slow_operations": slow_operations,
        "total_shards": response.get("_shards", {}).get("total"),
        "recommendations": _get_profile_recommendations(slow_operations)
    }
```

### Caching Strategy for Performance

```python
# Cache configuration based on query type and performance
CACHE_CONFIG = {
    "standard": {
        "ttl": 3600,         # 1 hour
        "hit_rate": 0.73,    # 73% achieved
        "avg_time_saved": 130  # ms saved per hit
    },
    "boolean": {
        "ttl": 3600,
        "hit_rate": 0.68,
        "avg_time_saved": 170
    },
    "wildcard": {
        "ttl": 1800,         # 30 min (more dynamic)
        "hit_rate": 0.45,
        "avg_time_saved": 300
    }
}

def should_cache_query(query_type: str, complexity_score: int) -> bool:
    """Determine if query should be cached."""

    # Always cache expensive queries
    if complexity_score > 50:
        return True

    # Cache based on type-specific rules
    config = CACHE_CONFIG.get(query_type, {})
    return config.get("hit_rate", 0) > 0.5
```

### Index Optimization

#### 1. Mapping Optimization

```python
{
    "mappings": {
        "properties": {
            "content": {
                "type": "text",
                "analyzer": "english",
                "index_options": "positions",  # For phrase queries
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256  # For aggregations
                    },
                    "shingles": {
                        "type": "text",
                        "analyzer": "shingle_analyzer"  # For phrases
                    }
                }
            },
            "document_type": {
                "type": "keyword",  # Not text! For exact match
                "doc_values": true   # For aggregations
            },
            "date": {
                "type": "date",
                "format": "yyyy-MM-dd",
                "doc_values": true   # For sorting
            }
        }
    }
}
```

#### 2. Index Settings

```python
{
    "settings": {
        "number_of_shards": 3,  # Based on data size
        "number_of_replicas": 1,
        "refresh_interval": "30s",  # Batch refreshes
        "index": {
            "search": {
                "slowlog": {
                    "threshold": {
                        "query": {
                            "warn": "10s",
                            "info": "5s",
                            "debug": "2s"
                        }
                    }
                }
            },
            "max_result_window": 10000,  # Limit deep pagination
            "max_regex_length": 1000     # Prevent regex abuse
        }
    }
}
```

### Monitoring and Alerting

```python
class PerformanceMonitor:
    """Monitor search performance metrics."""

    def __init__(self, threshold_ms: int = 500):
        self.threshold_ms = threshold_ms
        self.metrics = []

    async def track_query(self, query_type: str, took_ms: int, hit_cache: bool):
        """Track query performance."""

        self.metrics.append({
            "timestamp": datetime.now(),
            "query_type": query_type,
            "took_ms": took_ms,
            "hit_cache": hit_cache
        })

        # Alert if slow
        if took_ms > self.threshold_ms and not hit_cache:
            await self.alert_slow_query(query_type, took_ms)

        # Analyze patterns
        if len(self.metrics) >= 100:
            await self.analyze_performance_trends()

    async def analyze_performance_trends(self):
        """Analyze performance trends."""

        recent = self.metrics[-100:]

        # Calculate p50, p95, p99
        times = sorted([m["took_ms"] for m in recent])
        p50 = times[50]
        p95 = times[95]
        p99 = times[99]

        if p95 > self.threshold_ms:
            await self.alert(f"P95 latency {p95}ms exceeds {self.threshold_ms}ms")

        # Check cache effectiveness
        cache_hits = sum(1 for m in recent if m["hit_cache"])
        hit_rate = cache_hits / len(recent)

        if hit_rate < 0.5:
            await self.alert(f"Cache hit rate {hit_rate:.1%} below 50%")
```

### Common Performance Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Leading Wildcards** | Queries >1s | Use ngram analyzer |
| **Deep Pagination** | Slow after page 50 | Use search_after |
| **Large Documents** | High network I/O | Use source filtering |
| **Complex Aggregations** | Timeout errors | Add sampling |
| **No Caching** | Repeated slow queries | Implement Redis cache |
| **Poor Relevance** | Users complain | Tune field boosting |
| **Memory Issues** | OOM errors | Reduce bucket sizes |

### Performance Testing

```python
async def load_test(concurrent_users: int = 100):
    """Load test search API."""

    queries = [
        ("diabetes", "standard"),
        ("heart disease", "fuzzy"),
        ("cancer*", "wildcard"),
        ("patient NEAR diagnosis", "proximity")
    ]

    async def run_search(session, query, query_type):
        start = time.time()
        response = await session.get(
            f"/api/v1/search?q={query}&query_type={query_type}"
        )
        return time.time() - start

    # Run concurrent searches
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(concurrent_users):
            query, qtype = random.choice(queries)
            tasks.append(run_search(session, query, qtype))

        times = await asyncio.gather(*tasks)

    # Analyze results
    return {
        "min": min(times) * 1000,
        "max": max(times) * 1000,
        "avg": statistics.mean(times) * 1000,
        "p50": statistics.median(times) * 1000,
        "p95": np.percentile(times, 95) * 1000,
        "passed": all(t < 0.5 for t in times)  # All under 500ms
    }
```

## Example Implementation

### Complete Query Optimization Pipeline

```python
class SearchOptimizationPipeline:
    """Full optimization pipeline for search queries."""

    def __init__(self):
        self.optimizer = QueryOptimizer()
        self.analyzer = QueryComplexityAnalyzer()
        self.cache = QueryCache()
        self.monitor = PerformanceMonitor()

    async def execute_optimized_search(
        self,
        query_text: str,
        query_type: str,
        filters: Dict
    ) -> Dict:
        """Execute search with full optimization."""

        # 1. Check cache first
        cache_key = self.cache.get_key(query_text, query_type, filters)
        cached = await self.cache.get(cache_key)
        if cached:
            await self.monitor.track_query(query_type, 150, hit_cache=True)
            return cached

        # 2. Build base query
        es_query = self.build_query(query_text, query_type, filters)

        # 3. Analyze complexity
        complexity = self.analyzer.analyze(es_query)
        if complexity["is_complex"]:
            logger.warning(f"Complex query: {complexity['recommendations']}")

        # 4. Optimize query
        optimized, notes = self.optimizer.optimize(es_query, query_type)
        logger.info(f"Optimizations applied: {notes}")

        # 5. Execute with timeout
        start = time.time()
        try:
            results = await asyncio.wait_for(
                self.execute_query(optimized),
                timeout=2.0  # 2 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Query timeout after 2s")
            raise

        took_ms = (time.time() - start) * 1000

        # 6. Track performance
        await self.monitor.track_query(query_type, took_ms, hit_cache=False)

        # 7. Cache if appropriate
        if took_ms > 200:  # Cache slow queries
            await self.cache.set(cache_key, results)

        return results
```

## Related Skills

- **elasticsearch-query-expert**: For query building
- **redis-caching-patterns**: For cache implementation
- **test-coverage-analyzer**: For performance testing

## References

- [QueryOptimizer Implementation](clinical-care-tools/backend/app/services/elasticsearch/query_optimizer.py)
- [Performance Metrics](PROJECT_STATUS_REPORT.md#performance-metrics)
- [Elasticsearch Tuning Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)