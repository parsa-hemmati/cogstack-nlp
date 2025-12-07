"""Advanced Analytics Schemas (Sprint 9)"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class Registry(BaseModel):
    """Disease registry"""
    registry_id: UUID = Field(..., description="Registry ID")
    name: str = Field(..., description="Registry name")
    disease: str = Field(..., description="Disease/condition")
    patient_count: int = Field(..., description="Patient count")

    class Config:
        json_schema_extra = {
            "example": {
                "registry_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Diabetes Registry",
                "disease": "Type 2 Diabetes Mellitus",
                "patient_count": 5420
            }
        }


class Phenotype(BaseModel):
    """Deep phenotype"""
    phenotype_id: UUID = Field(..., description="Phenotype ID")
    name: str = Field(..., description="Phenotype name")
    description: str = Field(..., description="Description")
    criteria: List[Dict[str, Any]] = Field(..., description="Phenotype criteria")

    class Config:
        json_schema_extra = {
            "example": {
                "phenotype_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Diabetic Nephropathy",
                "description": "Diabetes with kidney disease",
                "criteria": [
                    {"condition": "E11.9", "required": True},
                    {"condition": "N18", "required": True}
                ]
            }
        }
