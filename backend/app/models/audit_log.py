"""
Audit Log Model
HIPAA-compliant audit logging for PHI access and system actions
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class AuditLog(Base):
    """
    Audit log for HIPAA compliance and security auditing.

    Retention: 8 years (2920 days) per HIPAA requirements
    """

    __tablename__ = "audit_logs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Who (user performing action)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    username = Column(String(50), nullable=False)  # Denormalized for faster queries

    # What (action performed)
    action = Column(String(100), nullable=False, index=True)  # e.g., "VIEW_PATIENT", "CREATE_USER"
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., "patient", "document"
    resource_id = Column(String(255), nullable=True, index=True)  # ID of affected resource

    # Details (JSON for flexibility)
    details = Column(JSONB, nullable=True)  # Additional context (e.g., search query, changes made)

    # When
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Where (network info)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)

    # Result
    success = Column(String(10), nullable=False, default="success")  # "success", "failure", "denied"
    error_message = Column(Text, nullable=True)  # Error details if action failed

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<AuditLog(user={self.username}, action={self.action}, resource={self.resource_type}/{self.resource_id})>"

    # Composite index for common queries
    __table_args__ = (
        Index("ix_audit_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_action_timestamp", "action", "timestamp"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )
