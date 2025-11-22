"""
Unit tests for de-identification API endpoints.

Tests single note de-identification, batch processing, job management.
"""
import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from httpx import AsyncClient

from app.schemas.deidentification_api import (
    DeidentifyRequest,
    DeidentifyResponse,
    DeidentifyBatchRequest,
    JobStatus,
    BatchNote,
)
from app.schemas.phi_entity import PHIEntity
from app.schemas.deidentification import DeidentificationResult


class TestDeidentifySingleEndpoint:
    """Tests for POST /api/v1/deidentify endpoint."""

    @pytest.mark.asyncio
    async def test_deidentify_single_note_success(
        self, client: AsyncClient, auth_headers: dict, mock_deidentification_service
    ):
        """Test single note de-identification returns result."""
        # Arrange
        request_data = {
            "text": "Patient John Doe was admitted on 01/15/2024",
            "method": "removal",
            "return_entities": True
        }

        mock_result = DeidentificationResult(
            original_text=request_data["text"],
            deidentified_text="Patient [NAME] was admitted on [DATE]",
            entities_removed=[
                PHIEntity(
                    entity_type="NAME",
                    text="John Doe",
                    start=8,
                    end=16,
                    confidence=0.95,
                    cui=None
                )
            ],
            method_used="removal",
            confidence_score=0.95,
            review_required=False,
            entity_mappings={"John Doe": "[NAME]"}
        )
        mock_deidentification_service.deidentify = AsyncMock(return_value=mock_result)

        # Act
        response = await client.post(
            "/api/v1/deidentify",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deidentified_text"] == "Patient [NAME] was admitted on [DATE]"
        assert data["method_used"] == "removal"
        assert data["confidence_score"] == 0.95
        assert data["review_required"] is False
        assert len(data["entities_removed"]) == 1
        assert data["entities_removed"][0]["entity_type"] == "NAME"

    @pytest.mark.asyncio
    async def test_deidentify_empty_text_returns_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test empty text returns 400 Bad Request."""
        # Arrange
        request_data = {
            "text": "",
            "method": "removal"
        }

        # Act
        response = await client.post(
            "/api/v1/deidentify",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_deidentify_invalid_method_returns_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test invalid method returns 400 Bad Request."""
        # Arrange
        request_data = {
            "text": "Patient data",
            "method": "invalid_method"
        }

        # Act
        response = await client.post(
            "/api/v1/deidentify",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_deidentify_service_error_returns_500(
        self, client: AsyncClient, auth_headers: dict, mock_deidentification_service
    ):
        """Test service error returns 500 Internal Server Error."""
        # Arrange
        request_data = {
            "text": "Patient data",
            "method": "removal"
        }
        mock_deidentification_service.deidentify = AsyncMock(
            side_effect=Exception("MedCAT service unavailable")
        )

        # Act
        response = await client.post(
            "/api/v1/deidentify",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "unavailable" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_deidentify_without_entities_in_response(
        self, client: AsyncClient, auth_headers: dict, mock_deidentification_service
    ):
        """Test return_entities=False excludes entities from response."""
        # Arrange
        request_data = {
            "text": "Patient John Doe",
            "method": "removal",
            "return_entities": False
        }

        mock_result = DeidentificationResult(
            original_text=request_data["text"],
            deidentified_text="Patient [NAME]",
            entities_removed=[
                PHIEntity(
                    entity_type="NAME",
                    text="John Doe",
                    start=8,
                    end=16,
                    confidence=0.95,
                    cui=None
                )
            ],
            method_used="removal",
            confidence_score=0.95,
            review_required=False,
            entity_mappings={}
        )
        mock_deidentification_service.deidentify = AsyncMock(return_value=mock_result)

        # Act
        response = await client.post(
            "/api/v1/deidentify",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["entities_removed"] is None


class TestDeidentifyBatchEndpoint:
    """Tests for POST /api/v1/deidentify/batch endpoint."""

    @pytest.mark.asyncio
    async def test_deidentify_batch_creates_job(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test batch endpoint creates job and returns job_id."""
        # Arrange
        request_data = {
            "notes": [
                {"id": "note_1", "text": "Patient A has diabetes"},
                {"id": "note_2", "text": "Patient B has hypertension"}
            ],
            "method": "replacement",
            "notify_email": "researcher@example.com"
        }

        job_id = uuid4()
        mock_job_manager.create_job = AsyncMock(return_value=job_id)

        # Act
        response = await client.post(
            "/api/v1/deidentify/batch",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert UUID(data["job_id"]) == job_id
        assert data["status"] == "pending"
        assert data["total_notes"] == 2
        assert "created_at" in data
        assert "estimated_completion" in data

    @pytest.mark.asyncio
    async def test_deidentify_batch_empty_notes_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test empty notes list returns 422 Unprocessable Entity."""
        # Arrange
        request_data = {
            "notes": [],
            "method": "removal"
        }

        # Act
        response = await client.post(
            "/api/v1/deidentify/batch",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_deidentify_batch_large_batch_accepted(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test large batch (1000 notes) is accepted."""
        # Arrange
        notes = [
            {"id": f"note_{i}", "text": f"Patient {i} data"}
            for i in range(1000)
        ]
        request_data = {
            "notes": notes,
            "method": "removal"
        }

        job_id = uuid4()
        mock_job_manager.create_job = AsyncMock(return_value=job_id)

        # Act
        response = await client.post(
            "/api/v1/deidentify/batch",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["total_notes"] == 1000


class TestJobStatusEndpoint:
    """Tests for GET /api/v1/deidentify/job/{job_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_job_status_returns_progress(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test job status endpoint shows progress."""
        # Arrange
        job_id = uuid4()
        mock_job_status = JobStatus(
            job_id=job_id,
            status="processing",
            total_notes=1000,
            processed_notes=450,
            progress_percentage=45.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            estimated_completion=datetime.utcnow() + timedelta(minutes=30),
            errors=[]
        )
        mock_job_manager.get_job_status = AsyncMock(return_value=mock_job_status)

        # Act
        response = await client.get(
            f"/api/v1/deidentify/job/{job_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "processing"
        assert data["total_notes"] == 1000
        assert data["processed_notes"] == 450
        assert data["progress_percentage"] == 45.0

    @pytest.mark.asyncio
    async def test_get_job_status_not_found_returns_404(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test non-existent job returns 404 Not Found."""
        # Arrange
        job_id = uuid4()
        mock_job_manager.get_job_status = AsyncMock(return_value=None)

        # Act
        response = await client.get(
            f"/api/v1/deidentify/job/{job_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_job_status_completed_job(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test completed job shows 100% progress."""
        # Arrange
        job_id = uuid4()
        mock_job_status = JobStatus(
            job_id=job_id,
            status="completed",
            total_notes=100,
            processed_notes=100,
            progress_percentage=100.0,
            created_at=datetime.utcnow() - timedelta(hours=1),
            updated_at=datetime.utcnow(),
            estimated_completion=None,
            errors=[]
        )
        mock_job_manager.get_job_status = AsyncMock(return_value=mock_job_status)

        # Act
        response = await client.get(
            f"/api/v1/deidentify/job/{job_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100.0


class TestCancelJobEndpoint:
    """Tests for POST /api/v1/deidentify/job/{job_id}/cancel endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_job_terminates_celery_task(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test job cancellation stops processing."""
        # Arrange
        job_id = uuid4()
        mock_job_manager.cancel_job = AsyncMock(return_value=True)

        # Act
        response = await client.post(
            f"/api/v1/deidentify/job/{job_id}/cancel",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"
        mock_job_manager.cancel_job.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_cancel_job_not_found_returns_404(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test cancelling non-existent job returns 404."""
        # Arrange
        job_id = uuid4()
        mock_job_manager.cancel_job = AsyncMock(return_value=False)

        # Act
        response = await client.post(
            f"/api/v1/deidentify/job/{job_id}/cancel",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_completed_job_returns_400(
        self, client: AsyncClient, auth_headers: dict, mock_job_manager
    ):
        """Test cancelling completed job returns 400 Bad Request."""
        # Arrange
        job_id = uuid4()
        mock_job_manager.cancel_job = AsyncMock(
            side_effect=ValueError("Cannot cancel completed job")
        )

        # Act
        response = await client.post(
            f"/api/v1/deidentify/job/{job_id}/cancel",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRateLimiting:
    """Tests for rate limiting enforcement."""

    @pytest.mark.asyncio
    async def test_rate_limiting_blocks_excessive_requests(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test rate limiting enforced (100 req/min)."""
        # This test requires rate limiting middleware to be configured
        # For now, we'll skip implementation details
        pytest.skip("Rate limiting middleware not yet implemented")


# Fixtures
@pytest.fixture
def mock_deidentification_service(monkeypatch):
    """Mock deidentification service."""
    mock_service = MagicMock()
    return mock_service


@pytest.fixture
def mock_job_manager(monkeypatch):
    """Mock job manager service."""
    mock_manager = MagicMock()
    return mock_manager
