"""
Document Schemas

Pydantic models for document upload, response, and processing.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class FileType(str, Enum):
    """Allowed file types for upload."""
    RTF = "rtf"
    TXT = "txt"
    PDF = "pdf"


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class PHICategory(str, Enum):
    """PHI classification categories."""
    DIRECT_IDENTIFIER = "DIRECT_IDENTIFIER"
    QUASI_IDENTIFIER = "QUASI_IDENTIFIER"
    CLINICAL_DATA = "CLINICAL_DATA"


class DocumentUpload(BaseModel):
    """Document upload request schema."""
    filename: str = Field(..., description="Original filename")
    file_type: FileType = Field(..., description="File type (rtf, txt, pdf)")
    content: bytes = Field(..., description="File content as bytes")
    document_type: Optional[str] = Field(None, description="Document type (clinical_letter, discharge_summary, etc.)")
    document_date: Optional[datetime] = Field(None, description="Date on the document")
    author: Optional[str] = Field(None, description="Document author")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("content")
    @classmethod
    def validate_file_size(cls, v: bytes) -> bytes:
        """Validate file size is within limits (10MB max)."""
        max_size_mb = 10
        max_size_bytes = max_size_mb * 1024 * 1024

        if len(v) > max_size_bytes:
            raise ValueError(f"File size exceeds maximum of {max_size_mb}MB")

        if len(v) == 0:
            raise ValueError("File content cannot be empty")

        return v


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: UUID
    project_id: UUID
    filename: str
    file_type: str
    file_size: int
    document_type: Optional[str] = None
    document_date: Optional[datetime] = None
    author: Optional[str] = None
    medcat_status: DocumentStatus
    medcat_processed_at: Optional[datetime] = None
    medcat_error: Optional[str] = None
    contains_phi: bool
    phi_types: List[str]
    uploaded_by: UUID
    uploaded_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """List of documents response."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class DocumentWithContent(DocumentResponse):
    """Document response with decrypted content."""
    content: str = Field(..., description="Decrypted document content")

    model_config = ConfigDict(from_attributes=True)


class DocumentProcessRequest(BaseModel):
    """Request to process document with NLP."""
    force_reprocess: bool = Field(False, description="Force reprocessing even if already processed")

    model_config = ConfigDict(from_attributes=True)


class ExtractedEntityResponse(BaseModel):
    """Extracted entity response schema."""
    id: UUID
    cui: str
    concept_name: str
    source_value: str
    start_char: int
    end_char: int
    confidence: float
    meta_annotations: Dict[str, Any]
    entity_type: str
    is_phi: bool
    phi_category: Optional[PHICategory] = None
    structured_data: Optional[Dict[str, Any]] = None
    extracted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentEntitiesResponse(BaseModel):
    """Document entities response."""
    document_id: UUID
    entities: List[ExtractedEntityResponse]
    total_entities: int
    phi_entities_count: int
    clinical_entities_count: int

    model_config = ConfigDict(from_attributes=True)


class DocumentFilter(BaseModel):
    """Document filter criteria."""
    medcat_status: Optional[DocumentStatus] = None
    document_type: Optional[str] = None
    contains_phi: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)