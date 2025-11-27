"""Clinical Decision Support Schemas (Sprint 6)"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class CDSRecommendationType(str, Enum):
    """CDS recommendation types"""
    DRUG_INTERACTION = "drug_interaction"
    CONTRAINDICATION = "contraindication"
    DOSE_ADJUSTMENT = "dose_adjustment"
    GUIDELINE_RECOMMENDATION = "guideline_recommendation"
    PREVENTIVE_CARE = "preventive_care"


class CDSSeverity(str, Enum):
    """CDS alert severity"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CDSRecommendation(BaseModel):
    """CDS recommendation"""
    recommendation_id: UUID = Field(..., description="Unique ID")
    recommendation_type: CDSRecommendationType = Field(..., description="Type")
    severity: CDSSeverity = Field(..., description="Severity")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    evidence: Optional[str] = Field(None, description="Evidence source")
    action: Optional[str] = Field(None, description="Recommended action")

    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "123e4567-e89b-12d3-a456-426614174000",
                "recommendation_type": "drug_interaction",
                "severity": "critical",
                "title": "Drug-Drug Interaction: Warfarin + Aspirin",
                "description": "Increased bleeding risk when combining anticoagulants",
                "evidence": "Evidence Grade A (multiple RCTs)",
                "action": "Consider alternative therapy or close INR monitoring"
            }
        }


class CDSRequest(BaseModel):
    """CDS request (CDS Hooks format)"""
    hook: str = Field(..., description="Hook ID")
    patient_id: UUID = Field(..., description="Patient ID")
    context: Dict[str, Any] = Field(..., description="Context data")


class CDSResponse(BaseModel):
    """CDS response (CDS Hooks format)"""
    cards: List[CDSRecommendation] = Field(..., description="Recommendation cards")
