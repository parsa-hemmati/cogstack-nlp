"""
Timeline API request and response schemas.

This module defines Pydantic models for the Timeline View API endpoints,
supporting timeline data retrieval, filtering, and export functionality.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from uuid import UUID


class MetaAnnotations(BaseModel):
    """Meta-annotations for clinical concept mentions.

    These annotations provide critical context about how the concept
    was mentioned in the clinical text (negated, historical, family history, etc.).
    """

    Negation: str = Field(
        ...,
        description="Negation status: 'Affirmed' or 'Negated'",
        example="Affirmed"
    )
    Temporality: str = Field(
        ...,
        description="Temporal status: 'Current', 'Recent', or 'Historical'",
        example="Current"
    )
    Experiencer: str = Field(
        ...,
        description="Who experienced the condition: 'Patient', 'Family', or 'Other'",
        example="Patient"
    )
    Certainty: str = Field(
        ...,
        description="Certainty level: 'High', 'Medium', or 'Low'",
        example="High"
    )


class ConceptMention(BaseModel):
    """A single mention of a clinical concept in a document.

    Represents one occurrence of a concept (e.g., "diabetes") in a specific
    document at a specific date, with associated meta-annotations and confidence.
    """

    concept_cui: str = Field(
        ...,
        description="SNOMED-CT Concept Unique Identifier",
        example="C0011849"
    )
    concept_name: str = Field(
        ...,
        description="Human-readable concept name",
        example="Diabetes Mellitus"
    )
    concept_type: str = Field(
        ...,
        description="Type of concept: 'condition', 'medication', 'procedure', 'symptom', 'lab_result'",
        example="condition"
    )
    document_id: str = Field(
        ...,
        description="UUID of the document containing this mention"
    )
    date: datetime = Field(
        ...,
        description="Date of the document (ISO 8601 format)"
    )
    sentence: str = Field(
        ...,
        description="Sentence or context where the concept was mentioned",
        example="Patient diagnosed with Type 2 Diabetes. HbA1c 8.5%."
    )
    meta_annotations: MetaAnnotations = Field(
        ...,
        description="Meta-annotations providing context about the mention"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from NLP model (0.0-1.0)",
        example=0.95
    )
    is_first_mention: bool = Field(
        default=False,
        description="Whether this is the first (earliest) mention of this concept for the patient",
        example=True
    )


class TimelineConcept(BaseModel):
    """An aggregated clinical concept across all mentions in patient timeline.

    Represents a concept (e.g., "Diabetes Mellitus") with all its mentions
    across the patient's documents, including first mention date and frequency.
    """

    concept_cui: str = Field(
        ...,
        description="SNOMED-CT Concept Unique Identifier",
        example="C0011849"
    )
    concept_name: str = Field(
        ...,
        description="Human-readable concept name",
        example="Diabetes Mellitus"
    )
    concept_type: str = Field(
        ...,
        description="Type of concept: 'condition', 'medication', 'procedure', 'symptom', 'lab_result'",
        example="condition"
    )
    first_mention_date: datetime = Field(
        ...,
        description="Date of the first mention of this concept"
    )
    mention_count: int = Field(
        ...,
        ge=1,
        description="Total number of times this concept was mentioned",
        example=12
    )
    mentions: List[ConceptMention] = Field(
        ...,
        description="All mentions of this concept (chronologically ordered)"
    )


class TimelineDocument(BaseModel):
    """A clinical document in the patient timeline.

    Represents a single document (clinical note, lab report, etc.) with
    metadata and associated concepts.
    """

    document_id: str = Field(
        ...,
        description="UUID of the document"
    )
    title: str = Field(
        ...,
        description="Document title or filename",
        example="Diabetes Clinic Note"
    )
    document_type: str = Field(
        ...,
        description="Type of document: 'clinical_note', 'discharge_summary', 'lab_report', etc.",
        example="clinical_note"
    )
    date: datetime = Field(
        ...,
        description="Document date (ISO 8601 format)"
    )
    author: Optional[str] = Field(
        None,
        description="Document author (if available)",
        example="Dr. Smith"
    )
    concepts: List[str] = Field(
        default_factory=list,
        description="List of concept CUIs mentioned in this document",
        example=["C0011849", "C0020538"]
    )


class DateRange(BaseModel):
    """Date range for timeline filtering.

    Represents a start and end date for filtering timeline data.
    """

    start: datetime = Field(
        ...,
        description="Start date (inclusive, ISO 8601 format)"
    )
    end: datetime = Field(
        ...,
        description="End date (inclusive, ISO 8601 format)"
    )


class TimelineFilters(BaseModel):
    """Filters for timeline data retrieval.

    Supports filtering by concepts, date range, meta-annotations, and document types.
    """

    concepts: Optional[List[str]] = Field(
        None,
        description="List of concept CUIs to filter by (AND logic)",
        example=["C0011849", "C0020538"]
    )
    date_range: Optional[DateRange] = Field(
        None,
        description="Date range to filter documents and concepts"
    )
    meta_annotations: Optional[dict] = Field(
        None,
        description="Meta-annotation filters (key-value pairs)",
        example={
            "Negation": "Affirmed",
            "Experiencer": "Patient",
            "Temporality": ["Current", "Recent"]
        }
    )
    document_types: Optional[List[str]] = Field(
        None,
        description="List of document types to include",
        example=["clinical_note", "discharge_summary"]
    )


class PatientTimeline(BaseModel):
    """Complete patient timeline with documents and concepts.

    This is the main response model for the GET /api/v1/timeline/{patient_id} endpoint.
    Contains all timeline data: documents, concepts, date range, and applied filters.
    """

    patient_id: str = Field(
        ...,
        description="UUID of the patient"
    )
    documents: List[TimelineDocument] = Field(
        ...,
        description="List of documents in chronological order"
    )
    concepts: List[TimelineConcept] = Field(
        ...,
        description="List of aggregated concepts across all documents"
    )
    date_range: DateRange = Field(
        ...,
        description="Actual date range covered by the timeline (min/max document dates)"
    )
    filters_applied: TimelineFilters = Field(
        ...,
        description="Filters that were applied to generate this timeline"
    )


class TimelineFilterPreset(BaseModel):
    """A saved filter preset for timeline view.

    Allows users to save commonly used filter combinations for quick reuse.
    """

    id: Optional[UUID] = Field(
        None,
        description="UUID of the filter preset (null for new presets)"
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user who created this preset"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the filter preset",
        example="Diabetes Management View"
    )
    description: Optional[str] = Field(
        None,
        description="Description of what this filter preset shows",
        example="Timeline filtered for diabetes-related concepts (diagnosis, medications, lab results)"
    )
    filters: TimelineFilters = Field(
        ...,
        description="The filter configuration"
    )
    is_default: bool = Field(
        False,
        description="Whether this is the user's default filter preset"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="When this preset was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When this preset was last updated"
    )


class TimelineExportRequest(BaseModel):
    """Request to export a patient timeline.

    Supports exporting to PDF, FHIR R4, or JSON formats with optional filters.
    """

    format: str = Field(
        ...,
        description="Export format: 'pdf', 'fhir', or 'json'",
        example="pdf"
    )
    filters: Optional[dict] = Field(
        None,
        description="Filters to apply before export (dict matching TimelineFilters structure)"
    )
    options: Optional[dict] = Field(
        None,
        description="Format-specific options (watermark, de_identified, etc.)",
        example={
            "watermark": True,
            "de_identified": False
        }
    )


class TimelineExportResponse(BaseModel):
    """Response after creating a timeline export.

    Supports both synchronous (data inline) and asynchronous (download URL) exports.
    """

    export_id: str = Field(
        ...,
        description="UUID of the export"
    )
    status: str = Field(
        ...,
        description="Export status: 'completed', 'processing', 'failed'",
        example="completed"
    )
    format: str = Field(
        ...,
        description="Export format: 'pdf', 'fhir', or 'json'"
    )
    content_type: str = Field(
        ...,
        description="MIME type of the export",
        example="application/pdf"
    )
    data: Optional[Any] = Field(
        None,
        description="Exported data (inline for sync exports). Base64-encoded for PDF, dict for JSON/FHIR."
    )
    download_url: Optional[str] = Field(
        None,
        description="URL to download the exported file (async exports only)",
        example="/api/v1/timeline/exports/export-789/download"
    )
    created_at: datetime = Field(
        ...,
        description="When the export was created"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="When this export will be automatically deleted (30 days for async exports)"
    )


# ========================================
# POST Timeline Endpoint Schemas (Task #001)
# ========================================


class EventType(str, Enum):
    """Event types for timeline filtering.

    Represents different types of clinical events that can appear in a timeline.
    """
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"
    MEDICATION = "medication"
    LAB = "lab"
    VISIT = "visit"


class DateRangeSchema(BaseModel):
    """Date range for timeline filtering (POST endpoint).

    Similar to DateRange but with explicit naming for POST request schema.
    """

    start: datetime = Field(
        ...,
        description="Start date (inclusive, ISO 8601 format)"
    )
    end: datetime = Field(
        ...,
        description="End date (inclusive, ISO 8601 format)"
    )


class TimelineRequest(BaseModel):
    """Request schema for POST /api/v1/timeline/patient/{patient_id}.

    Supports filtering by date range, event types, specialty, and pagination.
    """

    date_range: DateRangeSchema = Field(
        ...,
        description="Date range to filter events"
    )
    event_types: List[EventType] = Field(
        default=[EventType.DIAGNOSIS, EventType.PROCEDURE, EventType.MEDICATION, EventType.LAB, EventType.VISIT],
        description="Types of events to include in timeline"
    )
    specialty_filter: Optional[str] = Field(
        None,
        description="Filter events by medical specialty (e.g., 'cardiology', 'neurology')",
        example="cardiology"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)",
        example=1
    )
    page_size: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Number of events per page (max 10,000)",
        example=1000
    )


class QueryMetadata(BaseModel):
    """Metadata about the query execution.

    Provides performance and pagination information about the query results.
    """

    query_time_ms: float = Field(
        ...,
        ge=0,
        description="Query execution time in milliseconds",
        example=245.3
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages available",
        example=5
    )
    current_page: int = Field(
        ...,
        ge=1,
        description="Current page number",
        example=1
    )
    page_size: int = Field(
        ...,
        ge=1,
        description="Events per page",
        example=1000
    )
    filters_applied: dict = Field(
        ...,
        description="Filters that were applied to this query",
        example={
            "date_range": {"start": "2023-01-01", "end": "2023-12-31"},
            "event_types": ["diagnosis", "medication"],
            "specialty_filter": "cardiology"
        }
    )


class TimelineEvent(BaseModel):
    """A single clinical event in the patient timeline.

    Represents one event (diagnosis, procedure, etc.) with associated metadata.
    """

    id: str = Field(
        ...,
        description="Unique event identifier",
        example="event-abc123"
    )
    event_type: EventType = Field(
        ...,
        description="Type of clinical event"
    )
    date: datetime = Field(
        ...,
        description="Date of the event (ISO 8601 format)"
    )
    title: str = Field(
        ...,
        description="Event title or description",
        example="Type 2 Diabetes Mellitus diagnosis"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the event",
        example="Patient diagnosed with Type 2 Diabetes. HbA1c 8.5%. Started on Metformin 500mg BID."
    )
    specialty: Optional[str] = Field(
        None,
        description="Medical specialty associated with this event",
        example="endocrinology"
    )
    provider: Optional[str] = Field(
        None,
        description="Healthcare provider name",
        example="Dr. Jane Smith"
    )
    location: Optional[str] = Field(
        None,
        description="Location where event occurred",
        example="Main Hospital - Endocrinology Clinic"
    )
    concept_cui: Optional[str] = Field(
        None,
        description="SNOMED-CT Concept Unique Identifier (if applicable)",
        example="C0011849"
    )
    concept_name: Optional[str] = Field(
        None,
        description="Human-readable concept name (if applicable)",
        example="Diabetes Mellitus"
    )


class TimelineResponse(BaseModel):
    """Response schema for POST /api/v1/timeline/patient/{patient_id}.

    Contains patient timeline events with pagination and metadata.
    """

    patient_id: str = Field(
        ...,
        description="UUID of the patient"
    )
    patient_name: Optional[str] = Field(
        None,
        description="Patient's full name (None when de-identified)",
        example="John Doe"
    )
    date_range: DateRangeSchema = Field(
        ...,
        description="Date range that was queried"
    )
    events: List[TimelineEvent] = Field(
        ...,
        description="List of clinical events in chronological order"
    )
    total_events: int = Field(
        ...,
        ge=0,
        description="Total number of events matching the filter criteria",
        example=1250
    )
    metadata: QueryMetadata = Field(
        ...,
        description="Query execution metadata (performance, pagination)"
    )
