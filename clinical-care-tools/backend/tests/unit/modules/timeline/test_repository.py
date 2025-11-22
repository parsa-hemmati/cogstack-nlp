"""
Unit tests for Elasticsearch Timeline Repository.

Tests Elasticsearch queries for temporal concept aggregation and filtering with mocked ES client.
"""

import pytest
from datetime import date, datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.modules.timeline.repository import ElasticsearchTimelineRepository


@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client."""
    client = MagicMock()
    # Mock async search method
    client.search = AsyncMock()
    return client


@pytest.fixture
def repository(mock_es_client):
    """Create repository with mocked ES client."""
    return ElasticsearchTimelineRepository(
        es_client=mock_es_client,
        index_name="test_medcat_annotations"
    )


class TestQueryPatientConcepts:
    """Test query_patient_concepts method."""

    @pytest.mark.asyncio
    async def test_query_filters_by_patient_id(self, repository, mock_es_client):
        """Test that query filters by patient_id."""
        patient_id = uuid4()

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        # Execute
        await repository.query_patient_concepts(
            patient_id=patient_id,
        )

        # Verify
        mock_es_client.search.assert_called_once()
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Check patient_id filter exists in bool query
        assert "bool" in query
        assert "must" in query["bool"]

        # Find patient_id term
        patient_id_filter = None
        for clause in query["bool"]["must"]:
            if "term" in clause and "patient_id" in clause["term"]:
                patient_id_filter = clause["term"]["patient_id"]
                break

        assert patient_id_filter == str(patient_id)

    @pytest.mark.asyncio
    async def test_query_filters_by_date_range(self, repository, mock_es_client):
        """Test that query filters by date range."""
        patient_id = uuid4()
        date_start = date(2024, 1, 1)
        date_end = date(2024, 12, 31)

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        # Execute
        await repository.query_patient_concepts(
            patient_id=patient_id,
            date_start=date_start,
            date_end=date_end,
        )

        # Verify
        mock_es_client.search.assert_called_once()
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Check date range filter exists
        assert "bool" in query
        assert "must" in query["bool"]

        # Find range filter
        range_filter = None
        for clause in query["bool"]["must"]:
            if "range" in clause and "document_date" in clause["range"]:
                range_filter = clause["range"]["document_date"]
                break

        assert range_filter is not None
        assert "gte" in range_filter
        assert "lte" in range_filter

    @pytest.mark.asyncio
    async def test_query_filters_by_concept_cuis(self, repository, mock_es_client):
        """Test that query filters by concept CUIs."""
        patient_id = uuid4()
        concept_cuis = ["C0011860", "C0020538"]

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        # Execute
        await repository.query_patient_concepts(
            patient_id=patient_id,
            concept_cuis=concept_cuis,
        )

        # Verify
        mock_es_client.search.assert_called_once()
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Check concept_cui filter exists
        assert "bool" in query
        assert "must" in query["bool"]

        # Find terms filter for concept_cui
        concept_filter = None
        for clause in query["bool"]["must"]:
            if "terms" in clause and "concept_cui" in clause["terms"]:
                concept_filter = clause["terms"]["concept_cui"]
                break

        assert concept_filter == concept_cuis

    @pytest.mark.asyncio
    async def test_query_filters_by_meta_annotations(self, repository, mock_es_client):
        """Test that query filters by meta-annotations (Negation, Experiencer, Temporality)."""
        patient_id = uuid4()

        meta_annotations = {
            "negation": "Affirmed",
            "experiencer": "Patient",
            "temporality": ["Current", "Recent"],
        }

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        # Execute
        await repository.query_patient_concepts(
            patient_id=patient_id,
            meta_annotations=meta_annotations,
        )

        # Verify
        mock_es_client.search.assert_called_once()
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Check meta-annotation filters exist
        assert "bool" in query
        assert "must" in query["bool"]

        # Check for Negation filter
        negation_found = False
        experiencer_found = False
        temporality_found = False

        for clause in query["bool"]["must"]:
            if "term" in clause:
                if "meta_anns.Negation" in clause["term"]:
                    negation_found = True
                    assert clause["term"]["meta_anns.Negation"] == "Affirmed"
                if "meta_anns.Experiencer" in clause["term"]:
                    experiencer_found = True
                    assert clause["term"]["meta_anns.Experiencer"] == "Patient"
            if "terms" in clause:
                if "meta_anns.Temporality" in clause["terms"]:
                    temporality_found = True
                    assert clause["terms"]["meta_anns.Temporality"] == ["Current", "Recent"]

        assert negation_found, "Negation filter not found"
        assert experiencer_found, "Experiencer filter not found"
        assert temporality_found, "Temporality filter not found"

    @pytest.mark.asyncio
    async def test_query_returns_formatted_results(self, repository, mock_es_client):
        """Test that query returns formatted results with document metadata."""
        patient_id = uuid4()
        doc_id = uuid4()

        # Mock ES response with actual hit
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "document_id": str(doc_id),
                            "document_date": "2024-03-15",
                            "concept_cui": "C0011860",
                            "concept_name": "Diabetes Mellitus",
                            "concept_type": "Disease",
                            "sentence": "Patient has diabetes.",
                            "start_char": 12,
                            "end_char": 20,
                            "confidence": 0.95,
                            "meta_anns": {
                                "Negation": "Affirmed",
                                "Experiencer": "Patient",
                                "Temporality": "Current",
                            }
                        }
                    }
                ]
            }
        }

        # Execute
        results = await repository.query_patient_concepts(patient_id=patient_id)

        # Verify
        assert len(results) == 1
        assert results[0]["concept_cui"] == "C0011860"
        assert results[0]["concept_name"] == "Diabetes Mellitus"
        assert results[0]["meta_anns"]["Negation"] == "Affirmed"


class TestAggregateConceptFrequency:
    """Test aggregate_concept_frequency method."""

    @pytest.mark.asyncio
    async def test_aggregate_monthly_frequency(self, repository, mock_es_client):
        """Test monthly concept frequency aggregation."""
        patient_id = uuid4()

        # Mock ES aggregation response
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 10},
                "hits": []
            },
            "aggregations": {
                "concepts": {
                    "buckets": [
                        {
                            "key": "C0011860",
                            "doc_count": 5,
                            "date_histogram": {
                                "buckets": [
                                    {
                                        "key_as_string": "2024-01-01",
                                        "doc_count": 2
                                    },
                                    {
                                        "key_as_string": "2024-02-01",
                                        "doc_count": 3
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }

        # Execute
        results = await repository.aggregate_concept_frequency(
            patient_id=patient_id,
            granularity="month"
        )

        # Verify ES call
        mock_es_client.search.assert_called_once()
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]

        # Check aggregation structure
        assert "aggs" in query
        assert "concepts" in query["aggs"]

        # Verify results format
        assert "C0011860" in results
        assert len(results["C0011860"]) == 2
        assert results["C0011860"][0]["date"] == "2024-01-01"
        assert results["C0011860"][0]["count"] == 2

    @pytest.mark.asyncio
    async def test_aggregate_supports_granularity_day(self, repository, mock_es_client):
        """Test daily granularity aggregation."""
        patient_id = uuid4()

        mock_es_client.search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []},
            "aggregations": {"concepts": {"buckets": []}}
        }

        # Execute
        await repository.aggregate_concept_frequency(
            patient_id=patient_id,
            granularity="day"
        )

        # Verify interval is set to day
        call_args = mock_es_client.search.call_args
        aggs = call_args[1]["body"]["aggs"]

        # Check that date_histogram interval is set
        # Structure: aggs -> concepts -> aggs -> date_histogram -> date_histogram -> calendar_interval
        date_hist = aggs["concepts"]["aggs"]["date_histogram"]["date_histogram"]
        assert date_hist["calendar_interval"] == "day"

    @pytest.mark.asyncio
    async def test_aggregate_filters_by_patient_id(self, repository, mock_es_client):
        """Test that aggregation filters by patient_id."""
        patient_id = uuid4()

        mock_es_client.search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []},
            "aggregations": {"concepts": {"buckets": []}}
        }

        # Execute
        await repository.aggregate_concept_frequency(patient_id=patient_id)

        # Verify patient_id filter in query
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        assert "bool" in query
        assert "must" in query["bool"]

        # Find patient_id term
        patient_id_filter = None
        for clause in query["bool"]["must"]:
            if "term" in clause and "patient_id" in clause["term"]:
                patient_id_filter = clause["term"]["patient_id"]
                break

        assert patient_id_filter == str(patient_id)

    @pytest.mark.asyncio
    async def test_query_filters_by_document_types(self, repository, mock_es_client):
        """Test that query filters by document types."""
        patient_id = uuid4()
        document_types = ["discharge", "clinic"]

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        # Execute
        await repository.query_patient_concepts(
            patient_id=patient_id,
            document_types=document_types,
        )

        # Verify
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Find document_type filter
        doc_type_filter = None
        for clause in query["bool"]["must"]:
            if "terms" in clause and "document_type" in clause["terms"]:
                doc_type_filter = clause["terms"]["document_type"]
                break

        assert doc_type_filter == document_types

    @pytest.mark.asyncio
    async def test_aggregate_with_concept_cuis_filter(self, repository, mock_es_client):
        """Test aggregation with concept CUI filter."""
        patient_id = uuid4()
        concept_cuis = ["C0011860"]

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []},
            "aggregations": {"concepts": {"buckets": []}}
        }

        # Execute
        await repository.aggregate_concept_frequency(
            patient_id=patient_id,
            concept_cuis=concept_cuis
        )

        # Verify CUI filter is added
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Find concept_cui filter
        cui_filter = None
        for clause in query["bool"]["must"]:
            if "terms" in clause and "concept_cui" in clause["terms"]:
                cui_filter = clause["terms"]["concept_cui"]
                break

        assert cui_filter == concept_cuis

    @pytest.mark.asyncio
    async def test_aggregate_with_date_range(self, repository, mock_es_client):
        """Test aggregation with date range filter."""
        patient_id = uuid4()
        date_start = date(2024, 1, 1)
        date_end = date(2024, 12, 31)

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []},
            "aggregations": {"concepts": {"buckets": []}}
        }

        # Execute
        await repository.aggregate_concept_frequency(
            patient_id=patient_id,
            date_start=date_start,
            date_end=date_end
        )

        # Verify date range filter
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Find range filter
        range_filter = None
        for clause in query["bool"]["must"]:
            if "range" in clause and "document_date" in clause["range"]:
                range_filter = clause["range"]["document_date"]
                break

        assert range_filter is not None
        assert "gte" in range_filter
        assert "lte" in range_filter

    @pytest.mark.asyncio
    async def test_query_filters_by_certainty(self, repository, mock_es_client):
        """Test that query filters by certainty meta-annotation."""
        patient_id = uuid4()

        meta_annotations = {
            "certainty": ["Confirmed", "Suspected"],
        }

        # Mock ES response
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        # Execute
        await repository.query_patient_concepts(
            patient_id=patient_id,
            meta_annotations=meta_annotations,
        )

        # Verify certainty filter
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Find certainty filter
        certainty_found = False
        for clause in query["bool"]["must"]:
            if "terms" in clause and "meta_anns.Certainty" in clause["terms"]:
                certainty_found = True
                assert clause["terms"]["meta_anns.Certainty"] == ["Confirmed", "Suspected"]
                break

        assert certainty_found, "Certainty filter not found"
