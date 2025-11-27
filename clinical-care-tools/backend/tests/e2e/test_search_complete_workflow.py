"""End-to-end tests for complete search workflows.

Tests the entire search feature from API to results, including:
- All 7 query types
- Caching behavior
- Query validation
- Error handling
- Performance requirements
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.main import app
from app.core.config import settings
from tests.factories import UserFactory, DocumentFactory


class TestSearchE2E:
    """End-to-end tests for search functionality."""

    @pytest.fixture
    async def auth_headers(self, async_client: AsyncClient) -> Dict[str, str]:
        """Create authenticated user and return headers."""
        # Register user
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "test_searcher",
                "email": "searcher@test.com",
                "full_name": "Test Searcher",
                "password": "TestPass123!",
                "role": "clinician"
            }
        )
        assert response.status_code == 201

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "test_searcher",
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def admin_headers(self, async_client: AsyncClient) -> Dict[str, str]:
        """Create admin user and return headers."""
        # Register admin
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "admin_user",
                "email": "admin@test.com",
                "full_name": "Admin User",
                "password": "AdminPass123!",
                "role": "admin"
            }
        )
        assert response.status_code == 201

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin_user",
                "password": "AdminPass123!"
            }
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def sample_documents(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Create sample documents for testing."""
        documents = [
            {
                "title": "Diabetes Management Plan",
                "content": "Patient presents with type 2 diabetes mellitus and hypertension. "
                          "Current HbA1c is 8.2%, indicating poor glycemic control.",
                "document_type": "clinical_note",
                "author": "Dr. Smith",
                "department": "Endocrinology",
                "date": "2023-06-15"
            },
            {
                "title": "Cardiology Consultation",
                "content": "Patient has history of atrial fibrillation. "
                          "Echocardiogram shows left ventricular hypertrophy.",
                "document_type": "consultation",
                "author": "Dr. Johnson",
                "department": "Cardiology",
                "date": "2023-06-20"
            },
            {
                "title": "Emergency Department Visit",
                "content": "Patient denies chest pain but reports dyspnea on exertion. "
                          "Family history of cardiac disease noted.",
                "document_type": "emergency_note",
                "author": "Dr. Williams",
                "department": "Emergency",
                "date": "2023-07-01"
            }
        ]

        # Create documents in database
        created_docs = []
        for doc_data in documents:
            doc = await DocumentFactory.create(**doc_data)
            created_docs.append(doc)

        await db.commit()
        return created_docs

    @pytest.mark.asyncio
    async def test_standard_search_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test complete standard search workflow."""
        # 1. Get query help
        response = await async_client.get(
            "/api/v1/search/query-help?query_type=standard",
            headers=auth_headers
        )
        assert response.status_code == 200
        help_info = response.json()
        assert help_info["query_type"] == "standard"
        assert "examples" in help_info

        # 2. Validate query
        response = await async_client.post(
            "/api/v1/search/validate",
            params={"q": "diabetes", "query_type": "standard"},
            headers=auth_headers
        )
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] is True

        # 3. Get suggestions
        response = await async_client.get(
            "/api/v1/search/suggest",
            params={"q": "diab"},
            headers=auth_headers
        )
        assert response.status_code == 200
        suggestions = response.json()
        assert "suggestions" in suggestions
        assert any("diabetes" in s.lower() for s in suggestions["suggestions"])

        # 4. Execute search
        response = await async_client.get(
            "/api/v1/search",
            params={"q": "diabetes", "query_type": "standard"},
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()
        assert "results" in results
        assert "facets" in results
        assert results["total_results"] > 0
        assert results["query"] == "diabetes"

        # 5. Verify performance
        assert results["execution_time_ms"] < 500  # Must be under 500ms

    @pytest.mark.asyncio
    async def test_all_query_types(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test all 7 query types work correctly."""
        test_cases = [
            ("standard", "diabetes"),
            ("boolean", "diabetes AND hypertension"),
            ("wildcard", "diab*"),
            ("fuzzy", "diabets~"),
            ("proximity", "patient NEAR diabetes"),
            ("range", "date:[2023-01-01 TO 2023-12-31]"),
            ("regex", "/diabet.*/")
        ]

        for query_type, query_text in test_cases:
            # Validate query first
            response = await async_client.post(
                "/api/v1/search/validate",
                params={"q": query_text, "query_type": query_type},
                headers=auth_headers
            )
            assert response.status_code == 200, f"Validation failed for {query_type}"
            assert response.json()["valid"] is True

            # Execute search
            response = await async_client.get(
                "/api/v1/search",
                params={"q": query_text, "query_type": query_type},
                headers=auth_headers
            )
            assert response.status_code == 200, f"Search failed for {query_type}"
            results = response.json()
            assert "results" in results
            assert "execution_time_ms" in results

    @pytest.mark.asyncio
    async def test_caching_behavior(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test that caching improves performance."""
        query_params = {
            "q": "diabetes",
            "query_type": "standard",
            "page": 1,
            "page_size": 20
        }

        # First search - cache miss
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/search",
            params=query_params,
            headers=auth_headers
        )
        assert response.status_code == 200
        first_results = response.json()
        first_time = time.time() - start_time

        # Second search - cache hit
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/search",
            params=query_params,
            headers=auth_headers
        )
        assert response.status_code == 200
        second_results = response.json()
        second_time = time.time() - start_time

        # Cache hit should be faster
        assert second_time < first_time * 0.5  # At least 50% faster

        # Results should be identical
        assert first_results["total_results"] == second_results["total_results"]
        assert len(first_results["results"]) == len(second_results["results"])

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test pagination through search results."""
        # First page
        response = await async_client.get(
            "/api/v1/search",
            params={
                "q": "patient",
                "page": 1,
                "page_size": 2
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        page1 = response.json()
        assert page1["page"] == 1
        assert page1["page_size"] == 2
        assert len(page1["results"]) <= 2

        # Second page
        response = await async_client.get(
            "/api/v1/search",
            params={
                "q": "patient",
                "page": 2,
                "page_size": 2
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        page2 = response.json()
        assert page2["page"] == 2

        # Results should be different if both pages have results
        if page1["results"] and page2["results"]:
            page1_ids = {r["document_id"] for r in page1["results"]}
            page2_ids = {r["document_id"] for r in page2["results"]}
            assert page1_ids.isdisjoint(page2_ids)  # No overlap

    @pytest.mark.asyncio
    async def test_filtering(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test search with filters."""
        # Filter by document type
        response = await async_client.get(
            "/api/v1/search",
            params={
                "q": "patient",
                "document_type": "clinical_note"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()
        for result in results["results"]:
            assert result["document_type"] == "clinical_note"

        # Filter by department
        response = await async_client.get(
            "/api/v1/search",
            params={
                "q": "patient",
                "department": "Cardiology"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()
        for result in results["results"]:
            assert result["department"] == "Cardiology"

        # Filter by date range
        response = await async_client.get(
            "/api/v1/search",
            params={
                "q": "patient",
                "date_from": "2023-06-01",
                "date_to": "2023-06-30"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()
        for result in results["results"]:
            assert "2023-06" in result["date"]

    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test error handling for invalid queries."""
        error_cases = [
            # Invalid boolean syntax
            {
                "q": "diabetes AND",
                "query_type": "boolean",
                "expected_status": 400,
                "expected_error": "Incomplete AND expression"
            },
            # Invalid regex
            {
                "q": "/[invalid/",
                "query_type": "regex",
                "expected_status": 400,
                "expected_error": "Invalid regex"
            },
            # Invalid date range
            {
                "q": "date:[invalid]",
                "query_type": "range",
                "expected_status": 400,
                "expected_error": "Invalid date"
            },
            # Query too short
            {
                "q": "",
                "query_type": "standard",
                "expected_status": 422,
                "expected_error": "min_length"
            }
        ]

        for case in error_cases:
            response = await async_client.get(
                "/api/v1/search",
                params={
                    "q": case["q"],
                    "query_type": case["query_type"]
                },
                headers=auth_headers
            )
            assert response.status_code == case["expected_status"], \
                f"Wrong status for {case['q']}"

            if case["expected_status"] != 422:  # Validation error
                error = response.json()
                assert case["expected_error"].lower() in str(error).lower()

    @pytest.mark.asyncio
    async def test_query_validation(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test query validation endpoint."""
        # Valid query
        response = await async_client.post(
            "/api/v1/search/validate",
            params={
                "q": "diabetes AND hypertension",
                "query_type": "boolean"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] is True
        assert "elasticsearch_query" in validation

        # Invalid query
        response = await async_client.post(
            "/api/v1/search/validate",
            params={
                "q": "diabetes AND",
                "query_type": "boolean"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] is False
        assert "error" in validation
        assert "suggestion" in validation

    @pytest.mark.asyncio
    async def test_cache_management(
        self,
        async_client: AsyncClient,
        admin_headers: Dict[str, str],
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test cache statistics and invalidation (admin only)."""
        # Execute some searches to populate cache
        queries = [
            ("diabetes", "standard"),
            ("hypertension", "standard"),
            ("cardiac", "fuzzy"),
            ("diab*", "wildcard")
        ]

        for q, query_type in queries:
            await async_client.get(
                "/api/v1/search",
                params={"q": q, "query_type": query_type},
                headers=auth_headers
            )

        # Get cache stats (admin only)
        response = await async_client.get(
            "/api/v1/search/cache/stats",
            headers=admin_headers
        )
        assert response.status_code == 200
        stats = response.json()
        assert "cache_stats" in stats
        assert "standard" in stats["cache_stats"]
        assert stats["cache_stats"]["standard"]["sets"] > 0

        # Non-admin cannot access cache stats
        response = await async_client.get(
            "/api/v1/search/cache/stats",
            headers=auth_headers
        )
        assert response.status_code == 403

        # Invalidate cache (admin only)
        response = await async_client.post(
            "/api/v1/search/cache/invalidate",
            params={"pattern": "standard:*"},
            headers=admin_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert "invalidated" in result
        assert result["invalidated"] >= 2  # At least the 2 standard queries

        # Non-admin cannot invalidate cache
        response = await async_client.post(
            "/api/v1/search/cache/invalidate",
            params={"pattern": "standard:*"},
            headers=auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_faceted_search(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test faceted search aggregations."""
        response = await async_client.get(
            "/api/v1/search",
            params={"q": "patient"},
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()

        # Check facets are present
        assert "facets" in results
        facets = results["facets"]

        # Document type facet
        if "document_type" in facets:
            assert isinstance(facets["document_type"], dict)
            assert sum(facets["document_type"].values()) > 0

        # Department facet
        if "department" in facets:
            assert isinstance(facets["department"], dict)
            assert sum(facets["department"].values()) > 0

        # Date histogram facet
        if "date_histogram" in facets:
            assert isinstance(facets["date_histogram"], dict)

    @pytest.mark.asyncio
    async def test_highlighting(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test search result highlighting."""
        response = await async_client.get(
            "/api/v1/search",
            params={"q": "diabetes"},
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()

        # Check highlights in results
        for result in results["results"]:
            if result["highlights"]:
                # Highlights should contain the search term
                assert any(
                    "diabetes" in highlight.lower() or
                    "<em>diabetes</em>" in highlight.lower()
                    for highlight in result["highlights"]
                )

    @pytest.mark.asyncio
    async def test_performance_requirements(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test that searches meet performance requirements."""
        query_types = [
            ("standard", "diabetes", 500),
            ("boolean", "diabetes AND hypertension", 500),
            ("wildcard", "diab*", 800),  # Wildcard allowed more time
            ("fuzzy", "diabets~", 600),
            ("proximity", "patient NEAR diabetes", 600),
            ("range", "date:[2023-01-01 TO 2023-12-31]", 500)
        ]

        for query_type, query, max_time_ms in query_types:
            response = await async_client.get(
                "/api/v1/search",
                params={"q": query, "query_type": query_type},
                headers=auth_headers
            )
            assert response.status_code == 200
            results = response.json()

            # Check execution time
            assert results["execution_time_ms"] < max_time_ms, \
                f"{query_type} query took {results['execution_time_ms']}ms, max is {max_time_ms}ms"

    @pytest.mark.asyncio
    async def test_concurrent_searches(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test that concurrent searches work correctly."""
        queries = [
            ("diabetes", "standard"),
            ("hypertension", "fuzzy"),
            ("cardiac", "wildcard"),
            ("patient NEAR history", "proximity"),
            ("date:[2023-01-01 TO 2023-12-31]", "range")
        ]

        # Execute searches concurrently
        async def search(q: str, query_type: str):
            response = await async_client.get(
                "/api/v1/search",
                params={"q": q, "query_type": query_type},
                headers=auth_headers
            )
            return response

        tasks = [search(q, qt) for q, qt in queries]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            results = response.json()
            assert "results" in results

    @pytest.mark.asyncio
    async def test_search_with_special_characters(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test handling of special characters in queries."""
        special_queries = [
            "patient's",  # Apostrophe
            "HbA1c",  # Mixed case with number
            "type-2",  # Hyphen
            "8.2%",  # Percentage
            "patient & diabetes",  # Ampersand
        ]

        for query in special_queries:
            response = await async_client.get(
                "/api/v1/search",
                params={"q": query},
                headers=auth_headers
            )
            # Should not crash, may return 0 results
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_empty_results_handling(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test handling of queries that return no results."""
        response = await async_client.get(
            "/api/v1/search",
            params={"q": "nonexistentterm12345"},
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()
        assert results["total_results"] == 0
        assert results["results"] == []
        assert results["total_pages"] == 0


class TestSearchPerformance:
    """Performance-focused end-to-end tests."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_result_set(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        db: AsyncSession
    ):
        """Test search with large number of documents."""
        # Create 100 documents
        for i in range(100):
            await DocumentFactory.create(
                title=f"Document {i}",
                content=f"Patient {i} with various conditions",
                document_type="clinical_note"
            )
        await db.commit()

        # Search should still be fast
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/search",
            params={"q": "patient", "page_size": 50},
            headers=auth_headers
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_effectiveness(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_documents: List[Dict[str, Any]]
    ):
        """Test that cache significantly improves performance."""
        query_params = {"q": "diabetes", "query_type": "standard"}

        # Warm up cache
        await async_client.get(
            "/api/v1/search",
            params=query_params,
            headers=auth_headers
        )

        # Measure 10 cached requests
        cached_times = []
        for _ in range(10):
            start = time.time()
            response = await async_client.get(
                "/api/v1/search",
                params=query_params,
                headers=auth_headers
            )
            cached_times.append(time.time() - start)
            assert response.status_code == 200

        # Average cached response should be under 200ms
        avg_cached_time = sum(cached_times) / len(cached_times)
        assert avg_cached_time < 0.2  # 200ms

        # Clear cache and measure uncached
        redis_client = await redis.from_url(settings.REDIS_URL)
        await redis_client.flushdb()
        await redis_client.close()

        # Measure uncached request
        start = time.time()
        response = await async_client.get(
            "/api/v1/search",
            params=query_params,
            headers=auth_headers
        )
        uncached_time = time.time() - start
        assert response.status_code == 200

        # Cached should be at least 50% faster
        assert avg_cached_time < uncached_time * 0.5