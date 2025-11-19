"""
Unit tests for ElasticsearchTimelineRepository.

Tests use mocked Elasticsearch client to avoid external dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.repositories.elasticsearch_timeline_repo import ElasticsearchTimelineRepository
from app.schemas.timeline import ConceptMention, DateRange, MetaAnnotations


@pytest.fixture
def mock_es():
    """Mock AsyncElasticsearch client."""
    with patch('app.repositories.elasticsearch_timeline_repo.AsyncElasticsearch') as mock:
        es_instance = AsyncMock()
        mock.return_value = es_instance
        yield es_instance


@pytest.fixture
def repo(mock_es):
    """Elasticsearch repository with mocked client."""
    return ElasticsearchTimelineRepository()


@pytest.fixture
def sample_es_response():
    """Sample Elasticsearch response with concept mentions."""
    return {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "1",
                    "_source": {
                        "document_id": "doc-123",
                        "date": "2023-01-15T10:30:00Z",
                        "sentence": "Patient diagnosed with Type 2 Diabetes.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.95
                    }
                },
                {
                    "_id": "2",
                    "_source": {
                        "document_id": "doc-124",
                        "date": "2023-02-20T14:15:00Z",
                        "sentence": "HbA1c 8.5%, diabetes management plan updated.",
                        "meta_annotations": {
                            "Negation": "Affirmed",
                            "Temporality": "Current",
                            "Experiencer": "Patient",
                            "Certainty": "High"
                        },
                        "confidence": 0.92
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_aggregation_response():
    """Sample Elasticsearch aggregation response."""
    return {
        "aggregations": {
            "concepts_by_time": {
                "buckets": [
                    {
                        "key": "2023-01-01T00:00:00.000Z",
                        "doc_count": 15,
                        "concept_counts": {
                            "buckets": [
                                {"key": "C0011849", "doc_count": 5},
                                {"key": "C0020538", "doc_count": 3},
                                {"key": "C0008031", "doc_count": 2}
                            ]
                        }
                    },
                    {
                        "key": "2023-02-01T00:00:00.000Z",
                        "doc_count": 8,
                        "concept_counts": {
                            "buckets": [
                                {"key": "C0011849", "doc_count": 4},
                                {"key": "C0020538", "doc_count": 2}
                            ]
                        }
                    }
                ]
            }
        }
    }


@pytest.mark.asyncio
async def test_query_concepts_by_patient_basic(repo, mock_es, sample_es_response):
    """Test basic patient concept query."""
    # Arrange
    patient_id = "patient-123"
    mock_es.search.return_value = sample_es_response

    # Act
    mentions = await repo.query_concepts_by_patient(patient_id=patient_id)

    # Assert
    assert len(mentions) == 2
    assert all(isinstance(m, ConceptMention) for m in mentions)
    assert mentions[0].document_id == "doc-123"
    assert mentions[0].confidence == 0.95
    assert mentions[0].meta_annotations.Negation == "Affirmed"

    # Verify ES query
    mock_es.search.assert_called_once()
    call_kwargs = mock_es.search.call_args.kwargs
    assert call_kwargs["index"] == "clinical_concepts"
    assert call_kwargs["query"]["bool"]["must"][0] == {"term": {"patient_id": patient_id}}


@pytest.mark.asyncio
async def test_query_concepts_with_concept_filter(repo, mock_es, sample_es_response):
    """Test concept query with CUI filter."""
    # Arrange
    patient_id = "patient-123"
    concept_filter = ["C0011849", "C0020538"]
    mock_es.search.return_value = sample_es_response

    # Act
    mentions = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        concept_filter=concept_filter
    )

    # Assert
    assert len(mentions) == 2

    # Verify concept filter in query
    call_kwargs = mock_es.search.call_args.kwargs
    query_must = call_kwargs["query"]["bool"]["must"]
    assert {"terms": {"concept_cui": concept_filter}} in query_must


@pytest.mark.asyncio
async def test_query_concepts_with_date_range(repo, mock_es, sample_es_response):
    """Test concept query with date range filter."""
    # Arrange
    patient_id = "patient-123"
    date_range = DateRange(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 12, 31)
    )
    mock_es.search.return_value = sample_es_response

    # Act
    mentions = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        date_range=date_range
    )

    # Assert
    assert len(mentions) == 2

    # Verify date range filter in query
    call_kwargs = mock_es.search.call_args.kwargs
    query_must = call_kwargs["query"]["bool"]["must"]
    date_filter = next(f for f in query_must if "range" in f)
    assert date_filter["range"]["date"]["gte"] == "2023-01-01T00:00:00"
    assert date_filter["range"]["date"]["lte"] == "2023-12-31T00:00:00"


@pytest.mark.asyncio
async def test_query_concepts_with_meta_annotations_single_value(repo, mock_es, sample_es_response):
    """Test concept query with single-value meta-annotation filter."""
    # Arrange
    patient_id = "patient-123"
    meta_annotations = {
        "Negation": "Affirmed",
        "Experiencer": "Patient"
    }
    mock_es.search.return_value = sample_es_response

    # Act
    mentions = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        meta_annotations=meta_annotations
    )

    # Assert
    assert len(mentions) == 2

    # Verify meta-annotation filters in query
    call_kwargs = mock_es.search.call_args.kwargs
    query_must = call_kwargs["query"]["bool"]["must"]
    assert {"term": {"meta_annotations.Negation": "Affirmed"}} in query_must
    assert {"term": {"meta_annotations.Experiencer": "Patient"}} in query_must


@pytest.mark.asyncio
async def test_query_concepts_with_meta_annotations_list_value(repo, mock_es, sample_es_response):
    """Test concept query with list-value meta-annotation filter (OR logic)."""
    # Arrange
    patient_id = "patient-123"
    meta_annotations = {
        "Temporality": ["Current", "Recent"]
    }
    mock_es.search.return_value = sample_es_response

    # Act
    mentions = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        meta_annotations=meta_annotations
    )

    # Assert
    assert len(mentions) == 2

    # Verify list filter uses "terms" (OR logic)
    call_kwargs = mock_es.search.call_args.kwargs
    query_must = call_kwargs["query"]["bool"]["must"]
    assert {"terms": {"meta_annotations.Temporality": ["Current", "Recent"]}} in query_must


@pytest.mark.asyncio
async def test_query_concepts_with_all_filters(repo, mock_es, sample_es_response):
    """Test concept query with all filters combined."""
    # Arrange
    patient_id = "patient-123"
    concept_filter = ["C0011849"]
    date_range = DateRange(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 12, 31)
    )
    meta_annotations = {
        "Negation": "Affirmed",
        "Experiencer": "Patient",
        "Temporality": ["Current", "Recent"]
    }
    mock_es.search.return_value = sample_es_response

    # Act
    mentions = await repo.query_concepts_by_patient(
        patient_id=patient_id,
        concept_filter=concept_filter,
        date_range=date_range,
        meta_annotations=meta_annotations
    )

    # Assert
    assert len(mentions) == 2

    # Verify all filters present
    call_kwargs = mock_es.search.call_args.kwargs
    query_must = call_kwargs["query"]["bool"]["must"]
    assert len(query_must) == 6  # patient_id + concept + date + 3 meta-annotations


@pytest.mark.asyncio
async def test_query_concepts_empty_result(repo, mock_es):
    """Test concept query with no results."""
    # Arrange
    patient_id = "patient-999"
    mock_es.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

    # Act
    mentions = await repo.query_concepts_by_patient(patient_id=patient_id)

    # Assert
    assert mentions == []


@pytest.mark.asyncio
async def test_aggregate_concepts_by_date_basic(repo, mock_es, sample_aggregation_response):
    """Test basic concept aggregation by date."""
    # Arrange
    patient_id = "patient-123"
    mock_es.search.return_value = sample_aggregation_response

    # Act
    buckets = await repo.aggregate_concepts_by_date(
        patient_id=patient_id,
        granularity="month"
    )

    # Assert
    assert len(buckets) == 2
    assert buckets[0]["key"] == "2023-01-01T00:00:00.000Z"
    assert buckets[0]["doc_count"] == 15
    assert len(buckets[0]["concept_counts"]["buckets"]) == 3

    # Verify aggregation query
    mock_es.search.assert_called_once()
    call_kwargs = mock_es.search.call_args.kwargs
    assert call_kwargs["size"] == 0  # Aggregation only
    assert "date_histogram" in call_kwargs["aggs"]["concepts_by_time"]


@pytest.mark.asyncio
async def test_aggregate_concepts_by_date_with_filter(repo, mock_es, sample_aggregation_response):
    """Test concept aggregation with concept filter."""
    # Arrange
    patient_id = "patient-123"
    concept_filter = ["C0011849"]
    mock_es.search.return_value = sample_aggregation_response

    # Act
    buckets = await repo.aggregate_concepts_by_date(
        patient_id=patient_id,
        granularity="month",
        concept_filter=concept_filter
    )

    # Assert
    assert len(buckets) == 2

    # Verify concept filter in query
    call_kwargs = mock_es.search.call_args.kwargs
    assert "bool" in call_kwargs["query"]
    assert {"terms": {"concept_cui": concept_filter}} in call_kwargs["query"]["bool"]["must"]


@pytest.mark.asyncio
async def test_aggregate_concepts_different_granularities(repo, mock_es, sample_aggregation_response):
    """Test concept aggregation with different time granularities."""
    # Arrange
    patient_id = "patient-123"
    mock_es.search.return_value = sample_aggregation_response

    # Test each granularity
    for granularity in ["day", "week", "month", "quarter", "year"]:
        # Act
        buckets = await repo.aggregate_concepts_by_date(
            patient_id=patient_id,
            granularity=granularity
        )

        # Assert
        assert len(buckets) == 2

        # Verify granularity in aggregation
        call_kwargs = mock_es.search.call_args.kwargs
        date_hist = call_kwargs["aggs"]["concepts_by_time"]["date_histogram"]
        assert date_hist["calendar_interval"] == granularity


@pytest.mark.asyncio
async def test_repo_context_manager(mock_es):
    """Test repository as async context manager."""
    # Act
    async with ElasticsearchTimelineRepository() as repo:
        # Inside context
        assert repo.es is not None

    # Assert
    # close() should have been called
    mock_es.close.assert_called_once()


@pytest.mark.asyncio
async def test_repo_close(repo, mock_es):
    """Test repository close method."""
    # Act
    await repo.close()

    # Assert
    mock_es.close.assert_called_once()
