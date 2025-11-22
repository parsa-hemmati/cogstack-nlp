"""
Patient Schemas

Pydantic models for patient-related API requests and responses.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PatientResponse(BaseModel):
    """Patient response schema."""
    id: UUID
    nhs_number: Optional[str] = None
    mrn: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    source_document_ids: List[UUID]
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientListResponse(BaseModel):
    """List of patients response."""
    patients: List[PatientResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class PatientSearchRequest(BaseModel):
    """Patient search request schema."""
    query: Optional[str] = Field(None, description="General search query")
    nhs_number: Optional[str] = Field(None, description="NHS number search")
    mrn: Optional[str] = Field(None, description="MRN search")
    last_name: Optional[str] = Field(None, description="Last name search")
    postcode: Optional[str] = Field(None, description="Postcode search")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    model_config = ConfigDict(from_attributes=True)


class TimelineEvent(BaseModel):
    """Patient timeline event schema."""
    date: str
    type: str = Field(..., description="Event type (document, diagnosis, medication, etc.)")
    title: str
    description: Optional[str] = None
    document_id: Optional[str] = None
    cui: Optional[str] = None
    confidence: Optional[float] = None
    temporality: Optional[str] = None
    contains_phi: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class PatientTimelineResponse(BaseModel):
    """Patient timeline response."""
    patient_id: UUID
    events: List[TimelineEvent]
    total_events: int

    model_config = ConfigDict(from_attributes=True)


class PatientStatistics(BaseModel):
    """Patient statistics schema."""
    patient_id: str
    document_count: int
    total_entities: int
    phi_entities: int
    clinical_entities: int
    unique_conditions: int
    confidence_score: Optional[float] = None
    last_updated: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientAggregationRequest(BaseModel):
    """Request to aggregate patient from document."""
    document_id: UUID = Field(..., description="Document to process")

    model_config = ConfigDict(from_attributes=True)


class PatientMergeRequest(BaseModel):
    """Request to merge duplicate patients."""
    primary_patient_id: UUID = Field(..., description="Primary patient to keep")
    duplicate_patient_id: UUID = Field(..., description="Duplicate to merge")

    model_config = ConfigDict(from_attributes=True)


class PatientAggregatedData(BaseModel):
    """Aggregated patient data response."""
    patient_id: UUID
    identifiers: Dict[str, Optional[str]]
    demographics: Dict[str, Optional[str]]
    contact: Dict[str, Any]
    clinical_concepts: List[Dict[str, Any]]
    dates: List[Dict[str, str]]
    document_count: int

    model_config = ConfigDict(from_attributes=True)