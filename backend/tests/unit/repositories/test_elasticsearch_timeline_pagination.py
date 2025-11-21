"""
Unit tests for ElasticsearchTimelineRepository pagination functionality.

Tests cursor-based pagination for large patient timelines (>1,000 events).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.repositories.elasticsearch_timeline_repo import ElasticsearchTimelineRepository
from app.schemas.timeline import ConceptMention, MetaAnnotations, DateRange


@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client."""
    return AsyncMock()


@pytest.fixture
def sample_concept_mention():
    """Create a sample concept mention."""
    def _create_mention(cui="C0011849", name="Diabetes", date=None):
        return ConceptMention(
            concept_cui=cui,
            concept_name=name,
            concept_type="condition",
            document_id=str(uuid4()),
            date=date or datetime(2023, 1, 15),
            sentence=f"Patient has {name}.",
            meta_annotations=MetaAnnotations(
                Negation="Affirmed",
                Temporality="Current",
                Experiencer="Patient",
                Certainty="High"
            ),
            confidence=0.95
        )
    return _create_mention


@pytest.mark.asyncio
async def test_query_with_pagination_first_page(mock_es_client, sample_concept_mention):
    """Test querying first page with cursor-based pagination."""
    # Arrange
    repo = ElasticsearchTimelineRepository()
    repo.es = mock_es_client

    patient_id = str(uuid4())

    # Mock Elasticsearch response with search_after cursor
    mock_es_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "concept_cui": "C0011849",
                        "concept_name": "Diabetes",
                        "concept_type": "condition",
                        "document_id": str(uuid4()),
                        "date": "2023-01-15T10:30:00Z",
                        "sentence": "Patient has diabetes.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.95
                    },
                    "sort": [1673781000000, "doc1"]  # Cursor value for next page
                }
            ]
        }
    }

    # Act
    result = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        size=100
    )

    # Assert
    assert len(result.mentions) == 1
    assert result.mentions[0].concept_cui == "C0011849"
    assert result.cursor is not None  # Cursor should be returned
    assert result.has_more is False  # Only 1 result, no more pages


@pytest.mark.asyncio
async def test_query_with_pagination_next_page(mock_es_client):
    """Test querying next page using cursor."""
    # Arrange
    repo = ElasticsearchTimelineRepository()
    repo.es = mock_es_client

    patient_id = str(uuid4())
    cursor = [1673781000000, "doc1"]  # Cursor from previous page

    # Mock Elasticsearch response
    mock_es_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "concept_cui": "C0020538",
                        "concept_name": "Hypertension",
                        "concept_type": "condition",
                        "document_id": str(uuid4()),
                        "date": "2023-02-20T14:15:00Z",
                        "sentence": "Patient has hypertension.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.92
                    },
                    "sort": [1676900100000, "doc2"]
                }
            ]
        }
    }

    # Act
    result = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        cursor=cursor,
        size=100
    )

    # Assert
    assert len(result.mentions) == 1
    assert result.mentions[0].concept_cui == "C0020538"

    # Verify search_after was used in query
    call_args = mock_es_client.search.call_args
    assert "search_after" in call_args.kwargs
    assert call_args.kwargs["search_after"] == cursor


@pytest.mark.asyncio
async def test_pagination_has_more_flag(mock_es_client):
    """Test has_more flag when there are more results."""
    # Arrange
    repo = ElasticsearchTimelineRepository()
    repo.es = mock_es_client

    patient_id = str(uuid4())
    page_size = 2

    # Mock response with exactly page_size + 1 results (to check if more exist)
    mock_es_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "concept_cui": "C0011849",
                        "concept_name": "Diabetes",
                        "concept_type": "condition",
                        "document_id": str(uuid4()),
                        "date": "2023-01-15T10:30:00Z",
                        "sentence": "Patient has diabetes.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.95
                    },
                    "sort": [1673781000000, "doc1"]
                },
                {
                    "_source": {
                        "concept_cui": "C0020538",
                        "concept_name": "Hypertension",
                        "concept_type": "condition",
                        "document_id": str(uuid4()),
                        "date": "2023-02-20T14:15:00Z",
                        "sentence": "Patient has hypertension.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.92
                    },
                    "sort": [1676900100000, "doc2"]
                },
                {
                    "_source": {
                        "concept_cui": "C0004096",
                        "concept_name": "Asthma",
                        "concept_type": "condition",
                        "document_id": str(uuid4()),
                        "date": "2023-03-10T09:00:00Z",
                        "sentence": "Patient has asthma.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.88
                    },
                    "sort": [1678438800000, "doc3"]
                }
            ]
        }
    }

    # Act
    result = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        size=page_size
    )

    # Assert
    # Should return only page_size results
    assert len(result.mentions) == page_size
    # has_more should be True because we got page_size + 1 from ES
    assert result.has_more is True
    # Cursor should be the sort value of the last returned item
    assert result.cursor is not None


@pytest.mark.asyncio
async def test_pagination_no_more_results(mock_es_client):
    """Test has_more flag when there are no more results."""
    # Arrange
    repo = ElasticsearchTimelineRepository()
    repo.es = mock_es_client

    patient_id = str(uuid4())
    page_size = 10

    # Mock response with fewer results than page_size
    mock_es_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "concept_cui": "C0011849",
                        "concept_name": "Diabetes",
                        "concept_type": "condition",
                        "document_id": str(uuid4()),
                        "date": "2023-01-15T10:30:00Z",
                        "sentence": "Patient has diabetes.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.95
                    },
                    "sort": [1673781000000, "doc1"]
                }
            ]
        }
    }

    # Act
    result = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        size=page_size
    )

    # Assert
    assert len(result.mentions) == 1
    assert result.has_more is False  # Only 1 result, less than page_size


@pytest.mark.asyncio
async def test_pagination_preserves_filters_with_cursor(mock_es_client):
    """Test that filters are preserved when using cursor pagination."""
    # Arrange
    repo = ElasticsearchTimelineRepository()
    repo.es = mock_es_client

    patient_id = str(uuid4())
    cursor = [1673781000000, "doc1"]
    concept_filter = ["C0011849"]
    meta_annotations = {"Negation": "Affirmed"}

    mock_es_client.search.return_value = {
        "hits": {"hits": []}
    }

    # Act
    await repo.query_concepts_by_patient(
        patient_id=patient_id,
        concept_filter=concept_filter,
        meta_annotations=meta_annotations,
        cursor=cursor,
        size=100
    )

    # Assert
    call_args = mock_es_client.search.call_args
    query = call_args.kwargs["query"]

    # Verify filters are still applied
    assert {"terms": {"concept_cui": concept_filter}} in query["bool"]["must"]
    assert {"term": {"meta_annotations.Negation": "Affirmed"}} in query["bool"]["must"]

    # Verify cursor is used
    assert call_args.kwargs["search_after"] == cursor


@pytest.mark.asyncio
async def test_default_page_size_is_1000(mock_es_client):
    """Test that default page size is 1,000 for performance."""
    # Arrange
    repo = ElasticsearchTimelineRepository()
    repo.es = mock_es_client

    patient_id = str(uuid4())

    mock_es_client.search.return_value = {
        "hits": {"hits": []}
    }

    # Act
    await repo.query_concepts_by_patient(patient_id=patient_id)

    # Assert
    call_args = mock_es_client.search.call_args
    # Size should be 1000 + 1 (to check if more results exist)
    assert call_args.kwargs["size"] == 1001


@pytest.mark.asyncio
async def test_cursor_based_pagination_large_dataset():
    """Test pagination works for datasets >10,000 events."""
    # Arrange
    repo = ElasticsearchTimelineRepository()
    mock_es = AsyncMock()
    repo.es = mock_es

    patient_id = str(uuid4())

    # Simulate multiple pages
    page1_hits = []
    for i in range(1000):
        page1_hits.append({
            "_source": {
                "concept_cui": f"C{i:07d}",
                "concept_name": f"Concept {i}",
                "concept_type": "condition",
                "document_id": str(uuid4()),
                "date": "2023-01-15T10:30:00Z",
                "sentence": f"Mention {i}",
                "meta_annotations": {
                    "Negation": "Affirmed",
                    "Temporality": "Current",
                    "Experiencer": "Patient",
                    "Certainty": "High"
                },
                "confidence": 0.95
            },
            "sort": [1673781000000 + i, f"doc{i}"]
        })

    mock_es.search.return_value = {
        "hits": {"hits": page1_hits + [page1_hits[-1]]}  # +1 to indicate more
    }

    # Act
    result = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        size=1000
    )

    # Assert
    assert len(result.mentions) == 1000
    assert result.has_more is True
    assert result.cursor is not None

    # Cursor should allow fetching next page
    assert result.cursor == [1673781000000 + 999, "doc999"]
