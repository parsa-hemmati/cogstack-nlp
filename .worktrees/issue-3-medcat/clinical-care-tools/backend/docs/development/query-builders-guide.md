# Query Builders Developer Guide

## Overview

This guide provides detailed information for developers working with the query builder system in the Clinical Care Tools search infrastructure. The query builders transform user queries into optimized Elasticsearch DSL.

## Architecture

```
User Query → API Endpoint → SearchService → QueryBuilder → Elasticsearch
                                    ↓
                              QueryCache ← QueryOptimizer
```

## Core Components

### 1. SearchQueryBuilder

The main query builder class that handles all query type transformations.

**Location**: `app/services/elasticsearch/search_query_builder.py`

#### Supported Query Types

| Type | Method | Description |
|------|--------|-------------|
| standard | `build_query()` | Multi-field search with boosting |
| boolean | `build_boolean_query()` | AND/OR/NOT logic parsing |
| wildcard | `build_wildcard_query()` | Pattern matching with * and ? |
| fuzzy | `build_fuzzy_query()` | Typo-tolerant search |
| proximity | `build_proximity_query()` | NEAR/W/ADJ operators |
| range | `build_range_query()` | Numeric and date ranges |
| regex | `build_regex_query()` | Regular expression matching |

### 2. QueryCache

Redis-based caching system for query results.

**Location**: `app/services/elasticsearch/query_cache.py`

#### Key Features

- **Deterministic Key Generation**: SHA256 hash of normalized parameters
- **TTL Management**: Different TTLs per query type
- **Atomic Operations**: Thread-safe cache updates
- **Statistics Tracking**: Hit/miss rates per query type

#### Cache Key Format

```python
def _generate_cache_key(
    query_text: str,
    query_type: str,
    filters: Dict[str, str],
    page: int,
    page_size: int
) -> str:
    normalized = {
        "query": query_text.lower().strip(),
        "type": query_type,
        "filters": filters or {},
        "page": page,
        "size": page_size
    }
    key_string = json.dumps(normalized, sort_keys=True)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
    return f"search:{query_type}:{key_hash}"
```

### 3. QueryOptimizer

Automatic query optimization for better performance.

**Location**: `app/services/elasticsearch/query_optimizer.py`

#### Optimization Rules

##### Wildcard Optimizations
- Convert trailing wildcards to prefix queries
- Warn about expensive leading wildcards
- Suggest ngram tokenizers for substring matching

##### Boolean Optimizations
- Move term/range queries to filter context (caching)
- Remove empty clauses
- Flatten unnecessary nesting

##### Fuzzy Optimizations
- Add prefix_length for performance
- Limit max_expansions to prevent explosion

##### Regex Optimizations
- Convert simple patterns to prefix queries
- Add max_determinized_states limits
- Warn about expensive patterns

## Implementation Examples

### Adding a New Query Type

```python
# 1. Add to SearchQueryBuilder
@staticmethod
def build_new_query_type(
    query_text: str,
    filters: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Build query for new type."""

    # Parse query syntax
    parsed = NewTypeParser.parse(query_text)

    # Build Elasticsearch query
    es_query = {
        "query": {
            "bool": {
                "must": [
                    # Your query logic here
                ]
            }
        }
    }

    # Add filters if provided
    if filters:
        es_query["query"]["bool"]["filter"] = []
        # Add filter clauses

    return es_query

# 2. Update SearchService
elif query.query_type == "new_type":
    es_query = SearchQueryBuilder.build_new_query_type(
        query_text=query.q,
        filters=filters
    )

# 3. Add cache TTL
QueryCache.TTL_CONFIG["new_type"] = 1800  # 30 minutes

# 4. Add optimization rules
@staticmethod
def _optimize_new_type(query: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    notes = []
    optimized = query.copy()
    # Add optimization logic
    return optimized, notes
```

### Customizing Cache Behavior

```python
# Custom TTL based on query complexity
def get_ttl(query_type: str, query_text: str) -> int:
    base_ttl = QueryCache.TTL_CONFIG[query_type]

    # Reduce TTL for time-sensitive queries
    if "today" in query_text.lower() or "recent" in query_text.lower():
        return min(base_ttl, 300)  # 5 minutes max

    # Increase TTL for historical data
    if re.search(r'\d{4}-\d{2}-\d{2}', query_text):  # Date in query
        return base_ttl * 2

    return base_ttl
```

### Query Complexity Analysis

```python
# Analyze query before execution
complexity = QueryOptimizer.analyze_complexity(es_query)

if complexity["is_complex"]:
    # Log warning
    logger.warning(
        f"Complex query detected (score: {complexity['total_score']}): "
        f"{complexity['recommendations']}"
    )

    # Consider splitting or simplifying
    if complexity["total_score"] > 150:
        raise ValueError("Query too complex. Please simplify.")
```

## Testing Query Builders

### Unit Tests

```python
# tests/unit/services/elasticsearch/test_search_query_builder.py
import pytest
from app.services.elasticsearch.search_query_builder import SearchQueryBuilder

class TestBooleanQueryBuilder:
    def test_and_operator(self):
        query = SearchQueryBuilder.build_boolean_query(
            "diabetes AND hypertension"
        )

        assert "bool" in query["query"]
        assert "must" in query["query"]["bool"]
        assert len(query["query"]["bool"]["must"]) == 2

    def test_not_operator(self):
        query = SearchQueryBuilder.build_boolean_query(
            "diabetes NOT family"
        )

        assert "must_not" in query["query"]["bool"]
        assert any(
            "family" in str(clause)
            for clause in query["query"]["bool"]["must_not"]
        )
```

### Integration Tests

```python
# tests/integration/test_search_with_cache.py
import pytest
import redis.asyncio as redis
from app.services.elasticsearch.query_cache import QueryCache

@pytest.mark.asyncio
async def test_cache_hit_miss():
    # Setup
    redis_client = await redis.from_url("redis://localhost")
    cache = QueryCache(redis_client)

    # First call - cache miss
    result1 = await cache.get("diabetes", "standard")
    assert result1 is None

    # Set cache
    await cache.set("diabetes", "standard", {"results": []})

    # Second call - cache hit
    result2 = await cache.get("diabetes", "standard")
    assert result2 is not None
    assert result2["results"] == []

    # Cleanup
    await redis_client.close()
```

## Performance Considerations

### Query Type Selection

| Query Type | Use When | Performance Impact |
|------------|----------|-------------------|
| standard | General searches | Fast - uses match queries |
| boolean | Precise requirements | Fast - optimizable |
| wildcard | Pattern matching | Slow - avoid leading wildcards |
| fuzzy | Typo tolerance | Medium - limit fuzziness |
| proximity | Related terms | Medium - depends on slop |
| range | Filtering by values | Fast - uses inverted index |
| regex | Complex patterns | Very slow - use sparingly |

### Optimization Checklist

- [ ] Use filter context for non-scoring queries
- [ ] Add prefix_length to fuzzy queries
- [ ] Convert simple wildcards to prefix queries
- [ ] Limit regex complexity with max_determinized_states
- [ ] Cache frequently used queries
- [ ] Use source filtering to reduce payload size
- [ ] Enable doc_values for sorting/aggregations
- [ ] Use term queries for exact matches
- [ ] Avoid scripts in queries
- [ ] Profile slow queries with `"profile": true`

## Debugging

### Enable Query Logging

```python
# In search_service.py
if settings.DEBUG:
    logger.debug(f"Elasticsearch query: {json.dumps(es_query, indent=2)}")

    # Add explain parameter
    es_query["explain"] = True
```

### Query Profiling

```python
# Add profiling to slow queries
es_query["profile"] = True

response = await self.es.search(
    index=INDEX_NAME,
    body=es_query
)

if "profile" in response:
    logger.info(f"Query profile: {response['profile']}")
```

### Cache Debugging

```python
# Check cache stats
stats = await cache.get_stats()
logger.info(f"Cache hit rate: {stats['standard']['hit_rate']}%")

# Trace cache operations
if settings.DEBUG:
    logger.debug(f"Cache key: {cache_key}")
    logger.debug(f"Cache hit: {cached_result is not None}")
```

## Common Issues and Solutions

### Issue: Slow Wildcard Queries

**Problem**: Leading wildcards (*term) cause full index scan.

**Solution**:
```python
# Use ngram tokenizer in index mapping
{
    "settings": {
        "analysis": {
            "tokenizer": {
                "ngram_tokenizer": {
                    "type": "ngram",
                    "min_gram": 3,
                    "max_gram": 4
                }
            }
        }
    }
}
```

### Issue: Cache Invalidation

**Problem**: Stale data in cache after document updates.

**Solution**:
```python
# Invalidate related cache entries
async def invalidate_patient_cache(patient_id: str):
    pattern = f"search:*:*{patient_id}*"
    await cache.invalidate_pattern(pattern)
```

### Issue: Query Timeout

**Problem**: Complex queries timing out.

**Solution**:
```python
# Add timeout and terminate_after
es_query["timeout"] = "10s"
es_query["terminate_after"] = 10000  # Stop after 10k docs
```

## Best Practices

1. **Always validate queries** before execution
2. **Use appropriate query types** - don't use regex when wildcard suffices
3. **Cache strategically** - not all queries benefit from caching
4. **Monitor performance** - track slow queries and optimize
5. **Test edge cases** - empty queries, special characters, injection attempts
6. **Document query syntax** - provide clear examples for users
7. **Limit result size** - use pagination for large result sets
8. **Handle errors gracefully** - provide helpful error messages
9. **Profile before optimizing** - measure, don't guess
10. **Keep queries simple** - complex queries are hard to maintain

## Additional Resources

- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Redis Best Practices](https://redis.io/docs/management/optimization/)
- [Query Optimization Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)
- [Search API Documentation](./search-api-guide.md)

## Support

For questions or issues:
- Check the test suite for examples
- Review existing implementations in the codebase
- Open a GitHub issue with query details and performance metrics