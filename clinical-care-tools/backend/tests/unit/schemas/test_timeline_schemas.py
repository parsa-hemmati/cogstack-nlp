"""Unit tests for timeline schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.timeline import (
    ConceptOccurrence,
    TimelineConcept,
    TimelineDocument,
    TimelineQueryParams,
    TimelineResponse,
)


class TestTimelineQueryParams:
    """Tests for TimelineQueryParams schema."""

    def test_query_params_minimal(self):
        """Test minimal query params (patient_id only)."""
        patient_id = str(uuid4())
        params = TimelineQueryParams(patient_id=patient_id)

        assert params.patient_id == patient_id
        assert params.start_date is None
        assert params.end_date is None
        assert params.document_types is None
        assert params.concept_types is None
        assert params.include_negated is False
        assert params.include_family is False

    def test_query_params_with_filters(self):
        """Test query params with all filters."""
        patient_id = str(uuid4())
        start = "2023-01-01T00:00:00"
        end = "2023-12-31T23:59:59"

        params = TimelineQueryParams(
            patient_id=patient_id,
            start_date=start,
            end_date=end,
            document_types=["clinical_note", "lab_report"],
            concept_types=["condition", "medication"],
            include_negated=True,
            include_family=True,
        )

        assert params.patient_id == patient_id
        assert params.start_date == start
        assert params.end_date == end
        assert params.document_types == ["clinical_note", "lab_report"]
        assert params.concept_types == ["condition", "medication"]
        assert params.include_negated is True
        assert params.include_family is True

    def test_query_params_invalid_patient_id(self):
        """Test that invalid UUID is rejected."""
        with pytest.raises(ValidationError):
            TimelineQueryParams(patient_id="not-a-uuid")

    def test_query_params_defaults(self):
        """Test default values for boolean flags."""
        patient_id = str(uuid4())
        params = TimelineQueryParams(patient_id=patient_id)

        # Defaults should exclude negated and family history
        assert params.include_negated is False
        assert params.include_family is False


class TestTimelineDocument:
    """Tests for TimelineDocument schema."""

    def test_document_complete(self):
        """Test timeline document with all fields."""
        doc_id = str(uuid4())
        date = "2023-06-15T10:30:00"

        doc = TimelineDocument(
            id=doc_id,
            title="Clinical Note",
            type="clinical_note",
            date=date,
            author="Dr. Smith",
            department="Cardiology",
            content_preview="Patient presents with chest pain...",
            annotation_count=15,
        )

        assert doc.id == doc_id
        assert doc.title == "Clinical Note"
        assert doc.type == "clinical_note"
        assert doc.date == date
        assert doc.author == "Dr. Smith"
        assert doc.department == "Cardiology"
        assert doc.content_preview == "Patient presents with chest pain..."
        assert doc.annotation_count == 15

    def test_document_minimal(self):
        """Test timeline document with required fields only."""
        doc_id = str(uuid4())
        date = "2023-06-15T10:30:00"

        doc = TimelineDocument(
            id=doc_id,
            title="Clinical Note",
            type="clinical_note",
            date=date,
            annotation_count=0,
        )

        assert doc.id == doc_id
        assert doc.title == "Clinical Note"
        assert doc.type == "clinical_note"
        assert doc.date == date
        assert doc.author is None
        assert doc.department is None
        assert doc.content_preview is None
        assert doc.annotation_count == 0


class TestTimelineConcept:
    """Tests for TimelineConcept schema."""

    def test_concept_complete(self):
        """Test timeline concept with all fields."""
        concept_id = str(uuid4())
        first = "2023-01-15T08:00:00"
        last = "2023-11-30T14:00:00"

        concept = TimelineConcept(
            id=concept_id,
            cui="C0020538",
            name="Hypertension",
            type="condition",
            first_mentioned=first,
            last_mentioned=last,
            occurrences=[
                ConceptOccurrence(
                    document_id=str(uuid4()),
                    date="2023-01-15T08:00:00",
                    context="Patient has history of hypertension",
                    start_char=24,
                    end_char=36,
                )
            ],
            meta_annotations={
                "negation": "Affirmed",
                "temporality": "Current",
                "experiencer": "Patient",
            },
        )

        assert concept.id == concept_id
        assert concept.cui == "C0020538"
        assert concept.name == "Hypertension"
        assert concept.type == "condition"
        assert concept.first_mentioned == first
        assert concept.last_mentioned == last
        assert len(concept.occurrences) == 1
        assert concept.meta_annotations["negation"] == "Affirmed"
        assert concept.meta_annotations["temporality"] == "Current"
        assert concept.meta_annotations["experiencer"] == "Patient"

    def test_concept_occurrence(self):
        """Test ConceptOccurrence schema."""
        doc_id = str(uuid4())
        date = "2023-06-15T10:30:00"

        occurrence = ConceptOccurrence(
            document_id=doc_id,
            date=date,
            context="Patient diagnosed with diabetes mellitus type 2",
            start_char=24,
            end_char=48,
        )

        assert occurrence.document_id == doc_id
        assert occurrence.date == date
        assert occurrence.context == "Patient diagnosed with diabetes mellitus type 2"
        assert occurrence.start_char == 24
        assert occurrence.end_char == 48


class TestTimelineResponse:
    """Tests for TimelineResponse schema."""

    def test_timeline_response_complete(self):
        """Test complete timeline response."""
        patient_id = str(uuid4())
        doc_id = str(uuid4())
        concept_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        response = TimelineResponse(
            patient_id=patient_id,
            timeline={
                "documents": [
                    {
                        "id": doc_id,
                        "title": "Clinical Note",
                        "type": "clinical_note",
                        "date": "2023-06-15T10:30:00",
                        "annotation_count": 5,
                    }
                ],
                "concepts": [
                    {
                        "id": concept_id,
                        "cui": "C0020538",
                        "name": "Hypertension",
                        "type": "condition",
                        "first_mentioned": "2023-01-15T08:00:00",
                        "last_mentioned": "2023-11-30T14:00:00",
                        "occurrences": [],
                        "meta_annotations": {
                            "negation": "Affirmed",
                            "temporality": "Current",
                            "experiencer": "Patient",
                        },
                    }
                ],
                "date_range": {
                    "earliest": "2023-01-15T08:00:00",
                    "latest": "2023-11-30T14:00:00",
                },
            },
            metadata={
                "document_count": 1,
                "concept_count": 1,
                "generated_at": now,
            },
        )

        assert response.patient_id == patient_id
        assert len(response.timeline["documents"]) == 1
        assert len(response.timeline["concepts"]) == 1
        assert response.timeline["date_range"]["earliest"] == "2023-01-15T08:00:00"
        assert response.timeline["date_range"]["latest"] == "2023-11-30T14:00:00"
        assert response.metadata["document_count"] == 1
        assert response.metadata["concept_count"] == 1
        assert response.metadata["generated_at"] == now

    def test_timeline_response_empty(self):
        """Test timeline response with no documents or concepts."""
        patient_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        response = TimelineResponse(
            patient_id=patient_id,
            timeline={
                "documents": [],
                "concepts": [],
                "date_range": {
                    "earliest": None,
                    "latest": None,
                },
            },
            metadata={
                "document_count": 0,
                "concept_count": 0,
                "generated_at": now,
            },
        )

        assert response.patient_id == patient_id
        assert len(response.timeline["documents"]) == 0
        assert len(response.timeline["concepts"]) == 0
        assert response.timeline["date_range"]["earliest"] is None
        assert response.timeline["date_range"]["latest"] is None
        assert response.metadata["document_count"] == 0
        assert response.metadata["concept_count"] == 0


class TestTimelineSchemaValidation:
    """Tests for schema validation edge cases."""

    def test_date_format_validation(self):
        """Test that date strings must be ISO 8601 format."""
        # Valid ISO 8601
        doc_id = str(uuid4())
        doc = TimelineDocument(
            id=doc_id,
            title="Test",
            type="clinical_note",
            date="2023-06-15T10:30:00.000Z",  # ISO with timezone
            annotation_count=0,
        )
        assert doc.date == "2023-06-15T10:30:00.000Z"

    def test_empty_concept_occurrences(self):
        """Test concept with no occurrences."""
        concept = TimelineConcept(
            id=str(uuid4()),
            cui="C0011849",
            name="Diabetes Mellitus",
            type="condition",
            first_mentioned="2023-01-01T00:00:00",
            last_mentioned="2023-01-01T00:00:00",
            occurrences=[],  # Empty list
            meta_annotations={
                "negation": "Affirmed",
                "temporality": "Current",
                "experiencer": "Patient",
            },
        )
        assert len(concept.occurrences) == 0

    def test_meta_annotations_structure(self):
        """Test meta-annotations dictionary structure."""
        concept = TimelineConcept(
            id=str(uuid4()),
            cui="C0011849",
            name="Diabetes Mellitus",
            type="condition",
            first_mentioned="2023-01-01T00:00:00",
            last_mentioned="2023-01-01T00:00:00",
            occurrences=[],
            meta_annotations={
                "negation": "Negated",
                "temporality": "Past",
                "experiencer": "Family",
            },
        )

        assert concept.meta_annotations["negation"] == "Negated"
        assert concept.meta_annotations["temporality"] == "Past"
        assert concept.meta_annotations["experiencer"] == "Family"
