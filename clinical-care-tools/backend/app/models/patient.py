"""Patient model for storing patient demographics and metadata."""

from datetime import date
from typing import Optional

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Patient(Base):
    """
    Patient model for demographics and administrative data.

    Note: Clinical documents are stored in Elasticsearch.
    This model stores only non-PHI metadata and references.

    Attributes:
        patient_id: External patient identifier (MRN, NHS number, etc.)
        first_name: Patient first name
        last_name: Patient last name
        date_of_birth: Date of birth
        gender: Gender (M/F/Other)
        notes: Administrative notes (non-clinical)
    """

    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="External patient identifier (MRN, NHS number)",
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Patient(patient_id='{self.patient_id}', name='{self.first_name} {self.last_name}')>"
