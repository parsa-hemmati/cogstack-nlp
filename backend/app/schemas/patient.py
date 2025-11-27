"""
Patient CRUD Schemas
Pydantic models for patient management (Create, Read, Update, Delete)

Aligns with existing Patient model (backend/app/models/patient.py) which uses:
- nhs_number as primary identifier (UK NHS number, 10 digits)
- full_name instead of first_name/last_name
- date_of_birth for age calculation

PRD Requirement: Sprint 1 - GET /api/v1/patients/{mrn}
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PatientBase(BaseModel):
    """
    Base patient schema matching existing Patient model.

    Uses nhs_number as primary patient identifier (UK NHS standard).
    """

    nhs_number: str = Field(
        ...,
        description="UK NHS Number (10 digits)",
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Patient full name"
    )
    date_of_birth: Optional[date] = Field(
        None,
        description="Patient date of birth"
    )
    address: Optional[str] = Field(
        None,
        max_length=500,
        description="Patient address"
    )


class PatientCreate(PatientBase):
    """Schema for creating a new patient (aggregation trigger)."""

    first_seen_at: datetime = Field(
        ...,
        description="Date of first document"
    )


class PatientUpdate(BaseModel):
    """Schema for updating an existing patient (all fields optional)."""

    full_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Patient full name"
    )
    date_of_birth: Optional[date] = Field(
        None,
        description="Patient date of birth"
    )
    address: Optional[str] = Field(
        None,
        max_length=500,
        description="Patient address"
    )


class PatientResponse(PatientBase):
    """
    Schema for patient response (PRD-compliant).

    Matches GET /api/v1/patients/{mrn} response format.
    """

    id: UUID = Field(..., description="Patient UUID (internal)")
    first_seen_at: datetime = Field(..., description="Earliest document date")
    last_seen_at: datetime = Field(..., description="Most recent document date")
    document_count: int = Field(..., ge=0, description="Number of documents")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    # Computed fields for PRD compliance
    age: Optional[int] = Field(None, description="Patient age in years")

    class Config:
        """Pydantic configuration."""
        from_attributes = True

    @field_validator("age", mode="before")
    @classmethod
    def calculate_age(cls, v, info):
        """Calculate age from date_of_birth if not provided."""
        if v is not None:
            return v
        # Age calculation is done in the endpoint, not here
        return None


class PatientListResponse(BaseModel):
    """Schema for paginated patient list response."""

    patients: List[PatientResponse] = Field(..., description="List of patients")
    total: int = Field(..., ge=0, description="Total number of patients")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")


class PatientDetailResponse(PatientResponse):
    """
    Extended patient response with document summary.

    Used for GET /api/v1/patients/{mrn} endpoint with additional details.
    """

    # NHS number display (masked for privacy in listings, full in detail view)
    nhs_number_masked: Optional[str] = Field(
        None,
        description="Masked NHS number (XXX-XXX-1234)"
    )

    @field_validator("nhs_number_masked", mode="before")
    @classmethod
    def mask_nhs_number(cls, v, info):
        """Generate masked NHS number for display."""
        if v is not None:
            return v
        nhs = info.data.get("nhs_number", "")
        if len(nhs) == 10:
            return f"XXX-XXX-{nhs[-4:]}"
        return None
