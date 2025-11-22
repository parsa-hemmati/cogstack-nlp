"""
Patient Search Schemas

Pydantic models for patient search requests and responses.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class NegationValue(str, Enum):
    """Negation meta-annotation values."""
    AFFIRMED = "Affirmed"
    NEGATED = "Negated"
    POSSIBLE = "Possible"


class TemporalityValue(str, Enum):
    """Temporality meta-annotation values."""
    CURRENT = "Current"
    RECENT = "Recent"
    HISTORICAL = "Historical"
    FUTURE = "Future"


class ExperiencerValue(str, Enum):
    """Experiencer meta-annotation values."""
    PATIENT = "Patient"
    FAMILY = "Family"
    OTHER = "Other"


class CertaintyValue(str, Enum):
    """Certainty meta-annotation values."""
    CONFIRMED = "Confirmed"
    SUSPECTED = "Suspected"
    HYPOTHETICAL = "Hypothetical"
    NEGATIVE = "Negative"


class BooleanOperator(str, Enum):
    """Boolean operators for complex queries."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class ExportFormat(str, Enum):
    """Export format options."""
    CSV = "csv"
    FHIR = "fhir"
    JSON = "json"


class MetaAnnotationFilters(BaseModel):
    """
    Meta-annotation filters for high-precision filtering.

    These filters are critical for achieving 95% precision by excluding:
    - Negated mentions (patient denies chest pain)
    - Historical conditions (history of diabetes)
    - Family history (mother had breast cancer)
    - Hypothetical scenarios (risk of developing)
    """

    negation: Optional[NegationValue] = Field(
        default=NegationValue.AFFIRMED,
        description="Filter by negation status (default: Affirmed only)",
    )

    temporality: Optional[List[TemporalityValue]] = Field(
        default=[TemporalityValue.CURRENT, TemporalityValue.RECENT],
        description="Filter by temporality (default: Current and Recent)",
    )

    experiencer: Optional[ExperiencerValue] = Field(
        default=ExperiencerValue.PATIENT,
        description="Filter by who experiences the condition (default: Patient)",
    )

    certainty: Optional[List[CertaintyValue]] = Field(
        default=[CertaintyValue.CONFIRMED],
        description="Filter by certainty level (default: Confirmed only)",
    )

    confidence_min: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0.0-1.0, default: 0.7)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "negation": "Affirmed",
                "temporality": ["Current", "Recent"],
                "experiencer": "Patient",
                "certainty": ["Confirmed"],
                "confidence_min": 0.7,
            }
        }
    }


class SearchQuery(BaseModel):
    """
    Individual search query with concept and operator.
    """

    concept: str = Field(
        description="Medical concept to search for (e.g., 'diabetes', 'atrial flutter')",
        min_length=2,
        max_length=500,
    )

    operator: Optional[BooleanOperator] = Field(
        default=None,
        description="Boolean operator to combine with next query",
    )

    cui: Optional[str] = Field(
        default=None,
        description="Optional UMLS/SNOMED-CT concept unique identifier",
    )


class PatientSearchRequest(BaseModel):
    """
    Patient search request with query and filters.
    """

    query: str = Field(
        description="Search query (medical concept or SNOMED-CT code)",
        min_length=2,
        max_length=1000,
    )

    queries: Optional[List[SearchQuery]] = Field(
        default=None,
        description="Multiple queries with boolean operators for complex searches",
    )

    filters: MetaAnnotationFilters = Field(
        default_factory=MetaAnnotationFilters,
        description="Meta-annotation filters for precision",
    )

    date_from: Optional[date] = Field(
        default=None,
        description="Filter documents from this date",
    )

    date_to: Optional[date] = Field(
        default=None,
        description="Filter documents up to this date",
    )

    department_ids: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific departments",
    )

    document_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by document types (e.g., 'discharge', 'clinic')",
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of results to return",
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip (for pagination)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "diabetes mellitus",
                "filters": {
                    "negation": "Affirmed",
                    "temporality": ["Current", "Recent"],
                    "experiencer": "Patient",
                    "confidence_min": 0.7,
                },
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
                "limit": 50,
                "offset": 0,
            }
        }
    }


class ConceptMatch(BaseModel):
    """
    Matched medical concept with metadata.
    """

    text: str = Field(description="Original text that was matched")
    cui: str = Field(description="Concept unique identifier (UMLS/SNOMED)")
    pretty_name: str = Field(description="Human-readable concept name")
    confidence: float = Field(description="Confidence score (0.0-1.0)")

    # Meta-annotations
    negation: str = Field(description="Negation status")
    temporality: str = Field(description="Temporal status")
    experiencer: str = Field(description="Who experiences the condition")
    certainty: str = Field(description="Certainty level")

    # Context
    start_idx: int = Field(description="Start position in document")
    end_idx: int = Field(description="End position in document")
    context: str = Field(description="Surrounding text for context")


class PatientSearchResult(BaseModel):
    """
    Individual patient search result.
    """

    patient_id: UUID = Field(description="Patient unique identifier")
    patient_mrn: str = Field(description="Patient medical record number")

    # Basic demographics (limited for privacy)
    age: Optional[int] = Field(default=None, description="Patient age")
    gender: Optional[str] = Field(default=None, description="Patient gender")

    # Match information
    matched_concepts: List[ConceptMatch] = Field(
        description="Concepts that matched the search criteria"
    )

    relevance_score: float = Field(
        description="Overall relevance score (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    # Document information
    document_count: int = Field(
        description="Number of documents with matches"
    )

    latest_match_date: datetime = Field(
        description="Date of most recent match"
    )

    # Summary
    summary: Optional[str] = Field(
        default=None,
        description="AI-generated summary of patient's condition",
    )


class PatientSearchResponse(BaseModel):
    """
    Patient search response with results and metadata.
    """

    results: List[PatientSearchResult] = Field(
        description="List of matching patients"
    )

    total: int = Field(
        description="Total number of matching patients (before pagination)"
    )

    query_time_ms: int = Field(
        description="Query execution time in milliseconds"
    )

    filters_applied: MetaAnnotationFilters = Field(
        description="Filters that were applied"
    )

    # Statistics
    stats: Dict[str, Any] = Field(
        default={},
        description="Search statistics (concept distribution, etc.)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "results": [
                    {
                        "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                        "patient_mrn": "MRN123456",
                        "age": 65,
                        "gender": "M",
                        "matched_concepts": [
                            {
                                "text": "diabetes mellitus",
                                "cui": "C0011860",
                                "pretty_name": "Diabetes Mellitus, Type 2",
                                "confidence": 0.95,
                                "negation": "Affirmed",
                                "temporality": "Current",
                                "experiencer": "Patient",
                                "certainty": "Confirmed",
                                "start_idx": 150,
                                "end_idx": 167,
                                "context": "...diagnosed with diabetes mellitus in 2020...",
                            }
                        ],
                        "relevance_score": 0.92,
                        "document_count": 5,
                        "latest_match_date": "2024-03-15T10:30:00Z",
                        "summary": "Patient with well-controlled Type 2 diabetes",
                    }
                ],
                "total": 42,
                "query_time_ms": 235,
                "filters_applied": {
                    "negation": "Affirmed",
                    "temporality": ["Current"],
                    "experiencer": "Patient",
                    "confidence_min": 0.7,
                },
                "stats": {
                    "avg_confidence": 0.87,
                    "concept_distribution": {
                        "C0011860": 35,
                        "C0011854": 7,
                    },
                },
            }
        }
    }


class SavedSearchRequest(BaseModel):
    """
    Request to save a search query.
    """

    name: str = Field(
        description="Name for the saved search",
        min_length=1,
        max_length=255,
    )

    description: Optional[str] = Field(
        default=None,
        description="Optional description",
        max_length=1000,
    )

    search_request: PatientSearchRequest = Field(
        description="The search request to save"
    )

    is_public: bool = Field(
        default=False,
        description="Whether this search is visible to other users",
    )


class SavedSearchResponse(BaseModel):
    """
    Saved search information.
    """

    id: UUID
    name: str
    description: Optional[str]
    search_request: PatientSearchRequest
    is_public: bool
    created_by: UUID
    created_at: datetime
    last_used: Optional[datetime]
    use_count: int = 0


class ConceptSuggestion(BaseModel):
    """
    Concept suggestion for autocomplete.
    """

    cui: str = Field(description="Concept unique identifier")
    pretty_name: str = Field(description="Human-readable name")
    semantic_type: str = Field(description="Semantic type (e.g., 'Disease', 'Symptom')")
    synonyms: List[str] = Field(default=[], description="Alternative names")
    popularity: int = Field(
        default=0,
        description="Usage frequency in the system",
    )


class ExportRequest(BaseModel):
    """
    Request to export search results.
    """

    format: ExportFormat = Field(
        description="Export format (csv, fhir, json)"
    )

    patient_ids: List[UUID] = Field(
        description="List of patient IDs to export"
    )

    include_concepts: bool = Field(
        default=True,
        description="Include matched concepts in export",
    )

    include_context: bool = Field(
        default=False,
        description="Include text context around matches",
    )

    anonymize: bool = Field(
        default=False,
        description="Anonymize patient data in export",
    )