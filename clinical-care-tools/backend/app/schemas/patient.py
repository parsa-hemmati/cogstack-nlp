"""Pydantic schemas for patient-related requests and responses."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PatientBase(BaseModel):
    """Base patient schema."""

    patient_id: str = Field(..., description="External patient identifier (MRN, NHS number)")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(..., max_length=20)
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for creating a patient."""

    pass


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class PatientResponse(PatientBase):
    """Schema for patient response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PatientSearchRequest(BaseModel):
    """Schema for patient search request."""

    query: str = Field(..., description="Search query (medical concept or free text)")
    patient_id: Optional[str] = Field(None, description="Filter by patient ID")
    date_from: Optional[date] = Field(None, description="Filter documents from this date")
    date_to: Optional[date] = Field(None, description="Filter documents to this date")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    include_negated: bool = Field(
        default=False, description="Include negated mentions (default: False)"
    )
    include_family: bool = Field(
        default=False, description="Include family history (default: False)"
    )
    include_historical: bool = Field(
        default=False, description="Include historical conditions (default: False)"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class PatientSearchResult(BaseModel):
    """Schema for patient search result."""

    patient: PatientResponse
    matched_documents: List[str]
    matched_entities: List[dict]
    total_matches: int


class PatientListResponse(BaseModel):
    """Schema for patient list response."""

    patients: List[PatientResponse]
    total: int
    page: int
    page_size: int
