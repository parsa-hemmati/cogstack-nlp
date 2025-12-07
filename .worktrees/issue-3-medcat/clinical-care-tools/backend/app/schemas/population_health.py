"""Population Health Schemas (Sprint 8)"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from uuid import UUID


class CohortDefinition(BaseModel):
    """Cohort definition"""
    cohort_id: UUID = Field(..., description="Cohort ID")
    name: str = Field(..., description="Cohort name")
    description: str = Field(..., description="Description")
    inclusion_criteria: List[Dict] = Field(..., description="Inclusion criteria")
    exclusion_criteria: List[Dict] = Field(default_factory=list, description="Exclusion criteria")

    class Config:
        json_schema_extra = {
            "example": {
                "cohort_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Type 2 Diabetes Patients",
                "description": "All patients with Type 2 Diabetes diagnosis",
                "inclusion_criteria": [
                    {"field": "icd10_code", "operator": "equals", "value": "E11.9"}
                ],
                "exclusion_criteria": []
            }
        }


class QualityMetric(BaseModel):
    """Quality metric"""
    metric_id: UUID = Field(..., description="Metric ID")
    metric_name: str = Field(..., description="Metric name")
    numerator: int = Field(..., description="Numerator")
    denominator: int = Field(..., description="Denominator")
    percentage: float = Field(..., description="Percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "metric_id": "123e4567-e89b-12d3-a456-426614174000",
                "metric_name": "HbA1c Testing Rate (Diabetes)",
                "numerator": 850,
                "denominator": 1000,
                "percentage": 85.0
            }
        }
