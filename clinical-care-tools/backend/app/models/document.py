"""Document model for storing clinical documents metadata."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentType(str, PyEnum):
    """Document types."""

    CLINICAL_NOTE = "clinical_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    LAB_REPORT = "lab_report"
    RADIOLOGY_REPORT = "radiology_report"
    PATHOLOGY_REPORT = "pathology_report"
    CONSULTATION = "consultation"
    PRESCRIPTION = "prescription"
    OTHER = "other"


class DocumentStatus(str, PyEnum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """
    Document model for clinical document metadata.

    Full text content is stored in Elasticsearch.
    This model stores metadata and references.

    Attributes:
        patient_id: Foreign key to patient
        document_type: Type of clinical document
        document_date: Date of the document
        author: Document author (clinician)
        title: Document title
        elasticsearch_id: Reference to Elasticsearch document
        status: Processing status
        nlp_processed: Whether NLP processing is complete
        nlp_processed_at: Timestamp of NLP processing
        error_message: Error message if processing failed
        legal_hold: If true, document cannot be deleted per retention policy
        legal_hold_reason: Reason for legal hold (litigation, audit, etc.)
        legal_hold_by: User who placed the legal hold
        legal_hold_at: When legal hold was placed
    """

    __tablename__ = "documents"

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        nullable=False,
    )

    document_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    author: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    elasticsearch_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Reference to document in Elasticsearch",
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )

    nlp_processed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    nlp_processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Legal hold fields (for compliance/litigation holds)
    legal_hold: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
        comment="If true, document cannot be deleted per retention policy",
    )

    legal_hold_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for legal hold (e.g., litigation, audit)",
    )

    legal_hold_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="User who placed the legal hold",
    )

    legal_hold_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When legal hold was placed",
    )

    # Relationships
    patient = relationship("Patient", back_populates="documents")
    annotations = relationship(
        "Annotation",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Document(id='{self.id}', title='{self.title}', type='{self.document_type}')>"
