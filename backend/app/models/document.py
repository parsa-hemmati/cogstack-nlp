"""
Document model for encrypted document storage.

Stores clinical documents (RTF files) with AES-256 encryption,
SHA-256 hashing for deduplication, and processing status tracking.
"""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ProcessingStatus(str, enum.Enum):
    """Document processing status."""

    PENDING = "pending"  # Uploaded, waiting for processing
    PROCESSING = "processing"  # Currently being processed by MedCAT
    COMPLETED = "completed"  # Successfully processed
    FAILED = "failed"  # Processing failed


class Document(Base):
    """
    Document model for encrypted clinical document storage.

    Attributes:
        id: Unique document identifier (UUID)
        filename: Original filename (e.g., "clinical_note_001.rtf")
        content_type: MIME type (e.g., "application/rtf")
        content_hash: SHA-256 hash for deduplication (64 hex characters)
        encrypted_content: AES-256-GCM encrypted document content (BYTEA)
        encryption_algorithm: Algorithm used (e.g., "aes-256-gcm")
        file_size: Original file size in bytes
        uploaded_by: User ID who uploaded the document
        project_id: Optional project association
        processing_status: Current processing status (pending/processing/completed/failed)
        created_at: Upload timestamp

    Indexes:
        - content_hash (for fast deduplication lookups)

    Constraints:
        - Unique constraint on content_hash (prevents duplicate storage)
    """

    __tablename__ = "documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String(255), nullable=False, index=True)
    content_type = Column(String(100), nullable=False, default="application/rtf")
    content_hash = Column(
        String(64), nullable=False, unique=True, index=True
    )  # SHA-256 hash
    encrypted_content = Column(LargeBinary, nullable=False)  # BYTEA column
    encryption_algorithm = Column(
        String(50), nullable=False, default="aes-256-gcm"
    )  # AES-256-GCM
    file_size = Column(BigInteger, nullable=False)  # Original size in bytes
    uploaded_by = Column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    project_id = Column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )  # Future: projects table
    processing_status = Column(
        Enum(ProcessingStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by], backref="uploaded_documents")

    # Indexes for performance
    __table_args__ = (
        Index("ix_documents_content_hash", "content_hash"),  # Deduplication lookup
        Index("ix_documents_processing_status", "processing_status"),  # Filter by status
        Index("ix_documents_uploaded_by", "uploaded_by"),  # Filter by uploader
        Index("ix_documents_created_at", "created_at"),  # Sort by upload time
        UniqueConstraint("content_hash", name="uq_documents_content_hash"),  # Prevent duplicates
    )

    def __repr__(self):
        return (
            f"<Document(id={self.id}, filename={self.filename}, "
            f"status={self.processing_status.value}, uploaded_by={self.uploaded_by})>"
        )
