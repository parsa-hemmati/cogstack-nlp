"""Pydantic schemas for CDS Guidelines API."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class CDSGuidelineBase(BaseModel):
    """Base schema for CDS Guideline."""
    guideline_source: str = Field(..., description="Guideline source: ADA, AHA, USPSTF, NICE")
    guideline_name: str = Field(..., max_length=255, description="Guideline name/title")
    condition_code: str = Field(..., max_length=50, description="ICD-10 or SNOMED CT condition code")
    recommendation: str = Field(..., description="Clinical recommendation text")
    evidence_level: str = Field(..., description="Evidence level: A (strong), B (moderate), C (weak)")
    rationale: str = Field(..., description="Rationale and supporting evidence")
    last_updated: datetime = Field(..., description="Date guideline was last updated by source")


class CDSGuidelineCreate(CDSGuidelineBase):
    """Schema for creating a new CDS Guideline."""
    pass


class CDSGuidelineUpdate(BaseModel):
    """Schema for updating a CDS Guideline."""
    guideline_source: Optional[str] = Field(None, description="Guideline source")
    guideline_name: Optional[str] = Field(None, max_length=255, description="Guideline name")
    condition_code: Optional[str] = Field(None, max_length=50, description="Condition code")
    recommendation: Optional[str] = Field(None, description="Recommendation text")
    evidence_level: Optional[str] = Field(None, description="Evidence level")
    rationale: Optional[str] = Field(None, description="Rationale")
    last_updated: Optional[datetime] = Field(None, description="Last updated date")


class CDSGuidelineResponse(CDSGuidelineBase):
    """Schema for CDS Guideline response."""
    id: UUID = Field(..., description="Guideline ID")
    created_at: datetime = Field(..., description="Date record was created in database")

    class Config:
        from_attributes = True


class CDSGuidelineSearchRequest(BaseModel):
    """Schema for searching CDS Guidelines."""
    condition_code: Optional[str] = Field(None, description="Filter by condition code (ICD-10 or SNOMED CT)")
    guideline_source: Optional[str] = Field(None, description="Filter by source (ADA, AHA, USPSTF, NICE)")
    evidence_level: Optional[str] = Field(None, description="Filter by evidence level (A, B, C)")
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (1-100)")


class CDSGuidelineListResponse(BaseModel):
    """Schema for paginated list of CDS Guidelines."""
    items: List[CDSGuidelineResponse] = Field(..., description="List of guidelines")
    total: int = Field(..., description="Total number of guidelines matching filters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
