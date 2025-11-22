"""
Timeline Module Pydantic Models

Schemas for timeline API request/response validation and database models.
Follows Pydantic v2 patterns with comprehensive validation.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Enums
# ============================================================================


class ExportFormat(str, Enum):
    """Export format options for timeline data."""
    PDF = "pdf"
    FHIR = "fhir"
    JSON = "json"


class ExportStatus(str, Enum):
    """Status of export generation."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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


# ============================================================================
# Meta-Annotations
# ============================================================================


class MetaAnnotations(BaseModel):
    """
    Meta-annotation filters for high-precision concept filtering.

    Critical for achieving 95% precision by excluding:
    - Negated mentions (patient denies chest pain)
    - Historical conditions (history of diabetes)
    - Family history (mother had breast cancer)
    - Hypothetical scenarios (risk of developing)
    """

    negation: Optional[NegationValue] = Field(
        default=NegationValue.AFFIRMED,
        description="Filter by negation status (default: Affirmed only)",
    )

    experiencer: Optional[ExperiencerValue] = Field(
        default=ExperiencerValue.PATIENT,
        description="Filter by who experiences the condition (default: Patient)",
    )

    temporality: Optional[List[TemporalityValue]] = Field(
        default=[TemporalityValue.CURRENT, TemporalityValue.RECENT],
        description="Filter by temporality (default: Current and Recent)",
    )

    certainty: Optional[List[CertaintyValue]] = Field(
        default=[CertaintyValue.CONFIRMED],
        description="Filter by certainty level (default: Confirmed only)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "negation": "Affirmed",
                "experiencer": "Patient",
                "temporality": ["Current", "Recent"],
                "certainty": ["Confirmed"],
            }
        }
    }


# ============================================================================
# Concept Mention
# ============================================================================


class ConceptMention(BaseModel):
    """
    Single mention of a concept in a document.

    Represents one occurrence of a medical concept with context and metadata.
    """

    document_id: UUID = Field(
        description="Document containing this mention"
    )

    document_date: date = Field(
        description="Date of the document"
    )

    sentence: str = Field(
        description="Sentence containing the mention",
        min_length=1,
    )

    start_char: int = Field(
        description="Start character position in sentence",
        ge=0,
    )

    end_char: int = Field(
        description="End character position in sentence",
        ge=0,
    )

    meta_annotations: Dict[str, str] = Field(
        default={},
        description="Meta-annotation values (Negation, Experiencer, Temporality, Certainty)",
    )

    confidence: float = Field(
        description="Confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    @field_validator("end_char")
    @classmethod
    def validate_end_after_start(cls, v: int, info) -> int:
        """Validate end_char is after start_char."""
        if "start_char" in info.data and v < info.data["start_char"]:
            raise ValueError("end_char must be >= start_char")
        return v


# ============================================================================
# Timeline Concept
# ============================================================================


class TimelineConcept(BaseModel):
    """
    Aggregated concept with all mentions across documents.

    Groups multiple mentions of the same concept for timeline visualization.
    """

    concept_cui: str = Field(
        description="Concept unique identifier (UMLS/SNOMED-CT)",
        min_length=1,
    )

    name: str = Field(
        description="Human-readable concept name",
        min_length=1,
    )

    type: str = Field(
        description="Concept type (Disease, Symptom, Medication, etc.)",
        min_length=1,
    )

    first_mention_date: date = Field(
        description="Date of first mention in timeline"
    )

    mention_count: int = Field(
        description="Total number of mentions",
        ge=0,
    )

    mentions: List[ConceptMention] = Field(
        default=[],
        description="List of all mentions with context",
    )

    @model_validator(mode="after")
    def validate_mention_count_matches_list(self) -> "TimelineConcept":
        """Validate mention_count matches actual mentions list length."""
        if self.mention_count != len(self.mentions):
            raise ValueError(
                f"mention_count ({self.mention_count}) does not match mentions list length ({len(self.mentions)})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "concept_cui": "C0011860",
                "name": "Diabetes Mellitus",
                "type": "Disease",
                "first_mention_date": "2024-03-15",
                "mention_count": 3,
                "mentions": [],
            }
        }
    }


# ============================================================================
# Timeline Document
# ============================================================================


class TimelineDocument(BaseModel):
    """
    Document metadata for timeline view.

    Represents a single clinical document in the patient timeline.
    """

    id: UUID = Field(
        description="Document unique identifier"
    )

    title: str = Field(
        description="Document title",
        min_length=1,
    )

    type: str = Field(
        description="Document type (discharge, clinic, pathology, etc.)",
        min_length=1,
    )

    document_date: date = Field(
        description="Document date"
    )

    author: Optional[str] = Field(
        default=None,
        description="Document author",
    )

    concept_count: int = Field(
        description="Number of concepts extracted from this document",
        ge=0,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Clinic Note - Diabetes Follow-up",
                "type": "clinic",
                "document_date": "2024-03-15",
                "author": "Dr. Smith",
                "concept_count": 5,
            }
        }
    }


# ============================================================================
# Timeline Request & Response
# ============================================================================


class TimelineRequest(BaseModel):
    """
    Request to retrieve patient timeline with optional filters.
    """

    patient_id: UUID = Field(
        description="Patient unique identifier"
    )

    date_start: Optional[date] = Field(
        default=None,
        description="Start date for timeline range",
    )

    date_end: Optional[date] = Field(
        default=None,
        description="End date for timeline range",
    )

    concept_cuis: List[str] = Field(
        default=[],
        description="Filter by specific concept CUIs",
    )

    document_types: List[str] = Field(
        default=[],
        description="Filter by document types",
    )

    meta_annotations: Optional[MetaAnnotations] = Field(
        default=None,
        description="Meta-annotation filters for precision",
    )

    @field_validator("date_end")
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Validate date_end is after or equal to date_start."""
        if v is not None and "date_start" in info.data and info.data["date_start"] is not None:
            if v < info.data["date_start"]:
                raise ValueError("date_end must be after date_start")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "date_start": "2024-01-01",
                "date_end": "2024-12-31",
                "concept_cuis": ["C0011860", "C0020538"],
                "document_types": ["discharge", "clinic"],
                "meta_annotations": {
                    "negation": "Affirmed",
                    "experiencer": "Patient",
                    "temporality": ["Current", "Recent"],
                },
            }
        }
    }


class PatientTimeline(BaseModel):
    """
    Complete patient timeline with documents, concepts, and statistics.

    Response model for timeline API endpoint.
    """

    patient_id: UUID = Field(
        description="Patient unique identifier"
    )

    documents: List[TimelineDocument] = Field(
        description="Documents in timeline"
    )

    concepts: List[TimelineConcept] = Field(
        description="Concepts extracted from documents"
    )

    date_range: Tuple[date, date] = Field(
        description="Actual date range of timeline data"
    )

    filters_applied: Dict[str, Any] = Field(
        description="Filters that were applied to this timeline"
    )

    statistics: Dict[str, Any] = Field(
        description="Timeline statistics (document count, concept count, etc.)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "documents": [],
                "concepts": [],
                "date_range": ["2024-01-01", "2024-12-31"],
                "filters_applied": {},
                "statistics": {
                    "total_documents": 25,
                    "total_concepts": 42,
                    "date_span_days": 365,
                },
            }
        }
    }


# ============================================================================
# Export Models
# ============================================================================


class ExportRequest(BaseModel):
    """
    Request to export timeline data in specific format.
    """

    format: ExportFormat = Field(
        description="Export format (pdf, fhir, json)"
    )

    filters: Dict[str, Any] = Field(
        default={},
        description="Timeline filters to apply before export",
    )

    options: Dict[str, Any] = Field(
        default={},
        description="Format-specific export options",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "format": "pdf",
                "filters": {
                    "concept_cuis": ["C0011860"],
                    "date_range": ["2024-01-01", "2024-12-31"],
                },
                "options": {
                    "include_charts": True,
                    "page_size": "A4",
                },
            }
        }
    }


class TimelineExport(BaseModel):
    """
    Export generation status and download information.
    """

    id: UUID = Field(
        description="Export unique identifier"
    )

    patient_id: UUID = Field(
        description="Patient unique identifier"
    )

    status: ExportStatus = Field(
        description="Export generation status"
    )

    format: ExportFormat = Field(
        description="Export format"
    )

    download_url: Optional[str] = Field(
        default=None,
        description="Download URL (available when status=completed)",
    )

    expires_at: datetime = Field(
        description="When this export will be deleted"
    )

    audit_log_id: Optional[UUID] = Field(
        default=None,
        description="Audit log entry for this export",
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error message if status=failed",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "650e8400-e29b-41d4-a716-446655440000",
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "format": "pdf",
                "download_url": "https://example.com/exports/abc123.pdf",
                "expires_at": "2024-03-22T10:30:00Z",
                "audit_log_id": "750e8400-e29b-41d4-a716-446655440000",
            }
        }
    }


# ============================================================================
# Filter Models
# ============================================================================


class TimelineFilter(BaseModel):
    """
    Saved timeline filter preset.

    Matches database table: timeline_filters
    """

    id: UUID = Field(
        description="Filter unique identifier"
    )

    user_id: UUID = Field(
        description="User who owns this filter"
    )

    name: str = Field(
        description="Filter name",
        min_length=3,
        max_length=100,
    )

    description: Optional[str] = Field(
        default=None,
        description="Optional description",
    )

    filters: Dict[str, Any] = Field(
        description="Filter configuration (JSONB)",
    )

    is_default: bool = Field(
        default=False,
        description="Whether this is the user's default filter",
    )

    created_at: datetime = Field(
        description="When this filter was created"
    )

    updated_at: datetime = Field(
        description="When this filter was last updated"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "850e8400-e29b-41d4-a716-446655440000",
                "user_id": "950e8400-e29b-41d4-a716-446655440000",
                "name": "Active Diabetes Patients",
                "description": "Current diabetes diagnoses only",
                "filters": {
                    "concept_cuis": ["C0011860"],
                    "meta_annotations": {
                        "negation": "Affirmed",
                        "temporality": ["Current", "Recent"],
                    },
                },
                "is_default": False,
                "created_at": "2024-03-15T10:30:00Z",
                "updated_at": "2024-03-15T10:30:00Z",
            }
        }
    }


# ==============================================================================
# Filter Preset Models (API)
# ==============================================================================

class FilterPresetRequest(BaseModel):
    """Request model for saving timeline filter preset."""
    
    name: str = Field(..., min_length=3, max_length=100, description="Filter name (3-100 characters)")
    description: Optional[str] = Field(None, max_length=500, description="Filter description")
    filters: Dict[str, Any] = Field(..., description="Filter configuration (concept CUIs, dates, meta-annotations)")
    is_default: bool = Field(False, description="Set as default filter for user")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Diabetes Filter",
            "description": "Filter for diabetes-related concepts",
            "filters": {
                "concept_cuis": ["C0011860", "C0011849"],
                "meta_annotations": {
                    "negation": "Affirmed",
                    "experiencer": "Patient"
                }
            },
            "is_default": False
        }
    })


class FilterPresetResponse(BaseModel):
    """Response model for timeline filter preset."""
    
    id: UUID = Field(..., description="Filter UUID")
    name: str = Field(..., description="Filter name")
    description: Optional[str] = Field(None, description="Filter description")
    filters: Dict[str, Any] = Field(..., description="Filter configuration")
    is_default: bool = Field(..., description="Whether this is user's default filter")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Diabetes Filter",
            "description": "Filter for diabetes-related concepts",
            "filters": {
                "concept_cuis": ["C0011860"]
            },
            "is_default": False,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
    })
