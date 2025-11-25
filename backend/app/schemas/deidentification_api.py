"""
De-identification API Schemas.

Pydantic models for de-identification API requests and responses.
"""
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.phi_entity import PHIEntity


class DeidentifyRequest(BaseModel):
    """
    Request to de-identify a single note.

    Attributes:
        text: Clinical text to de-identify
        method: De-identification method (removal, replacement, generalization)
        return_entities: Include removed PHI entities in response
    """

    text: str = Field(
        ...,
        min_length=1,
        description="Clinical text to de-identify"
    )
    method: str = Field(
        default="removal",
        description="De-identification method"
    )
    return_entities: bool = Field(
        default=True,
        description="Include removed PHI entities in response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Patient John Doe was admitted on 01/15/2024",
                "method": "removal",
                "return_entities": True
            }
        }


class DeidentifyResponse(BaseModel):
    """
    Response from single note de-identification.

    Attributes:
        deidentified_text: De-identified clinical text
        entities_removed: PHI entities that were removed (if requested)
        method_used: Method that was applied
        confidence_score: Average confidence of detected PHI
        review_required: Whether manual review is recommended
        processing_time_ms: Processing time in milliseconds
    """

    deidentified_text: str = Field(
        ...,
        description="De-identified clinical text"
    )
    entities_removed: Optional[List[PHIEntity]] = Field(
        default=None,
        description="PHI entities removed (if return_entities=True)"
    )
    method_used: str = Field(
        ...,
        description="De-identification method applied"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average PHI detection confidence"
    )
    review_required: bool = Field(
        ...,
        description="Manual review recommended"
    )
    processing_time_ms: float = Field(
        ...,
        description="Processing time in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "deidentified_text": "Patient [NAME] was admitted on [DATE]",
                "entities_removed": [
                    {
                        "entity_type": "NAME",
                        "text": "John Doe",
                        "start": 8,
                        "end": 16,
                        "confidence": 0.95,
                        "cui": None
                    }
                ],
                "method_used": "removal",
                "confidence_score": 0.935,
                "review_required": False,
                "processing_time_ms": 450.5
            }
        }


class BatchNote(BaseModel):
    """
    Single note in a batch de-identification request.

    Attributes:
        id: Unique identifier for this note
        text: Clinical text to de-identify
    """

    id: str = Field(
        ...,
        description="Unique identifier for this note"
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Clinical text to de-identify"
    )


class DeidentifyBatchRequest(BaseModel):
    """
    Request to de-identify multiple notes in batch.

    Attributes:
        notes: List of notes to de-identify
        method: De-identification method
        notify_email: Email address for completion notification
    """

    notes: List[BatchNote] = Field(
        ...,
        min_items=1,
        description="List of notes to de-identify"
    )
    method: str = Field(
        default="removal",
        description="De-identification method"
    )
    notify_email: Optional[str] = Field(
        default=None,
        description="Email for completion notification"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "notes": [
                    {"id": "note_1", "text": "Patient A has diabetes"},
                    {"id": "note_2", "text": "Patient B has hypertension"}
                ],
                "method": "replacement",
                "notify_email": "researcher@example.com"
            }
        }


class DeidentifyBatchResponse(BaseModel):
    """
    Response from batch de-identification request.

    Attributes:
        job_id: Unique identifier for this batch job
        status: Current job status
        total_notes: Total number of notes in this batch
        created_at: When the job was created
        estimated_completion: Estimated completion time
    """

    job_id: UUID = Field(
        ...,
        description="Unique identifier for this batch job"
    )
    status: str = Field(
        ...,
        description="Job status (pending, processing, completed, failed, cancelled)"
    )
    total_notes: int = Field(
        ...,
        ge=1,
        description="Total number of notes in this batch"
    )
    created_at: datetime = Field(
        ...,
        description="When the job was created"
    )
    estimated_completion: datetime = Field(
        ...,
        description="Estimated completion time"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "total_notes": 1000,
                "created_at": "2024-01-15T10:30:00Z",
                "estimated_completion": "2024-01-15T11:00:00Z"
            }
        }


class JobStatus(BaseModel):
    """
    Status of a batch de-identification job.

    Attributes:
        job_id: Unique identifier for this job
        status: Current status
        total_notes: Total notes in batch
        processed_notes: Notes processed so far
        progress_percentage: Progress as percentage (0-100)
        created_at: When job was created
        updated_at: Last status update
        estimated_completion: Estimated completion time
        errors: List of error messages for failed notes
    """

    job_id: UUID = Field(
        ...,
        description="Unique identifier for this job"
    )
    status: str = Field(
        ...,
        description="Job status"
    )
    total_notes: int = Field(
        ...,
        description="Total notes in batch"
    )
    processed_notes: int = Field(
        ...,
        description="Notes processed so far"
    )
    progress_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Progress percentage"
    )
    created_at: datetime = Field(
        ...,
        description="When job was created"
    )
    updated_at: datetime = Field(
        ...,
        description="Last status update"
    )
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages for failed notes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "total_notes": 1000,
                "processed_notes": 450,
                "progress_percentage": 45.0,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:45:00Z",
                "estimated_completion": "2024-01-15T11:00:00Z",
                "errors": []
            }
        }
