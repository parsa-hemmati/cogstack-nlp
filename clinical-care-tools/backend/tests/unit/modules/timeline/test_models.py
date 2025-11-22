"""
Unit tests for Timeline Pydantic models.

Tests validation, serialization, and business logic for timeline schemas.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4, UUID
from pydantic import ValidationError

from app.modules.timeline.models import (
    TimelineRequest,
    PatientTimeline,
    TimelineDocument,
    TimelineConcept,
    ConceptMention,
    ExportRequest,
    TimelineExport,
    TimelineFilter,
    ExportFormat,
    ExportStatus,
    MetaAnnotations,
)


class TestTimelineRequest:
    """Test TimelineRequest schema validation."""

    def test_valid_timeline_request(self):
        """Test creating a valid timeline request."""
        request = TimelineRequest(
            patient_id=uuid4(),
            date_start=date(2024, 1, 1),
            date_end=date(2024, 12, 31),
            concept_cuis=["C0011860", "C0020538"],
            meta_annotations=MetaAnnotations(
                negation="Affirmed",
                experiencer="Patient",
                temporality=["Current", "Recent"],
            ),
        )

        assert request.patient_id is not None
        assert request.date_start == date(2024, 1, 1)
        assert request.date_end == date(2024, 12, 31)
        assert len(request.concept_cuis) == 2

    def test_timeline_request_date_validation_fails_when_start_after_end(self):
        """Test that date_start must be before or equal to date_end."""
        with pytest.raises(ValidationError) as exc_info:
            TimelineRequest(
                patient_id=uuid4(),
                date_start=date(2024, 12, 31),
                date_end=date(2024, 1, 1),  # Before start - invalid
            )

        assert "date_end must be after date_start" in str(exc_info.value)

    def test_timeline_request_allows_same_start_and_end_date(self):
        """Test that date_start can equal date_end (single day timeline)."""
        request = TimelineRequest(
            patient_id=uuid4(),
            date_start=date(2024, 6, 15),
            date_end=date(2024, 6, 15),
        )

        assert request.date_start == request.date_end

    def test_timeline_request_validates_meta_annotation_enums(self):
        """Test that invalid meta-annotation values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TimelineRequest(
                patient_id=uuid4(),
                meta_annotations=MetaAnnotations(
                    negation="InvalidValue",  # Should be Affirmed/Negated/Possible
                ),
            )

        assert "negation" in str(exc_info.value).lower()

    def test_timeline_request_optional_filters(self):
        """Test that all filter fields are optional."""
        request = TimelineRequest(
            patient_id=uuid4(),
        )

        assert request.concept_cuis == []
        assert request.document_types == []
        assert request.date_start is None
        assert request.date_end is None


class TestPatientTimeline:
    """Test PatientTimeline schema serialization."""

    def test_patient_timeline_serialization(self):
        """Test PatientTimeline serializes all nested structures correctly."""
        patient_id = uuid4()
        doc_id = uuid4()

        mention = ConceptMention(
            document_id=doc_id,
            document_date=date(2024, 3, 15),
            sentence="Patient diagnosed with diabetes mellitus.",
            start_char=24,
            end_char=41,
            meta_annotations={"Negation": "Affirmed", "Experiencer": "Patient"},
            confidence=0.95,
        )

        concept = TimelineConcept(
            concept_cui="C0011860",
            name="Diabetes Mellitus",
            type="Disease",
            first_mention_date=date(2024, 3, 15),
            mention_count=1,  # Must match len(mentions)
            mentions=[mention],
        )

        document = TimelineDocument(
            id=doc_id,
            title="Clinic Note - 2024-03-15",
            type="clinic",
            document_date=date(2024, 3, 15),
            author="Dr. Smith",
            concept_count=3,
        )

        timeline = PatientTimeline(
            patient_id=patient_id,
            documents=[document],
            concepts=[concept],
            date_range=(date(2024, 1, 1), date(2024, 12, 31)),
            filters_applied={},
            statistics={
                "total_documents": 1,
                "total_concepts": 1,
                "date_span_days": 365,
            },
        )

        # Verify serialization
        assert timeline.patient_id == patient_id
        assert len(timeline.documents) == 1
        assert len(timeline.concepts) == 1
        assert timeline.concepts[0].mention_count == 1
        assert timeline.statistics["total_documents"] == 1

    def test_patient_timeline_empty_results(self):
        """Test PatientTimeline handles empty results."""
        timeline = PatientTimeline(
            patient_id=uuid4(),
            documents=[],
            concepts=[],
            date_range=(date(2024, 1, 1), date(2024, 12, 31)),
            filters_applied={},
            statistics={
                "total_documents": 0,
                "total_concepts": 0,
            },
        )

        assert len(timeline.documents) == 0
        assert len(timeline.concepts) == 0


class TestTimelineConcept:
    """Test TimelineConcept schema and mention grouping."""

    def test_timeline_concept_groups_mentions(self):
        """Test TimelineConcept correctly groups multiple mentions."""
        doc1_id = uuid4()
        doc2_id = uuid4()

        mention1 = ConceptMention(
            document_id=doc1_id,
            document_date=date(2024, 3, 15),
            sentence="Patient has diabetes.",
            start_char=12,
            end_char=20,
            meta_annotations={"Negation": "Affirmed"},
            confidence=0.92,
        )

        mention2 = ConceptMention(
            document_id=doc2_id,
            document_date=date(2024, 6, 20),
            sentence="Diabetes management plan updated.",
            start_char=0,
            end_char=8,
            meta_annotations={"Negation": "Affirmed"},
            confidence=0.88,
        )

        concept = TimelineConcept(
            concept_cui="C0011860",
            name="Diabetes Mellitus",
            type="Disease",
            first_mention_date=date(2024, 3, 15),
            mention_count=2,
            mentions=[mention1, mention2],
        )

        assert concept.mention_count == 2
        assert len(concept.mentions) == 2
        assert concept.first_mention_date == date(2024, 3, 15)

    def test_timeline_concept_validates_mention_count_matches_list(self):
        """Test that mention_count matches actual mentions list length."""
        mention = ConceptMention(
            document_id=uuid4(),
            document_date=date(2024, 3, 15),
            sentence="Test",
            start_char=0,
            end_char=4,
            meta_annotations={},
            confidence=0.9,
        )

        # This should validate mention_count matches len(mentions)
        with pytest.raises(ValidationError) as exc_info:
            TimelineConcept(
                concept_cui="C0011860",
                name="Diabetes",
                type="Disease",
                first_mention_date=date(2024, 3, 15),
                mention_count=5,  # Says 5...
                mentions=[mention],  # But only 1 mention
            )

        assert "mention_count" in str(exc_info.value).lower()


class TestTimelineExport:
    """Test TimelineExport schema and format validation."""

    def test_timeline_export_format_enum_pdf(self):
        """Test TimelineExport validates PDF format."""
        export = TimelineExport(
            id=uuid4(),
            patient_id=uuid4(),
            status=ExportStatus.COMPLETED,
            format=ExportFormat.PDF,
            download_url="https://example.com/exports/abc123.pdf",
            expires_at=datetime.now() + timedelta(days=7),
        )

        assert export.format == ExportFormat.PDF
        assert export.status == ExportStatus.COMPLETED

    def test_timeline_export_format_enum_fhir(self):
        """Test TimelineExport validates FHIR format."""
        export = TimelineExport(
            id=uuid4(),
            patient_id=uuid4(),
            status=ExportStatus.PROCESSING,
            format=ExportFormat.FHIR,
            download_url=None,  # Still processing
            expires_at=datetime.now() + timedelta(days=7),
        )

        assert export.format == ExportFormat.FHIR
        assert export.download_url is None

    def test_timeline_export_format_enum_json(self):
        """Test TimelineExport validates JSON format."""
        export = TimelineExport(
            id=uuid4(),
            patient_id=uuid4(),
            status=ExportStatus.COMPLETED,
            format=ExportFormat.JSON,
            download_url="https://example.com/exports/xyz789.json",
            expires_at=datetime.now() + timedelta(days=7),
        )

        assert export.format == ExportFormat.JSON

    def test_timeline_export_invalid_format_rejected(self):
        """Test that invalid export formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TimelineExport(
                id=uuid4(),
                patient_id=uuid4(),
                status=ExportStatus.COMPLETED,
                format="xml",  # Invalid - only pdf/fhir/json allowed
                download_url="https://example.com/exports/test.xml",
                expires_at=datetime.now() + timedelta(days=7),
            )

        assert "format" in str(exc_info.value).lower()

    def test_timeline_export_status_enum(self):
        """Test TimelineExport validates status enum."""
        # Valid statuses: processing, completed, failed
        for status in [ExportStatus.PROCESSING, ExportStatus.COMPLETED, ExportStatus.FAILED]:
            export = TimelineExport(
                id=uuid4(),
                patient_id=uuid4(),
                status=status,
                format=ExportFormat.PDF,
                download_url="https://example.com/test.pdf" if status == ExportStatus.COMPLETED else None,
                expires_at=datetime.now() + timedelta(days=7),
            )
            assert export.status == status


class TestExportRequest:
    """Test ExportRequest schema validation."""

    def test_export_request_valid(self):
        """Test creating a valid export request."""
        request = ExportRequest(
            format=ExportFormat.PDF,
            filters={
                "concept_cuis": ["C0011860"],
                "date_range": ["2024-01-01", "2024-12-31"],
            },
            options={
                "include_charts": True,
                "page_size": "A4",
            },
        )

        assert request.format == ExportFormat.PDF
        assert "concept_cuis" in request.filters
        assert request.options["include_charts"] is True

    def test_export_request_format_enum_validation(self):
        """Test ExportRequest validates format enum."""
        with pytest.raises(ValidationError):
            ExportRequest(
                format="docx",  # Invalid format
                filters={},
            )


class TestTimelineFilter:
    """Test TimelineFilter schema (matches database table)."""

    def test_timeline_filter_matches_database_schema(self):
        """Test TimelineFilter schema matches database table structure."""
        user_id = uuid4()

        filter_obj = TimelineFilter(
            id=uuid4(),
            user_id=user_id,
            name="Active Diabetes Patients",
            description="Current diabetes diagnoses only",
            filters={
                "concept_cuis": ["C0011860"],
                "meta_annotations": {
                    "negation": "Affirmed",
                    "temporality": ["Current", "Recent"],
                },
            },
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert filter_obj.user_id == user_id
        assert filter_obj.name == "Active Diabetes Patients"
        assert filter_obj.is_default is False
        assert "concept_cuis" in filter_obj.filters

    def test_timeline_filter_name_minimum_length(self):
        """Test TimelineFilter validates name minimum length (3 chars)."""
        with pytest.raises(ValidationError) as exc_info:
            TimelineFilter(
                id=uuid4(),
                user_id=uuid4(),
                name="AB",  # Too short - minimum 3 characters
                filters={},
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "name" in str(exc_info.value).lower()

    def test_timeline_filter_default_flag(self):
        """Test TimelineFilter is_default flag."""
        filter_obj = TimelineFilter(
            id=uuid4(),
            user_id=uuid4(),
            name="My Default Filter",
            filters={},
            is_default=True,  # Default filter for user
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert filter_obj.is_default is True


class TestMetaAnnotations:
    """Test MetaAnnotations schema validation."""

    def test_meta_annotations_valid_values(self):
        """Test MetaAnnotations accepts valid enum values."""
        meta = MetaAnnotations(
            negation="Affirmed",
            experiencer="Patient",
            temporality=["Current", "Recent"],
            certainty=["Confirmed"],
        )

        assert meta.negation == "Affirmed"
        assert meta.experiencer == "Patient"
        assert "Current" in meta.temporality

    def test_meta_annotations_invalid_negation(self):
        """Test MetaAnnotations rejects invalid negation values."""
        with pytest.raises(ValidationError):
            MetaAnnotations(
                negation="Unknown",  # Invalid - must be Affirmed/Negated/Possible
            )

    def test_meta_annotations_invalid_experiencer(self):
        """Test MetaAnnotations rejects invalid experiencer values."""
        with pytest.raises(ValidationError):
            MetaAnnotations(
                experiencer="Doctor",  # Invalid - must be Patient/Family/Other
            )

    def test_meta_annotations_optional_fields(self):
        """Test all MetaAnnotations fields are optional."""
        meta = MetaAnnotations()

        # Should use defaults
        assert meta.negation is not None  # Has default
        assert meta.experiencer is not None  # Has default
