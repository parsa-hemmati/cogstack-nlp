"""
Document schemas for API requests/responses.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response from document upload endpoint."""

    document_id: UUID = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_hash: str = Field(..., description="SHA-256 content hash")
    status: str = Field(..., description="Processing status (pending/processing/completed/failed)")
    is_duplicate: bool = Field(..., description="Whether document is a duplicate")
    message: Optional[str] = Field(None, description="Status message")
    created_at: datetime = Field(..., description="Upload timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "clinical_note_001.rtf",
                "file_size": 45678,
                "content_hash": "abc123...",
                "status": "pending",
                "is_duplicate": False,
                "message": "Document uploaded successfully",
                "created_at": "2025-11-18T12:00:00Z",
            }
        }


class DocumentInfo(BaseModel):
    """Document information for list/detail endpoints."""

    id: UUID
    filename: str
    content_type: str
    file_size: int
    content_hash: str
    processing_status: str
    uploaded_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True
