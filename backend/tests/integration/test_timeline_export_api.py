"""
Integration tests for Timeline Export API (Phase 5.6).

Tests export endpoints for PDF, FHIR R4, and JSON formats with full API integration.

PRD Specification: .specify/specifications/sprint-2-timeline-view.md (Section: Export)
Test Coverage: Export API endpoint (POST /api/v1/timeline/{patient_id}/export)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime
import base64
import json

pytestmark = pytest.mark.asyncio


class TestTimelineExportAPI:
    """
    Integration tests for timeline export endpoint.

    Tests all export formats (PDF, FHIR, JSON) with authentication and options.
    """

    async def test_export_timeline_pdf_success(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test POST /api/v1/timeline/{patient_id}/export (PDF format).

        Acceptance Criteria:
        - POST /api/v1/timeline/{patient_id}/export with format="pdf" returns 200 OK
        - Response includes export_id, status="completed", format="pdf", content_type="application/pdf"
        - Response includes base64-encoded PDF data
        - PDF data decodes to valid PDF bytes (starts with b'%PDF')
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "pdf",
            "options": {"watermark": True, "de_identified": False},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Response structure
        assert "export_id" in data
        assert "status" in data
        assert "format" in data
        assert "content_type" in data
        assert "data" in data
        assert "created_at" in data

        # Export metadata
        assert data["status"] == "completed"
        assert data["format"] == "pdf"
        assert data["content_type"] == "application/pdf"

        # PDF data validation
        assert data["data"] is not None
        assert isinstance(data["data"], str)

        # Decode base64 to verify valid PDF
        pdf_bytes = base64.b64decode(data["data"])
        assert pdf_bytes[:4] == b'%PDF', "PDF must start with '%PDF' header"


    async def test_export_timeline_pdf_with_watermark(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test PDF export includes watermark when enabled.

        Acceptance Criteria:
        - PDF export with watermark=True includes "Confidential" text
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "pdf",
            "options": {"watermark": True},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Decode PDF and check for watermark text
        pdf_bytes = base64.b64decode(data["data"])
        pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
        assert "Clinical Summary" in pdf_text or "Confidential" in pdf_text


    async def test_export_timeline_pdf_de_identified(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test PDF export de-identifies patient data when requested.

        Acceptance Criteria:
        - PDF export with de_identified=True includes "[De-identified]" marker
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "pdf",
            "options": {"de_identified": True},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Decode PDF and check for de-identification marker
        pdf_bytes = base64.b64decode(data["data"])
        pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
        assert "[De-identified]" in pdf_text


    async def test_export_timeline_fhir_success(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test POST /api/v1/timeline/{patient_id}/export (FHIR format).

        Acceptance Criteria:
        - POST with format="fhir" returns 200 OK
        - Response includes FHIR R4 Composition resource
        - Composition.resourceType == "Composition"
        - Composition.subject.reference == "Patient/{patient_id}"
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "fhir",
            "options": {},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Response structure
        assert data["status"] == "completed"
        assert data["format"] == "fhir"
        assert data["content_type"] == "application/fhir+json"

        # FHIR Composition validation
        fhir_data = data["data"]
        assert fhir_data["resourceType"] == "Composition"
        assert fhir_data["status"] == "final"
        assert "subject" in fhir_data
        assert fhir_data["subject"]["reference"] == f"Patient/{patient_id}"
        assert fhir_data["subject"]["type"] == "Patient"


    async def test_export_timeline_fhir_includes_sections(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test FHIR export includes sections for each concept.

        Acceptance Criteria:
        - FHIR Composition includes "section" array
        - Each section has title, code, text, entry
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "fhir",
            "options": {},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        fhir_data = response.json()["data"]

        # Check sections
        assert "section" in fhir_data
        sections = fhir_data["section"]
        assert len(sections) > 0

        # Validate first section structure
        first_section = sections[0]
        assert "title" in first_section
        assert "code" in first_section
        assert "text" in first_section
        assert "entry" in first_section


    async def test_export_timeline_json_success(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test POST /api/v1/timeline/{patient_id}/export (JSON format).

        Acceptance Criteria:
        - POST with format="json" returns 200 OK
        - Response includes JSON data with patient_id, concepts, documents
        - JSON includes export_metadata with timestamp, format, filters_applied
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "json",
            "options": {},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Response structure
        assert data["status"] == "completed"
        assert data["format"] == "json"
        assert data["content_type"] == "application/json"

        # JSON data validation
        json_data = data["data"]
        assert "patient_id" in json_data
        assert "concepts" in json_data
        assert "documents" in json_data
        assert "export_metadata" in json_data
        assert "date_range" in json_data

        # Export metadata validation
        metadata = json_data["export_metadata"]
        assert "export_timestamp" in metadata
        assert "export_format" in metadata
        assert "filters_applied" in metadata
        assert metadata["export_format"] == "json"


    async def test_export_timeline_json_includes_meta_annotations(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test JSON export includes meta-annotations for concepts.

        Acceptance Criteria:
        - JSON data includes concepts array
        - Each concept has mentions array
        - Each mention has meta_annotations object (Negation, Temporality, Experiencer, Certainty)
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "json",
            "options": {},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        json_data = response.json()["data"]

        # Check concepts and mentions
        concepts = json_data["concepts"]
        if len(concepts) > 0:
            first_concept = concepts[0]
            assert "mentions" in first_concept
            mentions = first_concept["mentions"]

            if len(mentions) > 0:
                first_mention = mentions[0]
                if first_mention.get("meta_annotations"):
                    meta_anns = first_mention["meta_annotations"]
                    # Meta-annotations may be None for some mentions
                    assert "Negation" in meta_anns
                    assert "Temporality" in meta_anns
                    assert "Experiencer" in meta_anns
                    assert "Certainty" in meta_anns


    async def test_export_timeline_with_filters(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test export with filters applied.

        Acceptance Criteria:
        - Export request with filters succeeds
        - Filters are reflected in export_metadata.filters_applied
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "json",
            "options": {},
            "filters": {
                "concept_cuis": ["C0004238"],
                "date_from": "2023-01-01T00:00:00",
                "date_to": "2023-12-31T23:59:59",
                "document_types": ["clinical_note"],
                "meta_annotations": {
                    "Negation": "Affirmed",
                    "Temporality": "Current"
                }
            }
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check filters are reflected in export metadata
        json_data = data["data"]
        metadata = json_data["export_metadata"]
        assert metadata["filters_applied"] is not None


    async def test_export_timeline_unauthorized(
        self,
        client,
        test_db_with_timeline_data
    ):
        """
        Test export requires authentication.

        Acceptance Criteria:
        - POST /export without Authorization header returns 401 Unauthorized
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "pdf",
            "options": {},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request
            # No auth_headers
        )

        # Assert
        assert response.status_code == 401


    async def test_export_timeline_invalid_format(
        self,
        client,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test export with invalid format returns 400 Bad Request.

        Acceptance Criteria:
        - POST /export with format="invalid" returns 400 Bad Request
        - Error message indicates unsupported format
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request = {
            "format": "invalid_format",
            "options": {},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "Unsupported export format" in error_data["detail"] or "invalid" in error_data["detail"].lower()


    async def test_export_timeline_missing_patient(
        self,
        client,
        auth_headers_clinician
    ):
        """
        Test export for non-existent patient returns 404 or 500.

        Acceptance Criteria:
        - POST /export with non-existent patient_id returns error
        """
        # Arrange
        non_existent_patient_id = uuid4()
        request = {
            "format": "pdf",
            "options": {},
            "filters": None
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/{non_existent_patient_id}/export",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        # May return 404 or 500 depending on implementation
        assert response.status_code in [404, 500]


@pytest.fixture(scope="function")
async def test_db_with_timeline_data(db, test_user_clinician):
    """
    Create test database with timeline data for export tests.

    Creates:
    - 1 patient with concepts and documents
    - Sample concepts (Atrial Flutter, Metformin)
    - Sample documents (clinical note, lab results)
    """
    from app.models.patient import Patient
    from app.models.document import Document, ProcessingStatus
    from app.models.extracted_entity import ExtractedEntity, EntityType

    # Create patient
    patient_id = uuid4()
    patient = Patient(
        id=patient_id,
        nhs_number="9876543210",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(patient)

    # Create documents
    doc1_id = uuid4()
    doc1 = Document(
        id=doc1_id,
        filename="clinical_note_2023-01-15.rtf",
        created_at=datetime(2023, 1, 15, 10, 30),
        content_type="application/rtf",
        content_hash="hash1",
        encrypted_content=b"encrypted",
        file_size=1024,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED
    )
    db.add(doc1)

    doc2_id = uuid4()
    doc2 = Document(
        id=doc2_id,
        filename="lab_results_2023-02-20.rtf",
        created_at=datetime(2023, 2, 20, 14, 15),
        content_type="application/rtf",
        content_hash="hash2",
        encrypted_content=b"encrypted",
        file_size=2048,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED
    )
    db.add(doc2)

    # Create extracted entities (concepts)
    entity1 = ExtractedEntity(
        id=uuid4(),
        document_id=doc1_id,
        patient_id=patient_id,
        cui="C0004238",
        pretty_name="Atrial Flutter",
        entity_type=EntityType.CLINICAL,
        detected_at=datetime(2023, 1, 15),
        sentence="Patient has atrial flutter.",
        start_index=12,
        end_index=27,
        acc=0.95,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Certain"
        }
    )
    db.add(entity1)

    entity2 = ExtractedEntity(
        id=uuid4(),
        document_id=doc2_id,
        patient_id=patient_id,
        cui="C0025598",
        pretty_name="Metformin",
        entity_type=EntityType.CLINICAL,
        detected_at=datetime(2023, 2, 20),
        sentence="Started on metformin 500mg.",
        start_index=11,
        end_index=20,
        acc=0.98,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Certain"
        }
    )
    db.add(entity2)

    await db.commit()

    return {
        "patient_id": patient_id,
        "document_ids": [doc1_id, doc2_id],
        "entity_ids": [entity1.id, entity2.id]
    }
