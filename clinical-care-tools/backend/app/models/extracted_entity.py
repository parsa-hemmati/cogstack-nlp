"""
Extracted Entity Model

Represents medical entities extracted from documents by MedCAT NLP.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Float, Integer, func, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import Base


class ExtractedEntity(Base):
    """
    Medical entity extracted from clinical documents by MedCAT.

    Contains both the raw extraction from MedCAT (CUI, term, position) and
    additional processing (meta-annotations, PHI classification, confidence).

    Attributes:
        id: Unique entity identifier (UUID)
        document_id: Reference to source document
        project_id: Reference to project (denormalized for query efficiency)
        cui: UMLS/SNOMED-CT concept identifier (e.g., "C0004238" for Atrial Flutter)
        concept_name: Human-readable concept name
        source_value: Actual text from document
        start_char: Character position in document
        end_char: Character position in document
        confidence: MedCAT confidence score (0.0 - 1.0)
        meta_annotations: Meta-annotation results as JSON
        entity_type: Classification (PERSON, NHS_NUMBER, DATE, ADDRESS, CONDITION, etc.)
        is_phi: Whether this is identifiable PHI
        phi_category: PHI classification (DIRECT_IDENTIFIER, QUASI_IDENTIFIER, CLINICAL_DATA)
        structured_data: Type-specific structured fields as JSON
        extracted_at: When extraction occurred
        medcat_version: Version of MedCAT used

    Relationships:
        document: Reference to Document
        project: Reference to Project
    """

    __tablename__ = "extracted_entities"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    document_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    # MedCAT Extraction Metadata
    cui: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="UMLS/SNOMED-CT concept ID (e.g., 'C0004238')",
    )
    concept_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Human-readable concept name",
    )
    source_value: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="Actual text from document",
    )

    # Document Position
    start_char: Mapped[int] = mapped_column(Integer, nullable=False)
    end_char: Mapped[int] = mapped_column(Integer, nullable=False)

    # Confidence and Quality
    confidence: Mapped[float] = mapped_column(Float, nullable=False, comment="MedCAT confidence (0.0 - 1.0)")

    # Meta-Annotations (from MetaCAT)
    meta_annotations: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment='{"Negation": "Affirmed", "Temporality": "Current", "Experiencer": "Patient", "Certainty": "Confirmed"}',
    )

    # Entity Classification
    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="'PERSON', 'NHS_NUMBER', 'DATE', 'ADDRESS', 'CONDITION', 'MEDICATION', etc.",
    )

    # PHI Classification
    is_phi: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
        comment="TRUE if this is identifiable PHI",
    )
    phi_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="'DIRECT_IDENTIFIER', 'QUASI_IDENTIFIER', 'CLINICAL_DATA'",
    )

    # Type-Specific Structured Data
    structured_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Type-specific fields: nhs_number, first_name, last_name, etc.",
    )

    # Processing Metadata
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    medcat_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Version of MedCAT used for extraction",
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="extracted_entities",
        foreign_keys=[document_id],
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="extracted_entities",
        foreign_keys=[project_id],
    )

    # Indexes
    __table_args__ = (
        Index("idx_extracted_entities_document", "document_id"),
        Index("idx_extracted_entities_project", "project_id"),
        Index("idx_extracted_entities_cui", "cui"),
        Index("idx_extracted_entities_entity_type", "entity_type"),
        Index("idx_extracted_entities_is_phi", "is_phi"),
        Index("idx_extracted_entities_structured_data_gin", "structured_data", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation of ExtractedEntity."""
        return (
            f"<ExtractedEntity(id={self.id}, cui={self.cui}, concept={self.concept_name}, "
            f"type={self.entity_type}, confidence={self.confidence:.2f})>"
        )
