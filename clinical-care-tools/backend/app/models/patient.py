"""
Patient Model

Represents aggregated patient records created from extracted entities.
"""

from datetime import datetime, date
from typing import Optional
from uuid import uuid4
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, Index, String, Date, Float, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped

from app.models import Base


class Patient(Base):
    """
    Aggregated patient record created from extracted entities.

    This table aggregates demographics extracted from documents. Patient records
    are created/updated when MedCAT extracts identifiable PHI (name, NHS number, DOB, address).

    Attributes:
        id: Unique patient identifier (UUID)
        nhs_number: UK NHS number (10 digits, unique if present)
        mrn: Medical Record Number (unique if no NHS number)
        first_name: Patient first name
        last_name: Patient last name
        date_of_birth: Patient date of birth
        gender: Patient gender
        address_line1: Address line 1
        address_line2: Address line 2
        city: City
        postcode: Postcode
        source_document_ids: Array of document IDs that contributed data
        last_updated_from: Most recent document that updated this record
        confidence_score: Aggregate confidence of patient matching
        created_at: When record was created
        updated_at: When record was last updated

    Notes:
        - This table contains identifiable PHI (name, NHS number, DOB, address)
        - Requires encryption at rest and strict access controls
        - All queries must be logged for HIPAA/GDPR compliance
        - Patient matching uses: NHS number first, then fuzzy match on name + DOB
        - source_document_ids array allows tracing back to source documents
    """

    __tablename__ = "patients"

    # Primary Key
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Primary Identifiers (at least one must be present)
    nhs_number: Mapped[Optional[str]] = mapped_column(
        String(10),
        unique=True,
        nullable=True,
        index=True,
        comment="UK NHS number (10 digits), unique if present",
    )
    mrn: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Medical Record Number, unique if no NHS number",
    )

    # Demographics (extracted from documents)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Address (extracted from documents)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postcode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)

    # Aggregation Metadata
    source_document_ids: Mapped[list[PyUUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        default=list,
        comment="Array of document UUIDs that contributed data",
    )
    last_updated_from: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Most recent document that updated this record",
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Aggregate confidence of patient matching",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_patients_nhs_number",
            "nhs_number",
            postgresql_where="nhs_number IS NOT NULL",
        ),
        Index(
            "idx_patients_mrn",
            "mrn",
            postgresql_where="mrn IS NOT NULL",
        ),
        Index("idx_patients_last_name", "last_name"),
        Index("idx_patients_postcode", "postcode"),
        Index("idx_patients_updated_at", "updated_at", postgresql_using="desc"),
    )

    def __repr__(self) -> str:
        """String representation of Patient."""
        identifier = self.nhs_number or self.mrn
        name = f"{self.first_name} {self.last_name}".strip() if self.first_name or self.last_name else "Unknown"
        return f"<Patient(id={self.id}, identifier={identifier}, name={name})>"
