"""
Audit Log Model

Immutable audit trail for compliance with HIPAA, GDPR, and 21 CFR Part 11.
All PHI access, user actions, and system changes are logged here.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text, func, JSON, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import Base


class AuditLog(Base):
    """
    Immutable audit log for compliance tracking.

    This table is append-only (no updates or deletes). All user actions,
    system changes, and PHI access are logged here for regulatory compliance.

    Attributes:
        id: Unique audit log entry identifier (UUID)
        user_id: Reference to user who performed action (NULL for system actions)
        username: Username at time of action (denormalized for immutability)
        action: Type of action (login, logout, view, create, update, delete, search, export)
        resource_type: Type of resource affected (user, project, task, document, patient, etc.)
        resource_id: ID of affected resource
        resource_name: Human-readable name of resource
        details: Additional context as JSON (search criteria, changed fields, etc.)
        ip_address: IP address of requester
        session_id: Session ID for correlating related actions
        timestamp: When action occurred (immutable, server-side)

    Relationships:
        user: Reference to User model (optional, for system actions)

    Compliance Notes:
        - Table is append-only (no updates/deletes via database triggers)
        - Timestamps are server-side and cannot be modified
        - All PHI access is logged (patients table, extracted_entities table)
        - Retention: 7 years for healthcare records (2555 days)
        - Partitioned by month in production for performance
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # References (optional - NULL for system actions)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    # Denormalized username (immutable record of who performed action)
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    # Action Details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="'login', 'logout', 'view', 'create', 'update', 'delete', 'search', 'export'",
    )

    # Resource Identification
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="'user', 'project', 'task', 'document', 'patient', 'extracted_entity', etc.",
    )
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Additional Context
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Additional context: search criteria, changed fields, etc.",
    )

    # Security Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv4 or IPv6
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Timestamp (server-side, immutable)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="Server-side timestamp, immutable",
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[user_id],
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_timestamp", "timestamp", postgresql_using="desc"),
        Index("idx_audit_logs_session", "session_id"),
        # For compliance: find all actions by user in date range
        Index("idx_audit_logs_user_timestamp", "user_id", "timestamp"),
    )

    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return (
            f"<AuditLog(id={self.id}, user={self.username}, action={self.action}, "
            f"resource={self.resource_type}:{self.resource_id}, timestamp={self.timestamp})>"
        )
