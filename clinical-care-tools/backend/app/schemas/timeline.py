"""Pydantic schemas for timeline-related requests and responses."""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TimelineQueryParams(BaseModel):
    """Query parameters for timeline API."""

    patient_id: str = Field(..., description="Patient UUID")
    start_date: Optional[str] = Field(None, description="Filter start date (ISO 8601)")
    end_date: Optional[str] = Field(None, description="Filter end date (ISO 8601)")
    document_types: Optional[list[str]] = Field(
        None, description="Filter by document type"
    )
    concept_types: Optional[list[str]] = Field(
        None, description="Filter by concept type (condition/medication/procedure)"
    )
    include_negated: bool = Field(
        default=False, description="Include negated concepts (default: false)"
    )
    include_family: bool = Field(
        default=False, description="Include family history (default: false)"
    )


class ConceptOccurrence(BaseModel):
    """Single occurrence of a concept in a document."""

    document_id: str = Field(..., description="Document UUID where concept appears")
    date: str = Field(..., description="Document date (ISO 8601)")
    context: str = Field(..., description="Sentence containing the concept")
    start_char: int = Field(..., description="Start character position")
    end_char: int = Field(..., description="End character position")


class TimelineDocument(BaseModel):
    """Document representation in timeline."""

    id: str = Field(..., description="Document UUID")
    title: str = Field(..., description="Document title or filename")
    type: str = Field(
        ...,
        description="Document type (clinical_note, lab_report, discharge_summary)",
    )
    date: str = Field(..., description="Document date (ISO 8601)")
    author: Optional[str] = Field(None, description="Document author")
    department: Optional[str] = Field(None, description="Department/specialty")
    content_preview: Optional[str] = Field(
        None, description="First 200 characters of content"
    )
    annotation_count: int = Field(..., description="Number of clinical concepts")


class TimelineConcept(BaseModel):
    """Clinical concept representation in timeline."""

    id: str = Field(..., description="Concept identifier (typically CUI)")
    cui: str = Field(..., description="SNOMED-CT CUI")
    name: str = Field(..., description="Preferred term")
    type: str = Field(
        ..., description="Concept type (condition, medication, procedure)"
    )
    first_mentioned: str = Field(
        ..., description="First occurrence date (ISO 8601)"
    )
    last_mentioned: str = Field(..., description="Last occurrence date (ISO 8601)")
    occurrences: list[ConceptOccurrence] = Field(
        default_factory=list, description="All occurrences across documents"
    )
    meta_annotations: dict[str, str] = Field(
        ...,
        description="Meta-annotations (negation, temporality, experiencer, certainty)",
    )


class TimelineResponse(BaseModel):
    """Complete timeline response."""

    patient_id: str = Field(..., description="Patient UUID")
    timeline: dict[str, Any] = Field(
        ...,
        description="Timeline data including documents, concepts, and date range",
    )
    metadata: dict[str, Any] = Field(..., description="Response metadata")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "timeline": {
                    "documents": [
                        {
                            "id": "650e8400-e29b-41d4-a716-446655440000",
                            "title": "Clinical Note - General Medicine",
                            "type": "clinical_note",
                            "date": "2023-06-15T10:30:00Z",
                            "author": "Dr. Smith",
                            "department": "Cardiology",
                            "annotation_count": 15,
                        }
                    ],
                    "concepts": [
                        {
                            "id": "C0020538",
                            "cui": "C0020538",
                            "name": "Hypertension",
                            "type": "condition",
                            "first_mentioned": "2023-01-15T08:00:00Z",
                            "last_mentioned": "2023-11-30T14:00:00Z",
                            "occurrences": [
                                {
                                    "document_id": "650e8400-e29b-41d4-a716-446655440000",
                                    "date": "2023-06-15T10:30:00Z",
                                    "context": "Patient has history of hypertension",
                                    "start_char": 24,
                                    "end_char": 36,
                                }
                            ],
                            "meta_annotations": {
                                "negation": "Affirmed",
                                "temporality": "Current",
                                "experiencer": "Patient",
                            },
                        }
                    ],
                    "date_range": {
                        "earliest": "2023-01-15T08:00:00Z",
                        "latest": "2023-11-30T14:00:00Z",
                    },
                },
                "metadata": {
                    "document_count": 1,
                    "concept_count": 1,
                    "generated_at": "2025-11-18T10:00:00Z",
                },
            }
        }
