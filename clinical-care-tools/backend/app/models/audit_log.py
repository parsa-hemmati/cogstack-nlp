"""Audit log model for HIPAA compliance."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import Enum, JSON, String, Text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditAction(str, PyEnum):
    """Audit actions for tracking user activities."""

    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"

    # Patient Data Access (PHI)
    VIEW_PATIENT = "view_patient"
    SEARCH_PATIENTS = "search_patients"
    VIEW_DOCUMENT = "view_document"
    EXPORT_DATA = "export_data"

    # Emergency Access
    BREAK_GLASS_ACCESS = "break_glass_access"

    # Data Modification
    CREATE_RECORD = "create_record"
    UPDATE_RECORD = "update_record"
    DELETE_RECORD = "delete_record"

    # Admin Actions
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    CHANGE_PERMISSIONS = "change_permissions"


class AuditLog(Base):
    """
    Audit log for HIPAA compliance.

    Tracks all PHI access and system actions for regulatory compliance.
    Retention: 8 years (configurable via AUDIT_LOG_RETENTION_DAYS).

    Attributes:
        user_id: User who performed the action
        username: Username (denormalized for performance)
        action: Type of action performed
        resource_type: Type of resource accessed (e.g., "Patient", "Document")
        resource_id: ID of resource accessed
        patient_id: Patient ID if action involves patient data
        ip_address: IP address of the request
        user_agent: User agent string
        details: Additional details in JSON format
        success: Whether action succeeded
        error_message: Error message if action failed
        session_id: Session identifier for correlation
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    patient_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Patient ID if action involves PHI",
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    success: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    session_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditLog(user='{self.username}', action='{self.action}', "
            f"resource='{self.resource_type}:{self.resource_id}')>"
        )
