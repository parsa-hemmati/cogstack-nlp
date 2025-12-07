"""
Extracted Entity model for storing PHI and clinical entities.

Stores entities extracted from clinical documents by MedCAT/CogStack-ModelServe.
Includes both PHI entities (names, NHS numbers, etc.) and clinical entities (SNOMED-CT).

Meta-annotations (Negation, Temporality, Experiencer, Certainty) stored as JSONB
for flexible querying and filtering.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class EntityType(str, enum.Enum):
    """Entity type enumeration for PHI and clinical entities."""
    PHI_NAME = "phi_name"
    PHI_NHS_NUMBER = "phi_nhs_number"
    PHI_DOB = "phi_dob"
    PHI_DATE = "phi_date"
    PHI_ADDRESS = "phi_address"
    PHI_PHONE = "phi_phone"
    PHI_EMAIL = "phi_email"
    CLINICAL = "clinical"


class ExtractedEntity(Base):
    """
    Extracted Entity model for storing PHI and clinical entities.

    Stores entities extracted from clinical documents by CogStack-ModelServe (MedCAT).
    Includes both Protected Health Information (PHI) and clinical SNOMED-CT concepts.

    Meta-annotations provide contextual information:
    - Negation: Affirmed/Negated (e.g., "no diabetes" → Negated)
    - Temporality: Current/Historical/Future
    - Experiencer: Patient/Family/Other
    - Certainty: Certain/Uncertain/Hypothetical

    Attributes:
        id: Unique entity identifier (UUID)
        document_id: Document this entity was extracted from
        patient_id: Patient this entity belongs to (nullable, set during aggregation)
        entity_type: Type of entity (PHI or clinical)
        cui: Concept Unique Identifier (SNOMED-CT, UMLS, or PHI-*)
        pretty_name: Human-readable entity text
        start_char: Character position in document (start)
        end_char: Character position in document (end)
        accuracy: Model confidence score (0.0-1.0)
        meta_anns: Meta-annotations as JSONB (Negation, Temporality, etc.)
        created_at: Extraction timestamp

    Relationships:
        document: References Document.id
        patient: References Patient.id (nullable)

    Indexes:
        - document_id: For retrieving all entities from a document
        - patient_id: For retrieving all entities for a patient
        - entity_type: For filtering PHI vs clinical entities

    Example:
        >>> # PHI entity
        >>> entity = ExtractedEntity(
        ...     document_id=doc_id,
        ...     entity_type=EntityType.PHI_NAME,
        ...     cui="PHI-NAME",
        ...     pretty_name="John Doe",
        ...     start_char=8,
        ...     end_char=16,
        ...     accuracy=0.98,
        ...     meta_anns={
        ...         "Negation": {"value": "Affirmed", "confidence": 0.95}
        ...     }
        ... )
        >>>
        >>> # Clinical entity
        >>> entity = ExtractedEntity(
        ...     document_id=doc_id,
        ...     patient_id=patient_id,
        ...     entity_type=EntityType.CLINICAL,
        ...     cui="C0011849",
        ...     pretty_name="Diabetes Mellitus",
        ...     start_char=0,
        ...     end_char=17,
        ...     accuracy=0.92,
        ...     meta_anns={
        ...         "Negation": {"value": "Affirmed", "confidence": 0.96},
        ...         "Temporality": {"value": "Current", "confidence": 0.89},
        ...         "Experiencer": {"value": "Patient", "confidence": 0.98},
        ...         "Certainty": {"value": "Certain", "confidence": 0.94}
        ...     }
        ... )
    """

    __tablename__ = "extracted_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationships
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,  # Set during patient aggregation
        index=True
    )

    # Entity classification
    entity_type = Column(
        SQLEnum(EntityType, native_enum=False, length=20),
        nullable=False,
        index=True
    )

    # Entity identification
    cui = Column(String(100), nullable=False, index=True)  # SNOMED-CT, UMLS, or PHI-*
    pretty_name = Column(String(500), nullable=False)  # Human-readable text

    # Position in document
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)

    # Confidence and context
    accuracy = Column(Float, nullable=False)  # Model confidence (0.0-1.0)
    meta_anns = Column(JSONB, nullable=False, default=dict)  # Meta-annotations

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ExtractedEntity("
            f"id={self.id}, "
            f"type={self.entity_type}, "
            f"cui={self.cui}, "
            f"name={self.pretty_name[:30]}"
            f")>"
        )

    def is_phi(self) -> bool:
        """Check if entity is PHI (Protected Health Information)."""
        return self.entity_type != EntityType.CLINICAL

    def is_clinical(self) -> bool:
        """Check if entity is clinical (SNOMED-CT)."""
        return self.entity_type == EntityType.CLINICAL

    def is_affirmed(self) -> bool:
        """Check if entity is affirmed (not negated)."""
        negation = self.meta_anns.get("Negation", {})
        return negation.get("value", "Affirmed") == "Affirmed"

    def is_current(self) -> bool:
        """Check if entity is current (not historical)."""
        temporality = self.meta_anns.get("Temporality", {})
        return temporality.get("value", "Current") in ["Current", "Recent"]

    def is_patient_experiencer(self) -> bool:
        """Check if experiencer is patient (not family/other)."""
        experiencer = self.meta_anns.get("Experiencer", {})
        return experiencer.get("value", "Patient") == "Patient"
