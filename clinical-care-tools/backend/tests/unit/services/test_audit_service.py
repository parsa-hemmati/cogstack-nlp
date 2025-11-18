"""Tests for audit service."""

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService


@pytest.mark.asyncio
class TestAuditService:
    """Test audit service."""

    async def test_log_action(self, db_session, test_user):
        """Test logging an action."""
        service = AuditService(db_session)

        await service.log(
            user_id=test_user.id,
            action="VIEW_PATIENT",
            resource_type="patient",
            resource_id="patient-123",
            details={"field": "demographics"},
        )

        # Verify log created
        query = select(AuditLog).where(AuditLog.user_id == test_user.id)
        result = await db_session.execute(query)
        log = result.scalar_one()

        assert log.action == "VIEW_PATIENT"
        assert log.resource_type == "patient"
        assert log.resource_id == "patient-123"
        assert log.details["field"] == "demographics"

    async def test_log_without_user(self, db_session):
        """Test logging without user (system action)."""
        service = AuditService(db_session)

        await service.log(
            user_id=None,
            action="SYSTEM_BACKUP",
            resource_type="system",
            resource_id="backup-001",
        )

        # Verify log created
        query = select(AuditLog).where(AuditLog.action == "SYSTEM_BACKUP")
        result = await db_session.execute(query)
        log = result.scalar_one()

        assert log.user_id is None
        assert log.action == "SYSTEM_BACKUP"

    async def test_log_phi_access(self, db_session, test_clinician_user, test_patient):
        """Test logging PHI access."""
        service = AuditService(db_session)

        await service.log(
            user_id=test_clinician_user.id,
            action="VIEW_PATIENT_DOCUMENTS",
            resource_type="patient",
            resource_id=str(test_patient.id),
            details={
                "document_count": 5,
                "access_reason": "clinical_review",
            },
        )

        # Verify log
        query = select(AuditLog).where(AuditLog.user_id == test_clinician_user.id)
        result = await db_session.execute(query)
        log = result.scalar_one()

        assert log.resource_id == str(test_patient.id)
        assert log.details["access_reason"] == "clinical_review"

    async def test_multiple_logs(self, db_session, test_user):
        """Test creating multiple audit logs."""
        service = AuditService(db_session)

        actions = ["LOGIN", "VIEW_PATIENT", "EXPORT_DATA", "LOGOUT"]

        for action in actions:
            await service.log(
                user_id=test_user.id,
                action=action,
                resource_type="system",
            )

        # Verify all logs created
        query = select(AuditLog).where(AuditLog.user_id == test_user.id)
        result = await db_session.execute(query)
        logs = result.scalars().all()

        assert len(logs) == len(actions)
        assert [log.action for log in logs] == actions
