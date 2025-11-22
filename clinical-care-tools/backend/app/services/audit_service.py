"""
Audit Service

Provides comprehensive audit logging for HIPAA/GDPR compliance.
Tracks all PHI access, modifications, and system events.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.audit_log import AuditLog

logger = structlog.get_logger()


class AuditService:
    """
    Service for audit logging and compliance tracking.

    Records:
    - PHI access (view, search, export)
    - Document operations (upload, download, delete)
    - User authentication events
    - System configuration changes
    - Break-glass access
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    async def log_phi_access(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: Optional[UUID],
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log PHI access event.

        Args:
            user_id: User accessing PHI
            resource_type: Type of resource (document, patient, entity)
            resource_id: ID of the resource
            action: Action performed (view, search, export, etc.)
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional details
        """
        await self._create_log_entry(
            event_type="PHI_ACCESS",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

    async def log_document_upload(
        self,
        user_id: UUID,
        document_id: UUID,
        filename: str,
        file_size: int,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log document upload event.

        Args:
            user_id: User uploading document
            document_id: Created document ID
            filename: Original filename
            file_size: File size in bytes
            ip_address: Client IP address
        """
        await self._create_log_entry(
            event_type="DOCUMENT_UPLOAD",
            user_id=user_id,
            resource_type="document",
            resource_id=document_id,
            action="upload",
            ip_address=ip_address,
            details={
                "filename": filename,
                "file_size": file_size
            }
        )

    async def log_document_deletion(
        self,
        user_id: UUID,
        document_id: UUID,
        soft_delete: bool,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log document deletion event.

        Args:
            user_id: User deleting document
            document_id: Document ID
            soft_delete: Whether soft or hard delete
            ip_address: Client IP address
        """
        await self._create_log_entry(
            event_type="DOCUMENT_DELETE",
            user_id=user_id,
            resource_type="document",
            resource_id=document_id,
            action="delete",
            ip_address=ip_address,
            details={
                "soft_delete": soft_delete
            }
        )

    async def log_authentication(
        self,
        user_id: Optional[UUID],
        event: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log authentication event.

        Args:
            user_id: User ID (if known)
            event: Event type (login, logout, failed_login, etc.)
            success: Whether operation succeeded
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional details
        """
        await self._create_log_entry(
            event_type="AUTHENTICATION",
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            action=event,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "success": success,
                **(details or {})
            }
        )

    async def log_nlp_processing(
        self,
        user_id: UUID,
        document_id: UUID,
        model_name: str,
        entities_count: int,
        phi_count: int,
        processing_time_ms: float
    ) -> None:
        """
        Log NLP processing event.

        Args:
            user_id: User triggering processing
            document_id: Document processed
            model_name: NLP model used
            entities_count: Number of entities extracted
            phi_count: Number of PHI entities
            processing_time_ms: Processing time in milliseconds
        """
        await self._create_log_entry(
            event_type="NLP_PROCESSING",
            user_id=user_id,
            resource_type="document",
            resource_id=document_id,
            action="process",
            details={
                "model_name": model_name,
                "entities_count": entities_count,
                "phi_count": phi_count,
                "processing_time_ms": processing_time_ms
            }
        )

    async def log_break_glass(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        reason: str,
        approved_by: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log break-glass access event.

        Args:
            user_id: User requesting emergency access
            resource_type: Type of resource
            resource_id: Resource ID
            reason: Reason for emergency access
            approved_by: User who approved (if any)
            ip_address: Client IP address
        """
        await self._create_log_entry(
            event_type="BREAK_GLASS",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action="emergency_access",
            ip_address=ip_address,
            details={
                "reason": reason,
                "approved_by": str(approved_by) if approved_by else None
            }
        )

    async def log_configuration_change(
        self,
        user_id: UUID,
        setting_name: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log system configuration change.

        Args:
            user_id: User making change
            setting_name: Name of setting
            old_value: Previous value
            new_value: New value
            ip_address: Client IP address
        """
        await self._create_log_entry(
            event_type="CONFIGURATION",
            user_id=user_id,
            resource_type="system",
            resource_id=None,
            action="update",
            ip_address=ip_address,
            details={
                "setting": setting_name,
                "old_value": old_value,
                "new_value": new_value
            }
        )

    async def _create_log_entry(
        self,
        event_type: str,
        user_id: Optional[UUID],
        resource_type: str,
        resource_id: Optional[UUID],
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create audit log entry in database.

        Args:
            event_type: Type of event
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action performed
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional details
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                event_type=event_type,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details or {},
                timestamp=datetime.utcnow()
            )

            self.db.add(audit_log)
            await self.db.commit()

            # Also log to structured logger for real-time monitoring
            logger.info(
                "Audit event",
                event_type=event_type,
                user_id=str(user_id) if user_id else None,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                action=action,
                ip_address=ip_address
            )

        except Exception as e:
            # Never fail the main operation due to audit logging failure
            logger.error(
                "Failed to create audit log",
                error=str(e),
                event_type=event_type,
                user_id=str(user_id) if user_id else None
            )
            await self.db.rollback()

    async def get_user_activity(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Get user activity audit logs.

        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum records to return

        Returns:
            List of audit log entries
        """
        query = select(AuditLog).where(AuditLog.user_id == user_id)

        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_resource_access_log(
        self,
        resource_type: str,
        resource_id: UUID,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Get access logs for a specific resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            limit: Maximum records to return

        Returns:
            List of audit log entries
        """
        query = select(AuditLog).where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        )
        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()