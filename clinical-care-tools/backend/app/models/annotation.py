"""Annotation model for storing NLP-extracted clinical concepts."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Annotation(Base):
    """
    Annotation model for NLP-extracted clinical concepts.

    Stores concepts extracted by MedCAT with meta-annotations.

    Attributes:
        document_id: Foreign key to document
        start_char: Character offset where concept starts
        end_char: Character offset where concept ends
        text: Actual text span that was annotated
        cui: SNOMED-CT/UMLS Concept Unique Identifier
        preferred_name: Preferred term for the concept
        concept_type: Type of concept (condition, medication, procedure)
        negation: Negation status (Affirmed, Negated)
        temporality: Temporal status (Current, Past, Future, Hypothetical)
        experiencer: Who experiences this (Patient, Family, Other)
        certainty: Certainty level (Certain, Uncertain)
        confidence: MedCAT confidence score (0.0-1.0)
    """

    __tablename__ = "annotations"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Annotation span
    start_char: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Start character position in document",
    )

    end_char: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="End character position in document",
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Actual text span that was annotated",
    )

    # Concept information
    cui: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="SNOMED-CT/UMLS Concept Unique Identifier",
    )

    preferred_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Preferred term for the concept",
    )

    concept_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: condition, medication, procedure, etc.",
    )

    # Meta-annotations (from MedCAT)
    negation: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Affirmed or Negated",
    )

    temporality: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Current, Past, Future, or Hypothetical",
    )

    experiencer: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Patient, Family, or Other",
    )

    certainty: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Certain or Uncertain",
    )

    # Confidence score
    confidence: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="MedCAT confidence score (0.0-1.0)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    document = relationship("Document", back_populates="annotations")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Annotation(id='{self.id}', cui='{self.cui}', name='{self.preferred_name}')>"
