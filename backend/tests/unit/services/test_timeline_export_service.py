"""
Unit tests for TimelineExportService.

Tests all export formats (PDF, FHIR R4, JSON) with mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import json

from app.services.timeline_export_service import TimelineExportService
from app.schemas.timeline import (
    PatientTimeline, TimelineConcept, TimelineDocument, ConceptMention,
    MetaAnnotations, DateRange, TimelineFilters
)


@pytest.fixture
def export_service():
    """TimelineExportService instance."""
    return TimelineExportService()


@pytest.fixture
def sample_patient_id():
    """Sample patient UUID."""
    return uuid4()


@pytest.fixture
def sample_meta_annotations():
    """Sample meta-annotations."""
    return MetaAnnotations(
        Negation="Affirmed",
        Temporality="Current",
        Experiencer="Patient",
        Certainty="Certain"
    )


@pytest.fixture
def sample_mentions(sample_patient_id, sample_meta_annotations):
    """Sample concept mentions."""
    return [
        ConceptMention(
            concept_cui="C0004238",
            concept_name="Atrial Flutter",
            concept_type="condition",
            document_id=str(uuid4()),
            date=datetime(2023, 1, 15),
            sentence="Patient has atrial flutter.",
            meta_annotations=sample_meta_annotations,
            confidence=0.95,
            is_first_mention=True
        ),
        ConceptMention(
            concept_cui="C0004238",
            concept_name="Atrial Flutter",
            concept_type="condition",
            document_id=str(uuid4()),
            date=datetime(2023, 2, 20),
            sentence="Atrial flutter persists.",
            meta_annotations=sample_meta_annotations,
            confidence=0.92,
            is_first_mention=False
        )
    ]


@pytest.fixture
def sample_concepts(sample_mentions, sample_meta_annotations):
    """Sample timeline concepts."""
    return [
        TimelineConcept(
            concept_cui="C0004238",
            concept_name="Atrial Flutter",
            concept_type="condition",
            first_mention_date=datetime(2023, 1, 15),
            mention_count=2,
            mentions=sample_mentions
        ),
        TimelineConcept(
            concept_cui="C0025598",
            concept_name="Metformin",
            concept_type="medication",
            first_mention_date=datetime(2023, 2, 10),
            mention_count=1,
            mentions=[
                ConceptMention(
                    concept_cui="C0025598",
                    concept_name="Metformin",
                    concept_type="medication",
                    document_id=str(uuid4()),
                    date=datetime(2023, 2, 10),
                    sentence="Started on metformin 500mg.",
                    meta_annotations=sample_meta_annotations,
                    confidence=0.98,
                    is_first_mention=True
                )
            ]
        )
    ]


@pytest.fixture
def sample_documents():
    """Sample timeline documents."""
    return [
        TimelineDocument(
            document_id=str(uuid4()),
            title="Clinical Note 2023-01-15",
            document_type="clinical_note",
            date=datetime(2023, 1, 15),
            author="Dr. Smith",
            concepts=["C0004238"]
        ),
        TimelineDocument(
            document_id=str(uuid4()),
            title="Lab Results 2023-02-20",
            document_type="lab_results",
            date=datetime(2023, 2, 20),
            author="Lab Tech",
            concepts=["C0004238", "C0025598"]
        )
    ]


@pytest.fixture
def sample_timeline(sample_patient_id, sample_concepts, sample_documents):
    """Sample PatientTimeline data."""
    return PatientTimeline(
        patient_id=str(sample_patient_id),
        date_range=DateRange(
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        ),
        concepts=sample_concepts,
        documents=sample_documents,
        filters_applied=TimelineFilters(
            concept_cuis=[],
            date_from=None,
            date_to=None,
            document_types=[],
            meta_annotations={}
        )
    )


# ============================================================================
# PDF Export Tests
# ============================================================================

@pytest.mark.asyncio
async def test_export_to_pdf_generates_valid_pdf(export_service, sample_patient_id, sample_timeline):
    """Test PDF export returns valid PDF bytes with correct header."""
    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    assert pdf_bytes is not None
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b'%PDF', "PDF must start with '%PDF' header"


@pytest.mark.asyncio
async def test_export_to_pdf_with_watermark(export_service, sample_patient_id, sample_timeline):
    """Test PDF includes watermark when requested."""
    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline,
        options={"watermark": True}
    )

    # Check PDF contains watermark text
    pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
    assert "Clinical Summary" in pdf_text or "Confidential" in pdf_text


@pytest.mark.asyncio
async def test_export_to_pdf_without_watermark(export_service, sample_patient_id, sample_timeline):
    """Test PDF without watermark when disabled."""
    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline,
        options={"watermark": False}
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0


@pytest.mark.asyncio
async def test_export_to_pdf_de_identified(export_service, sample_patient_id, sample_timeline):
    """Test PDF de-identifies patient data when requested."""
    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline,
        options={"de_identified": True}
    )

    # Check PDF contains de-identification marker
    pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
    assert "[De-identified]" in pdf_text


@pytest.mark.asyncio
async def test_export_to_pdf_includes_concepts(export_service, sample_patient_id, sample_timeline):
    """Test PDF includes clinical concepts from timeline."""
    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
    # Check for concept names
    assert "Atrial Flutter" in pdf_text
    assert "Metformin" in pdf_text


@pytest.mark.asyncio
async def test_export_to_pdf_includes_documents(export_service, sample_patient_id, sample_timeline):
    """Test PDF includes source documents from timeline."""
    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
    # Check for document titles
    assert "Clinical Note" in pdf_text or "Lab Results" in pdf_text


@pytest.mark.asyncio
async def test_export_to_pdf_performance(export_service, sample_patient_id, sample_timeline):
    """Test PDF generation completes in <5 seconds."""
    import time
    start = time.time()

    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    duration = time.time() - start
    assert duration < 5.0, f"PDF generation took {duration}s (target <5s)"
    assert len(pdf_bytes) > 0


@pytest.mark.asyncio
async def test_export_to_pdf_default_options(export_service, sample_patient_id, sample_timeline):
    """Test PDF export with default options (watermark=True, de_identified=False)."""
    pdf_bytes = await export_service.export_to_pdf(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline,
        options=None  # Default options
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
    # Default: watermark enabled
    assert "Clinical Summary" in pdf_text or "Confidential" in pdf_text


# ============================================================================
# FHIR Export Tests
# ============================================================================

@pytest.mark.asyncio
async def test_export_to_fhir_generates_composition(export_service, sample_patient_id, sample_timeline):
    """Test FHIR export returns valid Composition resource."""
    fhir_composition = await export_service.export_to_fhir(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    assert fhir_composition is not None
    assert isinstance(fhir_composition, dict)
    assert fhir_composition["resourceType"] == "Composition"
    assert fhir_composition["status"] == "final"


@pytest.mark.asyncio
async def test_export_to_fhir_composition_type(export_service, sample_patient_id, sample_timeline):
    """Test FHIR Composition has correct type code."""
    fhir_composition = await export_service.export_to_fhir(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    assert "type" in fhir_composition
    assert "coding" in fhir_composition["type"]
    coding = fhir_composition["type"]["coding"][0]
    assert coding["code"] == "clinical-timeline"
    assert coding["system"] == "http://cogstack.org/fhir/composition-type"


@pytest.mark.asyncio
async def test_export_to_fhir_patient_reference(export_service, sample_patient_id, sample_timeline):
    """Test FHIR Composition includes correct patient reference."""
    fhir_composition = await export_service.export_to_fhir(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    assert "subject" in fhir_composition
    assert fhir_composition["subject"]["reference"] == f"Patient/{sample_patient_id}"
    assert fhir_composition["subject"]["type"] == "Patient"


@pytest.mark.asyncio
async def test_export_to_fhir_includes_sections(export_service, sample_patient_id, sample_timeline):
    """Test FHIR Composition includes sections for each concept."""
    fhir_composition = await export_service.export_to_fhir(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    assert "section" in fhir_composition
    sections = fhir_composition["section"]
    assert len(sections) == len(sample_timeline.concepts)

    # Check first section
    first_section = sections[0]
    assert first_section["title"] == "Atrial Flutter"
    assert "code" in first_section
    assert first_section["code"]["coding"][0]["code"] == "C0004238"


@pytest.mark.asyncio
async def test_export_to_fhir_includes_observations(export_service, sample_patient_id, sample_timeline):
    """Test FHIR sections include Observation references for each mention."""
    fhir_composition = await export_service.export_to_fhir(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    sections = fhir_composition["section"]
    first_section = sections[0]

    # Check Observation entries
    assert "entry" in first_section
    entries = first_section["entry"]
    assert len(entries) == 2  # Two mentions of Atrial Flutter

    # Check first entry
    first_entry = entries[0]
    assert first_entry["type"] == "Observation"
    assert "Observation/" in first_entry["reference"]


@pytest.mark.asyncio
async def test_export_to_fhir_validates_schema(export_service, sample_patient_id, sample_timeline):
    """Test FHIR output validates against FHIR R4 schema."""
    from fhir.resources.composition import Composition

    fhir_composition = await export_service.export_to_fhir(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    # Serialize and deserialize to validate schema
    json_str = json.dumps(fhir_composition)
    reloaded = Composition.parse_raw(json_str)

    assert reloaded.resource_type == "Composition"
    assert reloaded.status == "final"


@pytest.mark.asyncio
async def test_export_to_fhir_includes_author(export_service, sample_patient_id, sample_timeline):
    """Test FHIR Composition includes author reference."""
    fhir_composition = await export_service.export_to_fhir(
        patient_id=sample_patient_id,
        timeline_data=sample_timeline
    )

    assert "author" in fhir_composition
    assert len(fhir_composition["author"]) > 0
    author = fhir_composition["author"][0]
    assert author["reference"] == "Organization/cogstack-nlp"


# ============================================================================
# JSON Export Tests
# ============================================================================

@pytest.mark.asyncio
async def test_export_to_json_serializes_timeline(export_service, sample_timeline):
    """Test JSON export serializes complete timeline."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    assert json_data is not None
    assert isinstance(json_data, dict)
    assert "patient_id" in json_data
    assert "concepts" in json_data
    assert "documents" in json_data
    assert len(json_data["concepts"]) == len(sample_timeline.concepts)
    assert len(json_data["documents"]) == len(sample_timeline.documents)


@pytest.mark.asyncio
async def test_export_to_json_includes_metadata(export_service, sample_timeline):
    """Test JSON export includes export metadata."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    assert "export_metadata" in json_data
    metadata = json_data["export_metadata"]
    assert "export_timestamp" in metadata
    assert "export_format" in metadata
    assert "filters_applied" in metadata
    assert metadata["export_format"] == "json"


@pytest.mark.asyncio
async def test_export_to_json_includes_date_range(export_service, sample_timeline):
    """Test JSON export includes date range."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    assert "date_range" in json_data
    date_range = json_data["date_range"]
    assert "start" in date_range
    assert "end" in date_range
    assert date_range["start"] == "2023-01-01T00:00:00"
    assert date_range["end"] == "2023-12-31T00:00:00"


@pytest.mark.asyncio
async def test_export_to_json_includes_concept_details(export_service, sample_timeline):
    """Test JSON export includes detailed concept information."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    concepts = json_data["concepts"]
    first_concept = concepts[0]

    # Check concept fields
    assert "concept_cui" in first_concept
    assert "concept_name" in first_concept
    assert "concept_type" in first_concept
    assert "first_mention_date" in first_concept
    assert "mention_count" in first_concept
    assert "mentions" in first_concept

    # Check mentions
    assert len(first_concept["mentions"]) == 2
    first_mention = first_concept["mentions"][0]
    assert "date" in first_mention
    assert "sentence" in first_mention
    assert "meta_annotations" in first_mention
    assert "confidence" in first_mention


@pytest.mark.asyncio
async def test_export_to_json_includes_meta_annotations(export_service, sample_timeline):
    """Test JSON export includes meta-annotations for mentions."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    concepts = json_data["concepts"]
    first_mention = concepts[0]["mentions"][0]

    meta_anns = first_mention["meta_annotations"]
    assert meta_anns is not None
    assert "Negation" in meta_anns
    assert "Temporality" in meta_anns
    assert "Experiencer" in meta_anns
    assert "Certainty" in meta_anns


@pytest.mark.asyncio
async def test_export_to_json_includes_document_details(export_service, sample_timeline):
    """Test JSON export includes detailed document information."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    documents = json_data["documents"]
    first_doc = documents[0]

    # Check document fields
    assert "document_id" in first_doc
    assert "title" in first_doc
    assert "document_type" in first_doc
    assert "date" in first_doc
    assert "author" in first_doc
    assert "concepts" in first_doc


@pytest.mark.asyncio
async def test_export_to_json_machine_readable(export_service, sample_timeline):
    """Test JSON export is valid and machine-readable."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    # Serialize and deserialize to verify valid JSON
    json_str = json.dumps(json_data)
    reloaded = json.loads(json_str)

    assert reloaded["patient_id"] == sample_timeline.patient_id
    assert len(reloaded["concepts"]) == len(sample_timeline.concepts)


@pytest.mark.asyncio
async def test_export_to_json_iso_format_dates(export_service, sample_timeline):
    """Test JSON export uses ISO format for all dates."""
    json_data = await export_service.export_to_json(
        timeline_data=sample_timeline
    )

    # Check metadata timestamp
    assert "T" in json_data["export_metadata"]["export_timestamp"]

    # Check date range
    assert "T" in json_data["date_range"]["start"]

    # Check concept dates
    first_concept = json_data["concepts"][0]
    assert "T" in first_concept["first_mention_date"]
    assert "T" in first_concept["mentions"][0]["date"]


@pytest.mark.asyncio
async def test_export_to_json_handles_empty_timeline(export_service, sample_patient_id):
    """Test JSON export handles timeline with no concepts/documents."""
    empty_timeline = PatientTimeline(
        patient_id=str(sample_patient_id),
        date_range=DateRange(
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        ),
        concepts=[],
        documents=[],
        filters_applied=TimelineFilters(
            concept_cuis=[],
            date_from=None,
            date_to=None,
            document_types=[],
            meta_annotations={}
        )
    )

    json_data = await export_service.export_to_json(
        timeline_data=empty_timeline
    )

    assert json_data is not None
    assert len(json_data["concepts"]) == 0
    assert len(json_data["documents"]) == 0
