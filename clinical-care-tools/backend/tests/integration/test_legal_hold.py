"""Integration tests for legal hold workflow."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentStatus, DocumentType


@pytest.mark.asyncio
class TestLegalHoldWorkflow:
    """Test legal hold API endpoints."""

    async def test_place_legal_hold(
        self, client: AsyncClient, test_admin_user, test_patient, db_session
    ):
        """Test admin can place legal hold on document."""
        # Create document
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test Document",
            status=DocumentStatus.COMPLETED,
            legal_hold=False,
        )
        db_session.add(doc)
        await db_session.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_admin_user.email,
                "password": "adminpass123",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Place legal hold
        response = await client.post(
            f"/api/v1/admin/documents/{doc.id}/legal-hold",
            json={
                "reason": "Litigation hold for malpractice case #12345",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["legal_hold"] is True
        assert data["legal_hold_reason"] == "Litigation hold for malpractice case #12345"
        assert data["legal_hold_by"] == str(test_admin_user.id)

        # Verify audit log created
        query = select(AuditLog).where(
            AuditLog.action == "LEGAL_HOLD_PLACED",
            AuditLog.resource_id == str(doc.id),
        )
        result = await db_session.execute(query)
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None

    async def test_legal_hold_prevents_deletion(
        self, client: AsyncClient, test_admin_user, test_patient, db_session
    ):
        """Test legal hold prevents document deletion."""
        # Create old document (9 years) with legal hold
        old_date = datetime.utcnow() - timedelta(days=365 * 9)
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=old_date,
            title="Old Document",
            status=DocumentStatus.COMPLETED,
            legal_hold=True,
            legal_hold_reason="Investigation",
            legal_hold_by=test_admin_user.id,
            legal_hold_at=datetime.utcnow(),
        )
        db_session.add(doc)
        await db_session.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_admin_user.email,
                "password": "adminpass123",
            },
        )
        token = login_response.json()["access_token"]

        # Try to run data retention purge
        response = await client.post(
            "/api/v1/admin/data-retention/purge",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        results = response.json()

        # Verify document NOT deleted (legal hold)
        query = select(Document).where(Document.id == doc.id)
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is not None

    async def test_remove_legal_hold(
        self, client: AsyncClient, test_admin_user, test_patient, db_session
    ):
        """Test admin can remove legal hold."""
        # Create document with legal hold
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test Document",
            status=DocumentStatus.COMPLETED,
            legal_hold=True,
            legal_hold_reason="Investigation",
            legal_hold_by=test_admin_user.id,
            legal_hold_at=datetime.utcnow(),
        )
        db_session.add(doc)
        await db_session.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_admin_user.email,
                "password": "adminpass123",
            },
        )
        token = login_response.json()["access_token"]

        # Remove legal hold
        response = await client.delete(
            f"/api/v1/admin/documents/{doc.id}/legal-hold",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["legal_hold"] is False
        assert data["legal_hold_reason"] is None
        assert data["legal_hold_by"] is None

        # Verify audit log
        query = select(AuditLog).where(
            AuditLog.action == "LEGAL_HOLD_REMOVED",
            AuditLog.resource_id == str(doc.id),
        )
        result = await db_session.execute(query)
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None

    async def test_non_admin_cannot_place_hold(
        self, client: AsyncClient, test_clinician_user, test_patient, db_session
    ):
        """Test non-admin users cannot place legal hold."""
        # Create document
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test Document",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Login as clinician (not admin)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_clinician_user.email,
                "password": "clinicianpass123",
            },
        )
        token = login_response.json()["access_token"]

        # Try to place legal hold
        response = await client.post(
            f"/api/v1/admin/documents/{doc.id}/legal-hold",
            json={
                "reason": "Should not be allowed",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403  # Forbidden
