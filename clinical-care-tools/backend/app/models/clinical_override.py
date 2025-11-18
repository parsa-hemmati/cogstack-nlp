"""Clinical override model for tracking when clinicians override system recommendations."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClinicalOverride(Base):
    """
    Clinical override model.

    Tracks when clinicians override system recommendations or alerts.
    Critical for patient safety monitoring and system improvement.

    Attributes:
        user_id: Clinician who made the override
        patient_id: Patient affected by override
        recommendation_type: Type of recommendation overridden
        recommendation_value: Original system recommendation
        override_value: Clinician's override decision
        justification: Required justification (min 20 chars)
        severity: Severity of override (low, medium, high)
        created_at: When override was made
    """

    __tablename__ = "clinical_overrides"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Clinician who made the override",
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient affected by override",
    )

    recommendation_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of recommendation (e.g., 'critical_alert', 'dosage_warning')",
    )

    recommendation_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original system recommendation",
    )

    override_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Clinician's override decision",
    )

    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Required justification (min 20 characters)",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        comment="Severity of override: low, medium, high",
    )

    # Relationships
    user = relationship("User")
    patient = relationship("Patient")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ClinicalOverride(id='{self.id}', type='{self.recommendation_type}', severity='{self.severity}')>"
