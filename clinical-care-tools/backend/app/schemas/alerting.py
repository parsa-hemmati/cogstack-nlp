"""Automated Alerting Schemas (Sprint 7)"""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class AlertType(str, Enum):
    """Alert types"""
    CRITICAL_FINDING = "critical_finding"
    ABNORMAL_LAB = "abnormal_lab"
    MISSED_DIAGNOSIS = "missed_diagnosis"
    MEDICATION_ISSUE = "medication_issue"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Clinical alert"""
    alert_id: UUID = Field(..., description="Alert ID")
    alert_type: AlertType = Field(..., description="Alert type")
    severity: AlertSeverity = Field(..., description="Severity level")
    patient_id: UUID = Field(..., description="Patient ID")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    recommended_action: Optional[str] = Field(None, description="Recommended action")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "123e4567-e89b-12d3-a456-426614174000",
                "alert_type": "critical_finding",
                "severity": "critical",
                "patient_id": "patient-456",
                "title": "Critical Lab Result: Troponin Elevated",
                "description": "Troponin level 2.5 ng/mL (normal <0.04)",
                "recommended_action": "Immediate cardiology consult"
            }
        }
