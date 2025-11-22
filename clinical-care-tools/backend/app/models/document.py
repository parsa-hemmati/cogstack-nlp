"""
Document Model

Represents encrypted clinical documents stored in the system.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, LargeBinary, Integer, ARRAY, func, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import Base


class Document(Base):
    """
    Clinical document model for encrypted RTF/PDF storage.

    Documents are encrypted at rest with AES-256. The encryption key is stored
    separately in a Key Management System (KMS) or Hardware Security Module (HSM).

    Attributes:
        id: Unique document identifier (UUID)
        project_id: Reference to project
        filename: Original filename
        file_type: File type (rtf, txt, docx, pdf)
        file_size: File size in bytes
        content: Encrypted document content (BYTEA)
        content_hash: SHA-256 hash of unencrypted content (for deduplication)
        encryption_key_id: Reference to encryption key in KMS
        document_type: Type of clinical document (clinical_letter, discharge_summary, etc.)
        document_date: Date on the document itself
        author: Document author if available
        medcat_status: NLP processing status (pending, processing, complete, failed)
        medcat_processed_at: When MedCAT processing completed
        medcat_error: Error message if processing failed
        contains_phi: Whether document contains PHI (always TRUE for clinical documents)
        phi_types: Array of PHI types found (NHS_NUMBER, NAME, ADDRESS, DOB, etc.)
        uploaded_by: User who uploaded document
        uploaded_at: When document was uploaded
        updated_at: When document was last updated

    Relationships:
        project: Reference to Project
        uploader: Reference to User who uploaded
        extracted_entities: Entities extracted from this document
    """

    __tablename__ = "documents"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    project_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    uploaded_by: Mapped[UUID] = mapped_column(nullable=False, index=True)

    # File Storage
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="rtf",
        comment="'rtf', 'txt', 'docx', 'pdf'",
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, comment="AES-256 encrypted content")
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash for deduplication",
    )
    encryption_key_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Reference to encryption key in KMS/HSM (not stored in DB)",
    )

    # Document Metadata
    document_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="'clinical_letter', 'discharge_summary', 'lab_report', etc.",
    )
    document_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # MedCAT NLP Processing Status
    medcat_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="'pending', 'processing', 'complete', 'failed'",
    )
    medcat_processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    medcat_error: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # PHI Tracking
    contains_phi: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="Always TRUE for clinical documents",
    )
    phi_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        default=lambda: ["NHS_NUMBER", "NAME", "ADDRESS", "DOB"],
        comment="Array of PHI types found in document",
    )

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="documents",
        foreign_keys=[project_id],
    )

    uploader: Mapped["User"] = relationship(
        "User",
        back_populates="documents_uploaded",
        foreign_keys=[uploaded_by],
    )

    extracted_entities: Mapped[list["ExtractedEntity"]] = relationship(
        "ExtractedEntity",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_documents_project", "project_id"),
        Index("idx_documents_content_hash", "content_hash"),
        Index("idx_documents_medcat_status", "medcat_status"),
        Index("idx_documents_uploaded_by", "uploaded_by"),
        Index("idx_documents_uploaded_at", "uploaded_at", postgresql_using="desc"),
        Index("idx_documents_document_type", "document_type"),
    )

    def __repr__(self) -> str:
        """String representation of Document."""
        return (
            f"<Document(id={self.id}, filename={self.filename}, "
            f"medcat_status={self.medcat_status}, file_size={self.file_size})>"
        )
