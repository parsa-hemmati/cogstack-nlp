"""
Break-Glass Access Model (Phase 5)

Represents emergency access to patient data when standard authorization is insufficient.
Implements audit trail and mandatory review by security team.

HIPAA Compliance:
- Break-glass access is logged and audited
- Requires justification for emergency access
- Mandatory review by security team within 24 hours
- Alert notifications to security team
- Access window limited to 60 minutes
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import DateTime, Index, String, func, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import Base


class BreakGlassStatus(str, Enum):
    """Break-glass access request status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class BreakGlassAccess(Base):
    """
    Break-glass emergency access to patient data.

    Allows clinicians to request emergency access to patient data when standard
    authorization is insufficient. All access is logged and requires mandatory
    review by security team.

    Attributes:
        id: Unique access request identifier
        user_id: Clinician requesting access
        patient_id: Patient whose data is being accessed
        status: Request status (pending/approved/denied/revoked/expired)
        justification: Clinical reason for emergency access (required)
        access_granted_at: When access was approved
        access_expires_at: When access window expires (60 minutes)
        accessed_at: When data was actually accessed (if approved)
        reviewed_by: Security team member who reviewed request
        reviewed_at: When security team reviewed request
        review_notes: Security team comments on review
        revoked_by: User who revoked access (if applicable)
        revoked_at: When access was revoked
        ip_address: Client IP for access request
        user_agent: Client User-Agent for audit trail

    Security Features:
        - Limited 60-minute access window
        - Mandatory 24-hour review deadline
        - Audit trail of all access
        - Alert notifications to security team
        - Can be revoked at any time
    """

    __tablename__ = "break_glass_access"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Clinician requesting emergency access"
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Patient whose data is being accessed"
    )

    # Status and Justification
    status: Mapped[BreakGlassStatus] = mapped_column(
        SQLEnum(BreakGlassStatus),
        nullable=False,
        default=BreakGlassStatus.PENDING,
        index=True,
        comment="Request status: pending/approved/denied/revoked/expired"
    )
    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Clinical reason for emergency access (required by law)"
    )

    # Access Timeline
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="When access was requested"
    )
    access_granted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When access was approved by security team"
    )
    access_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When access window expires (60 minutes after approval)"
    )
    accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When clinician actually accessed the data"
    )

    # Review Information
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Security team member who reviewed request"
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When security team reviewed request (must be within 24 hours)"
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Security team notes on review decision"
    )

    # Revocation Information
    revoked_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="User who revoked access"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When access was revoked"
    )

    # Audit Trail
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address for audit"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Client User-Agent for audit trail"
    )

    # Indexes for queries
    __table_args__ = (
        Index("idx_break_glass_user", "user_id"),
        Index("idx_break_glass_patient", "patient_id"),
        Index("idx_break_glass_status", "status"),
        Index("idx_break_glass_created", "created_at"),
        Index("idx_break_glass_expires", "access_expires_at"),
        Index("idx_break_glass_pending", "status", postgresql_where="status = 'pending'"),
    )

    def __repr__(self) -> str:
        """String representation of BreakGlassAccess."""
        return f"<BreakGlassAccess(id={self.id}, patient_id={self.patient_id}, status={self.status})>"
