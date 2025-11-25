"""
Audit Logging Service
HIPAA-compliant audit trail for all PHI access and system actions
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """Service for creating audit log entries."""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        user: User,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        Create audit log entry.

        Args:
            db: Database session
            user: User performing action
            action: Action performed (e.g., "VIEW_PATIENT", "LOGIN", "CREATE_USER")
            resource_type: Type of resource (e.g., "patient", "document", "user")
            resource_id: ID of affected resource (optional)
            details: Additional context as JSON (optional)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            success: "success", "failure", or "denied"
            error_message: Error details if action failed (optional)

        Returns:
            Created audit log entry

        Security:
            - All PHI access MUST be logged
            - Logs retained for 8 years (HIPAA compliance)
            - Cannot be deleted or modified (append-only)
        """
        audit_log = AuditLog(
            user_id=user.id,
            username=user.username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        return audit_log

    @staticmethod
    async def log_phi_access(
        db: AsyncSession,
        user: User,
        patient_id: str,
        action: str = "VIEW_PATIENT",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log PHI access (HIPAA requirement).

        Args:
            db: Database session
            user: User accessing PHI
            patient_id: Patient ID being accessed
            action: Specific action (e.g., "VIEW_PATIENT", "SEARCH_PATIENT")
            details: Additional context (e.g., search query)
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Created audit log entry

        Security:
            - CRITICAL: All PHI access MUST be logged
            - Logged even for failed/denied access attempts
            - Retained for 8 years minimum
        """
        return await AuditService.log_action(
            db=db,
            user=user,
            action=action,
            resource_type="patient",
            resource_id=patient_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def log_deidentification(
        db: AsyncSession,
        user: User,
        job_id: str,
        note_id: str,
        entities_detected: int,
        entities_removed: int,
        method: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> AuditLog:
        """
        Log de-identification action.

        Args:
            db: Database session
            user: User performing de-identification
            job_id: De-identification job ID
            note_id: Note being de-identified
            entities_detected: Number of PHI entities detected
            entities_removed: Number of PHI entities removed
            method: De-identification method (removal, replacement, generalization)
            ip_address: Client IP
            user_agent: Client user agent
            processing_time_ms: Processing time in milliseconds
            error: Error message if failed

        Returns:
            Created audit log entry

        Security:
            - Logs de-identification activity for compliance
            - Does NOT log PHI content (only entity counts)
            - Retained for 8 years
        """
        details = {
            "job_id": job_id,
            "note_id": note_id,
            "entities_detected": entities_detected,
            "entities_removed": entities_removed,
            "method_used": method,
        }

        if processing_time_ms is not None:
            details["processing_time_ms"] = processing_time_ms

        success = "success" if error is None else "failure"

        return await AuditService.log_action(
            db=db,
            user=user,
            action="DEIDENTIFY_NOTE",
            resource_type="deidentification_job",
            resource_id=job_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error,
        )

    @staticmethod
    async def log_job_created(
        db: AsyncSession,
        user: User,
        job_id: str,
        total_notes: int,
        method: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log de-identification job creation.

        Args:
            db: Database session
            user: User creating job
            job_id: Job ID
            total_notes: Total notes in job
            method: De-identification method
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            user=user,
            action="CREATE_DEIDENTIFICATION_JOB",
            resource_type="deidentification_job",
            resource_id=job_id,
            details={
                "total_notes": total_notes,
                "method": method,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def log_job_completed(
        db: AsyncSession,
        user: User,
        job_id: str,
        processed_notes: int,
        error_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log de-identification job completion.

        Args:
            db: Database session
            user: User who created job
            job_id: Job ID
            processed_notes: Number of notes processed
            error_count: Number of errors
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            user=user,
            action="COMPLETE_DEIDENTIFICATION_JOB",
            resource_type="deidentification_job",
            resource_id=job_id,
            details={
                "processed_notes": processed_notes,
                "error_count": error_count,
                "error_rate": (error_count / processed_notes * 100) if processed_notes > 0 else 0,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def log_job_cancelled(
        db: AsyncSession,
        user: User,
        job_id: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log de-identification job cancellation.

        Args:
            db: Database session
            user: User cancelling job
            job_id: Job ID
            reason: Cancellation reason
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            user=user,
            action="CANCEL_DEIDENTIFICATION_JOB",
            resource_type="deidentification_job",
            resource_id=job_id,
            details={
                "reason": reason or "User cancelled",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def log_access(
        db: AsyncSession,
        user: User,
        action: str,
        resource_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log access to de-identified notes.

        Args:
            db: Database session
            user: User accessing notes
            action: Action (VIEW, DOWNLOAD, EXPORT)
            resource_id: Note ID or job ID
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            user=user,
            action=f"{action}_DEIDENTIFIED_NOTE",
            resource_type="deidentified_note",
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def search_audit_logs(
        db: AsyncSession,
        filters: Dict[str, Any],
    ) -> List[AuditLog]:
        """
        Search audit logs with filters.

        Args:
            db: Database session
            filters: Search filters
                - user_id: Filter by user ID
                - action: Filter by action
                - resource_type: Filter by resource type
                - resource_id: Filter by resource ID
                - start_date: Filter by start date (ISO format)
                - end_date: Filter by end date (ISO format)
                - success: Filter by success status
                - limit: Maximum results (default 100, max 1000)
                - offset: Pagination offset

        Returns:
            List of matching audit log entries

        Security:
            - Admin-only access (enforced by API layer)
            - No PHI content in logs
        """
        query = select(AuditLog)

        # Apply filters
        conditions = []

        if "user_id" in filters:
            conditions.append(AuditLog.user_id == filters["user_id"])

        if "action" in filters:
            conditions.append(AuditLog.action == filters["action"])

        if "resource_type" in filters:
            conditions.append(AuditLog.resource_type == filters["resource_type"])

        if "resource_id" in filters:
            conditions.append(AuditLog.resource_id == filters["resource_id"])

        if "success" in filters:
            conditions.append(AuditLog.success == filters["success"])

        # Date range filtering
        if "start_date" in filters:
            start_date = datetime.fromisoformat(filters["start_date"])
            conditions.append(AuditLog.timestamp >= start_date)

        if "end_date" in filters:
            end_date = datetime.fromisoformat(filters["end_date"])
            conditions.append(AuditLog.timestamp <= end_date)

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Order by timestamp descending (most recent first)
        query = query.order_by(AuditLog.timestamp.desc())

        # Pagination
        limit = min(filters.get("limit", 100), 1000)
        offset = filters.get("offset", 0)
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def cleanup_old_audit_logs(db: AsyncSession, retention_days: int = 2920) -> int:
        """
        Delete audit logs older than retention period.

        Args:
            db: Database session
            retention_days: Retention period in days (default 2920 = 8 years for HIPAA)

        Returns:
            Number of deleted logs

        Security:
            - HIPAA requires 8-year retention minimum
            - Should be called via scheduled task (Celery Beat)
            - Admin-only operation
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Count logs to delete
        count_query = select(func.count()).select_from(AuditLog).where(AuditLog.timestamp < cutoff_date)
        result = await db.execute(count_query)
        count = result.scalar()

        # Delete old logs
        delete_query = AuditLog.__table__.delete().where(AuditLog.timestamp < cutoff_date)
        await db.execute(delete_query)
        await db.commit()

        return count


# Global audit service instance
audit_service = AuditService()
