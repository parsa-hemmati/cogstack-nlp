"""
Unit tests for SearchService.

Tests search functionality including query execution, filtering, pagination,
analytics tracking, and audit logging.
"""
import pytest
from datetime import datetime, date
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.search_service import SearchService
from app.schemas.search import (
    SearchRequest,
    DocumentSearchFilters,
    SearchResponse,
    SortBy
)
from app.models.user import User


@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client."""
    client = AsyncMock()
    # Mock search response
    client.search = AsyncMock(return_value={
        "took": 125,
        "hits": {
            "total": {"value": 42, "relation": "eq"},
            "hits": [
                {
                    "_id": str(uuid4()),
                    "_score": 9.5,
                    "_source": {
                        "document_id": str(uuid4()),
                        "title": "Clinical Note 001",
                        "content": "Patient has diabetes mellitus",
                        "document_type": "rtf",
                        "author": "Dr. Smith",
                        "date": "2025-11-18T12:00:00Z",
                        "department": "Cardiology"
                    },
                    "highlight": {
                        "content": ["Patient has <em>diabetes</em> mellitus"]
                    }
                }
            ]
        }
    })
    return client


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    return user


@pytest.fixture
def search_service(mock_es_client, mock_db_session):
    """Create SearchService instance with mocks."""
    return SearchService(es_client=mock_es_client, db_session=mock_db_session)


@pytest.mark.asyncio
async def test_search_documents_returns_search_response(search_service, mock_user):
    """Test that search_documents returns SearchResponse."""
    request = SearchRequest(query="diabetes")

    response = await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    assert isinstance(response, SearchResponse)
    assert response.query == "diabetes"
    assert response.total_results == 42
    assert response.page == 1
    assert response.page_size == 20
    assert response.execution_time_ms == 125
    assert len(response.documents) == 1


@pytest.mark.asyncio
async def test_search_documents_queries_elasticsearch(search_service, mock_user, mock_es_client):
    """Test that search_documents queries Elasticsearch with correct parameters."""
    request = SearchRequest(query="diabetes mellitus")

    await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify Elasticsearch was called
    mock_es_client.search.assert_called_once()
    call_args = mock_es_client.search.call_args

    # Verify query structure
    assert call_args.kwargs["index"] == "documents"
    assert "query" in call_args.kwargs["body"]
    assert "highlight" in call_args.kwargs["body"]


@pytest.mark.asyncio
async def test_search_documents_applies_document_type_filter(search_service, mock_user, mock_es_client):
    """Test that search_documents applies document_type filter."""
    filters = DocumentSearchFilters(document_types=["rtf", "txt"])
    request = SearchRequest(query="diabetes", filters=filters)

    await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify filter was applied
    call_args = mock_es_client.search.call_args
    query_body = call_args.kwargs["body"]["query"]

    # Should have bool query with filter
    assert "bool" in query_body
    assert "filter" in query_body["bool"]


@pytest.mark.asyncio
async def test_search_documents_paginates_results(search_service, mock_user, mock_es_client):
    """Test that search_documents paginates results correctly."""
    request = SearchRequest(query="diabetes", page=2, page_size=50)

    await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify pagination parameters
    call_args = mock_es_client.search.call_args
    assert call_args.kwargs["from_"] == 50  # (page-1) * page_size = (2-1) * 50
    assert call_args.kwargs["size"] == 50


@pytest.mark.asyncio
async def test_search_documents_tracks_analytics(search_service, mock_user, mock_db_session):
    """Test that search_documents tracks analytics in database."""
    request = SearchRequest(query="diabetes")

    await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify SearchAnalytics was created and saved
    mock_db_session.add.assert_called_once()
    added_obj = mock_db_session.add.call_args[0][0]

    assert added_obj.__class__.__name__ == "SearchAnalytics"
    assert added_obj.user_id == mock_user.id
    assert added_obj.query == "diabetes"
    assert added_obj.results_count == 42
    assert added_obj.execution_time_ms == 125

    # Verify commit was called
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
@patch('app.services.search_service.AuditService.log_action')
async def test_search_documents_logs_audit_trail(mock_log_action, search_service, mock_user):
    """Test that search_documents logs audit trail."""
    request = SearchRequest(query="diabetes")

    await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify audit log was created
    mock_log_action.assert_called_once()
    call_args = mock_log_action.call_args

    assert call_args.kwargs["user"] == mock_user
    assert call_args.kwargs["action"] == "SEARCH_EXECUTED"
    assert call_args.kwargs["resource_type"] == "search"
    assert call_args.kwargs["ip_address"] == "127.0.0.1"
    assert "query" in call_args.kwargs["details"]


@pytest.mark.asyncio
async def test_search_documents_with_date_range_filter(search_service, mock_user, mock_es_client):
    """Test that search_documents applies date_range filter."""
    filters = DocumentSearchFilters(
        date_from=date(2025, 1, 1),
        date_to=date(2025, 12, 31)
    )
    request = SearchRequest(query="diabetes", filters=filters)

    await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify date range filter was applied
    call_args = mock_es_client.search.call_args
    query_body = call_args.kwargs["body"]["query"]

    # Should have range query in filters
    assert "bool" in query_body
    assert "filter" in query_body["bool"]


@pytest.mark.asyncio
async def test_search_documents_with_sorting(search_service, mock_user, mock_es_client):
    """Test that search_documents applies sorting."""
    request = SearchRequest(query="diabetes", sort=SortBy.DATE)

    await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify sort parameter was applied
    call_args = mock_es_client.search.call_args
    assert "sort" in call_args.kwargs["body"]


@pytest.mark.asyncio
async def test_search_documents_includes_highlights(search_service, mock_user):
    """Test that search_documents includes highlights in response."""
    request = SearchRequest(query="diabetes")

    response = await search_service.search_documents(
        request=request,
        user=mock_user,
        ip_address="127.0.0.1"
    )

    # Verify highlights are in response
    assert len(response.documents) > 0
    doc = response.documents[0]
    assert len(doc.highlights) > 0
    assert doc.highlights[0].field == "content"
    assert "<em>diabetes</em>" in doc.highlights[0].snippets[0]
