"""
Manual Annotation Schemas

Pydantic models for manual PHI annotation API requests/responses.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID


class ManualAnnotationCreate(BaseModel):
    """Request schema for creating a manual annotation."""

    note_id: str = Field(..., min_length=1, max_length=255, description="Note identifier")
    text: str = Field(..., min_length=1, max_length=500, description="Annotated PHI text")
    start_offset: int = Field(..., ge=0, description="Character start position")
    end_offset: int = Field(..., gt=0, description="Character end position")
    entity_type: str = Field(..., min_length=1, max_length=50, description="PHI category")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Annotator confidence")

    @validator("end_offset")
    def validate_offsets(cls, v, values):
        """Ensure end_offset > start_offset."""
        if "start_offset" in values and v <= values["start_offset"]:
            raise ValueError("end_offset must be greater than start_offset")
        return v

    @validator("entity_type")
    def validate_entity_type(cls, v):
        """Validate PHI entity type."""
        allowed_types = [
            "NAME", "DOB", "AGE", "MRN", "SSN", "PHONE", "FAX", "EMAIL",
            "ADDRESS", "CITY", "STATE", "ZIP", "HOSPITAL", "PHYSICIAN",
            "DATE", "DEVICE_ID", "LICENSE", "OTHER"
        ]
        if v.upper() not in allowed_types:
            raise ValueError(f"Invalid entity_type. Must be one of: {', '.join(allowed_types)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "note_id": "note_123",
                "text": "John Doe",
                "start_offset": 8,
                "end_offset": 16,
                "entity_type": "NAME",
                "confidence": 0.95
            }
        }


class ManualAnnotationUpdate(BaseModel):
    """Request schema for updating a manual annotation."""

    text: Optional[str] = Field(None, min_length=1, max_length=500)
    entity_type: Optional[str] = Field(None, min_length=1, max_length=50)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    @validator("entity_type")
    def validate_entity_type(cls, v):
        """Validate PHI entity type if provided."""
        if v is None:
            return v
        allowed_types = [
            "NAME", "DOB", "AGE", "MRN", "SSN", "PHONE", "FAX", "EMAIL",
            "ADDRESS", "CITY", "STATE", "ZIP", "HOSPITAL", "PHYSICIAN",
            "DATE", "DEVICE_ID", "LICENSE", "OTHER"
        ]
        if v.upper() not in allowed_types:
            raise ValueError(f"Invalid entity_type. Must be one of: {', '.join(allowed_types)}")
        return v.upper()


class ManualAnnotationResponse(BaseModel):
    """Response schema for a manual annotation."""

    annotation_id: UUID
    note_id: str
    user_id: UUID
    text: str
    start_offset: int
    end_offset: int
    entity_type: str
    confidence: float
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "annotation_id": "550e8400-e29b-41d4-a716-446655440000",
                "note_id": "note_123",
                "user_id": "user_456",
                "text": "John Doe",
                "start_offset": 8,
                "end_offset": 16,
                "entity_type": "NAME",
                "confidence": 0.95,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "is_active": True
            }
        }


class ManualAnnotationList(BaseModel):
    """Response schema for list of manual annotations."""

    annotations: list[ManualAnnotationResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "annotations": [
                    {
                        "annotation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "note_id": "note_123",
                        "user_id": "user_456",
                        "text": "John Doe",
                        "start_offset": 8,
                        "end_offset": 16,
                        "entity_type": "NAME",
                        "confidence": 0.95,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "is_active": True
                    }
                ],
                "total": 1
            }
        }


class JobAnalytics(BaseModel):
    """Response schema for job analytics."""

    total_jobs: int
    success_rate: float
    avg_processing_time: float
    total_notes: int
    jobs_over_time: list[dict]
    phi_distribution: list[dict]
    confidence_by_type: list[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "total_jobs": 150,
                "success_rate": 98.5,
                "avg_processing_time": 45.3,
                "total_notes": 15000,
                "jobs_over_time": [
                    {"date": "2024-01-01", "count": 10},
                    {"date": "2024-01-02", "count": 15}
                ],
                "phi_distribution": [
                    {"entity_type": "NAME", "count": 500},
                    {"entity_type": "DOB", "count": 300}
                ],
                "confidence_by_type": [
                    {"entity_type": "NAME", "avg_confidence": 0.95},
                    {"entity_type": "DOB", "avg_confidence": 0.92}
                ]
            }
        }
