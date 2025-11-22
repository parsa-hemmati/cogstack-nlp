"""
Unit tests for break-glass access service.

Tests cover:
- Emergency access requests
- Access approval/denial
- Access revocation
- Timeout and expiration
- Audit logging
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.break_glass_service import BreakGlassService
from app.models.break_glass_access import BreakGlassAccess, BreakGlassStatus


@pytest.mark.unit
class TestBreakGlassService:
    """Test cases for break-glass service."""

    @pytest.fixture
    async def service(self, db_session):
        """Create service instance."""
        return BreakGlassService(db_session)

    @pytest.fixture
    def test_data(self):
        """Test data."""
        return {
            "user_id": str(uuid4()),
            "patient_id": str(uuid4()),
            "justification": "Emergency: Patient in critical condition, immediate access required"
        }

    @pytest.mark.asyncio
    async def test_request_access_success(self, service, test_data):
        """Test successful emergency access request."""
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        assert access is not None
        assert access.user_id == test_data["user_id"]
        assert access.patient_id == test_data["patient_id"]
        assert access.status == BreakGlassStatus.PENDING
        assert access.justification == test_data["justification"]

    @pytest.mark.asyncio
    async def test_request_access_short_justification(self, service, test_data):
        """Test rejection of short justification."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await service.request_access(
                user_id=test_data["user_id"],
                patient_id=test_data["patient_id"],
                justification="Short"
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_approve_access(self, service, test_data):
        """Test approval of access request."""
        # Create request
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        # Approve
        reviewer_id = str(uuid4())
        approved = await service.approve_access(
            access_id=access.id,
            reviewer_id=reviewer_id,
            review_notes="Approved: Emergency condition verified"
        )

        assert approved.status == BreakGlassStatus.APPROVED
        assert approved.reviewed_by == reviewer_id
        assert approved.access_granted_at is not None
        assert approved.access_expires_at is not None

    @pytest.mark.asyncio
    async def test_deny_access(self, service, test_data):
        """Test denial of access request."""
        # Create request
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        # Deny
        reviewer_id = str(uuid4())
        denied = await service.deny_access(
            access_id=access.id,
            reviewer_id=reviewer_id,
            reason="Not an emergency"
        )

        assert denied.status == BreakGlassStatus.DENIED
        assert denied.reviewed_by == reviewer_id
        assert "Not an emergency" in denied.review_notes

    @pytest.mark.asyncio
    async def test_revoke_access(self, service, test_data):
        """Test revocation of approved access."""
        # Create and approve
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        await service.approve_access(
            access_id=access.id,
            reviewer_id=str(uuid4())
        )

        # Revoke
        revoked = await service.revoke_access(
            access_id=access.id,
            revoked_by=str(uuid4()),
            reason="Emergency resolved"
        )

        assert revoked.status == BreakGlassStatus.REVOKED
        assert revoked.revoked_at is not None

    @pytest.mark.asyncio
    async def test_record_access(self, service, test_data):
        """Test recording of actual data access."""
        # Create and approve
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        await service.approve_access(
            access_id=access.id,
            reviewer_id=str(uuid4())
        )

        # Record access
        accessed = await service.record_access(access_id=access.id)

        assert accessed.accessed_at is not None

    @pytest.mark.asyncio
    async def test_check_access_valid(self, service, test_data):
        """Test checking valid access."""
        # Create and approve
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        await service.approve_access(
            access_id=access.id,
            reviewer_id=str(uuid4())
        )

        # Check access
        result = await service.check_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"]
        )

        assert result is not None
        assert result.id == access.id

    @pytest.mark.asyncio
    async def test_cleanup_expired_access(self, service, test_data):
        """Test cleanup of expired access."""
        # Create and approve with immediate expiration
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        await service.approve_access(
            access_id=access.id,
            reviewer_id=str(uuid4())
        )

        # Manually set expiration to past
        access.access_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await service.db.commit()

        # Cleanup
        count = await service.cleanup_expired_access()

        assert count > 0

    @pytest.mark.asyncio
    async def test_access_expires_after_window(self, service, test_data):
        """Test access expires after time window."""
        # Create and approve
        access = await service.request_access(
            user_id=test_data["user_id"],
            patient_id=test_data["patient_id"],
            justification=test_data["justification"]
        )

        await service.approve_access(
            access_id=access.id,
            reviewer_id=str(uuid4())
        )

        # Set expiration to past
        access.access_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await service.db.commit()

        # Try to record access - should fail
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await service.record_access(access_id=access.id)

        assert exc_info.value.status_code == 403
