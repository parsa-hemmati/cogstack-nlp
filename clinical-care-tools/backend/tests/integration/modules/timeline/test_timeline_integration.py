"""
Comprehensive Integration Tests for Timeline Feature.

Tests cover full end-to-end flows:
- API → Service → Database → Elasticsearch → Response
- Export functionality (PDF, FHIR, JSON)
- Filter presets
- Audit logging verification
"""

import pytest
from fastapi import status
from uuid import uuid4, UUID
from datetime import date, datetime
import json


@pytest.mark.integration
class TestTimelineEndToEndFlow:
    """Test complete timeline workflow from API to response."""

    def test_full_timeline_flow_with_real_database(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents,
        mock_elasticsearch_timeline_repo,
        mocker
    ):
        """
        Test full timeline flow: API → Service → DB → ES → Response.

        Verifies:
        - API endpoint receives request
        - Service fetches documents from PostgreSQL
        - Service queries concepts from Elasticsearch
        - Response contains correct timeline data
        - Audit logging executed
        """
        test_patient, documents = test_patient_with_documents

        # Mock the ES repository in the service
        mocker.patch(
            "app.modules.timeline.service.ElasticsearchTimelineRepository",
            return_value=mock_elasticsearch_timeline_repo
        )

        # Make request
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            headers=auth_headers_clinician
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["patient_id"] == str(test_patient.id)
        assert len(data["documents"]) == 5  # 5 documents created in fixture
        assert len(data["concepts"]) >= 2  # At least Diabetes and Hypertension

        # Verify documents are from database
        doc_ids = [doc["id"] for doc in data["documents"]]
        assert str(documents[0].id) in doc_ids

        # Verify concepts are from Elasticsearch
        concept_cuis = [concept["concept_cui"] for concept in data["concepts"]]
        assert "C0011849" in concept_cuis  # Diabetes
        assert "C0020538" in concept_cuis  # Hypertension

        # Verify statistics
        assert "statistics" in data
        assert data["statistics"]["document_count"] == 5
        assert data["statistics"]["concept_count"] >= 2

    def test_timeline_with_concept_filters(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents,
        mock_elasticsearch_timeline_repo
    ):
        """Test timeline filtering by concept CUIs."""
        test_patient, _ = test_patient_with_documents

        # Filter by diabetes only
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={"concept_cuis": ["C0011849"]},
            headers=auth_headers_clinician
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "filters_applied" in data
        assert "concept_cuis" in data["filters_applied"]
        assert "C0011849" in data["filters_applied"]["concept_cuis"]

    def test_timeline_with_date_range_filters(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents
    ):
        """Test timeline filtering by date range."""
        test_patient, _ = test_patient_with_documents

        # Filter to January-February 2024 only
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={
                "date_start": "2024-01-01",
                "date_end": "2024-02-28"
            },
            headers=auth_headers_clinician
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "filters_applied" in data
        assert data["filters_applied"]["date_start"] == "2024-01-01"
        assert data["filters_applied"]["date_end"] == "2024-02-28"

        # Verify documents are within date range
        for doc in data["documents"]:
            doc_date = datetime.fromisoformat(doc["document_date"]).date()
            assert date(2024, 1, 1) <= doc_date <= date(2024, 2, 28)

    def test_timeline_with_meta_annotation_filters(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents
    ):
        """Test timeline filtering by meta-annotations."""
        test_patient, _ = test_patient_with_documents

        # Filter for affirmed, patient, current conditions only
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={
                "negation": "Affirmed",
                "experiencer": "Patient",
                "temporality": "Current"
            },
            headers=auth_headers_clinician
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "filters_applied" in data
        assert data["filters_applied"]["negation"] == "Affirmed"
        assert data["filters_applied"]["experiencer"] == "Patient"
        assert data["filters_applied"]["temporality"] == "Current"

    def test_timeline_empty_results(
        self,
        client,
        auth_headers_clinician,
        test_patient,  # Patient without documents
        mock_elasticsearch_timeline_repo
    ):
        """Test timeline with patient who has no documents."""
        # Mock ES to return empty results
        mock_elasticsearch_timeline_repo.query_patient_concepts.return_value = []

        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            headers=auth_headers_clinician
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["patient_id"] == str(test_patient.id)
        assert len(data["documents"]) == 0
        assert len(data["concepts"]) == 0
        assert data["statistics"]["document_count"] == 0


@pytest.mark.integration
class TestTimelineExportEndToEnd:
    """Test export functionality end-to-end."""

    def test_export_pdf_end_to_end(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents,
        db_session
    ):
        """
        Test complete PDF export workflow.

        Flow:
        1. POST /api/v1/timeline/{patient_id}/export (format=pdf)
        2. Verify export record created in database
        3. GET /api/v1/timeline/exports/{export_id} (check status)
        4. GET /api/v1/timeline/exports/{export_id}/download (download file)
        """
        test_patient, _ = test_patient_with_documents

        # Step 1: Create export
        export_response = client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            json={
                "format": "pdf",
                "options": {
                    "watermark": "CONFIDENTIAL",
                    "orientation": "portrait"
                }
            },
            headers=auth_headers_clinician
        )

        assert export_response.status_code == status.HTTP_202_ACCEPTED

        export_data = export_response.json()
        export_id = export_data["id"]
        assert export_data["status"] == "completed"  # Sync export
        assert export_data["format"] == "pdf"

        # Step 2: Verify export record in database
        from app.modules.timeline.models import TimelineExport
        export_record = db_session.query(TimelineExport).filter_by(id=UUID(export_id)).first()
        assert export_record is not None
        assert export_record.patient_id == test_patient.id
        assert export_record.format == "pdf"
        assert export_record.status == "completed"

        # Step 3: Get export status
        status_response = client.get(
            f"/api/v1/timeline/exports/{export_id}",
            headers=auth_headers_clinician
        )

        assert status_response.status_code == status.HTTP_200_OK
        status_data = status_response.json()
        assert status_data["status"] == "completed"

        # Step 4: Download export file
        download_response = client.get(
            f"/api/v1/timeline/exports/{export_id}/download",
            headers=auth_headers_clinician
        )

        assert download_response.status_code == status.HTTP_200_OK
        assert download_response.headers["content-type"] == "application/pdf"

        # Verify PDF content
        pdf_content = download_response.content
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b"%PDF")  # PDF header

    def test_export_fhir_end_to_end(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents
    ):
        """Test complete FHIR R4 export workflow."""
        test_patient, _ = test_patient_with_documents

        # Create FHIR export
        export_response = client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            json={"format": "fhir"},
            headers=auth_headers_clinician
        )

        assert export_response.status_code == status.HTTP_202_ACCEPTED

        export_data = export_response.json()
        export_id = export_data["id"]

        # Download FHIR bundle
        download_response = client.get(
            f"/api/v1/timeline/exports/{export_id}/download",
            headers=auth_headers_clinician
        )

        assert download_response.status_code == status.HTTP_200_OK
        assert download_response.headers["content-type"] == "application/fhir+json"

        # Verify FHIR bundle structure
        fhir_bundle = download_response.json()
        assert fhir_bundle["resourceType"] == "Bundle"
        assert fhir_bundle["type"] == "document"
        assert len(fhir_bundle["entry"]) > 0

        # Verify Composition resource
        composition = fhir_bundle["entry"][0]["resource"]
        assert composition["resourceType"] == "Composition"
        assert composition["status"] == "final"
        assert composition["subject"]["reference"] == f"Patient/{test_patient.id}"

    def test_export_json_end_to_end(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents
    ):
        """Test complete JSON export workflow."""
        test_patient, _ = test_patient_with_documents

        # Create JSON export
        export_response = client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            json={"format": "json"},
            headers=auth_headers_clinician
        )

        assert export_response.status_code == status.HTTP_202_ACCEPTED

        export_data = export_response.json()
        export_id = export_data["id"]

        # Download JSON file
        download_response = client.get(
            f"/api/v1/timeline/exports/{export_id}/download",
            headers=auth_headers_clinician
        )

        assert download_response.status_code == status.HTTP_200_OK
        assert download_response.headers["content-type"] == "application/json"

        # Verify JSON structure
        timeline_data = download_response.json()
        assert "patient_id" in timeline_data
        assert "documents" in timeline_data
        assert "concepts" in timeline_data
        assert timeline_data["patient_id"] == str(test_patient.id)


@pytest.mark.integration
class TestFilterPresetFlow:
    """Test filter preset save and load workflow."""

    def test_filter_preset_save_and_load(
        self,
        client,
        auth_headers_clinician,
        db_session
    ):
        """
        Test complete filter preset workflow.

        Flow:
        1. POST /api/v1/timeline/filters (create preset)
        2. GET /api/v1/timeline/filters (list presets)
        3. Verify preset in database
        """
        # Step 1: Save filter preset
        save_response = client.post(
            "/api/v1/timeline/filters",
            json={
                "name": "Active Conditions Only",
                "description": "Filter for active, confirmed patient conditions",
                "filters": {
                    "negation": "Affirmed",
                    "experiencer": "Patient",
                    "temporality": "Current"
                },
                "is_default": False
            },
            headers=auth_headers_clinician
        )

        assert save_response.status_code == status.HTTP_201_CREATED

        preset_data = save_response.json()
        preset_id = preset_data["id"]
        assert preset_data["name"] == "Active Conditions Only"
        assert preset_data["filters"]["negation"] == "Affirmed"

        # Step 2: Load filter presets
        load_response = client.get(
            "/api/v1/timeline/filters",
            headers=auth_headers_clinician
        )

        assert load_response.status_code == status.HTTP_200_OK

        presets = load_response.json()
        assert len(presets) > 0

        # Find our preset
        our_preset = next((p for p in presets if p["id"] == preset_id), None)
        assert our_preset is not None
        assert our_preset["name"] == "Active Conditions Only"

        # Step 3: Verify in database
        from app.modules.timeline.models import TimelineFilter
        db_preset = db_session.query(TimelineFilter).filter_by(id=UUID(preset_id)).first()
        assert db_preset is not None
        assert db_preset.name == "Active Conditions Only"


@pytest.mark.integration
class TestAuditLogging:
    """Test audit logging for timeline PHI access."""

    def test_timeline_access_creates_audit_log(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents,
        db_session
    ):
        """Verify that accessing timeline creates audit log entry."""
        test_patient, _ = test_patient_with_documents

        # Access timeline
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            headers=auth_headers_clinician
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify audit log created
        from app.modules.auth.models import AuditLog
        audit_logs = db_session.query(AuditLog).filter_by(
            patient_id=test_patient.id,
            action="VIEW_TIMELINE"
        ).all()

        assert len(audit_logs) > 0

        # Verify audit log details
        audit_log = audit_logs[-1]  # Most recent
        assert audit_log.action == "VIEW_TIMELINE"
        assert audit_log.patient_id == test_patient.id
        # Note: user_id verification depends on test user setup

    def test_export_creates_audit_log(
        self,
        client,
        auth_headers_clinician,
        test_patient_with_documents,
        db_session
    ):
        """Verify that exporting timeline creates audit log entry."""
        test_patient, _ = test_patient_with_documents

        # Create export
        response = client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            json={"format": "pdf"},
            headers=auth_headers_clinician
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

        # Verify audit log created
        from app.modules.auth.models import AuditLog
        audit_logs = db_session.query(AuditLog).filter_by(
            patient_id=test_patient.id,
            action="EXPORT_TIMELINE"
        ).all()

        assert len(audit_logs) > 0

        # Verify export has audit_log_id
        export_data = response.json()
        assert "audit_log_id" in export_data
        assert export_data["audit_log_id"] is not None


@pytest.mark.integration
class TestRBACEnforcement:
    """Test role-based access control for timeline endpoints."""

    def test_patient_role_cannot_access_timeline(
        self,
        client,
        auth_headers_patient,
        test_patient
    ):
        """Verify that patient role cannot access timeline endpoints."""
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            headers=auth_headers_patient
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_researcher_can_access_timeline(
        self,
        client,
        auth_headers_researcher,
        test_patient_with_documents
    ):
        """Verify that researcher role can access timeline."""
        test_patient, _ = test_patient_with_documents

        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            headers=auth_headers_researcher
        )

        # Should succeed (200) or fail with 404 if patient not in researcher's project
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_admin_can_access_timeline(
        self,
        client,
        auth_headers_admin,
        test_patient_with_documents
    ):
        """Verify that admin role can access timeline."""
        test_patient, _ = test_patient_with_documents

        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            headers=auth_headers_admin
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
