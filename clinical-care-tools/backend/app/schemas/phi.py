"""PHI Detection Schemas for De-identification (Sprint 4)"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class PHIEntityType(str, Enum):
    """PHI entity types detected by NER model"""
    PERSON = "PERSON"  # Patient names, doctor names
    DATE = "DATE"  # Birth dates, admission dates
    ID = "ID"  # SSN, MRN, insurance numbers
    LOCATION = "LOCATION"  # Addresses, cities, states
    PHONE = "PHONE"  # Phone numbers
    EMAIL = "EMAIL"  # Email addresses
    ORGANIZATION = "ORGANIZATION"  # Hospital names, clinics
    AGE = "AGE"  # Ages over 89


class DetectedEntity(BaseModel):
    """PHI entity detected in text"""
    text: str = Field(..., description="Entity text")
    label: PHIEntityType = Field(..., description="Entity type")
    start: int = Field(..., ge=0, description="Start position in text")
    end: int = Field(..., gt=0, description="End position in text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "John Doe",
                "label": "PERSON",
                "start": 8,
                "end": 16,
                "confidence": 0.98
            }
        }


class PHIDetectionRequest(BaseModel):
    """Request for PHI detection"""
    text: str = Field(..., min_length=1, description="Text to analyze for PHI")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Patient John Doe (DOB: 01/15/1980) presents with chest pain."
            }
        }


class PHIDetectionResponse(BaseModel):
    """Response from PHI detection"""
    entities: List[DetectedEntity] = Field(default_factory=list, description="Detected PHI entities")
    total_entities: int = Field(..., ge=0, description="Total number of entities detected")

    class Config:
        json_schema_extra = {
            "example": {
                "entities": [
                    {"text": "John Doe", "label": "PERSON", "start": 8, "end": 16, "confidence": 0.98},
                    {"text": "01/15/1980", "label": "DATE", "start": 23, "end": 33, "confidence": 0.95}
                ],
                "total_entities": 2
            }
        }
