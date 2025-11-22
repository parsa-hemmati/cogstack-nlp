"""
Pydantic schemas for clinical safety validation.

Defines request/response models for safety checks and warnings.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SafetyCheckRequest(BaseModel):
    """Request to validate clinical data."""

    data_type: str = Field(
        ...,
        description="Type of data being validated: nlp_confidence, critical_concept, duplicate_patient, etc."
    )
    patient_id: Optional[str] = Field(
        None,
        description="Patient ID (optional, depends on check type)"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Data to validate (format depends on data_type)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data_type": "nlp_confidence",
                "patient_id": "patient-123",
                "data": {
                    "concept": "diabetes mellitus",
                    "confidence": 0.65
                }
            }
        }


class SafetyWarningResponse(BaseModel):
    """Clinical safety warning details."""

    id: str = Field(
        ...,
        description="Warning ID"
    )
    user_id: str = Field(
        ...,
        description="Clinician seeing the warning"
    )
    patient_id: Optional[str] = Field(
        None,
        description="Patient affected by warning"
    )
    warning_type: str = Field(
        ...,
        description="Type of warning: low_confidence, critical_concept, duplicate_patient, future_date, missing_field"
    )
    warning_level: str = Field(
        ...,
        description="Severity: info/warning/critical/alert"
    )
    message: str = Field(
        ...,
        description="Human-readable warning message"
    )
    is_active: bool = Field(
        ...,
        description="Whether warning is still active"
    )
    created_at: datetime = Field(
        ...,
        description="When warning was created"
    )
    dismissed_at: Optional[datetime] = Field(
        None,
        description="When warning was dismissed"
    )
    dismissed_by: Optional[str] = Field(
        None,
        description="Who dismissed the warning"
    )
    override_justification: Optional[str] = Field(
        None,
        description="Justification for overriding warning"
    )

    class Config:
        from_attributes = True


class SafetyCheckResponse(BaseModel):
    """Response from safety check."""

    has_warning: bool = Field(
        ...,
        description="Whether check generated a warning"
    )
    warning: Optional[SafetyWarningResponse] = Field(
        None,
        description="Warning details if generated"
    )
    message: str = Field(
        ...,
        description="Summary message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "has_warning": True,
                "warning": {
                    "id": "warning-123",
                    "warning_type": "low_confidence",
                    "warning_level": "warning",
                    "message": "Low confidence (0.65) for concept 'diabetes'. Manual review recommended.",
                    "is_active": True
                },
                "message": "Safety check completed with 1 warning"
            }
        }


class SafetyDismiss(BaseModel):
    """Request to dismiss a safety warning."""

    reason: Optional[str] = Field(
        None,
        description="Reason for dismissal"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Already confirmed by senior clinician"
            }
        }


class SafetyOverride(BaseModel):
    """Request to override a safety warning."""

    justification: str = Field(
        ...,
        min_length=10,
        description="Clinical justification for override (min 10 chars)"
    )
    severity: str = Field(
        "low",
        pattern="^(low|medium|high)$",
        description="Override severity: low/medium/high"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "justification": "Patient history confirms allergy information is correct despite low confidence",
                "severity": "medium"
            }
        }


class SafetyWarningsList(BaseModel):
    """List of active safety warnings."""

    total: int = Field(
        ...,
        description="Total active warnings"
    )
    limit: int = Field(
        ...,
        description="Limit of results returned"
    )
    offset: int = Field(
        ...,
        description="Pagination offset"
    )
    warnings: List[SafetyWarningResponse] = Field(
        ...,
        description="List of warnings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "limit": 20,
                "offset": 0,
                "warnings": []
            }
        }


class SafetyStatistics(BaseModel):
    """Safety statistics and metrics."""

    total_warnings: int = Field(
        ...,
        description="Total warnings generated"
    )
    active_warnings: int = Field(
        ...,
        description="Currently active warnings"
    )
    dismissed_warnings: int = Field(
        ...,
        description="Dismissed warnings"
    )
    overrides: int = Field(
        ...,
        description="Warning overrides"
    )
    critical_alerts: int = Field(
        ...,
        description="Critical-level alerts"
    )
    warnings_by_type: Dict[str, int] = Field(
        ...,
        description="Count by warning type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_warnings": 150,
                "active_warnings": 5,
                "dismissed_warnings": 145,
                "overrides": 10,
                "critical_alerts": 2,
                "warnings_by_type": {
                    "low_confidence": 80,
                    "critical_concept": 50,
                    "future_date": 20
                }
            }
        }
