"""
Audit Log model for comprehensive action logging.

Immutable logs for HIPAA compliance tracking WHO/WHAT/WHEN/WHERE.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class AuditLog(Base):
    """
    Immutable audit log for all user actions.

    Compliance: HIPAA requires audit trails for all PHI access.
    Captures: WHO (user), WHAT (action), WHEN (timestamp), WHERE (IP/UA).

    Immutability enforced by PostgreSQL rules (see migration).
    UPDATE and DELETE operations blocked at database level.
    """

    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique audit log identifier"
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When the action occurred (UTC)"
    )

    # WHO: User identification
    user_id = Column(
        String(255),
        nullable=False,
        index=True,
        doc="User ID who performed the action"
    )

    username = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Username who performed the action (for human readability)"
    )

    # WHAT: Action details
    action = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Action performed (e.g., VIEW_PATIENT, UPDATE_DOCUMENT, DELETE_USER)"
    )

    resource_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of resource affected (e.g., patient, document, user)"
    )

    resource_id = Column(
        String(255),
        nullable=False,
        index=True,
        doc="ID of specific resource affected"
    )

    # WHERE: Source information
    ip_address = Column(
        String(45),
        nullable=False,
        doc="IP address of request (IPv4 or IPv6)"
    )

    user_agent = Column(
        Text,
        nullable=False,
        doc="User-Agent header from request"
    )

    # Additional context (flexible JSONB for any extra data)
    details = Column(
        JSONB,
        nullable=True,
        doc="Additional action context (JSONB for flexible schema)"
    )

    def __repr__(self) -> str:
        """String representation of audit log."""
        return (
            f"<AuditLog(id={self.id}, timestamp={self.timestamp}, "
            f"user={self.username}, action={self.action}, "
            f"resource={self.resource_type}:{self.resource_id})>"
        )

    def to_dict(self) -> dict:
        """
        Convert audit log to dictionary.

        Returns:
            Dictionary with all audit log fields

        Example:
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-08T12:34:56",
                "user_id": "user-123",
                "username": "john_doe",
                "action": "VIEW_PATIENT",
                "resource_type": "patient",
                "resource_id": "patient-456",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "details": {"reason": "routine checkup"}
            }
        """
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
        }
