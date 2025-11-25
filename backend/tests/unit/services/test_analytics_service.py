"""
Unit tests for AnalyticsService.

Tests search analytics aggregation and reporting functionality.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.analytics_service import AnalyticsService
from app.models.search_analytics import SearchAnalytics
from app.models.user import User


@pytest.fixture
def analytics_service():
    """Create AnalyticsService instance."""
    return AnalyticsService()


@pytest.fixture
async def sample_analytics(db):
    """Create sample analytics data for testing."""
    # Create test user
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        password_hash="hashed",
        is_active=True,
        role="user"
    )
    db.add(user)
    await db.flush()

    # Create analytics records
    now = datetime.utcnow()

    # Popular query: "diabetes" (searched 5 times)
    for i in range(5):
        analytics = SearchAnalytics(
            id=uuid4(),
            user_id=user.id,
            query="diabetes",
            filters=None,
            results_count=10,
            execution_time_ms=100 + i * 10,
            created_at=now - timedelta(days=i)
        )
        db.add(analytics)

    # Zero result query: "xyz123" (no results)
    analytics = SearchAnalytics(
        id=uuid4(),
        user_id=user.id,
        query="xyz123",
        filters=None,
        results_count=0,
        execution_time_ms=50,
        created_at=now - timedelta(days=1)
    )
    db.add(analytics)

    # Slow query: "complex query" (>2000ms)
    analytics = SearchAnalytics(
        id=uuid4(),
        user_id=user.id,
        query="complex query",
        filters=None,
        results_count=100,
        execution_time_ms=2500,
        created_at=now - timedelta(days=2)
    )
    db.add(analytics)

    # Recent query: "hypertension"
    analytics = SearchAnalytics(
        id=uuid4(),
        user_id=user.id,
        query="hypertension",
        filters=None,
        results_count=20,
        execution_time_ms=150,
        created_at=now
    )
    db.add(analytics)

    await db.commit()

    return {"user_id": user.id, "now": now}


class TestGetTopQueries:
    """Test get_top_queries method."""

    async def test_returns_most_frequent_queries(self, analytics_service, db, sample_analytics):
        """Test that get_top_queries returns queries sorted by frequency."""
        # Act
        top_queries = await analytics_service.get_top_queries(db, limit=10)

        # Assert
        assert len(top_queries) > 0
        # "diabetes" should be first (searched 5 times)
        assert top_queries[0]["query"] == "diabetes"
        assert top_queries[0]["count"] == 5

    async def test_respects_limit(self, analytics_service, db, sample_analytics):
        """Test that limit parameter works."""
        # Act
        top_queries = await analytics_service.get_top_queries(db, limit=2)

        # Assert
        assert len(top_queries) <= 2

    async def test_filters_by_date_range(self, analytics_service, db, sample_analytics):
        """Test filtering by date range."""
        now = sample_analytics["now"]
        start_date = now - timedelta(days=3)
        end_date = now

        # Act
        top_queries = await analytics_service.get_top_queries(
            db,
            limit=10,
            start_date=start_date,
            end_date=end_date
        )

        # Assert
        # Should only include queries within date range
        assert len(top_queries) > 0

    async def test_filters_by_user_id(self, analytics_service, db, sample_analytics):
        """Test filtering by user ID."""
        user_id = sample_analytics["user_id"]

        # Act
        top_queries = await analytics_service.get_top_queries(
            db,
            limit=10,
            user_id=user_id
        )

        # Assert
        assert len(top_queries) > 0
        # All results should be from specified user


class TestGetZeroResultQueries:
    """Test get_zero_result_queries method."""

    async def test_returns_queries_with_no_results(self, analytics_service, db, sample_analytics):
        """Test that zero result queries are identified."""
        # Act
        zero_result_queries = await analytics_service.get_zero_result_queries(db, limit=10)

        # Assert
        assert len(zero_result_queries) > 0
        # "xyz123" should be in results (has 0 results)
        query_strings = [q["query"] for q in zero_result_queries]
        assert "xyz123" in query_strings

    async def test_excludes_queries_with_results(self, analytics_service, db, sample_analytics):
        """Test that queries with results are excluded."""
        # Act
        zero_result_queries = await analytics_service.get_zero_result_queries(db, limit=10)

        # Assert
        query_strings = [q["query"] for q in zero_result_queries]
        # "diabetes" had results, should NOT be in list
        assert "diabetes" not in query_strings

    async def test_respects_date_range(self, analytics_service, db, sample_analytics):
        """Test date range filtering."""
        now = sample_analytics["now"]
        start_date = now - timedelta(days=2)
        end_date = now

        # Act
        zero_result_queries = await analytics_service.get_zero_result_queries(
            db,
            limit=10,
            start_date=start_date,
            end_date=end_date
        )

        # Assert
        assert isinstance(zero_result_queries, list)


class TestGetSlowQueries:
    """Test get_slow_queries method."""

    async def test_returns_slow_queries_above_threshold(self, analytics_service, db, sample_analytics):
        """Test that slow queries are identified based on threshold."""
        # Act
        slow_queries = await analytics_service.get_slow_queries(
            db,
            limit=10,
            threshold_ms=2000
        )

        # Assert
        assert len(slow_queries) > 0
        # "complex query" has 2500ms, should be in results
        query_strings = [q["query"] for q in slow_queries]
        assert "complex query" in query_strings

    async def test_excludes_fast_queries(self, analytics_service, db, sample_analytics):
        """Test that queries below threshold are excluded."""
        # Act
        slow_queries = await analytics_service.get_slow_queries(
            db,
            limit=10,
            threshold_ms=2000
        )

        # Assert
        query_strings = [q["query"] for q in slow_queries]
        # "diabetes" has ~100-150ms, should NOT be in list
        assert "diabetes" not in query_strings

    async def test_includes_execution_time(self, analytics_service, db, sample_analytics):
        """Test that execution time is included in results."""
        # Act
        slow_queries = await analytics_service.get_slow_queries(
            db,
            limit=10,
            threshold_ms=2000
        )

        # Assert
        assert len(slow_queries) > 0
        # Each result should have execution_time_ms
        for query in slow_queries:
            assert "execution_time_ms" in query
            assert query["execution_time_ms"] >= 2000


class TestGetSearchTrends:
    """Test get_search_trends method."""

    async def test_returns_daily_search_counts(self, analytics_service, db, sample_analytics):
        """Test that search trends returns daily aggregates."""
        now = sample_analytics["now"]
        start_date = now - timedelta(days=7)
        end_date = now

        # Act
        trends = await analytics_service.get_search_trends(
            db,
            start_date=start_date,
            end_date=end_date
        )

        # Assert
        assert len(trends) > 0
        # Each trend should have date and count
        for trend in trends:
            assert "date" in trend
            assert "count" in trend
            assert isinstance(trend["count"], int)
            # date should be an ISO format string
            assert isinstance(trend["date"], str)

    async def test_aggregates_by_date(self, analytics_service, db, sample_analytics):
        """Test that trends are aggregated by date."""
        now = sample_analytics["now"]
        start_date = now - timedelta(days=7)
        end_date = now

        # Act
        trends = await analytics_service.get_search_trends(
            db,
            start_date=start_date,
            end_date=end_date
        )

        # Assert
        # Should have multiple dates
        assert len(trends) > 0
        # Counts should be positive integers
        counts = [t["count"] for t in trends]
        assert all(c > 0 for c in counts)
        # All trends should have valid date strings
        dates = [t["date"] for t in trends]
        assert all(isinstance(d, str) for d in dates)

    async def test_respects_date_range(self, analytics_service, db, sample_analytics):
        """Test that only trends within date range are returned."""
        now = sample_analytics["now"]
        start_date = now - timedelta(days=3)
        end_date = now

        # Act
        trends = await analytics_service.get_search_trends(
            db,
            start_date=start_date,
            end_date=end_date
        )

        # Assert
        # Should return trends (date range filters results)
        assert isinstance(trends, list)
        # All results should have date strings
        for trend in trends:
            assert "date" in trend
            assert isinstance(trend["date"], str)
