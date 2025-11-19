"""Pydantic schemas for timeline filter presets."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class FilterPresetBase(BaseModel):
    """Base schema for filter preset."""

    name: str = Field(..., min_length=1, max_length=100, description="Preset name (e.g., 'Diabetes Management')")
    filters: Dict[str, Any] = Field(..., description="Serialized filter configuration")

    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v):
        """Validate filters structure contains required fields."""
        # Basic validation - filters should contain at least one filter criterion
        if not isinstance(v, dict):
            raise ValueError("filters must be a dictionary")
        return v


class FilterPresetCreate(FilterPresetBase):
    """Schema for creating a new filter preset."""

    is_default: bool = Field(default=False, description="Set as default preset for user")


class FilterPresetUpdate(BaseModel):
    """Schema for updating an existing filter preset."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated preset name")
    filters: Optional[Dict[str, Any]] = Field(None, description="Updated filter configuration")
    is_default: Optional[bool] = Field(None, description="Update default status")

    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v):
        """Validate filters structure if provided."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("filters must be a dictionary")
        return v


class FilterPresetResponse(FilterPresetBase):
    """Schema for filter preset response."""

    id: UUID = Field(..., description="Preset unique ID")
    user_id: UUID = Field(..., description="Owner user ID")
    is_default: bool = Field(..., description="Whether this is the user's default preset")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
                "user_id": "f1e2d3c4-b5a6-4b5c-8d9e-0f1a2b3c4d5e",
                "name": "Diabetes Management",
                "filters": {
                    "concept_cuis": ["C0011849", "C0011860"],
                    "meta_annotations": {
                        "Negation": "Affirmed",
                        "Experiencer": "Patient",
                        "Temporality": ["Current", "Recent"]
                    },
                    "document_types": ["clinical_note", "lab_result"]
                },
                "is_default": True,
                "created_at": "2025-01-08T10:30:00Z",
                "updated_at": "2025-01-08T10:30:00Z"
            }
        }
    }


class FilterPresetListResponse(BaseModel):
    """Schema for list of filter presets."""

    presets: List[FilterPresetResponse] = Field(..., description="List of user's filter presets")
    total: int = Field(..., description="Total number of presets")

    model_config = {
        "json_schema_extra": {
            "example": {
                "presets": [
                    {
                        "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
                        "user_id": "f1e2d3c4-b5a6-4b5c-8d9e-0f1a2b3c4d5e",
                        "name": "Diabetes Management",
                        "filters": {
                            "concept_cuis": ["C0011849"],
                            "meta_annotations": {"Negation": "Affirmed"}
                        },
                        "is_default": True,
                        "created_at": "2025-01-08T10:30:00Z",
                        "updated_at": "2025-01-08T10:30:00Z"
                    }
                ],
                "total": 1
            }
        }
    }
