"""
Integration tests for batch de-identification processing.

Tests end-to-end workflows with real database, Celery, and services.
"""
import pytest
import asyncio
from datetime import datetime
from uuid import UUID
from typing import List

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.deidentification_api import JobStatus, BatchNote


class TestBatchDeidentificationWorkflow:
    """Integration tests for complete batch processing workflow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_deidentify_1000_notes(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test 1,000 notes processed in <2 hours."""
        # Arrange
        notes = [
            {"id": f"note_{i}", "text": f"Patient {i} has condition X"}
            for i in range(1000)
        ]
        request_data = {
            "notes": notes,
            "method": "removal",
            "notify_email": "researcher@example.com"
        }

        # Act - Submit batch job
        response = await client.post(
            "/api/v1/deidentify/batch",
            json=request_data,
            headers=auth_headers
        )

        # Assert - Job created
        assert response.status_code == 202
        job_data = response.json()
        job_id = UUID(job_data["job_id"])

        # Act - Poll for completion (with timeout)
        max_wait_seconds = 7200  # 2 hours
        poll_interval = 5  # Poll every 5 seconds
        start_time = datetime.utcnow()

        status_response = None
        while True:
            status_response = await client.get(
                f"/api/v1/deidentify/job/{job_id}",
                headers=auth_headers
            )
            status_data = status_response.json()

            if status_data["status"] in ["completed", "failed", "cancelled"]:
                break

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > max_wait_seconds:
                pytest.fail(f"Job did not complete within {max_wait_seconds} seconds")

            await asyncio.sleep(poll_interval)

        # Assert - Job completed successfully
        assert status_response.status_code == 200
        final_status = status_response.json()
        assert final_status["status"] == "completed"
        assert final_status["processed_notes"] == 1000
        assert final_status["progress_percentage"] == 100.0
        assert len(final_status["errors"]) == 0

        # Verify processing time
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        assert elapsed_time < 7200, f"Processing took {elapsed_time}s (expected <7200s)"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_handles_partial_failures(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test some notes fail, others succeed."""
        # Arrange - Mix of valid and invalid notes
        notes = [
            {"id": "note_1", "text": "Valid patient data"},
            {"id": "note_2", "text": ""},  # Empty text - will fail
            {"id": "note_3", "text": "Another valid patient"},
            {"id": "note_4", "text": "A" * 1000000},  # Too large - will fail
            {"id": "note_5", "text": "Valid data again"}
        ]
        request_data = {
            "notes": notes,
            "method": "removal"
        }

        # Act - Submit batch
        response = await client.post(
            "/api/v1/deidentify/batch",
            json=request_data,
            headers=auth_headers
        )

        job_id = UUID(response.json()["job_id"])

        # Wait for completion
        await asyncio.sleep(10)  # Wait for processing

        # Get final status
        status_response = await client.get(
            f"/api/v1/deidentify/job/{job_id}",
            headers=auth_headers
        )

        # Assert - Some succeeded, some failed
        status_data = status_response.json()
        assert status_data["status"] in ["completed", "partial_failure"]
        assert status_data["processed_notes"] == 5
        assert len(status_data["errors"]) > 0  # At least 1 error
        assert len(status_data["errors"]) < 5  # Not all failed

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_email_notification_sent_on_completion(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        mock_email_service,
    ):
        """Test email sent when job completes."""
        # Arrange
        notes = [
            {"id": f"note_{i}", "text": f"Patient {i} data"}
            for i in range(10)
        ]
        notify_email = "researcher@example.com"
        request_data = {
            "notes": notes,
            "method": "removal",
            "notify_email": notify_email
        }

        # Act - Submit job
        response = await client.post(
            "/api/v1/deidentify/batch",
            json=request_data,
            headers=auth_headers
        )

        job_id = UUID(response.json()["job_id"])

        # Wait for completion
        await asyncio.sleep(5)

        # Assert - Email sent
        mock_email_service.send_completion_email.assert_called_once()
        call_args = mock_email_service.send_completion_email.call_args
        assert call_args[0][0] == notify_email  # First arg is email address
        assert str(job_id) in str(call_args)  # Job ID mentioned

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_job_cancellation_stops_processing(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test cancelling a job stops processing."""
        # Arrange - Large batch to ensure we can cancel mid-processing
        notes = [
            {"id": f"note_{i}", "text": f"Patient {i} data"}
            for i in range(1000)
        ]
        request_data = {
            "notes": notes,
            "method": "removal"
        }

        # Act - Submit job
        response = await client.post(
            "/api/v1/deidentify/batch",
            json=request_data,
            headers=auth_headers
        )

        job_id = UUID(response.json()["job_id"])

        # Wait a bit for processing to start
        await asyncio.sleep(2)

        # Cancel the job
        cancel_response = await client.post(
            f"/api/v1/deidentify/job/{job_id}/cancel",
            headers=auth_headers
        )

        # Assert - Cancellation successful
        assert cancel_response.status_code == 200

        # Wait a bit more
        await asyncio.sleep(3)

        # Check final status
        status_response = await client.get(
            f"/api/v1/deidentify/job/{job_id}",
            headers=auth_headers
        )

        status_data = status_response.json()
        assert status_data["status"] == "cancelled"
        # Should not have processed all notes
        assert status_data["processed_notes"] < 1000

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_batch_jobs(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test multiple batch jobs can run concurrently."""
        # Arrange - Create 3 concurrent jobs
        job_ids = []

        for i in range(3):
            notes = [
                {"id": f"batch{i}_note_{j}", "text": f"Patient {j} data"}
                for j in range(100)
            ]
            request_data = {
                "notes": notes,
                "method": "removal"
            }

            response = await client.post(
                "/api/v1/deidentify/batch",
                json=request_data,
                headers=auth_headers
            )

            job_ids.append(UUID(response.json()["job_id"]))

        # Wait for all to complete
        await asyncio.sleep(15)

        # Assert - All jobs completed
        for job_id in job_ids:
            status_response = await client.get(
                f"/api/v1/deidentify/job/{job_id}",
                headers=auth_headers
            )

            status_data = status_response.json()
            assert status_data["status"] == "completed"
            assert status_data["processed_notes"] == 100


# Fixtures
@pytest.fixture
def mock_email_service(monkeypatch):
    """Mock email service for testing notifications."""
    from unittest.mock import MagicMock
    mock_service = MagicMock()
    mock_service.send_completion_email = MagicMock()
    # Patch the email service in the appropriate module
    # monkeypatch.setattr("app.services.email_service.EmailService", mock_service)
    return mock_service
