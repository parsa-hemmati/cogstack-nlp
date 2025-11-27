"""
Unit tests for search schemas.

Tests search request/response schemas, validation rules, and structure.
"""
import pytest
from datetime import datetime, date
from uuid import UUID

from app.schemas.search import (
    DocumentSearchFilters,
    SearchRequest,
    Highlight,
    SearchResultDocument,
    FacetValue,
    Facets,
    SearchResponse,
    SavedSearchCreate,
    SavedSearchResponse,
    SearchAnalyticsResponse,
    SortBy
)


class TestSearchRequest:
    """Test SearchRequest validation."""

    def test_search_request_requires_query(self):
        """Test that query field is required."""
        with pytest.raises(ValueError):
            SearchRequest(query="")  # Empty query should fail

    def test_search_request_validates_query_max_length(self):
        """Test that query must be ≤ 1000 characters."""
        long_query = "x" * 1001
        with pytest.raises(ValueError):
            SearchRequest(query=long_query)

    def test_search_request_validates_page_size_max(self):
        """Test that page_size must be ≤ 100."""
        with pytest.raises(ValueError):
            SearchRequest(query="diabetes", page_size=101)

    def test_search_request_accepts_valid_data(self):
        """Test that SearchRequest accepts valid data."""
        request = SearchRequest(
            query="diabetes mellitus",
            page=1,
            page_size=20,
            sort=SortBy.RELEVANCE
        )
        assert request.query == "diabetes mellitus"
        assert request.page == 1
        assert request.page_size == 20
        assert request.sort == SortBy.RELEVANCE

    def test_search_request_accepts_filters(self):
        """Test that SearchRequest accepts optional filters."""
        filters = DocumentSearchFilters(
            document_types=["rtf", "txt"],
            authors=["user-123"],
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31)
        )
        request = SearchRequest(
            query="hypertension",
            filters=filters
        )
        assert request.filters.document_types == ["rtf", "txt"]
        assert request.filters.authors == ["user-123"]

    def test_search_request_default_values(self):
        """Test SearchRequest default values."""
        request = SearchRequest(query="test")
        assert request.page == 1
        assert request.page_size == 20
        assert request.sort == SortBy.RELEVANCE
        assert request.filters is None


class TestSearchResultDocument:
    """Test SearchResultDocument schema."""

    def test_search_result_document_includes_highlights(self):
        """Test that SearchResultDocument includes highlights array."""
        doc = SearchResultDocument(
            document_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            title="Clinical Note 001",
            document_type="rtf",
            author="Dr. Smith",
            date=datetime(2025, 11, 18, 12, 0, 0),
            department="Cardiology",
            relevance_score=0.95,
            highlights=[
                Highlight(field="content", snippets=["<em>diabetes</em> mellitus"])
            ]
        )
        assert len(doc.highlights) == 1
        assert doc.highlights[0].field == "content"
        assert "<em>diabetes</em>" in doc.highlights[0].snippets[0]

    def test_search_result_document_optional_fields(self):
        """Test that SearchResultDocument has optional fields."""
        doc = SearchResultDocument(
            document_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            title="Test",
            document_type="txt",
            relevance_score=0.5,
            highlights=[]
        )
        assert doc.author is None
        assert doc.date is None
        assert doc.department is None


class TestSearchResponse:
    """Test SearchResponse schema."""

    def test_search_response_includes_all_required_fields(self):
        """Test that SearchResponse includes all required fields."""
        response = SearchResponse(
            query="diabetes",
            total_results=42,
            page=1,
            page_size=20,
            documents=[],
            facets=Facets(
                document_types=[FacetValue(value="rtf", count=30)],
                authors=[FacetValue(value="Dr. Smith", count=20)],
                departments=[FacetValue(value="Cardiology", count=15)]
            ),
            execution_time_ms=125
        )
        assert response.query == "diabetes"
        assert response.total_results == 42
        assert response.page == 1
        assert response.page_size == 20
        assert response.execution_time_ms == 125
        assert len(response.facets.document_types) == 1


class TestFacets:
    """Test Facets structure."""

    def test_facets_structure_matches_es_aggregations(self):
        """Test that Facets structure matches Elasticsearch aggregations."""
        facets = Facets(
            document_types=[
                FacetValue(value="rtf", count=100),
                FacetValue(value="txt", count=50)
            ],
            authors=[
                FacetValue(value="Dr. Smith", count=75)
            ],
            departments=[
                FacetValue(value="Cardiology", count=60),
                FacetValue(value="Neurology", count=40)
            ]
        )
        assert len(facets.document_types) == 2
        assert facets.document_types[0].value == "rtf"
        assert facets.document_types[0].count == 100


class TestSavedSearchSchemas:
    """Test SavedSearch schemas."""

    def test_saved_search_create_validates_name(self):
        """Test SavedSearchCreate validates name field."""
        with pytest.raises(ValueError):
            SavedSearchCreate(name="", query="test")

    def test_saved_search_create_accepts_valid_data(self):
        """Test SavedSearchCreate accepts valid data."""
        create = SavedSearchCreate(
            name="My diabetes search",
            description="Search for diabetes patients",
            query="diabetes mellitus",
            filters={"document_types": ["rtf"]},
            is_shared=True
        )
        assert create.name == "My diabetes search"
        assert create.query == "diabetes mellitus"
        assert create.is_shared is True

    def test_saved_search_response_includes_metadata(self):
        """Test SavedSearchResponse includes metadata fields."""
        response = SavedSearchResponse(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            user_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            name="Test search",
            query="test",
            filters={},
            is_shared=False,
            execution_count=5,
            created_at=datetime(2025, 11, 18, 12, 0, 0),
            updated_at=datetime(2025, 11, 18, 12, 30, 0)
        )
        assert response.execution_count == 5
        assert response.created_at is not None


class TestSearchAnalyticsResponse:
    """Test SearchAnalyticsResponse schema."""

    def test_search_analytics_response_includes_performance_metrics(self):
        """Test SearchAnalyticsResponse includes performance metrics."""
        analytics = SearchAnalyticsResponse(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            user_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            query="diabetes",
            filters={},
            results_count=42,
            execution_time_ms=125,
            clicked_documents=[
                UUID("770e8400-e29b-41d4-a716-446655440000"),
                UUID("880e8400-e29b-41d4-a716-446655440000")
            ],
            created_at=datetime(2025, 11, 18, 12, 0, 0)
        )
        assert analytics.results_count == 42
        assert analytics.execution_time_ms == 125
        assert len(analytics.clicked_documents) == 2
