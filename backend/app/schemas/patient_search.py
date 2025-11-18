"""
Patient Search Schemas
Pydantic models for patient search request/response validation (PRD-compliant)
"""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Enums for filtering and sorting
# ============================================================================

class TemporalFilter(str, Enum):
    """Temporal filter options"""
    CURRENT = "current"
    HISTORICAL = "historical"
    FUTURE = "future"
    ANY = "any"


class SortOption(str, Enum):
    """Sort order options"""
    RELEVANCE = "relevance"
    NAME = "name"
    LAST_UPDATED = "lastUpdated"


# ============================================================================
# Nested schemas for complex objects
# ============================================================================

class DateRangeFilter(BaseModel):
    """Date range filter for search results"""
    start: Optional[str] = Field(None, description="Start date (ISO 8601)")
    end: Optional[str] = Field(None, description="End date (ISO 8601)")


class SearchFilters(BaseModel):
    """
    Search filters for patient search.

    Attributes:
        temporal: Filter by temporal context (current, historical, future, any)
        includeNegated: Include negated mentions (e.g., "no chest pain")
        includeFamily: Include family history mentions
        dateRange: Optional date range filter
    """
    temporal: TemporalFilter = Field(
        default=TemporalFilter.CURRENT,
        description="Temporal filter: current | historical | future | any"
    )
    includeNegated: bool = Field(
        default=False,
        description="Include negated mentions"
    )
    includeFamily: bool = Field(
        default=False,
        description="Include family history mentions"
    )
    dateRange: Optional[DateRangeFilter] = Field(
        default=None,
        description="Optional date range filter"
    )


class Pagination(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    pageSize: int = Field(default=20, ge=1, le=100, description="Results per page (max 100)")


class MetaAnnotations(BaseModel):
    """
    MedCAT meta-annotations for a concept.

    Attributes:
        temporality: Current, historical, or future
        negated: Whether the concept is negated
        experiencer: Patient, family, or other
        certainty: Definite, probable, or possible
    """
    temporality: Optional[str] = Field(None, description="Temporal context")
    negated: Optional[bool] = Field(None, description="Is negated")
    experiencer: Optional[str] = Field(None, description="Who experiences this")
    certainty: Optional[str] = Field(None, description="Diagnostic certainty")


class Annotation(BaseModel):
    """
    Single concept annotation from MedCAT.

    Represents a medical concept extracted from clinical text with metadata.

    Attributes:
        cui: Concept Unique Identifier (UMLS CUI)
        conceptName: Human-readable concept name
        sourceValue: Actual text span from document
        documentId: Document containing this annotation
        documentType: Type of clinical document
        documentDate: Date of the document (ISO 8601)
        startChar: Character offset where concept starts
        endChar: Character offset where concept ends
        confidence: Confidence score (0.0 to 1.0)
        metaAnnotations: Meta-annotations (negation, temporality, etc.)
        snomedCT: SNOMED-CT codes (if available)
        icd10: ICD-10 codes (if available)
    """
    cui: str = Field(..., description="UMLS Concept Unique Identifier")
    conceptName: str = Field(..., description="Human-readable concept name")
    sourceValue: str = Field(..., description="Actual text from document")
    documentId: str = Field(..., description="Document ID")
    documentType: str = Field(..., description="Document type")
    documentDate: str = Field(..., description="Document date (ISO 8601)")
    startChar: int = Field(..., description="Start character offset")
    endChar: int = Field(..., description="End character offset")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metaAnnotations: MetaAnnotations = Field(..., description="Meta-annotations")
    snomedCT: Optional[List[str]] = Field(None, description="SNOMED-CT codes")
    icd10: Optional[List[str]] = Field(None, description="ICD-10 codes")


class Demographics(BaseModel):
    """
    Patient demographics.

    Attributes:
        age: Patient age in years
        gender: Patient gender
        department: Primary department (optional)
    """
    age: int = Field(..., description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")
    department: Optional[str] = Field(None, description="Primary department")


# ============================================================================
# Request/Response schemas
# ============================================================================

class PatientSearchRequest(BaseModel):
    """
    Request schema for patient search (PRD-compliant).

    Attributes:
        concept: Medical concept to search for (name or CUI)
            - Concept name: "diabetes", "atrial flutter", "myocardial infarction"
            - SNOMED-CT CUI: "C0011849", "C0004238", "C0027051"
        filters: Search filters (temporal, negation, family history, date range)
        pagination: Pagination parameters (page, pageSize)
        sort: Sort order (relevance, name, lastUpdated)

    Example:
        >>> request = PatientSearchRequest(
        ...     concept="atrial flutter",
        ...     filters=SearchFilters(temporal="current", includeNegated=False),
        ...     pagination=Pagination(page=1, pageSize=20),
        ...     sort="relevance"
        ... )
    """
    concept: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Medical concept (name or CUI)"
    )
    filters: SearchFilters = Field(
        default_factory=SearchFilters,
        description="Search filters"
    )
    pagination: Pagination = Field(
        default_factory=Pagination,
        description="Pagination parameters"
    )
    sort: SortOption = Field(
        default=SortOption.RELEVANCE,
        description="Sort order"
    )


class PatientSearchResult(BaseModel):
    """
    Single patient search result (PRD-compliant).

    Attributes:
        mrn: Medical Record Number (masked for privacy)
        demographics: Patient demographics
        annotations: List of concept annotations found in patient's documents
        lastUpdated: Timestamp of most recent document (ISO 8601)

    Example:
        >>> result = PatientSearchResult(
        ...     mrn="XXX-XXX-1234",
        ...     demographics=Demographics(age=72, gender="Male"),
        ...     annotations=[...],
        ...     lastUpdated="2024-01-15T10:30:00Z"
        ... )
    """
    mrn: str = Field(..., description="Masked Medical Record Number")
    demographics: Demographics = Field(..., description="Patient demographics")
    annotations: List[Annotation] = Field(..., description="Concept annotations")
    lastUpdated: str = Field(..., description="Last document timestamp (ISO 8601)")


class PatientSearchResponse(BaseModel):
    """
    Response schema for patient search (PRD-compliant).

    Attributes:
        results: List of patient search results
        total: Total number of matching patients (across all pages)
        page: Current page number
        pageSize: Results per page
        queryTimeMs: Query execution time in milliseconds

    Example:
        >>> response = PatientSearchResponse(
        ...     results=[...],
        ...     total=145,
        ...     page=1,
        ...     pageSize=20,
        ...     queryTimeMs=234
        ... )
    """
    results: List[PatientSearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total matching patients")
    page: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Results per page")
    queryTimeMs: int = Field(..., description="Query time (ms)")
