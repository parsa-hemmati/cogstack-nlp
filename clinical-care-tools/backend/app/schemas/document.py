"""Pydantic schemas for document-related requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.document import DocumentStatus, DocumentType


class DocumentBase(BaseModel):
    """Base document schema."""

    document_type: DocumentType
    document_date: datetime
    author: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""

    patient_id: UUID
    content: str = Field(..., description="Full document text content")


class DocumentUpdate(BaseModel):
    """Schema for updating document."""

    document_type: Optional[DocumentType] = None
    document_date: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: UUID
    patient_id: UUID
    elasticsearch_id: Optional[str]
    status: DocumentStatus
    nlp_processed: bool
    nlp_processed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class DocumentWithContent(DocumentResponse):
    """Schema for document with full content."""

    content: str
    entities: list[dict] = []


class DocumentProcessRequest(BaseModel):
    """Schema for document processing request."""

    document_id: UUID
    force_reprocess: bool = Field(default=False, description="Force reprocessing if already processed")
