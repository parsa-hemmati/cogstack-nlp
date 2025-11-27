"""
Integration tests for ElasticsearchTimelineRepository.

These tests require a running Elasticsearch instance with the clinical_concepts index.
Set ELASTICSEARCH_URL environment variable to override default (localhost:9200).

Run with: pytest backend/tests/integration/repositories/test_elasticsearch_timeline_repo_integration.py
"""

import pytest
import os
from datetime import datetime, timedelta
from uuid import uuid4
from elasticsearch import AsyncElasticsearch

from app.repositories.elasticsearch_timeline_repo import ElasticsearchTimelineRepository
from app.schemas.timeline import DateRange


# Skip if Elasticsearch not available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true",
    reason="Integration tests skipped (set SKIP_INTEGRATION_TESTS=false to run)"
)


@pytest.fixture(scope="module")
async def es_client():
    """Create Elasticsearch client for test data setup."""
    es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    client = AsyncElasticsearch([es_url])

    # Check connection
    try:
        await client.ping()
    except Exception as e:
        pytest.skip(f"Elasticsearch not available: {e}")

    yield client
    await client.close()


@pytest.fixture(scope="module")
async def test_index(es_client):
    """Create test index with clinical_concepts mapping."""
    index_name = "test_clinical_concepts"

    # Delete if exists
    if await es_client.indices.exists(index=index_name):
        await es_client.indices.delete(index=index_name)

    # Create index with mapping
    mapping = {
        "mappings": {
            "properties": {
                "patient_id": {"type": "keyword"},
                "document_id": {"type": "keyword"},
                "concept_cui": {"type": "keyword"},
                "concept_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "concept_type": {"type": "keyword"},
                "date": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis"
                },
                "meta_annotations": {
                    "properties": {
                        "Negation": {"type": "keyword"},
                        "Temporality": {"type": "keyword"},
                        "Experiencer": {"type": "keyword"},
                        "Certainty": {"type": "keyword"}
                    }
                },
                "confidence": {"type": "float"},
                "sentence": {"type": "text"}
            }
        }
    }
    await es_client.indices.create(index=index_name, body=mapping)

    yield index_name

    # Cleanup
    await es_client.indices.delete(index=index_name)


@pytest.fixture
async def test_data(es_client, test_index):
    """Insert test data into Elasticsearch."""
    patient_id = str(uuid4())
    documents = [
        {
            "patient_id": patient_id,
            "document_id": "doc-1",
            "concept_cui": "C0011849",
            "concept_name": "Diabetes Mellitus",
            "concept_type": "condition",
            "date": datetime(2023, 1, 15, 10, 30).isoformat(),
            "meta_annotations": {
                "Negation": "Affirmed",
                "Temporality": "Current",
                "Experiencer": "Patient",
                "Certainty": "High"
            },
            "confidence": 0.95,
            "sentence": "Patient diagnosed with Type 2 Diabetes."
        },
        {
            "patient_id": patient_id,
            "document_id": "doc-2",
            "concept_cui": "C0011849",
            "concept_name": "Diabetes Mellitus",
            "concept_type": "condition",
            "date": datetime(2023, 2, 20, 14, 15).isoformat(),
            "meta_annotations": {
                "Negation": "Affirmed",
                "Temporality": "Current",
                "Experiencer": "Patient",
                "Certainty": "High"
            },
            "confidence": 0.92,
            "sentence": "HbA1c 8.5%, diabetes management plan updated."
        },
        {
            "patient_id": patient_id,
            "document_id": "doc-3",
            "concept_cui": "C0020538",
            "concept_name": "Hypertension",
            "concept_type": "condition",
            "date": datetime(2023, 1, 10, 9, 0).isoformat(),
            "meta_annotations": {
                "Negation": "Affirmed",
                "Temporality": "Historical",
                "Experiencer": "Patient",
                "Certainty": "High"
            },
            "confidence": 0.88,
            "sentence": "History of hypertension, well controlled."
        },
        {
            "patient_id": patient_id,
            "document_id": "doc-4",
            "concept_cui": "C0008031",
            "concept_name": "Chest Pain",
            "concept_type": "symptom",
            "date": datetime(2023, 3, 5, 16, 45).isoformat(),
            "meta_annotations": {
                "Negation": "Negated",
                "Temporality": "Current",
                "Experiencer": "Patient",
                "Certainty": "High"
            },
            "confidence": 0.90,
            "sentence": "Patient denies chest pain."
        },
        {
            "patient_id": patient_id,
            "document_id": "doc-5",
            "concept_cui": "C0004238",
            "concept_name": "Atrial Fibrillation",
            "concept_type": "condition",
            "date": datetime(2022, 12, 1, 11, 30).isoformat(),
            "meta_annotations": {
                "Negation": "Affirmed",
                "Temporality": "Current",
                "Experiencer": "Family",
                "Certainty": "Medium"
            },
            "confidence": 0.75,
            "sentence": "Family history of atrial fibrillation."
        }
    ]

    # Index documents
    for doc in documents:
        await es_client.index(index=test_index, document=doc)

    # Refresh index to make documents searchable
    await es_client.indices.refresh(index=test_index)

    return {"patient_id": patient_id, "documents": documents}


@pytest.fixture
async def repo(test_index):
    """Create repository instance for testing."""
    repo = ElasticsearchTimelineRepository()
    repo.index_name = test_index  # Override to use test index
    yield repo
    await repo.close()


@pytest.mark.asyncio
async def test_query_all_concepts_for_patient(repo, test_data):
    """Test querying all concepts for a patient."""
    # Act
    mentions = await repo.query_concepts_by_patient(
        patient_id=test_data["patient_id"]
    )

    # Assert
    assert len(mentions) == 5
    # Should be sorted by date ascending
    dates = [m.date for m in mentions]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_query_concepts_with_concept_filter(repo, test_data):
    """Test filtering by concept CUI."""
    # Act - filter for diabetes only
    mentions = await repo.query_concepts_by_patient(
        patient_id=test_data["patient_id"],
        concept_filter=["C0011849"]
    )

    # Assert
    assert len(mentions) == 2
    assert all(m.meta_annotations.Negation == "Affirmed" for m in mentions)


@pytest.mark.asyncio
async def test_query_concepts_with_date_range(repo, test_data):
    """Test filtering by date range."""
    # Act - get concepts from Jan-Feb 2023
    mentions = await repo.query_concepts_by_patient(
        patient_id=test_data["patient_id"],
        date_range=DateRange(
            start=datetime(2023, 1, 1),
            end=datetime(2023, 2, 28)
        )
    )

    # Assert
    assert len(mentions) == 3
    for mention in mentions:
        assert datetime(2023, 1, 1) <= mention.date <= datetime(2023, 2, 28)


@pytest.mark.asyncio
async def test_query_concepts_with_negation_filter(repo, test_data):
    """Test filtering by meta-annotation (Negation)."""
    # Act - only affirmed concepts
    mentions = await repo.query_concepts_by_patient(
        patient_id=test_data["patient_id"],
        meta_annotations={"Negation": "Affirmed"}
    )

    # Assert
    assert len(mentions) == 4  # Excludes "denies chest pain"
    assert all(m.meta_annotations.Negation == "Affirmed" for m in mentions)


@pytest.mark.asyncio
async def test_query_concepts_with_experiencer_filter(repo, test_data):
    """Test filtering by meta-annotation (Experiencer)."""
    # Act - only patient (not family history)
    mentions = await repo.query_concepts_by_patient(
        patient_id=test_data["patient_id"],
        meta_annotations={"Experiencer": "Patient"}
    )

    # Assert
    assert len(mentions) == 4  # Excludes family history
    assert all(m.meta_annotations.Experiencer == "Patient" for m in mentions)


@pytest.mark.asyncio
async def test_query_concepts_with_temporality_list_filter(repo, test_data):
    """Test filtering by list of temporality values (OR logic)."""
    # Act - Current OR Recent
    mentions = await repo.query_concepts_by_patient(
        patient_id=test_data["patient_id"],
        meta_annotations={"Temporality": ["Current", "Recent"]}
    )

    # Assert
    assert len(mentions) == 4  # Excludes Historical
    for mention in mentions:
        assert mention.meta_annotations.Temporality in ["Current", "Recent"]


@pytest.mark.asyncio
async def test_query_concepts_with_combined_filters(repo, test_data):
    """Test combining multiple filters."""
    # Act - Affirmed + Patient + Current/Recent + 2023
    mentions = await repo.query_concepts_by_patient(
        patient_id=test_data["patient_id"],
        concept_filter=["C0011849", "C0020538"],
        date_range=DateRange(
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        ),
        meta_annotations={
            "Negation": "Affirmed",
            "Experiencer": "Patient",
            "Temporality": ["Current", "Recent"]
        }
    )

    # Assert
    assert len(mentions) == 2  # Only diabetes mentions (hypertension is Historical)
    assert all(m.meta_annotations.Negation == "Affirmed" for m in mentions)
    assert all(m.meta_annotations.Experiencer == "Patient" for m in mentions)


@pytest.mark.asyncio
async def test_aggregate_concepts_by_month(repo, test_data):
    """Test concept aggregation by month."""
    # Act
    buckets = await repo.aggregate_concepts_by_date(
        patient_id=test_data["patient_id"],
        granularity="month"
    )

    # Assert
    assert len(buckets) > 0
    # Check bucket structure
    assert "key" in buckets[0]
    assert "doc_count" in buckets[0]
    assert "concept_counts" in buckets[0]


@pytest.mark.asyncio
async def test_aggregate_concepts_by_day(repo, test_data):
    """Test concept aggregation by day."""
    # Act
    buckets = await repo.aggregate_concepts_by_date(
        patient_id=test_data["patient_id"],
        granularity="day"
    )

    # Assert
    assert len(buckets) == 5  # 5 distinct days
    # Each day should have at least 1 concept
    assert all(b["doc_count"] >= 1 for b in buckets)


@pytest.mark.asyncio
async def test_aggregate_concepts_with_filter(repo, test_data):
    """Test aggregation with concept filter."""
    # Act - aggregate only diabetes
    buckets = await repo.aggregate_concepts_by_date(
        patient_id=test_data["patient_id"],
        granularity="month",
        concept_filter=["C0011849"]
    )

    # Assert
    # Should only have buckets for months with diabetes mentions
    total_docs = sum(b["doc_count"] for b in buckets)
    assert total_docs == 2  # 2 diabetes mentions


@pytest.mark.asyncio
async def test_query_nonexistent_patient(repo):
    """Test querying a patient with no data."""
    # Act
    mentions = await repo.query_concepts_by_patient(
        patient_id="nonexistent-patient-id"
    )

    # Assert
    assert mentions == []
