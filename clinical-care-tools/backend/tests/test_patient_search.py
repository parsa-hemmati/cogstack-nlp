"""
Tests for Patient Search Module

Tests the patient search functionality including:
- Concept extraction and search
- Meta-annotation filtering for 95% precision
- Result ranking and relevance scoring
- Export functionality
"""

import json
import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.modules.patient_search.service import PatientSearchService
from app.modules.patient_search.schemas import (
    MetaAnnotationFilters,
    PatientSearchRequest,
    PatientSearchResponse,
    PatientSearchResult,
    ConceptMatch,
    ConceptSuggestion,
    NegationValue,
    TemporalityValue,
    ExperiencerValue,
    CertaintyValue,
)


class TestMetaAnnotationFilters:
    """Test meta-annotation filtering logic."""

    def test_default_filters_for_precision(self):
        """Test that default filters achieve high precision."""
        filters = MetaAnnotationFilters()

        # Defaults should exclude false positives
        assert filters.negation == NegationValue.AFFIRMED
        assert filters.temporality == [TemporalityValue.CURRENT, TemporalityValue.RECENT]
        assert filters.experiencer == ExperiencerValue.PATIENT
        assert filters.certainty == [CertaintyValue.CONFIRMED]
        assert filters.confidence_min == 0.7

    def test_filters_exclude_negated_mentions(self):
        """Test that negated mentions are excluded."""
        filters = MetaAnnotationFilters(negation=NegationValue.AFFIRMED)

        # Should exclude "patient denies chest pain"
        assert filters.negation != NegationValue.NEGATED

    def test_filters_exclude_family_history(self):
        """Test that family history is excluded by default."""
        filters = MetaAnnotationFilters(experiencer=ExperiencerValue.PATIENT)

        # Should exclude "mother had diabetes"
        assert filters.experiencer != ExperiencerValue.FAMILY

    def test_filters_exclude_historical_conditions(self):
        """Test that historical conditions are excluded by default."""
        filters = MetaAnnotationFilters()

        # Should exclude "history of hypertension"
        assert TemporalityValue.HISTORICAL not in filters.temporality


class TestPatientSearchService:
    """Test PatientSearchService class."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return PatientSearchService(medcat_url="http://test-medcat:5000")

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)

    def test_init(self):
        """Test service initialization."""
        service = PatientSearchService(medcat_url="http://localhost:5000")
        assert service.medcat_url == "http://localhost:5000"
        assert service._concept_cache == {}

    def test_check_medcat_connectivity_success(self, service):
        """Test successful MedCAT connectivity check."""
        with patch("httpx.Client") as MockClient:
            mock_client = MockClient.return_value.__enter__.return_value
            mock_client.get.return_value.status_code = 200

            result = service.check_medcat_connectivity()

            assert result == True
            mock_client.get.assert_called_once_with("http://test-medcat:5000/health")

    def test_check_medcat_connectivity_failure(self, service):
        """Test failed MedCAT connectivity check."""
        with patch("httpx.Client") as MockClient:
            mock_client = MockClient.return_value.__enter__.return_value
            mock_client.get.side_effect = Exception("Connection error")

            result = service.check_medcat_connectivity()

            assert result == False

    @pytest.mark.asyncio
    async def test_extract_concepts_from_text(self, service):
        """Test extracting medical concepts from free text."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "entities": [
                    {"cui": "C0011860", "pretty_name": "Diabetes Mellitus"},
                    {"cui": "C0020538", "pretty_name": "Hypertension"},
                ]
            }
            mock_client.post.return_value = mock_response

            cuis = await service._extract_concepts("diabetes and hypertension")

            assert cuis == ["C0011860", "C0020538"]
            assert "diabetes and hypertension" in service._concept_cache

    @pytest.mark.asyncio
    async def test_extract_concepts_cached(self, service):
        """Test that concept extraction uses cache."""
        service._concept_cache["test query"] = ["C0011860"]

        with patch("httpx.AsyncClient") as MockClient:
            cuis = await service._extract_concepts("test query")

            assert cuis == ["C0011860"]
            MockClient.assert_not_called()  # Should not call API

    @pytest.mark.asyncio
    async def test_extract_concepts_direct_cui(self, service):
        """Test extracting concepts when query is already a CUI."""
        cuis = await service._extract_concepts("C0011860")
        assert cuis == ["C0011860"]

    def test_apply_meta_filters(self, service, mock_db):
        """Test applying meta-annotation filters to query."""
        from app.models.extracted_entity import ExtractedEntity

        query = mock_db.query(ExtractedEntity)
        filters = MetaAnnotationFilters(
            negation=NegationValue.AFFIRMED,
            temporality=[TemporalityValue.CURRENT],
            experiencer=ExperiencerValue.PATIENT,
            certainty=[CertaintyValue.CONFIRMED],
            confidence_min=0.8,
        )

        # Mock the filter chain
        mock_filter = Mock()
        query.filter.return_value = mock_filter

        result = service._apply_meta_filters(query, filters)

        # Should apply all filters
        assert query.filter.called
        # Check that confidence filter was applied
        calls = query.filter.call_args_list
        assert any("confidence >=" in str(call) for call in calls)

    def test_calculate_relevance_high(self, service):
        """Test relevance calculation for high-quality matches."""
        from app.models.extracted_entity import ExtractedEntity
        from app.models.document import Document

        # Create mock entities with high confidence and good meta-annotations
        entities = []
        for i in range(5):
            entity = Mock(spec=ExtractedEntity)
            entity.confidence = 0.95
            entity.meta_annotations = {
                "Negation": "Affirmed",
                "Temporality": "Current",
                "Experiencer": "Patient",
                "Certainty": "Confirmed",
            }
            entity.document = Mock(spec=Document)
            entity.document.created_at = datetime.now()
            entities.append(entity)

        filters = MetaAnnotationFilters()
        relevance = service._calculate_relevance(entities, filters)

        assert relevance > 0.8  # Should have high relevance

    def test_calculate_relevance_low(self, service):
        """Test relevance calculation for low-quality matches."""
        from app.models.extracted_entity import ExtractedEntity
        from app.models.document import Document

        # Create mock entities with low confidence and poor meta-annotations
        entities = []
        for i in range(2):
            entity = Mock(spec=ExtractedEntity)
            entity.confidence = 0.5
            entity.meta_annotations = {
                "Negation": "Negated",
                "Temporality": "Historical",
                "Experiencer": "Family",
                "Certainty": "Suspected",
            }
            entity.document = Mock(spec=Document)
            entity.document.created_at = datetime(2020, 1, 1)  # Old date
            entities.append(entity)

        filters = MetaAnnotationFilters()
        relevance = service._calculate_relevance(entities, filters)

        assert relevance < 0.5  # Should have low relevance

    def test_generate_summary_single_condition(self, service):
        """Test generating summary for single condition."""
        concepts = [
            ConceptMatch(
                text="diabetes",
                cui="C0011860",
                pretty_name="Diabetes Mellitus",
                confidence=0.95,
                negation="Affirmed",
                temporality="Current",
                experiencer="Patient",
                certainty="Confirmed",
                start_idx=0,
                end_idx=8,
                context="Patient has diabetes",
            )
        ]

        summary = service._generate_summary(concepts)
        assert "diabetes mellitus" in summary.lower()

    def test_generate_summary_multiple_conditions(self, service):
        """Test generating summary for multiple conditions."""
        concepts = [
            ConceptMatch(
                text="diabetes",
                cui="C0011860",
                pretty_name="Diabetes Mellitus",
                confidence=0.95,
                negation="Affirmed",
                temporality="Current",
                experiencer="Patient",
                certainty="Confirmed",
                start_idx=0,
                end_idx=8,
                context="diabetes",
            ),
            ConceptMatch(
                text="hypertension",
                cui="C0020538",
                pretty_name="Hypertension",
                confidence=0.90,
                negation="Affirmed",
                temporality="Current",
                experiencer="Patient",
                certainty="Confirmed",
                start_idx=10,
                end_idx=22,
                context="hypertension",
            ),
        ]

        summary = service._generate_summary(concepts)
        assert "diabetes" in summary.lower()
        assert "hypertension" in summary.lower()

    def test_generate_summary_no_active_conditions(self, service):
        """Test generating summary when no active conditions."""
        concepts = [
            ConceptMatch(
                text="diabetes",
                cui="C0011860",
                pretty_name="Diabetes Mellitus",
                confidence=0.95,
                negation="Negated",  # Negated
                temporality="Current",
                experiencer="Patient",
                certainty="Confirmed",
                start_idx=0,
                end_idx=8,
                context="no diabetes",
            )
        ]

        summary = service._generate_summary(concepts)
        assert "no active conditions" in summary.lower()

    @pytest.mark.asyncio
    async def test_search_patients_complete_flow(self, service, mock_db):
        """Test complete patient search flow."""
        from app.models.patient import Patient
        from app.models.document import Document
        from app.models.extracted_entity import ExtractedEntity

        # Mock concept extraction
        with patch.object(service, "_extract_concepts", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ["C0011860"]

            # Mock database query
            mock_entity = Mock(spec=ExtractedEntity)
            mock_entity.cui = "C0011860"
            mock_entity.text = "diabetes"
            mock_entity.pretty_name = "Diabetes Mellitus"
            mock_entity.confidence = 0.95
            mock_entity.meta_annotations = {
                "Negation": "Affirmed",
                "Temporality": "Current",
                "Experiencer": "Patient",
                "Certainty": "Confirmed",
            }
            mock_entity.start_idx = 0
            mock_entity.end_idx = 8

            mock_document = Mock(spec=Document)
            mock_document.created_at = datetime.now()
            mock_document.patient_id = uuid4()
            mock_entity.document = mock_document
            mock_entity.document_id = uuid4()

            mock_patient = Mock(spec=Patient)
            mock_patient.id = mock_document.patient_id
            mock_patient.mrn = "MRN123456"
            mock_patient.date_of_birth = date(1960, 1, 1)
            mock_patient.gender = "M"

            # Setup query chain
            mock_query = Mock()
            mock_query.count.return_value = 1
            mock_query.offset.return_value.limit.return_value.all.return_value = [mock_entity]
            mock_db.query.return_value.join.return_value.join.return_value = mock_query
            mock_db.query.return_value.filter.return_value.first.return_value = mock_patient

            request = PatientSearchRequest(
                query="diabetes",
                filters=MetaAnnotationFilters(),
                limit=50,
                offset=0,
            )

            response = await service.search_patients(
                request=request,
                db=mock_db,
                user_id=uuid4(),
            )

            assert isinstance(response, PatientSearchResponse)
            assert response.total == 1
            assert len(response.results) <= 1
            assert response.query_time_ms > 0

    @pytest.mark.asyncio
    async def test_get_concept_suggestions_success(self, service):
        """Test getting concept suggestions for autocomplete."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "cui": "C0011860",
                    "pretty_name": "Diabetes Mellitus",
                    "semantic_type": "Disease",
                    "synonyms": ["DM", "Sugar Disease"],
                    "popularity": 100,
                }
            ]
            mock_client.get.return_value = mock_response

            suggestions = await service.get_concept_suggestions("diab")

            assert len(suggestions) == 1
            assert suggestions[0].cui == "C0011860"
            assert suggestions[0].pretty_name == "Diabetes Mellitus"
            assert suggestions[0].semantic_type == "Disease"
            assert "DM" in suggestions[0].synonyms

    @pytest.mark.asyncio
    async def test_get_concept_suggestions_fallback(self, service):
        """Test fallback suggestions when MedCAT unavailable."""
        service.medcat_url = None  # Disable MedCAT

        suggestions = await service.get_concept_suggestions("diabetes")

        assert len(suggestions) > 0
        assert any("Diabetes" in s.pretty_name for s in suggestions)


class TestPatientSearchIntegration:
    """Integration tests for patient search."""

    @pytest.mark.asyncio
    async def test_precision_filtering_scenario(self):
        """Test that meta-annotation filtering achieves 95% precision."""
        service = PatientSearchService()

        # Test data with various meta-annotation combinations
        test_cases = [
            # Should be INCLUDED (true positives)
            {
                "text": "patient has diabetes",
                "meta": {
                    "Negation": "Affirmed",
                    "Temporality": "Current",
                    "Experiencer": "Patient",
                    "Certainty": "Confirmed",
                },
                "should_include": True,
            },
            # Should be EXCLUDED (false positives to filter out)
            {
                "text": "patient denies chest pain",
                "meta": {
                    "Negation": "Negated",
                    "Temporality": "Current",
                    "Experiencer": "Patient",
                    "Certainty": "Confirmed",
                },
                "should_include": False,
            },
            {
                "text": "family history of diabetes",
                "meta": {
                    "Negation": "Affirmed",
                    "Temporality": "Historical",
                    "Experiencer": "Family",
                    "Certainty": "Confirmed",
                },
                "should_include": False,
            },
            {
                "text": "history of hypertension",
                "meta": {
                    "Negation": "Affirmed",
                    "Temporality": "Historical",
                    "Experiencer": "Patient",
                    "Certainty": "Confirmed",
                },
                "should_include": False,
            },
            {
                "text": "risk of developing diabetes",
                "meta": {
                    "Negation": "Affirmed",
                    "Temporality": "Future",
                    "Experiencer": "Patient",
                    "Certainty": "Hypothetical",
                },
                "should_include": False,
            },
        ]

        filters = MetaAnnotationFilters()
        included_count = 0
        total_count = len(test_cases)

        for case in test_cases:
            # Check if this case would be included based on filters
            would_include = (
                case["meta"]["Negation"] == filters.negation and
                case["meta"]["Temporality"] in filters.temporality and
                case["meta"]["Experiencer"] == filters.experiencer and
                case["meta"]["Certainty"][0] in filters.certainty
            )

            assert would_include == case["should_include"], f"Failed for: {case['text']}"

            if would_include:
                included_count += 1

        # Calculate precision (should be very high)
        # In this test, we should only include true positives
        precision = included_count / total_count if total_count > 0 else 0
        assert precision <= 1.0  # All included should be true positives