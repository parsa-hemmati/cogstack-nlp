"""
Audit Logging Service
HIPAA-compliant audit trail for all PHI access and system actions
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
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


# Global audit service instance
audit_service = AuditService()
