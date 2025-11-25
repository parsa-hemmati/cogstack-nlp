"""
Unit Tests for SearchAnalytics Model

Tests SQLAlchemy model for search_analytics table.
Follows TDD approach: Write tests first, then implement.
"""

import pytest
import uuid
from datetime import datetime


@pytest.mark.asyncio
async def test_create_search_analytics_with_valid_data():
    """Test creating SearchAnalytics with valid data"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    analytics = SearchAnalytics(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        query="diabetes mellitus",
        filters={"Negation": "Affirmed", "Temporality": "Current"},
        results_count=45,
        execution_time_ms=250,
        clicked_documents=[uuid.uuid4(), uuid.uuid4()]
    )

    # Assert
    assert analytics.id is not None
    assert analytics.user_id is not None
    assert analytics.query == "diabetes mellitus"
    assert analytics.filters == {"Negation": "Affirmed", "Temporality": "Current"}
    assert analytics.results_count == 45
    assert analytics.execution_time_ms == 250
    assert len(analytics.clicked_documents) == 2
    assert isinstance(analytics.created_at, datetime)


@pytest.mark.asyncio
async def test_search_analytics_default_values():
    """Test SearchAnalytics model default values"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    analytics = SearchAnalytics(
        user_id=uuid.uuid4(),
        query="test query",
        results_count=10,
        execution_time_ms=100
    )

    # Assert
    assert analytics.id is not None  # UUID generated
    assert analytics.filters is None  # Optional field
    assert analytics.clicked_documents is None  # Optional field
    assert analytics.created_at is not None


@pytest.mark.asyncio
async def test_search_analytics_repr():
    """Test SearchAnalytics string representation"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    user_id = uuid.uuid4()
    analytics = SearchAnalytics(
        user_id=user_id,
        query="hypertension",
        results_count=30,
        execution_time_ms=180
    )

    # Act
    repr_str = repr(analytics)

    # Assert
    assert "SearchAnalytics" in repr_str
    assert "hypertension" in repr_str
    assert str(user_id) in repr_str


@pytest.mark.asyncio
async def test_search_analytics_to_dict():
    """Test SearchAnalytics to_dict serialization"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    analytics_id = uuid.uuid4()
    user_id = uuid.uuid4()
    doc_id_1 = uuid.uuid4()
    doc_id_2 = uuid.uuid4()

    analytics = SearchAnalytics(
        id=analytics_id,
        user_id=user_id,
        query="covid-19",
        filters={"Negation": "Affirmed"},
        results_count=50,
        execution_time_ms=320,
        clicked_documents=[doc_id_1, doc_id_2]
    )

    # Act
    result = analytics.to_dict()

    # Assert
    assert result["id"] == str(analytics_id)
    assert result["user_id"] == str(user_id)
    assert result["query"] == "covid-19"
    assert result["filters"] == {"Negation": "Affirmed"}
    assert result["results_count"] == 50
    assert result["execution_time_ms"] == 320
    assert len(result["clicked_documents"]) == 2
    assert str(doc_id_1) in result["clicked_documents"]
    assert str(doc_id_2) in result["clicked_documents"]
    assert "created_at" in result


@pytest.mark.asyncio
async def test_search_analytics_clicked_documents_array():
    """Test clicked_documents array field works correctly"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    doc_ids = [uuid.uuid4() for _ in range(5)]
    analytics = SearchAnalytics(
        user_id=uuid.uuid4(),
        query="test",
        results_count=100,
        execution_time_ms=500,
        clicked_documents=doc_ids
    )

    # Assert
    assert len(analytics.clicked_documents) == 5
    assert all(isinstance(doc_id, uuid.UUID) for doc_id in analytics.clicked_documents)
    assert analytics.clicked_documents == doc_ids


@pytest.mark.asyncio
async def test_search_analytics_empty_clicked_documents():
    """Test SearchAnalytics with no clicked documents"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    analytics = SearchAnalytics(
        user_id=uuid.uuid4(),
        query="test",
        results_count=50,
        execution_time_ms=200,
        clicked_documents=[]
    )

    # Assert
    assert analytics.clicked_documents == []


@pytest.mark.asyncio
async def test_search_analytics_filters_jsonb():
    """Test filters field supports complex JSONB data"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    complex_filters = {
        "Negation": "Affirmed",
        "Temporality": "Current",
        "Experiencer": "Patient",
        "Certainty": "Certain",
        "date_range": {
            "start": "2023-01-01",
            "end": "2023-12-31"
        }
    }

    analytics = SearchAnalytics(
        user_id=uuid.uuid4(),
        query="test",
        filters=complex_filters,
        results_count=20,
        execution_time_ms=150
    )

    # Assert
    assert analytics.filters == complex_filters
    assert analytics.filters["Negation"] == "Affirmed"
    assert analytics.filters["date_range"]["start"] == "2023-01-01"


@pytest.mark.asyncio
async def test_search_analytics_performance_metrics():
    """Test tracking performance metrics"""
    from app.models.search_analytics import SearchAnalytics

    # Arrange
    fast_query = SearchAnalytics(
        user_id=uuid.uuid4(),
        query="fast",
        results_count=10,
        execution_time_ms=50
    )

    slow_query = SearchAnalytics(
        user_id=uuid.uuid4(),
        query="slow",
        results_count=1000,
        execution_time_ms=2500
    )

    # Assert
    assert fast_query.execution_time_ms < 100  # Fast query
    assert slow_query.execution_time_ms > 1000  # Slow query
    assert slow_query.results_count > fast_query.results_count
