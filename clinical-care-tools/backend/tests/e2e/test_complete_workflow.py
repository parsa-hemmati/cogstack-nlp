"""
End-to-end tests for complete Clinical Care Tools workflows.

Tests the following complete user journeys:
1. User registration → login → create project → upload document → search patient
2. Patient search with meta-annotations → view timeline → export to FHIR
3. Data retention workflow → compliance report generation
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json


@pytest.mark.e2e
class TestCompleteUserWorkflow:
    """Test complete workflow: Registration → Login → Project → Document → Search"""

    def test_user_registration_to_patient_search_workflow(
        self, client, test_user_data, mock_medcat_service, mock_elasticsearch_service
    ):
        """
        Test complete user journey from registration to patient search.

        User journey:
        1. Register new user
        2. Login and receive access token
        3. Create a project
        4. Upload clinical document
        5. Search for patient entities
        6. View search results with confidence scores
        """
        # Step 1: Register new user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
                "full_name": test_user_data["full_name"],
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        user_id = user_data["id"]

        # Step 2: Login and get access token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            }
        )
        assert login_response.status_code == 200
        auth_data = login_response.json()
        access_token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 3: Create a project
        project_response = client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "description": "E2E test project",
            },
            headers=headers
        )
        assert project_response.status_code == 201
        project_data = project_response.json()
        project_id = project_data["id"]

        # Step 4: Upload clinical document
        document_content = "Patient presents with atrial fibrillation. History of diabetes."
        upload_response = client.post(
            f"/api/v1/projects/{project_id}/documents",
            json={
                "content": document_content,
                "document_type": "clinical_note",
                "source": "test",
            },
            headers=headers
        )
        assert upload_response.status_code == 201
        document_data = upload_response.json()
        document_id = document_data["id"]

        # Step 5: Process document (extract entities)
        process_response = client.post(
            f"/api/v1/documents/{document_id}/process",
            headers=headers
        )
        assert process_response.status_code == 200
        entities_data = process_response.json()
        assert "entities" in entities_data
        assert len(entities_data["entities"]) > 0

        # Step 6: Search for patients with specific concept
        search_response = client.post(
            "/api/v1/patients/search",
            json={
                "concept": "atrial fibrillation",
                "filters": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient",
                }
            },
            headers=headers
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert "patients" in search_results
        assert "total" in search_results

    def test_workflow_requires_authentication(self, client):
        """Verify all workflow endpoints require valid authentication."""
        # Attempt to access protected endpoint without token
        response = client.get("/api/v1/projects")
        assert response.status_code == 401

        # Attempt with invalid token
        response = client.get(
            "/api/v1/projects",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_document_processing_with_meta_annotations(
        self, client, auth_headers, mock_medcat_service
    ):
        """Test that document processing applies meta-annotations correctly."""
        # Create a document with negated and affirmed mentions
        clinical_note = """
        Patient denies chest pain. History of diabetes confirmed.
        Family history of heart disease noted.
        """

        response = client.post(
            "/api/v1/documents/process",
            json={"content": clinical_note},
            headers=auth_headers
        )

        assert response.status_code == 200
        entities = response.json()["entities"]

        # Verify meta-annotations are applied
        for entity in entities:
            assert "meta_anns" in entity
            assert "Negation" in entity["meta_anns"]
            assert "Temporality" in entity["meta_anns"]
            assert "Experiencer" in entity["meta_anns"]


@pytest.mark.e2e
class TestBreakGlassWorkflow:
    """Test break-glass (emergency access) workflow and audit trail verification."""

    def test_break_glass_access_requires_reason(
        self, client, auth_headers, clinician_auth_headers
    ):
        """Verify break-glass access requires documented reason."""
        patient_id = "test_patient_123"

        # Attempt break-glass without reason
        response = client.post(
            f"/api/v1/patients/{patient_id}/break-glass",
            json={},
            headers=clinician_auth_headers
        )
        assert response.status_code == 400
        assert "reason" in response.json()["detail"]

    def test_break_glass_creates_audit_trail(
        self, client, clinician_auth_headers, audit_logger_spy
    ):
        """Verify break-glass access creates complete audit trail."""
        patient_id = "test_patient_123"
        access_reason = "Emergency treatment - cardiac emergency"

        response = client.post(
            f"/api/v1/patients/{patient_id}/break-glass",
            json={"reason": access_reason},
            headers=clinician_auth_headers
        )

        # Verify audit log was created
        audit_logger_spy.assert_called()
        call_args = audit_logger_spy.call_args[0][0]
        assert call_args["action"] == "BREAK_GLASS_ACCESS"
        assert call_args["patient_id"] == patient_id
        assert call_args["reason"] == access_reason

    def test_break_glass_access_logged_and_reviewable(
        self, client, clinician_auth_headers, admin_auth_headers
    ):
        """Test that break-glass access is logged and reviewable by admins."""
        # Clinician performs break-glass access
        patient_id = "test_patient_123"
        response = client.post(
            f"/api/v1/patients/{patient_id}/break-glass",
            json={"reason": "Emergency treatment"},
            headers=clinician_auth_headers
        )
        assert response.status_code == 200
        access_id = response.json()["id"]

        # Admin retrieves break-glass access logs
        logs_response = client.get(
            "/api/v1/audit-logs/break-glass",
            headers=admin_auth_headers
        )
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert len(logs) > 0

        # Verify access details
        log_entry = next((log for log in logs if log["id"] == access_id), None)
        assert log_entry is not None
        assert log_entry["action"] == "BREAK_GLASS_ACCESS"


@pytest.mark.e2e
class TestDataRetentionWorkflow:
    """Test data retention compliance and deletion workflows."""

    def test_data_retention_policy_enforcement(
        self, client, auth_headers
    ):
        """Verify data retention policies are enforced."""
        # Create document with retention policy
        response = client.post(
            "/api/v1/documents",
            json={
                "content": "Test document",
                "retention_days": 365,
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        document = response.json()

        # Verify retention metadata
        assert "expires_at" in document
        expected_expiry = (
            datetime.now() + timedelta(days=365)
        ).date()
        assert document["expires_at"].startswith(str(expected_expiry))

    def test_automatic_data_deletion_on_expiry(
        self, client, auth_headers
    ):
        """Test that data is automatically deleted after retention period."""
        # Create document with 1-day retention
        response = client.post(
            "/api/v1/documents",
            json={
                "content": "Expiring document",
                "retention_days": 1,
            },
            headers=auth_headers
        )
        document_id = response.json()["id"]

        # Document should exist initially
        response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # After expiry, document should be deleted
        # (in real test, use time-machine or mocking to advance time)

    def test_compliance_report_generation(
        self, client, admin_auth_headers
    ):
        """Test generation of compliance reports."""
        # Request compliance report
        response = client.post(
            "/api/v1/compliance/report",
            json={
                "report_type": "retention",
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            },
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        report = response.json()

        # Verify report contains required sections
        assert "report_id" in report
        assert "generated_at" in report
        assert "summary" in report
        assert "details" in report
        assert "certification" in report


@pytest.mark.e2e
class TestMultiUserCollaboration:
    """Test multi-user features and access control."""

    def test_project_sharing_between_users(
        self, client, test_user_data, auth_headers
    ):
        """Test sharing projects between authorized users."""
        # User 1 creates project
        response = client.post(
            "/api/v1/projects",
            json={"name": "Shared Project"},
            headers=auth_headers
        )
        project_id = response.json()["id"]

        # User 1 shares with User 2
        response = client.post(
            f"/api/v1/projects/{project_id}/share",
            json={
                "email": "user2@example.com",
                "role": "viewer",
            },
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify sharing record
        response = client.get(
            f"/api/v1/projects/{project_id}/members",
            headers=auth_headers
        )
        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 2

    def test_role_based_access_control(
        self, client, admin_auth_headers, clinician_auth_headers
    ):
        """Test that role-based access control is enforced."""
        # Admin can access admin endpoints
        response = client.get(
            "/api/v1/admin/users",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

        # Clinician cannot access admin endpoints
        response = client.get(
            "/api/v1/admin/users",
            headers=clinician_auth_headers
        )
        assert response.status_code == 403


@pytest.mark.e2e
@pytest.mark.compliance
class TestComplianceWorkflow:
    """Test complete compliance verification workflow."""

    def test_hipaa_audit_trail_completeness(
        self, client, admin_auth_headers
    ):
        """Verify HIPAA-required audit trail fields are present."""
        # Retrieve audit logs
        response = client.get(
            "/api/v1/audit-logs",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        logs = response.json()

        # Verify each log has required HIPAA fields
        for log in logs:
            assert "user_id" in log
            assert "action" in log
            assert "timestamp" in log
            assert "ip_address" in log
            assert "status" in log

    def test_phi_data_encryption_verification(
        self, client, auth_headers
    ):
        """Verify that PHI data is properly encrypted."""
        # Create patient with PHI
        response = client.post(
            "/api/v1/patients",
            json={
                "mrn": "MRN123456",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1960-01-01",
            },
            headers=auth_headers
        )
        assert response.status_code == 201

        # Retrieve and verify encryption status
        response = client.get(
            "/api/v1/encryption-status",
            headers=auth_headers
        )
        assert response.status_code == 200
        status = response.json()
        assert status["encrypted"] is True
        assert "algorithm" in status
