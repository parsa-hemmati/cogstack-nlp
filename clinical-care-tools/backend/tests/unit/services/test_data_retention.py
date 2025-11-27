"""Tests for data retention service."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.user import User
from app.services.data_retention_service import DataRetentionService


@pytest.mark.asyncio
class TestDataRetentionService:
    """Test data retention service."""

    async def test_purge_old_documents(self, db_session, test_patient):
        """Test purging documents older than retention period."""
        # Create old document (9 years old)
        old_date = datetime.utcnow() - timedelta(days=365 * 9)
        old_doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=old_date,
            title="Old Document",
            status=DocumentStatus.COMPLETED,
            legal_hold=False,
        )
        db_session.add(old_doc)

        # Create recent document (1 year old)
        recent_date = datetime.utcnow() - timedelta(days=365)
        recent_doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=recent_date,
            title="Recent Document",
            status=DocumentStatus.COMPLETED,
            legal_hold=False,
        )
        db_session.add(recent_doc)

        await db_session.commit()

        # Run purge
        service = DataRetentionService(db_session)
        results = await service.purge_old_data()

        # Verify old document deleted
        assert results["documents_deleted"] == 1

        # Verify recent document still exists
        query = select(Document).where(Document.id == recent_doc.id)
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is not None

        # Verify old document deleted
        query = select(Document).where(Document.id == old_doc.id)
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is None

    async def test_legal_hold_prevents_deletion(self, db_session, test_patient, test_user):
        """Test legal hold prevents document deletion."""
        # Create old document with legal hold
        old_date = datetime.utcnow() - timedelta(days=365 * 9)
        doc_on_hold = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=old_date,
            title="Document on Legal Hold",
            status=DocumentStatus.COMPLETED,
            legal_hold=True,
            legal_hold_reason="Litigation hold",
            legal_hold_by=test_user.id,
            legal_hold_at=datetime.utcnow(),
        )
        db_session.add(doc_on_hold)
        await db_session.commit()

        # Run purge
        service = DataRetentionService(db_session)
        results = await service.purge_old_data()

        # Verify no documents deleted (legal hold)
        assert results["documents_deleted"] == 0

        # Verify document still exists
        query = select(Document).where(Document.id == doc_on_hold.id)
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is not None

    async def test_purge_old_audit_logs(self, db_session, test_user):
        """Test purging audit logs older than retention period."""
        # Create old audit log (8 years old)
        old_date = datetime.utcnow() - timedelta(days=365 * 8)
        old_log = AuditLog(
            user_id=test_user.id,
            action="VIEW_PATIENT",
            resource_type="patient",
            resource_id=str(uuid4()),
            created_at=old_date,
        )
        db_session.add(old_log)

        # Create recent audit log (1 year old)
        recent_date = datetime.utcnow() - timedelta(days=365)
        recent_log = AuditLog(
            user_id=test_user.id,
            action="VIEW_PATIENT",
            resource_type="patient",
            resource_id=str(uuid4()),
            created_at=recent_date,
        )
        db_session.add(recent_log)

        await db_session.commit()

        # Run purge
        service = DataRetentionService(db_session)
        results = await service.purge_old_data()

        # Verify old log deleted
        assert results["audit_logs_deleted"] == 1

        # Verify recent log still exists
        query = select(AuditLog).where(AuditLog.id == recent_log.id)
        result = await db_session.execute(query)
        assert result.scalar_one_or_none() is not None

    async def test_purge_old_sessions(self, db_session):
        """Test purging old session tokens."""
        # Create user with old session
        old_login = datetime.utcnow() - timedelta(days=100)
        old_user = User(
            email="old@example.com",
            hashed_password="hash",
            full_name="Old User",
            role="viewer",
            is_active=True,
            last_login=old_login,
            session_token="old-session-token",
        )
        db_session.add(old_user)

        # Create user with recent session
        recent_login = datetime.utcnow() - timedelta(days=30)
        recent_user = User(
            email="recent@example.com",
            hashed_password="hash",
            full_name="Recent User",
            role="viewer",
            is_active=True,
            last_login=recent_login,
            session_token="recent-session-token",
        )
        db_session.add(recent_user)

        await db_session.commit()

        # Run purge
        service = DataRetentionService(db_session)
        results = await service.purge_old_data()

        # Verify one session cleared
        assert results["sessions_deleted"] == 1

        # Refresh users
        await db_session.refresh(old_user)
        await db_session.refresh(recent_user)

        # Verify old session cleared
        assert old_user.session_token is None

        # Verify recent session still exists
        assert recent_user.session_token == "recent-session-token"

    async def test_get_retention_stats(self, db_session, test_patient):
        """Test getting retention statistics."""
        # Create old document
        old_date = datetime.utcnow() - timedelta(days=365 * 9)
        old_doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=old_date,
            title="Old Document",
            status=DocumentStatus.COMPLETED,
            legal_hold=False,
        )
        db_session.add(old_doc)

        # Create old document on legal hold
        doc_on_hold = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=old_date,
            title="Document on Hold",
            status=DocumentStatus.COMPLETED,
            legal_hold=True,
            legal_hold_reason="Litigation",
        )
        db_session.add(doc_on_hold)

        await db_session.commit()

        # Get stats
        service = DataRetentionService(db_session)
        stats = await service.get_retention_stats()

        # Verify stats
        assert "documents" in stats
        assert stats["documents"]["eligible_for_deletion"] == 1
        assert stats["documents"]["on_legal_hold"] == 1
        assert "cutoff_date" in stats["documents"]

        assert "audit_logs" in stats
        assert "sessions" in stats
