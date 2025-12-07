"""Data retention service for automated purging per compliance policies."""

import logging
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.user import User

logger = logging.getLogger(__name__)


class DataRetentionService:
    """
    Data retention service.

    Implements automated data purging per retention policies:
    - Clinical documents: 8 years (NHS compliance)
    - Audit logs: 7 years (HIPAA compliance)
    - User sessions: 90 days (security best practice)

    Respects legal holds on documents (cannot delete if legal_hold=True).
    """

    # Retention periods in days
    DOCUMENT_RETENTION_DAYS = 8 * 365  # 8 years
    AUDIT_LOG_RETENTION_DAYS = 7 * 365  # 7 years
    SESSION_RETENTION_DAYS = 90  # 90 days

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def purge_old_data(self) -> Dict[str, int]:
        """
        Purge old data per retention policy.

        Returns:
            Dict with counts of deleted records by type

        Raises:
            Exception: If purging fails
        """
        logger.info("Starting automated data retention purge")

        results = {
            "documents_deleted": 0,
            "audit_logs_deleted": 0,
            "sessions_deleted": 0,
        }

        try:
            # 1. Purge old documents (respect legal holds)
            results["documents_deleted"] = await self._purge_old_documents()

            # 2. Purge old audit logs
            results["audit_logs_deleted"] = await self._purge_old_audit_logs()

            # 3. Purge old sessions (clear session tokens from users table)
            results["sessions_deleted"] = await self._purge_old_sessions()

            await self.db.commit()

            logger.info(
                f"Data retention purge completed: "
                f"{results['documents_deleted']} documents, "
                f"{results['audit_logs_deleted']} audit logs, "
                f"{results['sessions_deleted']} sessions deleted"
            )

            return results

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Data retention purge failed: {str(e)}")
            raise

    async def _purge_old_documents(self) -> int:
        """
        Delete documents older than retention period.

        Only deletes documents where:
        - document_date is older than DOCUMENT_RETENTION_DAYS
        - legal_hold is False (or NULL)

        Returns:
            Number of documents deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.DOCUMENT_RETENTION_DAYS)

        # Get count first for logging
        count_query = select(func.count(Document.id)).where(
            and_(
                Document.document_date < cutoff_date,
                Document.legal_hold.is_(False),
            )
        )
        result = await self.db.execute(count_query)
        count = result.scalar_one()

        if count > 0:
            # Delete documents
            delete_query = delete(Document).where(
                and_(
                    Document.document_date < cutoff_date,
                    Document.legal_hold.is_(False),
                )
            )
            await self.db.execute(delete_query)

            logger.info(
                f"Deleted {count} documents older than {cutoff_date.date()} "
                f"(retention period: {self.DOCUMENT_RETENTION_DAYS} days)"
            )

        return count

    async def _purge_old_audit_logs(self) -> int:
        """
        Delete audit logs older than retention period.

        Returns:
            Number of audit logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.AUDIT_LOG_RETENTION_DAYS)

        # Get count first for logging
        count_query = select(func.count(AuditLog.id)).where(
            AuditLog.created_at < cutoff_date
        )
        result = await self.db.execute(count_query)
        count = result.scalar_one()

        if count > 0:
            # Delete audit logs
            delete_query = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
            await self.db.execute(delete_query)

            logger.info(
                f"Deleted {count} audit logs older than {cutoff_date.date()} "
                f"(retention period: {self.AUDIT_LOG_RETENTION_DAYS} days)"
            )

        return count

    async def _purge_old_sessions(self) -> int:
        """
        Clear session tokens for inactive users.

        Sets session_token to NULL for users whose last_login is older
        than SESSION_RETENTION_DAYS.

        Returns:
            Number of sessions cleared
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.SESSION_RETENTION_DAYS)

        # Count users with old sessions
        count_query = select(func.count(User.id)).where(
            and_(
                User.last_login < cutoff_date,
                User.session_token.isnot(None),
            )
        )
        result = await self.db.execute(count_query)
        count = result.scalar_one()

        if count > 0:
            # Clear session tokens
            # Note: We're not deleting users, just invalidating their sessions
            query = select(User).where(
                and_(
                    User.last_login < cutoff_date,
                    User.session_token.isnot(None),
                )
            )
            result = await self.db.execute(query)
            users = result.scalars().all()

            for user in users:
                user.session_token = None

            logger.info(
                f"Cleared {count} session tokens for users inactive since {cutoff_date.date()} "
                f"(retention period: {self.SESSION_RETENTION_DAYS} days)"
            )

        return count

    async def get_retention_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics on data eligible for purging.

        Returns:
            Dict with stats for each data type
        """
        cutoff_dates = {
            "documents": datetime.utcnow()
            - timedelta(days=self.DOCUMENT_RETENTION_DAYS),
            "audit_logs": datetime.utcnow()
            - timedelta(days=self.AUDIT_LOG_RETENTION_DAYS),
            "sessions": datetime.utcnow() - timedelta(days=self.SESSION_RETENTION_DAYS),
        }

        stats = {}

        # Documents eligible for deletion
        doc_count_query = select(func.count(Document.id)).where(
            and_(
                Document.document_date < cutoff_dates["documents"],
                Document.legal_hold.is_(False),
            )
        )
        result = await self.db.execute(doc_count_query)
        stats["documents"] = {
            "eligible_for_deletion": result.scalar_one(),
            "cutoff_date": cutoff_dates["documents"].isoformat(),
        }

        # Documents on legal hold (cannot delete)
        legal_hold_query = select(func.count(Document.id)).where(
            and_(
                Document.document_date < cutoff_dates["documents"],
                Document.legal_hold.is_(True),
            )
        )
        result = await self.db.execute(legal_hold_query)
        stats["documents"]["on_legal_hold"] = result.scalar_one()

        # Audit logs eligible for deletion
        audit_count_query = select(func.count(AuditLog.id)).where(
            AuditLog.created_at < cutoff_dates["audit_logs"]
        )
        result = await self.db.execute(audit_count_query)
        stats["audit_logs"] = {
            "eligible_for_deletion": result.scalar_one(),
            "cutoff_date": cutoff_dates["audit_logs"].isoformat(),
        }

        # Sessions eligible for clearing
        session_count_query = select(func.count(User.id)).where(
            and_(
                User.last_login < cutoff_dates["sessions"],
                User.session_token.isnot(None),
            )
        )
        result = await self.db.execute(session_count_query)
        stats["sessions"] = {
            "eligible_for_deletion": result.scalar_one(),
            "cutoff_date": cutoff_dates["sessions"].isoformat(),
        }

        return stats
