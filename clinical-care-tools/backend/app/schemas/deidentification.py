"""De-identification Schemas (Sprint 4, Phase 4.2)"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum
from uuid import UUID

from app.schemas.phi import DetectedEntity


class RedactionMode(str, Enum):
    """De-identification redaction modes"""
    MASK = "mask"  # Replace with [REDACTED] or ***
    SURROGATE = "surrogate"  # Replace with surrogates (Patient-A, Date-1, etc.)
    REMOVE = "remove"  # Remove entirely


class DeidentificationPreviewRequest(BaseModel):
    """Request for de-identification preview"""
    document_ids: List[UUID] = Field(..., min_length=1, max_length=100, description="Document IDs to preview")
    redaction_mode: RedactionMode = Field(..., description="How to redact PHI")

    class Config:
        json_schema_extra = {
            "example": {
                "document_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "redaction_mode": "surrogate"
            }
        }


class EntityWithSurrogate(DetectedEntity):
    """Detected entity with surrogate value"""
    surrogate: Optional[str] = Field(None, description="Surrogate value (if surrogate mode)")


class DeidentificationPreview(BaseModel):
    """Preview of de-identified document"""
    document_id: UUID = Field(..., description="Original document ID")
    original_text: str = Field(..., description="Original document text")
    entities: List[EntityWithSurrogate] = Field(default_factory=list, description="Detected PHI entities")
    redacted_text: str = Field(..., description="Preview of redacted text")
    entities_count: int = Field(..., ge=0, description="Number of entities to be redacted")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "original_text": "Patient John Doe (DOB: 01/15/1980) presents with chest pain.",
                "entities": [
                    {
                        "text": "John Doe",
                        "label": "PERSON",
                        "start": 8,
                        "end": 16,
                        "confidence": 0.98,
                        "surrogate": "Patient-A"
                    }
                ],
                "redacted_text": "Patient [Patient-A] (DOB: [01/15/19XX]) presents with chest pain.",
                "entities_count": 2
            }
        }


class DeidentificationPreviewResponse(BaseModel):
    """Response from preview endpoint"""
    previews: List[DeidentificationPreview] = Field(default_factory=list, description="Document previews")
    total_documents: int = Field(..., ge=0, description="Total documents previewed")


class DeidentificationApplyRequest(BaseModel):
    """Request to apply de-identification"""
    document_ids: List[UUID] = Field(..., min_length=1, max_length=1000, description="Document IDs to de-identify")
    redaction_mode: RedactionMode = Field(..., description="How to redact PHI")
    store_mapping: bool = Field(True, description="Store re-identification mapping?")

    class Config:
        json_schema_extra = {
            "example": {
                "document_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "redaction_mode": "surrogate",
                "store_mapping": True
            }
        }


class DeidentifiedDocumentResult(BaseModel):
    """Result of de-identifying a single document"""
    original_document_id: UUID = Field(..., description="Original document ID")
    deidentified_document_id: UUID = Field(..., description="De-identified document ID")
    redaction_mode: RedactionMode = Field(..., description="Redaction mode used")
    entities_redacted: int = Field(..., ge=0, description="Number of entities redacted")
    mapping_id: Optional[UUID] = Field(None, description="Re-identification mapping ID")
    audit_log_id: UUID = Field(..., description="Audit log entry ID")

    class Config:
        json_schema_extra = {
            "example": {
                "original_document_id": "123e4567-e89b-12d3-a456-426614174000",
                "deidentified_document_id": "987fcdeb-51a3-42e7-9876-543210987654",
                "redaction_mode": "surrogate",
                "entities_redacted": 5,
                "mapping_id": "456e7890-a12b-34c5-d678-901234567890",
                "audit_log_id": "789abcde-f012-3456-7890-abcdef012345"
            }
        }


class DeidentificationApplyResponse(BaseModel):
    """Response from apply endpoint"""
    deidentified_documents: List[DeidentifiedDocumentResult] = Field(
        default_factory=list,
        description="Results for each document"
    )
    total_documents: int = Field(..., ge=0, description="Total documents processed")
    total_entities_redacted: int = Field(..., ge=0, description="Total entities redacted")


class BatchDeidentificationRequest(BaseModel):
    """Request for batch de-identification"""
    document_ids: List[UUID] = Field(..., min_length=1, max_length=10000, description="Document IDs (up to 10,000)")
    redaction_mode: RedactionMode = Field(..., description="How to redact PHI")
    store_mapping: bool = Field(True, description="Store re-identification mapping?")

    class Config:
        json_schema_extra = {
            "example": {
                "document_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "redaction_mode": "surrogate",
                "store_mapping": True
            }
        }


class BatchDeidentificationResponse(BaseModel):
    """Response from batch de-identification"""
    job_id: UUID = Field(..., description="Batch job ID for status tracking")
    status: str = Field("pending", description="Job status")
    total_documents: int = Field(..., ge=0, description="Total documents to process")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time (ISO format)")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "111e2222-a33b-44c5-d666-777788889999",
                "status": "pending",
                "total_documents": 1000,
                "estimated_completion": "2023-11-17T11:30:00Z"
            }
        }
