# Search Feature Testing Guide

## Overview

This guide covers testing strategies and examples for the advanced search functionality in Clinical Care Tools. It includes unit tests, integration tests, and end-to-end test scenarios.

## Test Structure

```
tests/
├── unit/
│   ├── services/
│   │   ├── elasticsearch/
│   │   │   ├── test_search_query_builder.py
│   │   │   ├── test_query_cache.py
│   │   │   └── test_query_optimizer.py
│   │   └── test_search_service.py
│   └── api/
│       └── test_search_endpoints.py
├── integration/
│   ├── test_search_with_cache.py
│   ├── test_query_optimization.py
│   └── test_search_analytics.py
└── e2e/
    └── test_search_workflows.py
```

## Unit Tests

### Testing Query Builders

```python
# tests/unit/services/elasticsearch/test_search_query_builder.py
import pytest
from app.services.elasticsearch.search_query_builder import SearchQueryBuilder

class TestStandardQueryBuilder:
    """Test standard multi-field search queries."""

    def test_simple_query(self):
        """Test basic keyword search."""
        query = SearchQueryBuilder.build_query(
            query_text="diabetes",
            fields=["title", "content"]
        )

        assert query["query"]["multi_match"]["query"] == "diabetes"
        assert query["query"]["multi_match"]["fields"] == ["title^2", "content"]

    def test_query_with_filters(self):
        """Test query with document type filter."""
        query = SearchQueryBuilder.build_query(
            query_text="hypertension",
            document_type="clinical_note"
        )

        filters = query["query"]["bool"]["filter"]
        assert any(f["term"]["document_type"] == "clinical_note" for f in filters)

class TestBooleanQueryBuilder:
    """Test boolean logic query parsing."""

    @pytest.mark.parametrize("query_text,expected_must,expected_must_not", [
        ("diabetes AND hypertension", ["diabetes", "hypertension"], []),
        ("diabetes NOT family", ["diabetes"], ["family"]),
        ("(diabetes OR obesity) AND exercise", None, []),  # Complex
    ])
    def test_boolean_operators(self, query_text, expected_must, expected_must_not):
        """Test AND, OR, NOT operators."""
        query = SearchQueryBuilder.build_boolean_query(query_text)

        if expected_must is not None:
            must_clauses = query["query"]["bool"].get("must", [])
            for term in expected_must:
                assert any(term in str(clause) for clause in must_clauses)

        if expected_must_not:
            must_not_clauses = query["query"]["bool"].get("must_not", [])
            for term in expected_must_not:
                assert any(term in str(clause) for clause in must_not_clauses)

class TestWildcardQueryBuilder:
    """Test wildcard pattern matching."""

    def test_trailing_wildcard(self):
        """Test optimization of trailing wildcards."""
        query = SearchQueryBuilder.build_wildcard_query("diab*")

        # Should be optimized to prefix query
        assert "prefix" in str(query) or "wildcard" in str(query)

    def test_leading_wildcard_warning(self):
        """Test that leading wildcards generate warnings."""
        query = SearchQueryBuilder.build_wildcard_query("*betes")

        # Query should still be built but may have warnings
        assert "wildcard" in str(query)

class TestFuzzyQueryBuilder:
    """Test fuzzy (typo-tolerant) queries."""

    def test_auto_fuzziness(self):
        """Test automatic fuzziness detection."""
        query = SearchQueryBuilder.build_fuzzy_query("diabets")

        assert "fuzzy" in str(query) or "fuzziness" in query["query"]["multi_match"]

    def test_explicit_fuzziness(self):
        """Test explicit fuzziness syntax."""
        query = SearchQueryBuilder.build_fuzzy_query("diabets~2")

        # Should have fuzziness of 2
        assert any("fuzziness" in str(clause) for clause in [query])

class TestProximityQueryBuilder:
    """Test proximity/span queries."""

    def test_near_operator(self):
        """Test NEAR operator for proximity search."""
        query = SearchQueryBuilder.build_proximity_query("heart NEAR failure")

        assert "span_near" in str(query) or "match_phrase" in str(query)

    def test_within_operator(self):
        """Test W/n operator for word distance."""
        query = SearchQueryBuilder.build_proximity_query("blood W/2 pressure")

        # Should specify slop of 2
        assert "slop" in str(query)

class TestRangeQueryBuilder:
    """Test range queries for numeric and date fields."""

    def test_numeric_range(self):
        """Test numeric range syntax."""
        query = SearchQueryBuilder.build_range_query("age:[18 TO 65]")

        assert "range" in str(query)
        assert "gte" in str(query) or "lte" in str(query)

    def test_date_range(self):
        """Test date range syntax."""
        query = SearchQueryBuilder.build_range_query(
            "date:[2023-01-01 TO 2023-12-31]"
        )

        assert "range" in str(query)

    def test_comparison_operators(self):
        """Test >, <, >=, <= operators."""
        query = SearchQueryBuilder.build_range_query("bp_systolic:>140")

        assert "range" in str(query)
        assert "gt" in str(query) or "gte" in str(query)

class TestRegexQueryBuilder:
    """Test regular expression queries."""

    def test_simple_regex(self):
        """Test basic regex pattern."""
        query = SearchQueryBuilder.build_regex_query("/diabet.*/")

        assert "regexp" in str(query)

    def test_complex_regex(self):
        """Test complex regex with groups."""
        query = SearchQueryBuilder.build_regex_query(
            "/heart.+(failure|disease)/"
        )

        assert "regexp" in str(query)

    def test_regex_safety_limits(self):
        """Test that safety limits are applied."""
        query = SearchQueryBuilder.build_regex_query("/.*complex.*/")

        # Should have max_determinized_states
        assert "max_determinized_states" in str(query)
```

### Testing Query Cache

```python
# tests/unit/services/elasticsearch/test_query_cache.py
import pytest
import json
import hashlib
from unittest.mock import AsyncMock, MagicMock
from app.services.elasticsearch.query_cache import QueryCache

class TestQueryCache:
    """Test Redis-based query caching."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()
        redis.hincrby = AsyncMock()
        return redis

    @pytest.fixture
    def cache(self, mock_redis):
        """Create QueryCache instance with mock Redis."""
        return QueryCache(mock_redis)

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache, mock_redis):
        """Test cache miss returns None."""
        result = await cache.get("diabetes", "standard")

        assert result is None
        mock_redis.get.assert_called_once()
        mock_redis.hincrby.assert_called_with("cache:stats:standard", "misses", 1)

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache, mock_redis):
        """Test cache hit returns stored data."""
        cached_data = {"results": [{"id": "1"}]}
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        result = await cache.get("diabetes", "standard")

        assert result == cached_data
        mock_redis.hincrby.assert_called_with("cache:stats:standard", "hits", 1)

    @pytest.mark.asyncio
    async def test_cache_set(self, cache, mock_redis):
        """Test setting cache with TTL."""
        data = {"results": []}

        await cache.set("diabetes", "standard", data)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 3600  # TTL for standard queries
        mock_redis.hincrby.assert_called_with("cache:stats:standard", "sets", 1)

    def test_cache_key_generation(self, cache):
        """Test deterministic cache key generation."""
        key1 = cache._generate_cache_key(
            "diabetes", "standard", {}, 1, 20
        )
        key2 = cache._generate_cache_key(
            "diabetes", "standard", {}, 1, 20
        )

        assert key1 == key2  # Same inputs = same key

        key3 = cache._generate_cache_key(
            "DIABETES", "standard", {}, 1, 20
        )
        key4 = cache._generate_cache_key(
            "diabetes ", "standard", {}, 1, 20
        )

        assert key3 == key1  # Case insensitive
        assert key4 == key1  # Whitespace normalized

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache, mock_redis):
        """Test pattern-based cache invalidation."""
        mock_redis.scan_iter = AsyncMock(return_value=['key1', 'key2'])
        mock_redis.delete = AsyncMock()

        count = await cache.invalidate_pattern("wildcard:*")

        assert count == 2
        mock_redis.delete.assert_called_once_with('key1', 'key2')
```

### Testing Query Optimizer

```python
# tests/unit/services/elasticsearch/test_query_optimizer.py
import pytest
from app.services.elasticsearch.query_optimizer import QueryOptimizer

class TestQueryOptimizer:
    """Test query optimization rules."""

    def test_wildcard_optimization(self):
        """Test wildcard to prefix conversion."""
        query = {
            "query": {
                "wildcard": {
                    "content": "diabetes*"
                }
            }
        }

        optimized, notes = QueryOptimizer.optimize_query(query, "wildcard")

        # Should convert to prefix query
        assert any("prefix" in note.lower() or "optimized" in note.lower()
                  for note in notes)

    def test_leading_wildcard_warning(self):
        """Test warning for expensive leading wildcards."""
        query = {
            "query": {
                "wildcard": {
                    "content": "*betes"
                }
            }
        }

        optimized, notes = QueryOptimizer.optimize_query(query, "wildcard")

        assert any("warning" in note.lower() for note in notes)
        assert any("leading wildcard" in note.lower() for note in notes)

    def test_boolean_filter_optimization(self):
        """Test moving non-scoring queries to filter context."""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"content": "diabetes"}},
                        {"term": {"document_type": "note"}},
                        {"range": {"date": {"gte": "2023-01-01"}}}
                    ]
                }
            }
        }

        optimized, notes = QueryOptimizer.optimize_query(query, "boolean")

        # Term and range should move to filter
        assert "filter" in optimized["query"]["bool"]
        assert any("filter context" in note.lower() for note in notes)

    def test_fuzzy_safety_limits(self):
        """Test that fuzzy queries get safety limits."""
        query = {
            "query": {
                "fuzzy": {
                    "content": {
                        "value": "diabetes"
                    }
                }
            }
        }

        optimized, notes = QueryOptimizer.optimize_query(query, "fuzzy")

        # Should add prefix_length and max_expansions
        fuzzy_params = optimized["query"]["fuzzy"]["content"]
        assert "prefix_length" in fuzzy_params
        assert "max_expansions" in fuzzy_params

    def test_complexity_analysis(self):
        """Test query complexity scoring."""
        complex_query = {
            "query": {
                "bool": {
                    "must": [
                        {"regexp": {"field1": ".*test.*"}},
                        {"wildcard": {"field2": "*value*"}},
                        {"fuzzy": {"field3": "term"}}
                    ]
                }
            }
        }

        analysis = QueryOptimizer.analyze_complexity(complex_query)

        assert analysis["total_score"] > 0
        assert "regexp" in analysis["breakdown"]
        assert "recommendations" in analysis
```

## Integration Tests

### Testing Search with Cache

```python
# tests/integration/test_search_with_cache.py
import pytest
import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from app.services.elasticsearch.search_service import SearchService
from app.services.elasticsearch.search_query_builder import SearchQueryBuilder

@pytest.mark.integration
class TestSearchWithCache:
    """Test search service with real cache integration."""

    @pytest.fixture
    async def redis_client(self):
        """Create real Redis client."""
        client = await redis.from_url("redis://localhost:6379/1")
        yield client
        await client.flushdb()  # Clean test database
        await client.close()

    @pytest.fixture
    async def es_client(self):
        """Create real Elasticsearch client."""
        client = AsyncElasticsearch(["http://localhost:9200"])
        yield client
        await client.close()

    @pytest.fixture
    def search_service(self, es_client, redis_client):
        """Create search service with real dependencies."""
        return SearchService(es_client, redis_client)

    @pytest.mark.asyncio
    async def test_cache_flow(self, search_service, redis_client):
        """Test complete cache flow: miss, set, hit."""
        query = SearchQuery(
            q="diabetes",
            query_type="standard",
            page=1,
            page_size=20
        )

        # First search - cache miss
        result1 = await search_service.search(query)
        assert not result1.get("from_cache", False)

        # Second search - cache hit
        result2 = await search_service.search(query)
        assert result2.get("from_cache", False)

        # Results should be identical
        assert result1["results"] == result2["results"]

    @pytest.mark.asyncio
    async def test_different_query_types_cached_separately(
        self, search_service, redis_client
    ):
        """Test that different query types have separate cache entries."""
        # Same text, different query types
        queries = [
            SearchQuery(q="heart", query_type="standard"),
            SearchQuery(q="heart", query_type="fuzzy"),
            SearchQuery(q="heart", query_type="wildcard")
        ]

        results = []
        for query in queries:
            result = await search_service.search(query)
            results.append(result)

        # All should be cache misses (different types)
        assert all(not r.get("from_cache", False) for r in results)

        # Cache keys should be different
        keys = await redis_client.keys("search:*")
        assert len(keys) == 3
```

### Testing Query Optimization

```python
# tests/integration/test_query_optimization.py
import pytest
import time
from elasticsearch import AsyncElasticsearch
from app.services.elasticsearch.query_optimizer import QueryOptimizer

@pytest.mark.integration
class TestQueryOptimizationPerformance:
    """Test that optimizations actually improve performance."""

    @pytest.fixture
    async def es_client(self):
        """Create Elasticsearch client."""
        client = AsyncElasticsearch(["http://localhost:9200"])
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_wildcard_optimization_performance(self, es_client):
        """Test that prefix queries are faster than wildcards."""
        # Unoptimized wildcard query
        wildcard_query = {
            "query": {"wildcard": {"content": "diabet*"}},
            "size": 100
        }

        # Optimized to prefix
        prefix_query = {
            "query": {"prefix": {"content": "diabet"}},
            "size": 100
        }

        # Time wildcard query
        start = time.time()
        await es_client.search(index="test_index", body=wildcard_query)
        wildcard_time = time.time() - start

        # Time prefix query
        start = time.time()
        await es_client.search(index="test_index", body=prefix_query)
        prefix_time = time.time() - start

        # Prefix should be faster (or at least not slower)
        assert prefix_time <= wildcard_time * 1.1  # Allow 10% variance

    @pytest.mark.asyncio
    async def test_filter_context_caching(self, es_client):
        """Test that filter context queries are cached."""
        # Query with filters in must (not cached)
        must_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"document_type": "note"}},
                        {"range": {"date": {"gte": "2023-01-01"}}}
                    ]
                }
            }
        }

        # Same query with filters in filter context (cached)
        filter_query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"document_type": "note"}},
                        {"range": {"date": {"gte": "2023-01-01"}}}
                    ]
                }
            }
        }

        # Run each query twice to test caching
        times = []
        for query in [must_query, filter_query]:
            for _ in range(2):
                start = time.time()
                await es_client.search(index="test_index", body=query)
                times.append(time.time() - start)

        # Second run of filter query should be faster (cached)
        assert times[3] < times[2] * 0.8  # At least 20% faster
```

## End-to-End Tests

### Testing Complete Search Workflows

```python
# tests/e2e/test_search_workflows.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.e2e
class TestSearchWorkflows:
    """Test complete search workflows from API to results."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": "test_pass"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_standard_search_workflow(self, client, auth_headers):
        """Test complete standard search workflow."""
        # 1. Get query help
        response = client.get(
            "/api/v1/search/query-help?query_type=standard",
            headers=auth_headers
        )
        assert response.status_code == 200
        help_info = response.json()
        assert "examples" in help_info

        # 2. Validate query
        response = client.post(
            "/api/v1/search/validate?q=diabetes&query_type=standard",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True

        # 3. Get suggestions
        response = client.get(
            "/api/v1/search/suggest?q=diab",
            headers=auth_headers
        )
        assert response.status_code == 200
        suggestions = response.json()["suggestions"]
        assert "diabetes" in suggestions

        # 4. Execute search
        response = client.get(
            "/api/v1/search?q=diabetes&query_type=standard",
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()
        assert "results" in results
        assert "facets" in results
        assert "total_results" in results

    def test_advanced_query_types(self, client, auth_headers):
        """Test all advanced query types."""
        test_cases = [
            ("boolean", "diabetes AND hypertension"),
            ("wildcard", "diab*"),
            ("fuzzy", "diabets~"),
            ("proximity", "heart NEAR failure"),
            ("range", "age:[50 TO 70]"),
            ("regex", "/diabet.*/")
        ]

        for query_type, query_text in test_cases:
            response = client.get(
                f"/api/v1/search?q={query_text}&query_type={query_type}",
                headers=auth_headers
            )
            assert response.status_code == 200, f"Failed for {query_type}"
            assert "results" in response.json()

    def test_pagination_workflow(self, client, auth_headers):
        """Test pagination through results."""
        # First page
        response = client.get(
            "/api/v1/search?q=patient&page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        page1 = response.json()
        assert page1["page"] == 1
        assert len(page1["results"]) <= 10

        # Second page
        response = client.get(
            "/api/v1/search?q=patient&page=2&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        page2 = response.json()
        assert page2["page"] == 2

        # Results should be different
        if page1["results"] and page2["results"]:
            assert page1["results"][0]["document_id"] != \
                   page2["results"][0]["document_id"]

    def test_error_handling(self, client, auth_headers):
        """Test error handling for invalid queries."""
        # Invalid regex
        response = client.get(
            "/api/v1/search?q=/[invalid&query_type=regex",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "error" in response.json()

        # Invalid boolean syntax
        response = client.get(
            "/api/v1/search?q=diabetes AND&query_type=boolean",
            headers=auth_headers
        )
        assert response.status_code == 400

        # Invalid date range
        response = client.get(
            "/api/v1/search?q=date:[invalid]&query_type=range",
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_cache_management(self, client, auth_headers):
        """Test cache statistics and invalidation (admin only)."""
        # Get admin token
        admin_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin_pass"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Get cache stats
        response = client.get(
            "/api/v1/search/cache/stats",
            headers=admin_headers
        )
        assert response.status_code == 200
        stats = response.json()
        assert "cache_stats" in stats

        # Invalidate cache
        response = client.post(
            "/api/v1/search/cache/invalidate?pattern=standard:*",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "invalidated" in response.json()
```

## Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import random

class SearchUser(HttpUser):
    """Simulate search API usage patterns."""
    wait_time = between(1, 3)

    def on_start(self):
        """Login and get auth token."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": "test_pass"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def standard_search(self):
        """Most common: standard searches."""
        queries = ["diabetes", "hypertension", "cancer", "heart disease"]
        query = random.choice(queries)
        self.client.get(
            f"/api/v1/search?q={query}&query_type=standard",
            headers=self.headers
        )

    @task(2)
    def boolean_search(self):
        """Common: boolean searches."""
        queries = [
            "diabetes AND hypertension",
            "cancer NOT lung",
            "heart OR cardiac"
        ]
        query = random.choice(queries)
        self.client.get(
            f"/api/v1/search?q={query}&query_type=boolean",
            headers=self.headers
        )

    @task(1)
    def wildcard_search(self):
        """Less common: wildcard searches."""
        queries = ["diab*", "card*", "*itis"]
        query = random.choice(queries)
        self.client.get(
            f"/api/v1/search?q={query}&query_type=wildcard",
            headers=self.headers
        )

    @task(1)
    def fuzzy_search(self):
        """Less common: fuzzy searches."""
        queries = ["diabets~", "hyprtension~", "cancr~"]
        query = random.choice(queries)
        self.client.get(
            f"/api/v1/search?q={query}&query_type=fuzzy",
            headers=self.headers
        )
```

### Running Performance Tests

```bash
# Run load test with 100 users
locust -f tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users=100 \
       --spawn-rate=10 \
       --time=5m

# Run with headless mode for CI/CD
locust -f tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users=100 \
       --spawn-rate=10 \
       --time=5m \
       --headless \
       --html=report.html
```

## Test Data Setup

### Creating Test Indices

```python
# tests/fixtures/create_test_indices.py
import asyncio
from elasticsearch import AsyncElasticsearch

async def create_test_index():
    """Create test index with sample data."""
    es = AsyncElasticsearch(["http://localhost:9200"])

    # Create index with mapping
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "document_type": {"type": "keyword"},
                "date": {"type": "date"},
                "author": {"type": "keyword"},
                "department": {"type": "keyword"}
            }
        }
    }

    await es.indices.create(index="test_index", body=mapping)

    # Add sample documents
    documents = [
        {
            "title": "Diabetes Management",
            "content": "Patient with type 2 diabetes...",
            "document_type": "clinical_note",
            "date": "2023-01-15",
            "author": "Dr. Smith",
            "department": "Endocrinology"
        },
        # Add more test documents...
    ]

    for doc in documents:
        await es.index(index="test_index", body=doc)

    await es.close()

if __name__ == "__main__":
    asyncio.run(create_test_index())
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test-search.yml
name: Search Feature Tests

on:
  pull_request:
    paths:
      - 'backend/app/services/elasticsearch/**'
      - 'backend/app/api/v1/search.py'
      - 'backend/tests/**'

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      elasticsearch:
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        env:
          discovery.type: single-node
          xpack.security.enabled: false
        ports:
          - 9200:9200

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-test.txt

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=app/services/elasticsearch

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration -v

      - name: Run E2E tests
        run: |
          cd backend
          pytest tests/e2e -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Testing Best Practices

1. **Test Pyramid**: Follow 60% unit, 30% integration, 10% E2E distribution
2. **Mock External Services**: Use mocks for Redis/Elasticsearch in unit tests
3. **Test Data Isolation**: Each test should create and clean its own data
4. **Performance Benchmarks**: Set and test against performance targets
5. **Error Scenarios**: Test error handling and edge cases
6. **Security Testing**: Include tests for injection attacks and auth
7. **Accessibility Testing**: Test keyboard navigation and screen readers
8. **Cache Testing**: Verify cache hit/miss behavior
9. **Concurrent Testing**: Test race conditions and concurrent access
10. **Documentation**: Keep test documentation up-to-date

## Troubleshooting

### Common Test Issues

| Issue | Solution |
|-------|----------|
| Redis connection refused | Ensure Redis is running: `docker-compose up redis` |
| Elasticsearch timeout | Increase timeout or check ES health |
| Flaky cache tests | Clear cache between tests |
| Slow integration tests | Use test containers or mock services |
| Permission errors | Run with proper test user permissions |

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Elasticsearch Testing Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/testing.html)
- [Redis Testing Best Practices](https://redis.io/docs/manual/patterns/testing/)
- [Locust Performance Testing](https://docs.locust.io/)