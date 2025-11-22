"""
Clinical Safety Models (Phase 6)

Tracks clinical safety warnings and checks to prevent patient harm.
Implements NLP confidence thresholds, critical concept detection, and
clinician alerts.

Safety Features:
- Low confidence warnings (NLP < 0.7)
- Critical concept detection (allergies, medications)
- Duplicate patient detection
- Date validation (prevent future dates)
- Required field validation
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import DateTime, Index, String, func, Boolean, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import mapped_column, Mapped

from app.models import Base


class SafetyWarningType(str, Enum):
    """Types of clinical safety warnings."""
    LOW_CONFIDENCE = "low_confidence"  # NLP confidence < 0.7
    CRITICAL_CONCEPT = "critical_concept"  # Allergy, medication, adverse reaction
    DUPLICATE_PATIENT = "duplicate_patient"  # Likely duplicate patient
    FUTURE_DATE = "future_date"  # Invalid future date
    MISSING_FIELD = "missing_field"  # Required demographic field
    CONFLICTING_DATA = "conflicting_data"  # Conflicting information detected
    HIGH_RISK_MODIFICATION = "high_risk_modification"  # Modifying critical data


class SafetyWarningLevel(str, Enum):
    """Severity level of safety warning."""
    INFO = "info"  # Informational
    WARNING = "warning"  # Moderate concern
    CRITICAL = "critical"  # Must be addressed
    ALERT = "alert"  # Immediate action required


class ClinicalSafetyWarning(Base):
    """
    Clinical safety warning for data entry validation.

    Warns clinicians about potential patient safety issues before data is saved.
    Tracks warning dismissals and overrides.

    Attributes:
        id: Unique warning identifier
        user_id: Clinician seeing the warning
        patient_id: Patient affected by warning
        warning_type: Type of warning (low_confidence, critical_concept, etc.)
        warning_level: Severity (info/warning/critical/alert)
        message: Human-readable warning message
        is_active: Whether warning is currently active
        dismissed_at: When clinician dismissed the warning
        dismissed_by: Who dismissed the warning
        dismissed_reason: Why clinician dismissed the warning
        override_justification: Clinical justification for overriding warning
        override_approved_by: Manager who approved override
        override_approved_at: When override was approved
        created_at: When warning was generated
    """

    __tablename__ = "clinical_safety_warnings"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Context
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Clinician seeing the warning"
    )
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="Patient affected by warning (null for patient-independent warnings)"
    )

    # Warning Details
    warning_type: Mapped[SafetyWarningType] = mapped_column(
        SQLEnum(SafetyWarningType),
        nullable=False,
        index=True,
        comment="Type of warning: low_confidence, critical_concept, etc."
    )
    warning_level: Mapped[SafetyWarningLevel] = mapped_column(
        SQLEnum(SafetyWarningLevel),
        nullable=False,
        default=SafetyWarningLevel.WARNING,
        comment="Severity: info/warning/critical/alert"
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable warning message for clinician"
    )

    # Additional Context
    context_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON with additional context (concept, confidence, etc.)"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether warning is still active"
    )

    # Dismissal Tracking
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When clinician dismissed the warning"
    )
    dismissed_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Who dismissed the warning (clinician)"
    )
    dismissed_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Why clinician dismissed the warning"
    )

    # Override Tracking
    override_justification: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Clinical justification for overriding warning"
    )
    override_approved_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Manager who approved override"
    )
    override_approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When override was approved"
    )

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="When warning was generated"
    )

    # Indexes
    __table_args__ = (
        Index("idx_safety_warning_user", "user_id"),
        Index("idx_safety_warning_patient", "patient_id"),
        Index("idx_safety_warning_type", "warning_type"),
        Index("idx_safety_warning_level", "warning_level"),
        Index("idx_safety_warning_active", "is_active"),
        Index("idx_safety_warning_created", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of ClinicalSafetyWarning."""
        return f"<ClinicalSafetyWarning(type={self.warning_type}, level={self.warning_level}, patient={self.patient_id})>"


class ClinicalSafetyOverride(Base):
    """
    Override record for clinical safety warnings.

    Documents when clinicians override safety warnings with justification.
    Required for audit trail and compliance.

    Attributes:
        id: Unique override identifier
        warning_id: Reference to warning being overridden
        user_id: Clinician overriding the warning
        justification: Clinical reason for override
        severity: Severity of override (low/medium/high)
        approved_by: Manager who approved override
        approved_at: When override was approved
        access_level_required: Minimum access level for override (clinician/senior/admin)
        created_at: When override was requested
    """

    __tablename__ = "clinical_safety_overrides"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Reference
    warning_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Reference to clinical safety warning"
    )

    # Context
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Clinician requesting override"
    )

    # Override Details
    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Clinical reason for overriding the warning"
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="low",
        comment="Severity of override: low/medium/high"
    )

    # Approval
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Manager who approved override"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When override was approved"
    )

    # Access Control
    access_level_required: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="clinician",
        comment="Minimum access level needed: clinician/senior_clinician/manager/admin"
    )

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="When override was requested"
    )

    # Indexes
    __table_args__ = (
        Index("idx_safety_override_warning", "warning_id"),
        Index("idx_safety_override_user", "user_id"),
        Index("idx_safety_override_created", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of ClinicalSafetyOverride."""
        return f"<ClinicalSafetyOverride(warning_id={self.warning_id}, user_id={self.user_id})>"
