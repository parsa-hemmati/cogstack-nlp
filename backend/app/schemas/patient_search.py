"""
Patient Search Schemas
Pydantic models for patient search request/response validation
"""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class NegationFilter(str, Enum):
    """Negation filter options"""
    AFFIRMED = "Affirmed"
    NEGATED = "Negated"
    ANY = "Any"


class TemporalityFilter(str, Enum):
    """Temporality filter options"""
    CURRENT = "Current"
    HISTORICAL = "Historical"
    ANY = "Any"


class ExperiencerFilter(str, Enum):
    """Experiencer filter options"""
    PATIENT = "Patient"
    FAMILY = "Family"
    OTHER = "Other"
    ANY = "Any"


class CertaintyFilter(str, Enum):
    """Certainty filter options"""
    CONFIRMED = "Confirmed"
    SUSPECTED = "Suspected"
    ANY = "Any"


class SortByOption(str, Enum):
    """Sort order options"""
    RELEVANCE = "relevance"
    NAME = "name"
    LAST_UPDATED = "last_updated"


class MetaAnnotationFilters(BaseModel):
    """
    Filters for MedCAT meta-annotations.

    Used to refine patient search by filtering extracted clinical concepts
    based on meta-annotations (negation, temporality, experiencer, certainty).

    Attributes:
        negation: Filter by negation status
            - "Affirmed": Concept is present (default)
            - "Negated": Concept is negated (e.g., "no chest pain")
            - "Any": Don't filter by negation
        temporality: Filter by temporal context
            - "Current": Recent or current condition (default)
            - "Historical": Past condition
            - "Any": Don't filter by temporality
        experiencer: Filter by who experiences the condition
            - "Patient": Patient has the condition (default)
            - "Family": Family member has it (family history)
            - "Other": Other person mentioned
            - "Any": Don't filter by experiencer
        certainty: Filter by diagnostic certainty
            - "Confirmed": Confirmed diagnosis
            - "Suspected": Suspected/possible diagnosis
            - "Any" or None: Don't filter by certainty (default)

    Example:
        >>> # Find patients with current, affirmed diabetes (not family history)
        >>> filters = MetaAnnotationFilters(
        ...     negation="Affirmed",
        ...     temporality="Current",
        ...     experiencer="Patient"
        ... )
    """
    negation: NegationFilter = Field(
        default=NegationFilter.AFFIRMED,
        description="Negation filter: Affirmed | Negated | Any"
    )
    temporality: TemporalityFilter = Field(
        default=TemporalityFilter.CURRENT,
        description="Temporality filter: Current | Historical | Any"
    )
    experiencer: ExperiencerFilter = Field(
        default=ExperiencerFilter.PATIENT,
        description="Experiencer filter: Patient | Family | Other | Any"
    )
    certainty: Optional[CertaintyFilter] = Field(
        default=None,
        description="Certainty filter: Confirmed | Suspected | Any"
    )


class PatientSearchRequest(BaseModel):
    """
    Request schema for patient search.

    Attributes:
        query: Search query (concept name or CUI)
            - Concept name: "diabetes", "atrial flutter", "myocardial infarction"
            - SNOMED-CT CUI: "C0011849", "C0004238", "C0027051"
        filters: Meta-annotation filters (default: current, affirmed, patient)
        sort_by: Sort order for results
            - "relevance": By concept document count (most mentions first)
            - "name": Alphabetical by patient name
            - "last_updated": By most recent document
        page: Page number (1-indexed)
        page_size: Number of results per page (max 100)

    Example:
        >>> request = PatientSearchRequest(
        ...     query="diabetes",
        ...     filters=MetaAnnotationFilters(),
        ...     sort_by="relevance",
        ...     page=1,
        ...     page_size=20
        ... )
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search query (concept name or CUI)"
    )
    filters: MetaAnnotationFilters = Field(
        default_factory=MetaAnnotationFilters,
        description="Meta-annotation filters"
    )
    sort_by: SortByOption = Field(
        default=SortByOption.RELEVANCE,
        description="Sort order: relevance | name | last_updated"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Results per page (max 100)"
    )


class PatientSearchResult(BaseModel):
    """
    Single patient search result.

    Attributes:
        patient_id: Unique patient identifier
        nhs_number: Masked NHS number (e.g., "XXX-XXX-1234")
        full_name: Patient's full name
        date_of_birth: Patient's date of birth
        age: Calculated age in years
        document_count: Total number of documents for this patient
        concept_document_count: Number of documents containing the searched concept
        last_updated: Timestamp of most recent document

    Example:
        >>> result = PatientSearchResult(
        ...     patient_id=UUID("..."),
        ...     nhs_number="XXX-XXX-1234",
        ...     full_name="John Doe",
        ...     date_of_birth=date(1980, 5, 15),
        ...     age=44,
        ...     document_count=25,
        ...     concept_document_count=8,
        ...     last_updated=datetime.now()
        ... )
    """
    patient_id: UUID = Field(..., description="Unique patient identifier")
    nhs_number: str = Field(..., description="Masked NHS number (XXX-XXX-1234)")
    full_name: str = Field(..., description="Patient's full name")
    date_of_birth: date = Field(..., description="Patient's date of birth")
    age: int = Field(..., description="Calculated age in years")
    document_count: int = Field(..., description="Total documents for patient")
    concept_document_count: int = Field(
        ...,
        description="Documents containing searched concept"
    )
    last_updated: datetime = Field(..., description="Most recent document timestamp")


class PatientSearchResponse(BaseModel):
    """
    Response schema for patient search.

    Attributes:
        results: List of patient search results
        total_count: Total number of matching patients (across all pages)
        page: Current page number
        page_size: Number of results per page
        query_time_ms: Query execution time in milliseconds

    Example:
        >>> response = PatientSearchResponse(
        ...     results=[...],  # List of PatientSearchResult
        ...     total_count=150,
        ...     page=1,
        ...     page_size=20,
        ...     query_time_ms=245
        ... )
    """
    results: List[PatientSearchResult] = Field(
        ...,
        description="List of patient search results"
    )
    total_count: int = Field(
        ...,
        description="Total matching patients (all pages)"
    )
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    query_time_ms: int = Field(..., description="Query execution time (ms)")
