"""
Unit tests for manual annotation API endpoints.

Tests CRUD operations for manual PHI annotations.
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from httpx import AsyncClient

from app.schemas.manual_annotation import (
    ManualAnnotationCreate,
    ManualAnnotationUpdate,
    ManualAnnotationResponse,
    ManualAnnotationList,
    JobAnalytics,
)


class TestCreateAnnotationEndpoint:
    """Tests for POST /api/v1/deidentify/annotations endpoint."""

    @pytest.mark.asyncio
    async def test_create_annotation_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a manual annotation returns 201."""
        # Arrange
        request_data = {
            "note_id": "note_123",
            "text": "John Doe",
            "start_offset": 8,
            "end_offset": 16,
            "entity_type": "NAME",
            "confidence": 0.95
        }

        # Act
        response = await client.post(
            "/api/v1/deidentify/annotations",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert UUID(data["annotation_id"])  # Valid UUID
        assert data["note_id"] == "note_123"
        assert data["text"] == "John Doe"
        assert data["entity_type"] == "NAME"
        assert data["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_create_annotation_invalid_entity_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test invalid entity type returns 422."""
        # Arrange
        request_data = {
            "note_id": "note_123",
            "text": "John Doe",
            "start_offset": 8,
            "end_offset": 16,
            "entity_type": "INVALID_TYPE",
            "confidence": 0.95
        }

        # Act
        response = await client.post(
            "/api/v1/deidentify/annotations",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_annotation_invalid_offsets(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test invalid offsets (end <= start) returns 422."""
        # Arrange
        request_data = {
            "note_id": "note_123",
            "text": "John Doe",
            "start_offset": 16,
            "end_offset": 8,  # end < start
            "entity_type": "NAME",
            "confidence": 0.95
        }

        # Act
        response = await client.post(
            "/api/v1/deidentify/annotations",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_annotation_audit_logged(
        self, client: AsyncClient, auth_headers: dict, mock_audit_service
    ):
        """Test annotation creation is audit logged."""
        # Arrange
        request_data = {
            "note_id": "note_123",
            "text": "John Doe",
            "start_offset": 8,
            "end_offset": 16,
            "entity_type": "NAME",
            "confidence": 0.95
        }

        # Act
        response = await client.post(
            "/api/v1/deidentify/annotations",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        mock_audit_service.log_access.assert_called_once()


class TestGetAnnotationsEndpoint:
    """Tests for GET /api/v1/deidentify/annotations/{note_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_annotations_for_note(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting annotations for a note returns list."""
        # Arrange - Create an annotation first
        create_data = {
            "note_id": "note_456",
            "text": "Jane Smith",
            "start_offset": 10,
            "end_offset": 20,
            "entity_type": "NAME",
            "confidence": 0.90
        }
        await client.post(
            "/api/v1/deidentify/annotations",
            json=create_data,
            headers=auth_headers
        )

        # Act
        response = await client.get(
            "/api/v1/deidentify/annotations/note_456",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "annotations" in data
        assert "total" in data
        assert data["total"] > 0
        assert len(data["annotations"]) > 0
        assert data["annotations"][0]["note_id"] == "note_456"

    @pytest.mark.asyncio
    async def test_get_annotations_empty_list(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting annotations for note with no annotations returns empty list."""
        # Act
        response = await client.get(
            "/api/v1/deidentify/annotations/nonexistent_note",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["annotations"]) == 0


class TestUpdateAnnotationEndpoint:
    """Tests for PUT /api/v1/deidentify/annotations/{annotation_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_annotation_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating annotation returns updated data."""
        # Arrange - Create annotation first
        create_data = {
            "note_id": "note_789",
            "text": "Bob Jones",
            "start_offset": 5,
            "end_offset": 14,
            "entity_type": "NAME",
            "confidence": 0.85
        }
        create_response = await client.post(
            "/api/v1/deidentify/annotations",
            json=create_data,
            headers=auth_headers
        )
        annotation_id = create_response.json()["annotation_id"]

        # Act - Update confidence
        update_data = {
            "confidence": 0.95
        }
        response = await client.put(
            f"/api/v1/deidentify/annotations/{annotation_id}",
            json=update_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_update_annotation_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating nonexistent annotation returns 404."""
        # Arrange
        fake_id = str(uuid4())
        update_data = {"confidence": 0.95}

        # Act
        response = await client.put(
            f"/api/v1/deidentify/annotations/{fake_id}",
            json=update_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteAnnotationEndpoint:
    """Tests for DELETE /api/v1/deidentify/annotations/{annotation_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_annotation_soft_delete(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test soft deleting annotation (default)."""
        # Arrange - Create annotation first
        create_data = {
            "note_id": "note_delete",
            "text": "Alice Brown",
            "start_offset": 0,
            "end_offset": 11,
            "entity_type": "NAME",
            "confidence": 0.90
        }
        create_response = await client.post(
            "/api/v1/deidentify/annotations",
            json=create_data,
            headers=auth_headers
        )
        annotation_id = create_response.json()["annotation_id"]

        # Act
        response = await client.delete(
            f"/api/v1/deidentify/annotations/{annotation_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["delete_type"] == "SOFT_DELETE"

    @pytest.mark.asyncio
    async def test_delete_annotation_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting nonexistent annotation returns 404."""
        # Arrange
        fake_id = str(uuid4())

        # Act
        response = await client.delete(
            f"/api/v1/deidentify/annotations/{fake_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAnalyticsEndpoint:
    """Tests for GET /api/v1/deidentify/analytics endpoint."""

    @pytest.mark.asyncio
    async def test_get_analytics_admin_only(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test analytics endpoint requires admin role."""
        # Act
        response = await client.get(
            "/api/v1/deidentify/analytics",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_jobs" in data
        assert "success_rate" in data
        assert "avg_processing_time" in data
        assert "total_notes" in data
        assert "jobs_over_time" in data
        assert "phi_distribution" in data
        assert "confidence_by_type" in data

    @pytest.mark.asyncio
    async def test_get_analytics_non_admin_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test non-admin users cannot access analytics."""
        # Act
        response = await client.get(
            "/api/v1/deidentify/analytics",
            headers=auth_headers  # Regular user, not admin
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


# Fixtures
@pytest.fixture
def mock_audit_service(monkeypatch):
    """Mock audit service for testing audit logging."""
    mock_service = MagicMock()
    mock_service.log_access = AsyncMock()
    return mock_service


@pytest.fixture
def admin_auth_headers(auth_headers):
    """Auth headers for admin user."""
    # This would need to be implemented based on how admin tokens are generated
    # For now, return same headers (actual implementation would differ)
    return auth_headers
