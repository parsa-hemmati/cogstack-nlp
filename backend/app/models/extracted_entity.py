"""
ExtractedEntity model for storing PHI and clinical entities.

Stores medical concepts and PHI extracted by MedCAT with meta-annotations
for filtering (Negation, Temporality, Experiencer, Certainty).
"""
import enum
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EntityType(str, enum.Enum):
    """Entity type: clinical concept or PHI category."""

    # Clinical entities
    CLINICAL = "clinical"  # SNOMED-CT or UMLS clinical concept

    # PHI categories (for de-identification)
    PHI_NAME = "phi_name"  # Patient name
    PHI_NHS_NUMBER = "phi_nhs_number"  # NHS number (UK)
    PHI_DOB = "phi_dob"  # Date of birth
    PHI_ADDRESS = "phi_address"  # Address


class ExtractedEntity(Base):
    """
    Extracted entity model for clinical concepts and PHI.

    Stores entities extracted by MedCAT from clinical documents:
    - Clinical concepts: diagnoses, symptoms, medications, procedures (SNOMED-CT)
    - PHI: patient identifiers for de-identification

    Attributes:
        id: Unique entity identifier (UUID)
        document_id: Source document (foreign key)
        patient_id: Aggregated patient record (nullable, for linkage)
        entity_type: clinical, phi_name, phi_nhs_number, phi_dob, phi_address
        cui: SNOMED-CT or UMLS Concept Unique Identifier (null for PHI)
        pretty_name: Human-readable concept name (e.g., "Diabetes mellitus")
        start_char: Character offset where entity starts in document
        end_char: Character offset where entity ends
        accuracy: MedCAT confidence score (0.0-1.0)
        meta_anns: Meta-annotations (JSONB):
            - Negation: Affirmed | Negated (e.g., "no diabetes")
            - Temporality: Current | Historical | Future | Hypothetical
            - Experiencer: Patient | Family | Other (e.g., "family history of diabetes")
            - Certainty: Definite | Probable | Possible | Unlikely
        created_at: Extraction timestamp

    Indexes:
        - document_id (foreign key, frequent joins)
        - patient_id (foreign key, aggregation queries)
        - entity_type (filter PHI vs clinical)
        - cui (concept-based searches)

    Example:
        >>> entity = ExtractedEntity(
        >>>     document_id=doc.id,
        >>>     entity_type=EntityType.CLINICAL,
        >>>     cui="C0011849",
        >>>     pretty_name="Diabetes mellitus",
        >>>     start_char=10,
        >>>     end_char=28,
        >>>     accuracy=0.95,
        >>>     meta_anns={"Negation": "Affirmed", "Experiencer": "Patient"}
        >>> )
    """

    __tablename__ = "extracted_entities"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    patient_id = Column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )  # Future: ForeignKey("patients.id")
    entity_type = Column(Enum(EntityType), nullable=False, index=True)

    # Clinical concept fields (null for PHI)
    cui = Column(String(20), nullable=True, index=True)  # SNOMED-CT or UMLS CUI

    # Entity text
    pretty_name = Column(String(500), nullable=False)  # Human-readable name

    # Position in document
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)

    # Confidence
    accuracy = Column(Float, nullable=True)  # MedCAT confidence (0.0-1.0)

    # Meta-annotations (JSONB for flexibility)
    meta_anns = Column(JSONB, nullable=True, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", foreign_keys=[document_id], backref="entities")
    # patient relationship will be added when Patient model is created

    # Indexes for performance
    __table_args__ = (
        Index("ix_extracted_entities_document_id", "document_id"),
        Index("ix_extracted_entities_patient_id", "patient_id"),
        Index("ix_extracted_entities_entity_type", "entity_type"),
        Index("ix_extracted_entities_cui", "cui"),
        # Composite index for common query: get entities for document by type
        Index(
            "ix_extracted_entities_doc_type", "document_id", "entity_type"
        ),
    )

    def __repr__(self):
        return (
            f"<ExtractedEntity(id={self.id}, type={self.entity_type.value}, "
            f"cui={self.cui}, name={self.pretty_name[:30]})>"
        )

    def is_phi(self) -> bool:
        """Check if entity is PHI (Protected Health Information)."""
        return self.entity_type != EntityType.CLINICAL

    def is_clinical(self) -> bool:
        """Check if entity is a clinical concept."""
        return self.entity_type == EntityType.CLINICAL

    def is_negated(self) -> bool:
        """Check if entity is negated (e.g., 'no diabetes')."""
        if not self.meta_anns:
            return False
        return self.meta_anns.get("Negation") == "Negated"

    def is_family_history(self) -> bool:
        """Check if entity is family history (not patient's condition)."""
        if not self.meta_anns:
            return False
        return self.meta_anns.get("Experiencer") in ["Family", "Other"]

    def is_active_patient_condition(self) -> bool:
        """
        Check if entity represents an active patient condition.

        Filters out:
        - Negated mentions (e.g., "no diabetes")
        - Family history (e.g., "father has diabetes")
        - Historical conditions (e.g., "history of diabetes in 1990")
        - Hypothetical scenarios (e.g., "if patient develops diabetes")

        Returns:
            True if entity is an affirmed, current, patient condition
        """
        if not self.meta_anns:
            return True  # Conservative: include if no meta-annotations

        # Check Negation
        if self.meta_anns.get("Negation") == "Negated":
            return False

        # Check Experiencer
        if self.meta_anns.get("Experiencer") in ["Family", "Other"]:
            return False

        # Check Temporality (current conditions only)
        if self.meta_anns.get("Temporality") in ["Historical", "Hypothetical"]:
            return False

        return True
