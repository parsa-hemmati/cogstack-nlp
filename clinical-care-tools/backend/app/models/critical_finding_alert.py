"""Critical finding alert model for patient safety."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FindingSeverity(str, PyEnum):
    """Severity levels for critical findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CriticalFindingAlert(Base):
    """
    Critical finding alert model.

    Automatically generated when critical medical concepts are detected
    (e.g., cancer, acute MI, sepsis). Ensures clinicians are notified
    of time-sensitive findings.

    Attributes:
        patient_id: Patient with critical finding
        concept_cui: UMLS/SNOMED concept identifier
        concept_name: Human-readable concept name
        severity: Alert severity (low, medium, high, critical)
        document_id: Source document where finding was detected
        acknowledged_by: Clinician who acknowledged the alert
        acknowledged_at: When alert was acknowledged
        notified_users: List of user IDs who were notified
        notification_sent_at: When notification was sent
        created_at: When alert was created
    """

    __tablename__ = "critical_finding_alerts"

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient with critical finding",
    )

    concept_cui: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="UMLS/SNOMED concept identifier",
    )

    concept_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Human-readable concept name",
    )

    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity),
        nullable=False,
        default=FindingSeverity.MEDIUM,
        index=True,
    )

    document_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        comment="Source document where finding was detected",
    )

    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Clinician who acknowledged the alert",
    )

    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    notified_users: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON array of user IDs who were notified",
    )

    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    patient = relationship("Patient")
    document = relationship("Document")
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by])

    def __repr__(self) -> str:
        """String representation."""
        return f"<CriticalFindingAlert(id='{self.id}', concept='{self.concept_name}', severity='{self.severity}')>"

    @property
    def is_acknowledged(self) -> bool:
        """Check if alert has been acknowledged."""
        return self.acknowledged_at is not None
