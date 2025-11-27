"""Clinical incident model for safety reporting."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentType(str, PyEnum):
    """Types of clinical incidents."""

    DATA_ACCURACY = "data_accuracy"
    SYSTEM_ERROR = "system_error"
    USER_ERROR = "user_error"
    SAFETY_CONCERN = "safety_concern"
    PRIVACY_BREACH = "privacy_breach"
    OTHER = "other"


class IncidentSeverity(str, PyEnum):
    """Severity levels for incidents."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, PyEnum):
    """Incident workflow status."""

    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ClinicalIncident(Base):
    """
    Clinical incident model.

    Tracks clinical safety incidents, system errors, and data quality issues.
    Supports investigation workflow and resolution tracking.

    Attributes:
        incident_type: Type of incident
        severity: Incident severity (low, medium, high, critical)
        description: Detailed incident description
        patient_id: Patient affected (if applicable)
        reported_by: User who reported the incident
        investigated_by: User assigned to investigate
        resolution: How the incident was resolved
        status: Current status (reported, under_investigation, resolved, closed)
        created_at: When incident was reported
        resolved_at: When incident was resolved
        closed_at: When incident was closed
    """

    __tablename__ = "clinical_incidents"

    incident_type: Mapped[IncidentType] = mapped_column(
        Enum(IncidentType),
        nullable=False,
        index=True,
    )

    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed incident description",
    )

    patient_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Patient affected (if applicable)",
    )

    reported_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who reported the incident",
    )

    investigated_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User assigned to investigate",
    )

    resolution: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="How the incident was resolved",
    )

    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus),
        nullable=False,
        default=IncidentStatus.REPORTED,
        index=True,
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    patient = relationship("Patient")
    reporter = relationship("User", foreign_keys=[reported_by])
    investigator = relationship("User", foreign_keys=[investigated_by])

    def __repr__(self) -> str:
        """String representation."""
        return f"<ClinicalIncident(id='{self.id}', type='{self.incident_type}', severity='{self.severity}', status='{self.status}')>"
