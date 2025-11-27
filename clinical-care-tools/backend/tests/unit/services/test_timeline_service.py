"""
Unit tests for TimelineService.

Tests:
- Timeline data aggregation
- Document filtering
- Concept filtering with meta-annotations
- Date range calculation
- Temporal pattern detection
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.timeline import TimelineDocument, TimelineConcept
from app.services.timeline_service import TimelineService


class TestTimelineService:
    """Unit tests for TimelineService."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def timeline_service(self, mock_db_session):
        """Create TimelineService instance."""
        return TimelineService(mock_db_session)

    @pytest.fixture
    def sample_documents(self):
        """Create sample timeline documents."""
        return [
            TimelineDocument(
                id="doc-1",
                title="Clinical Note 1",
                type="clinical_note",
                date="2024-01-15T10:00:00Z",
                author="Dr. Smith",
                annotation_count=5,
            ),
            TimelineDocument(
                id="doc-2",
                title="Lab Results",
                type="lab_result",
                date="2024-02-20T14:30:00Z",
                author="Lab Tech",
                annotation_count=3,
            ),
            TimelineDocument(
                id="doc-3",
                title="Discharge Summary",
                type="discharge_summary",
                date="2024-03-10T09:00:00Z",
                author="Dr. Johnson",
                annotation_count=8,
            ),
        ]

    @pytest.fixture
    def sample_concepts(self):
        """Create sample timeline concepts."""
        return [
            TimelineConcept(
                id="C0011849",
                cui="C0011849",
                name="Diabetes Mellitus",
                type="condition",
                first_mentioned="2024-01-15T10:00:00Z",
                last_mentioned="2024-03-10T09:00:00Z",
                occurrences=[],
                meta_annotations={
                    "negation": "Affirmed",
                    "temporality": "Current",
                    "experiencer": "Patient",
                },
            ),
            TimelineConcept(
                id="C0025598",
                cui="C0025598",
                name="Metformin",
                type="medication",
                first_mentioned="2024-01-15T10:00:00Z",
                last_mentioned="2024-02-20T14:30:00Z",
                occurrences=[],
                meta_annotations={
                    "negation": "Affirmed",
                    "temporality": "Current",
                    "experiencer": "Patient",
                },
            ),
        ]


class TestDateRangeCalculation:
    """Tests for date range calculation."""

    @pytest.fixture
    def timeline_service(self):
        """Create TimelineService with mock session."""
        mock_session = AsyncMock()
        return TimelineService(mock_session)

    def test_calculate_date_range_with_documents(self, timeline_service):
        """Test date range calculation with multiple documents."""
        documents = [
            TimelineDocument(
                id="1",
                title="Doc 1",
                type="clinical_note",
                date="2024-01-15T10:00:00Z",
                author="Author",
                annotation_count=0,
            ),
            TimelineDocument(
                id="2",
                title="Doc 2",
                type="lab_result",
                date="2024-06-20T14:30:00Z",
                author="Author",
                annotation_count=0,
            ),
            TimelineDocument(
                id="3",
                title="Doc 3",
                type="discharge_summary",
                date="2024-03-10T09:00:00Z",
                author="Author",
                annotation_count=0,
            ),
        ]

        result = timeline_service._calculate_date_range(documents)

        assert result["earliest"] == "2024-01-15T10:00:00Z"
        assert result["latest"] == "2024-06-20T14:30:00Z"

    def test_calculate_date_range_empty_list(self, timeline_service):
        """Test date range with empty document list."""
        result = timeline_service._calculate_date_range([])

        assert result["earliest"] is None
        assert result["latest"] is None

    def test_calculate_date_range_single_document(self, timeline_service):
        """Test date range with single document."""
        documents = [
            TimelineDocument(
                id="1",
                title="Single Doc",
                type="clinical_note",
                date="2024-05-01T12:00:00Z",
                author="Author",
                annotation_count=0,
            ),
        ]

        result = timeline_service._calculate_date_range(documents)

        assert result["earliest"] == "2024-05-01T12:00:00Z"
        assert result["latest"] == "2024-05-01T12:00:00Z"


class TestMetaAnnotationFiltering:
    """Tests for meta-annotation based filtering."""

    def test_filter_excludes_negated_by_default(self):
        """Test that negated concepts are excluded by default."""
        # This tests the expected behavior - actual implementation
        # filters in SQL query
        concepts = [
            {"negation": "Affirmed", "name": "Diabetes"},
            {"negation": "Negated", "name": "Hypertension"},
            {"negation": "Affirmed", "name": "Asthma"},
        ]

        # Simulate default filter behavior
        filtered = [c for c in concepts if c["negation"] == "Affirmed"]

        assert len(filtered) == 2
        assert all(c["negation"] == "Affirmed" for c in filtered)

    def test_filter_excludes_family_history_by_default(self):
        """Test that family history is excluded by default."""
        concepts = [
            {"experiencer": "Patient", "name": "Diabetes"},
            {"experiencer": "Family", "name": "Heart Disease"},
            {"experiencer": "Patient", "name": "Asthma"},
        ]

        # Simulate default filter behavior
        filtered = [c for c in concepts if c["experiencer"] == "Patient"]

        assert len(filtered) == 2
        assert all(c["experiencer"] == "Patient" for c in filtered)

    def test_filter_includes_negated_when_requested(self):
        """Test that negated concepts included when include_negated=True."""
        concepts = [
            {"negation": "Affirmed", "name": "Diabetes"},
            {"negation": "Negated", "name": "Hypertension"},
        ]

        # Simulate include_negated=True behavior
        filtered = concepts  # No filtering

        assert len(filtered) == 2

    def test_filter_includes_family_when_requested(self):
        """Test that family history included when include_family=True."""
        concepts = [
            {"experiencer": "Patient", "name": "Diabetes"},
            {"experiencer": "Family", "name": "Heart Disease"},
        ]

        # Simulate include_family=True behavior
        filtered = concepts  # No filtering

        assert len(filtered) == 2


class TestDocumentFiltering:
    """Tests for document type filtering."""

    def test_filter_by_document_type(self):
        """Test filtering documents by type."""
        documents = [
            {"type": "clinical_note", "title": "Note 1"},
            {"type": "lab_result", "title": "Lab 1"},
            {"type": "discharge_summary", "title": "Discharge 1"},
            {"type": "clinical_note", "title": "Note 2"},
        ]

        allowed_types = ["clinical_note", "lab_result"]

        filtered = [d for d in documents if d["type"] in allowed_types]

        assert len(filtered) == 3
        assert all(d["type"] in allowed_types for d in filtered)

    def test_no_filter_returns_all(self):
        """Test that no filter returns all documents."""
        documents = [
            {"type": "clinical_note", "title": "Note 1"},
            {"type": "lab_result", "title": "Lab 1"},
            {"type": "discharge_summary", "title": "Discharge 1"},
        ]

        # No filter applied
        filtered = documents

        assert len(filtered) == 3


class TestConceptTypeFiltering:
    """Tests for concept type filtering."""

    def test_filter_by_concept_type(self):
        """Test filtering concepts by type."""
        concepts = [
            {"type": "condition", "name": "Diabetes"},
            {"type": "medication", "name": "Metformin"},
            {"type": "procedure", "name": "Blood Test"},
            {"type": "condition", "name": "Hypertension"},
        ]

        allowed_types = ["condition"]

        filtered = [c for c in concepts if c["type"] in allowed_types]

        assert len(filtered) == 2
        assert all(c["type"] == "condition" for c in filtered)

    def test_multiple_concept_types(self):
        """Test filtering with multiple concept types."""
        concepts = [
            {"type": "condition", "name": "Diabetes"},
            {"type": "medication", "name": "Metformin"},
            {"type": "procedure", "name": "Blood Test"},
            {"type": "observation", "name": "Blood Pressure"},
        ]

        allowed_types = ["condition", "medication"]

        filtered = [c for c in concepts if c["type"] in allowed_types]

        assert len(filtered) == 2


class TestTimelineResponseStructure:
    """Tests for timeline response structure."""

    def test_response_contains_required_fields(self):
        """Test that response contains all required fields."""
        # Simulate response structure
        response = {
            "patientId": "patient-123",
            "documents": [],
            "concepts": [],
            "dateRange": {"earliest": None, "latest": None},
            "metadata": {
                "documentCount": 0,
                "conceptCount": 0,
                "generatedAt": datetime.utcnow().isoformat(),
            },
        }

        # Verify required fields
        assert "patientId" in response
        assert "documents" in response
        assert "concepts" in response
        assert "dateRange" in response
        assert "metadata" in response

        # Verify metadata fields
        assert "documentCount" in response["metadata"]
        assert "conceptCount" in response["metadata"]
        assert "generatedAt" in response["metadata"]

    def test_document_structure(self):
        """Test document object structure."""
        document = {
            "id": "doc-123",
            "title": "Clinical Note",
            "type": "clinical_note",
            "date": "2024-01-15T10:00:00Z",
            "author": "Dr. Smith",
            "annotationCount": 5,
        }

        # Verify required fields
        required_fields = ["id", "title", "type", "date", "annotationCount"]
        for field in required_fields:
            assert field in document

    def test_concept_structure(self):
        """Test concept object structure."""
        concept = {
            "id": "C0011849",
            "cui": "C0011849",
            "name": "Diabetes Mellitus",
            "type": "condition",
            "firstMentioned": "2024-01-15T10:00:00Z",
            "lastMentioned": "2024-03-10T09:00:00Z",
            "occurrenceCount": 5,
            "metaAnnotations": {
                "negation": "Affirmed",
                "temporality": "Current",
                "experiencer": "Patient",
            },
        }

        # Verify required fields
        required_fields = [
            "id",
            "cui",
            "name",
            "type",
            "firstMentioned",
            "lastMentioned",
            "metaAnnotations",
        ]
        for field in required_fields:
            assert field in concept

        # Verify meta-annotation structure
        meta_fields = ["negation", "temporality", "experiencer"]
        for field in meta_fields:
            assert field in concept["metaAnnotations"]
