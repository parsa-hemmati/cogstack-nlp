"""
Document model for encrypted clinical document storage.

Stores RTF documents with AES-256 encryption, SHA-256 content hashing,
and processing status tracking for MedCAT NLP extraction.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, LargeBinary, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ProcessingStatus(str, enum.Enum):
    """Document processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """
    Document model for encrypted clinical document storage.

    Stores RTF documents with encryption for PHI protection. Content is encrypted
    using AES-256-GCM before storage. SHA-256 hash ensures deduplication and
    integrity verification.

    Attributes:
        id: Unique document identifier (UUID)
        filename: Original filename (max 255 characters)
        content_type: MIME type (e.g., "application/rtf")
        content_hash: SHA-256 hash of original content (before encryption)
        encrypted_content: AES-256-GCM encrypted content stored as BYTEA
        encryption_algorithm: Encryption algorithm used (e.g., "AES-256-GCM")
        file_size: Original file size in bytes (before encryption)
        uploaded_by: User ID who uploaded the document
        project_id: Project this document belongs to
        processing_status: NLP processing status (pending, processing, completed, failed)
        created_at: Timestamp when document was uploaded

    Relationships:
        uploaded_by: References User.id
        project_id: References Project.id (CASCADE DELETE)

    Constraints:
        - content_hash must be unique (prevents duplicate uploads)
        - content_hash is indexed for fast lookups
        - project_id CASCADE DELETE (removing project removes documents)

    Example:
        >>> import hashlib
        >>> content = b"Patient clinical notes..."
        >>> content_hash = hashlib.sha256(content).hexdigest()
        >>> doc = Document(
        ...     filename="patient_notes.rtf",
        ...     content_type="application/rtf",
        ...     content_hash=content_hash,
        ...     encrypted_content=encrypted_content,
        ...     encryption_algorithm="AES-256-GCM",
        ...     file_size=len(content),
        ...     uploaded_by=user_id,
        ...     project_id=project_id,
        ...     processing_status=ProcessingStatus.PENDING
        ... )
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File metadata
    filename = Column(String(255), nullable=False, index=True)
    content_type = Column(String(100), nullable=False)

    # Content integrity and storage
    content_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hex
    encrypted_content = Column(LargeBinary, nullable=False)  # BYTEA in PostgreSQL
    encryption_algorithm = Column(String(50), nullable=False, default="AES-256-GCM")
    file_size = Column(Integer, nullable=False)  # Original size in bytes

    # Ownership and organization
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Processing tracking
    processing_status = Column(
        SQLEnum(ProcessingStatus, native_enum=False, length=20),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.processing_status})>"
