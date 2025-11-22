"""
Integration tests for Timeline API endpoints.

Tests cover:
- GET /api/v1/timeline/{patient_id} - Get patient timeline
- GET /api/v1/timeline/{patient_id}/concepts/{concept_cui} - Get concept details
- POST /api/v1/timeline/{patient_id}/export - Create export
- GET /api/v1/timeline/exports/{export_id} - Get export status
- GET /api/v1/timeline/exports/{export_id}/download - Download export file
- GET /api/v1/timeline/filters - List saved filters
- POST /api/v1/timeline/filters - Save filter preset
- Authentication and authorization
"""

import pytest
from fastapi import status
from uuid import uuid4
from datetime import date


@pytest.mark.integration
class TestGetPatientTimeline:
    """Test GET /api/v1/timeline/{patient_id} endpoint."""

    def test_returns_401_without_jwt(self, client):
        """Test that endpoint requires authentication."""
        patient_id = uuid4()
        response = client.get(f"/api/v1/timeline/{patient_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_403_without_proper_role(self, client, auth_headers_patient):
        """Test that endpoint requires clinician/researcher/admin role."""
        patient_id = uuid4()
        response = client.get(
            f"/api/v1/timeline/{patient_id}",
            headers=auth_headers_patient  # Patient role not allowed
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_returns_404_if_patient_not_found(self, client, auth_headers_clinician):
        """Test that 404 is returned for non-existent patient."""
        patient_id = uuid4()  # Random UUID that doesn't exist
        response = client.get(
            f"/api/v1/timeline/{patient_id}",
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_200_with_valid_request(self, client, auth_headers_clinician, test_patient):
        """Test successful timeline retrieval."""
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["patient_id"] == str(test_patient.id)
        assert "documents" in data
        assert "concepts" in data
        assert "statistics" in data

    def test_applies_date_filters_correctly(self, client, auth_headers_clinician, test_patient):
        """Test that date filters are applied to timeline query."""
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={
                "date_start": "2024-01-01",
                "date_end": "2024-12-31"
            },
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["date_range"]["start"] == "2024-01-01"
        assert data["date_range"]["end"] == "2024-12-31"

    def test_applies_concept_filters_correctly(self, client, auth_headers_clinician, test_patient):
        """Test that concept CUI filters are applied."""
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={"concept_cuis": ["C0011860", "C0004238"]},
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "concepts" in data

    def test_applies_meta_annotation_filters(self, client, auth_headers_clinician, test_patient):
        """Test that meta-annotation filters are applied."""
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={
                "negation": "Affirmed",
                "experiencer": "Patient"
            },
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestGetConceptDetails:
    """Test GET /api/v1/timeline/{patient_id}/concepts/{concept_cui} endpoint."""

    def test_returns_401_without_jwt(self, client):
        """Test that endpoint requires authentication."""
        patient_id = uuid4()
        concept_cui = "C0011860"
        response = client.get(f"/api/v1/timeline/{patient_id}/concepts/{concept_cui}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_concept_details(self, client, auth_headers_clinician, test_patient):
        """Test successful concept details retrieval."""
        concept_cui = "C0011860"
        response = client.get(
            f"/api/v1/timeline/{test_patient.id}/concepts/{concept_cui}",
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cui"] == concept_cui
        assert "mentions" in data


@pytest.mark.integration
class TestExportTimeline:
    """Test POST /api/v1/timeline/{patient_id}/export endpoint."""

    def test_returns_401_without_jwt(self, client):
        """Test that endpoint requires authentication."""
        patient_id = uuid4()
        response = client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json={"format": "pdf", "filters": {}}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creates_export_successfully(self, client, auth_headers_clinician, test_patient):
        """Test successful export creation."""
        response = client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            json={"format": "pdf", "filters": {}},
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "export_id" in data
        assert data["format"] == "pdf"
        assert data["status"] == "processing"

    def test_validates_export_format(self, client, auth_headers_clinician, test_patient):
        """Test that invalid export format is rejected."""
        response = client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            json={"format": "invalid", "filters": {}},
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
class TestGetExportStatus:
    """Test GET /api/v1/timeline/exports/{export_id} endpoint."""

    def test_returns_401_without_jwt(self, client):
        """Test that endpoint requires authentication."""
        export_id = uuid4()
        response = client.get(f"/api/v1/timeline/exports/{export_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_export_status(self, client, auth_headers_clinician, test_export):
        """Test successful export status retrieval."""
        response = client.get(
            f"/api/v1/timeline/exports/{test_export.id}",
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["export_id"] == str(test_export.id)
        assert "status" in data
        assert "format" in data


@pytest.mark.integration
class TestDownloadExport:
    """Test GET /api/v1/timeline/exports/{export_id}/download endpoint."""

    def test_returns_401_without_jwt(self, client):
        """Test that endpoint requires authentication."""
        export_id = uuid4()
        response = client.get(f"/api/v1/timeline/exports/{export_id}/download")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_404_if_export_not_completed(self, client, auth_headers_clinician, test_export_processing):
        """Test that download fails if export not completed."""
        response = client.get(
            f"/api/v1/timeline/exports/{test_export_processing.id}/download",
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_downloads_completed_export(self, client, auth_headers_clinician, test_export_completed):
        """Test successful file download."""
        response = client.get(
            f"/api/v1/timeline/exports/{test_export_completed.id}/download",
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] in ["application/pdf", "application/json", "application/fhir+json"]


@pytest.mark.integration
class TestListFilters:
    """Test GET /api/v1/timeline/filters endpoint."""

    def test_returns_401_without_jwt(self, client):
        """Test that endpoint requires authentication."""
        response = client.get("/api/v1/timeline/filters")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_user_filters(self, client, auth_headers_clinician, test_filter):
        """Test successful filter list retrieval."""
        response = client.get(
            "/api/v1/timeline/filters",
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "name" in data[0]
            assert "filters" in data[0]


@pytest.mark.integration
class TestSaveFilter:
    """Test POST /api/v1/timeline/filters endpoint."""

    def test_returns_401_without_jwt(self, client):
        """Test that endpoint requires authentication."""
        response = client.post(
            "/api/v1/timeline/filters",
            json={"name": "My Filter", "filters": {}}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creates_filter_successfully(self, client, auth_headers_clinician):
        """Test successful filter creation."""
        response = client.post(
            "/api/v1/timeline/filters",
            json={
                "name": "Diabetes Filter",
                "description": "Filter for diabetes patients",
                "filters": {"concept_cuis": ["C0011860"]},
                "is_default": False
            },
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Diabetes Filter"
        assert "id" in data

    def test_validates_filter_name_length(self, client, auth_headers_clinician):
        """Test that filter name must be at least 3 characters."""
        response = client.post(
            "/api/v1/timeline/filters",
            json={"name": "AB", "filters": {}},
            headers=auth_headers_clinician
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
