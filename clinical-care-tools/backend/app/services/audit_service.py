"""Audit logging service for HIPAA compliance."""

import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating and managing audit logs.

    All PHI access must be logged for HIPAA compliance.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def log(
        self,
        user: User,
        action: AuditAction,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Create audit log entry.

        Args:
            user: User who performed the action
            action: Type of action performed
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            patient_id: Patient ID if action involves PHI
            ip_address: IP address of request
            user_agent: User agent string
            details: Additional details (JSON)
            success: Whether action succeeded
            error_message: Error message if failed
            session_id: Session identifier

        Returns:
            Created audit log entry
        """
        audit_log = AuditLog(
            user_id=user.id,
            username=user.username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=success,
            error_message=error_message,
            session_id=session_id,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        # Also log to application logs
        log_message = (
            f"AUDIT: user={user.username} action={action.value} "
            f"resource={resource_type}:{resource_id} patient={patient_id} "
            f"success={success}"
        )

        if success:
            logger.info(log_message, extra={"audit_log_id": str(audit_log.id)})
        else:
            logger.warning(f"{log_message} error={error_message}")

        return audit_log

    async def log_phi_access(
        self,
        user: User,
        action: AuditAction,
        patient_id: str,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log PHI (Protected Health Information) access.

        This is a convenience method for logging patient data access.
        HIPAA requires all PHI access to be audited.

        Args:
            user: User who accessed PHI
            action: Action performed
            patient_id: Patient identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            ip_address: IP address
            user_agent: User agent
            details: Additional details

        Returns:
            Audit log entry
        """
        return await self.log(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=True,
        )

    async def log_break_glass_access(
        self,
        user: User,
        patient_id: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log emergency "break-the-glass" access to patient data.

        HIPAA allows emergency access to patient data outside normal
        authorization, but requires strict auditing.

        Args:
            user: User who performed emergency access
            patient_id: Patient identifier
            reason: Reason for emergency access
            ip_address: IP address
            user_agent: User agent

        Returns:
            Audit log entry
        """
        logger.warning(
            f"BREAK-THE-GLASS ACCESS: user={user.username} patient={patient_id} reason={reason}"
        )

        return await self.log(
            user=user,
            action=AuditAction.BREAK_GLASS_ACCESS,
            resource_type="Patient",
            resource_id=patient_id,
            patient_id=patient_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"reason": reason, "break_glass": True},
            success=True,
        )


def get_audit_service(db: AsyncSession) -> AuditService:
    """Dependency for getting audit service."""
    return AuditService(db)
