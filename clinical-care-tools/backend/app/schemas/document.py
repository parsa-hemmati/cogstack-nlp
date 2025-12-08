"""
Pydantic schemas for Document API endpoints.

Schemas:
- DocumentUploadResponse: Response after uploading new document
- DocumentDuplicateResponse: Response when duplicate document detected
- DocumentResponse: Document data in responses
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class DocumentUploadResponse(BaseModel):
    """Schema for successful document upload response."""

    document_id: UUID = Field(
        ...,
        description="Unique document identifier (UUID)"
    )
    status: str = Field(
        ...,
        description="Processing status (pending, processing, completed, failed)"
    )
    filename: str = Field(
        ...,
        description="Original filename"
    )
    content_type: str = Field(
        ...,
        description="MIME type (e.g., application/rtf)"
    )
    file_size: int = Field(
        ...,
        description="File size in bytes (original, before encryption)"
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 hash of content (for deduplication)"
    )
    created_at: datetime = Field(
        ...,
        description="Upload timestamp"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "document_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "pending",
                    "filename": "patient_notes.rtf",
                    "content_type": "application/rtf",
                    "file_size": 51200,
                    "content_hash": "abc123def456...",
                    "created_at": "2025-01-08T12:34:56"
                }
            ]
        }
    }


class DocumentDuplicateResponse(BaseModel):
    """Schema for duplicate document detection response."""

    document_id: UUID = Field(
        ...,
        description="Existing document identifier (UUID)"
    )
    status: str = Field(
        default="duplicate",
        description="Status indicating duplicate"
    )
    message: str = Field(
        ...,
        description="Explanation of duplicate detection"
    )
    filename: str = Field(
        ...,
        description="Original filename of existing document"
    )
    created_at: datetime = Field(
        ...,
        description="Original upload timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "duplicate",
                    "message": "Document already exists with same content",
                    "filename": "patient_notes.rtf",
                    "created_at": "2025-01-08T12:34:56"
                }
            ]
        }
    }


class DocumentResponse(BaseModel):
    """Schema for document data in responses."""

    id: UUID
    filename: str
    content_type: str
    file_size: int
    content_hash: str
    uploaded_by: UUID
    project_id: UUID
    processing_status: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "filename": "clinical_notes.rtf",
                    "content_type": "application/rtf",
                    "file_size": 51200,
                    "content_hash": "abc123def456...",
                    "uploaded_by": "550e8400-e29b-41d4-a716-446655440001",
                    "project_id": "550e8400-e29b-41d4-a716-446655440002",
                    "processing_status": "pending",
                    "created_at": "2025-01-08T12:34:56"
                }
            ]
        }
    }
