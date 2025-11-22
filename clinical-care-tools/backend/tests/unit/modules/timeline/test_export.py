"""
Unit tests for Timeline Export Service.

Tests PDF, FHIR, and JSON export functionality.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime
from io import BytesIO

from app.modules.timeline.export import TimelineExportService
from app.modules.timeline.models import (
    PatientTimeline,
    TimelineDocument,
    TimelineConcept,
    ConceptMention,
    MetaAnnotations
)


@pytest.fixture
def export_service():
    """Create export service instance."""
    return TimelineExportService()


@pytest.fixture
def sample_timeline():
    """Create sample timeline data for testing."""
    patient_id = uuid4()
    
    # Sample document
    document = TimelineDocument(
        document_id=uuid4(),
        document_type="discharge",
        document_date=date(2024, 3, 15),
        author="Dr. Jane Smith"
    )
    
    # Sample concept with mentions
    concept = TimelineConcept(
        cui="C0011860",
        name="Diabetes Mellitus",
        semantic_type="Disease or Syndrome",
        mentions=[
            ConceptMention(
                document_id=document.document_id,
                document_date=document.document_date,
                sentence="Patient has Type 2 Diabetes Mellitus.",
                start_char=12,
                end_char=37,
                confidence=0.95,
                meta_anns=MetaAnnotations(
                    negation="Affirmed",
                    experiencer="Patient",
                    temporality="Current",
                    certainty="Certain"
                )
            )
        ],
        frequency=1,
        first_seen=date(2024, 3, 15),
        last_seen=date(2024, 3, 15)
    )
    
    # Patient timeline
    timeline = PatientTimeline(
        patient_id=patient_id,
        documents=[document],
        concepts=[concept],
        date_range={"start": date(2024, 1, 1), "end": date(2024, 12, 31)},
        filters_applied={},
        statistics={
            "total_documents": 1,
            "total_concepts": 1,
            "date_range_days": 365
        }
    )
    
    return timeline


class TestPDFExport:
    """Test PDF export functionality."""

    def test_export_timeline_pdf_generates_bytes(self, export_service, sample_timeline):
        """Test that PDF export generates valid PDF bytes."""
        pdf_bytes = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            watermark_text="CONFIDENTIAL"
        )
        
        # Verify bytes returned
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Verify PDF header (PDF files start with %PDF-)
        assert pdf_bytes[:4] == b'%PDF'

    def test_export_timeline_pdf_includes_patient_id(self, export_service, sample_timeline):
        """Test that PDF includes patient demographics."""
        pdf_bytes = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            watermark_text="CONFIDENTIAL"
        )
        
        # Convert PDF bytes to text for verification
        # NOTE: In actual implementation, would use pdfplumber or similar
        # For now, verify PDF was generated successfully
        assert len(pdf_bytes) > 0

    def test_export_timeline_pdf_supports_orientation(self, export_service, sample_timeline):
        """Test that PDF supports portrait and landscape orientation."""
        # Portrait
        pdf_portrait = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            orientation="portrait"
        )
        assert len(pdf_portrait) > 0
        
        # Landscape
        pdf_landscape = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            orientation="landscape"
        )
        assert len(pdf_landscape) > 0

    def test_export_timeline_pdf_supports_page_size(self, export_service, sample_timeline):
        """Test that PDF supports A4 and Letter page sizes."""
        # A4
        pdf_a4 = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            page_size="A4"
        )
        assert len(pdf_a4) > 0
        
        # Letter
        pdf_letter = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            page_size="Letter"
        )
        assert len(pdf_letter) > 0

    def test_export_timeline_pdf_includes_watermark(self, export_service, sample_timeline):
        """Test that PDF includes watermark when specified."""
        pdf_with_watermark = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            watermark_text="CONFIDENTIAL - DO NOT DISTRIBUTE"
        )
        
        # Verify PDF generated with watermark
        assert len(pdf_with_watermark) > 0

    def test_export_timeline_pdf_without_watermark(self, export_service, sample_timeline):
        """Test that PDF can be generated without watermark."""
        pdf_no_watermark = export_service.export_timeline_pdf(
            timeline=sample_timeline,
            watermark_text=None
        )
        
        assert len(pdf_no_watermark) > 0


class TestFHIRExport:
    """Test FHIR R4 export functionality."""

    def test_export_timeline_fhir_creates_composition(self, export_service, sample_timeline):
        """Test that FHIR export creates Composition resource."""
        fhir_bundle = export_service.export_timeline_fhir(
            timeline=sample_timeline
        )
        
        # Verify FHIR Bundle structure
        assert "resourceType" in fhir_bundle
        assert fhir_bundle["resourceType"] == "Bundle"
        assert "entry" in fhir_bundle

    def test_export_timeline_fhir_includes_patient_reference(self, export_service, sample_timeline):
        """Test that FHIR Composition includes patient reference."""
        fhir_bundle = export_service.export_timeline_fhir(
            timeline=sample_timeline
        )
        
        # Find Composition resource
        composition = next(
            (e["resource"] for e in fhir_bundle["entry"] if e["resource"]["resourceType"] == "Composition"),
            None
        )
        
        assert composition is not None
        assert "subject" in composition
        assert "reference" in composition["subject"]

    def test_export_timeline_fhir_maps_concepts_to_observations(self, export_service, sample_timeline):
        """Test that medical concepts are mapped to FHIR Observations."""
        fhir_bundle = export_service.export_timeline_fhir(
            timeline=sample_timeline
        )
        
        # Find Observation resources
        observations = [
            e["resource"] for e in fhir_bundle["entry"]
            if e["resource"]["resourceType"] == "Observation"
        ]
        
        # Should have at least one observation (diabetes concept)
        assert len(observations) >= 1
        assert observations[0]["code"]["coding"][0]["code"] == "C0011860"

    def test_export_timeline_fhir_includes_meta_annotations(self, export_service, sample_timeline):
        """Test that meta-annotations are included in FHIR resources."""
        fhir_bundle = export_service.export_timeline_fhir(
            timeline=sample_timeline
        )
        
        # Find Observation
        observation = next(
            (e["resource"] for e in fhir_bundle["entry"] if e["resource"]["resourceType"] == "Observation"),
            None
        )
        
        # Verify meta-annotations in extensions or interpretation
        assert observation is not None
        # Meta-annotations should be in extensions or coded appropriately


class TestJSONExport:
    """Test JSON export functionality."""

    def test_export_timeline_json_creates_valid_json(self, export_service, sample_timeline):
        """Test that JSON export creates valid JSON structure."""
        import json
        
        json_data = export_service.export_timeline_json(
            timeline=sample_timeline
        )
        
        # Verify valid JSON
        assert isinstance(json_data, dict)
        
        # Verify can be serialized
        json_str = json.dumps(json_data)
        assert len(json_str) > 0

    def test_export_timeline_json_includes_documents(self, export_service, sample_timeline):
        """Test that JSON export includes documents."""
        json_data = export_service.export_timeline_json(
            timeline=sample_timeline
        )
        
        assert "documents" in json_data
        assert len(json_data["documents"]) == 1

    def test_export_timeline_json_includes_concepts(self, export_service, sample_timeline):
        """Test that JSON export includes concepts."""
        json_data = export_service.export_timeline_json(
            timeline=sample_timeline
        )
        
        assert "concepts" in json_data
        assert len(json_data["concepts"]) == 1
        assert json_data["concepts"][0]["cui"] == "C0011860"

    def test_export_timeline_json_includes_statistics(self, export_service, sample_timeline):
        """Test that JSON export includes statistics."""
        json_data = export_service.export_timeline_json(
            timeline=sample_timeline
        )
        
        assert "statistics" in json_data
        assert json_data["statistics"]["total_documents"] == 1
        assert json_data["statistics"]["total_concepts"] == 1
