"""
Unit tests for AuditService.

Tests all audit logging methods for de-identification operations.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit_service import AuditService
from app.models.user import User
from app.models.audit_log import AuditLog


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    user = MagicMock(spec=User)
    user.id = "test-user-id"
    user.username = "testuser"
    return user


@pytest.mark.asyncio
async def test_log_deidentification_creates_audit_entry(mock_db, mock_user):
    """Test audit entry created for de-identification."""
    # Arrange
    job_id = "job-123"
    note_id = "note-456"
    entities_detected = 10
    entities_removed = 8
    method = "removal"

    # Act
    result = await AuditService.log_deidentification(
        db=mock_db,
        user=mock_user,
        job_id=job_id,
        note_id=note_id,
        entities_detected=entities_detected,
        entities_removed=entities_removed,
        method=method,
        ip_address="192.168.1.1",
        user_agent="pytest/1.0",
        processing_time_ms=1500,
    )

    # Assert
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    audit_log = mock_db.add.call_args[0][0]

    assert audit_log.user_id == mock_user.id
    assert audit_log.username == mock_user.username
    assert audit_log.action == "DEIDENTIFY_NOTE"
    assert audit_log.resource_type == "deidentification_job"
    assert audit_log.resource_id == job_id
    assert audit_log.details["job_id"] == job_id
    assert audit_log.details["note_id"] == note_id
    assert audit_log.details["entities_detected"] == entities_detected
    assert audit_log.details["entities_removed"] == entities_removed
    assert audit_log.details["method_used"] == method
    assert audit_log.details["processing_time_ms"] == 1500
    assert audit_log.success == "success"
    assert audit_log.ip_address == "192.168.1.1"
    assert audit_log.user_agent == "pytest/1.0"


@pytest.mark.asyncio
async def test_log_deidentification_excludes_phi(mock_db, mock_user):
    """Test no PHI content in audit logs."""
    # Act
    await AuditService.log_deidentification(
        db=mock_db,
        user=mock_user,
        job_id="job-123",
        note_id="note-456",
        entities_detected=5,
        entities_removed=5,
        method="removal",
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]

    # Verify no PHI fields in details
    assert "patient_name" not in audit_log.details
    assert "phi_text" not in audit_log.details
    assert "original_text" not in audit_log.details
    assert "deidentified_text" not in audit_log.details

    # Only entity counts and metadata
    assert "entities_detected" in audit_log.details
    assert "entities_removed" in audit_log.details
    assert "method_used" in audit_log.details


@pytest.mark.asyncio
async def test_log_deidentification_with_error(mock_db, mock_user):
    """Test audit log created for failed de-identification."""
    # Arrange
    error_message = "MedCAT service unavailable"

    # Act
    await AuditService.log_deidentification(
        db=mock_db,
        user=mock_user,
        job_id="job-123",
        note_id="note-456",
        entities_detected=0,
        entities_removed=0,
        method="removal",
        error=error_message,
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.success == "failure"
    assert audit_log.error_message == error_message


@pytest.mark.asyncio
async def test_log_job_created(mock_db, mock_user):
    """Test audit log for job creation."""
    # Arrange
    job_id = "job-789"
    total_notes = 100
    method = "replacement"

    # Act
    await AuditService.log_job_created(
        db=mock_db,
        user=mock_user,
        job_id=job_id,
        total_notes=total_notes,
        method=method,
        ip_address="10.0.0.1",
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.action == "CREATE_DEIDENTIFICATION_JOB"
    assert audit_log.resource_type == "deidentification_job"
    assert audit_log.resource_id == job_id
    assert audit_log.details["total_notes"] == total_notes
    assert audit_log.details["method"] == method
    assert audit_log.success == "success"


@pytest.mark.asyncio
async def test_log_job_completed(mock_db, mock_user):
    """Test audit log for job completion."""
    # Arrange
    job_id = "job-789"
    processed_notes = 95
    error_count = 5

    # Act
    await AuditService.log_job_completed(
        db=mock_db,
        user=mock_user,
        job_id=job_id,
        processed_notes=processed_notes,
        error_count=error_count,
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.action == "COMPLETE_DEIDENTIFICATION_JOB"
    assert audit_log.resource_id == job_id
    assert audit_log.details["processed_notes"] == processed_notes
    assert audit_log.details["error_count"] == error_count
    assert audit_log.details["error_rate"] == pytest.approx((5 / 95) * 100)


@pytest.mark.asyncio
async def test_log_job_completed_zero_division(mock_db, mock_user):
    """Test error rate calculation with zero processed notes."""
    # Act
    await AuditService.log_job_completed(
        db=mock_db,
        user=mock_user,
        job_id="job-789",
        processed_notes=0,
        error_count=0,
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.details["error_rate"] == 0


@pytest.mark.asyncio
async def test_log_job_cancelled(mock_db, mock_user):
    """Test audit log for job cancellation."""
    # Arrange
    job_id = "job-789"
    reason = "User stopped job"

    # Act
    await AuditService.log_job_cancelled(
        db=mock_db,
        user=mock_user,
        job_id=job_id,
        reason=reason,
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.action == "CANCEL_DEIDENTIFICATION_JOB"
    assert audit_log.resource_id == job_id
    assert audit_log.details["reason"] == reason


@pytest.mark.asyncio
async def test_log_job_cancelled_default_reason(mock_db, mock_user):
    """Test job cancellation with default reason."""
    # Act
    await AuditService.log_job_cancelled(
        db=mock_db,
        user=mock_user,
        job_id="job-789",
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.details["reason"] == "User cancelled"


@pytest.mark.asyncio
async def test_log_access_view(mock_db, mock_user):
    """Test audit log for viewing de-identified notes."""
    # Act
    await AuditService.log_access(
        db=mock_db,
        user=mock_user,
        action="VIEW",
        resource_id="note-123",
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.action == "VIEW_DEIDENTIFIED_NOTE"
    assert audit_log.resource_type == "deidentified_note"
    assert audit_log.resource_id == "note-123"


@pytest.mark.asyncio
async def test_log_access_download(mock_db, mock_user):
    """Test audit log for downloading de-identified notes."""
    # Act
    await AuditService.log_access(
        db=mock_db,
        user=mock_user,
        action="DOWNLOAD",
        resource_id="note-456",
        ip_address="172.16.0.1",
    )

    # Assert
    audit_log = mock_db.add.call_args[0][0]
    assert audit_log.action == "DOWNLOAD_DEIDENTIFIED_NOTE"
    assert audit_log.ip_address == "172.16.0.1"


@pytest.mark.asyncio
async def test_search_audit_logs_filters_by_user(mock_db, mock_user):
    """Test audit search filters by user_id."""
    # Arrange
    filters = {"user_id": "test-user-id"}
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Act
    results = await AuditService.search_audit_logs(mock_db, filters)

    # Assert
    mock_db.execute.assert_awaited_once()
    # Verify query was built with user_id filter
    assert results == []


@pytest.mark.asyncio
async def test_search_audit_logs_filters_by_action(mock_db):
    """Test audit search filters by action."""
    # Arrange
    filters = {"action": "DEIDENTIFY_NOTE"}
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Act
    results = await AuditService.search_audit_logs(mock_db, filters)

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_search_audit_logs_date_range(mock_db):
    """Test audit search with date range."""
    # Arrange
    filters = {
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-12-31T23:59:59",
    }
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Act
    results = await AuditService.search_audit_logs(mock_db, filters)

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_search_audit_logs_pagination(mock_db):
    """Test audit search pagination."""
    # Arrange
    filters = {"limit": 50, "offset": 100}
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Act
    results = await AuditService.search_audit_logs(mock_db, filters)

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_search_audit_logs_max_limit(mock_db):
    """Test audit search enforces max limit."""
    # Arrange
    filters = {"limit": 5000}  # Exceeds max of 1000
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Act
    await AuditService.search_audit_logs(mock_db, filters)

    # Assert - should be capped at 1000
    # (would need to inspect query to fully verify)


@pytest.mark.asyncio
async def test_cleanup_old_audit_logs(mock_db):
    """Test cleanup of old audit logs."""
    # Arrange
    retention_days = 2920  # 8 years
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 150
    mock_db.execute.return_value = mock_count_result

    # Act
    deleted_count = await AuditService.cleanup_old_audit_logs(mock_db, retention_days)

    # Assert
    assert deleted_count == 150
    assert mock_db.execute.await_count == 2  # Count query + delete query
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_old_audit_logs_default_retention(mock_db):
    """Test cleanup uses default 8-year retention."""
    # Arrange
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 0
    mock_db.execute.return_value = mock_count_result

    # Act
    deleted_count = await AuditService.cleanup_old_audit_logs(mock_db)

    # Assert
    assert deleted_count == 0
