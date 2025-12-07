"""
Patient model for aggregated patient records.

Stores patient demographic information aggregated from extracted PHI entities.
NHS number serves as the unique identifier for linking entities to patients.

Patient records are created automatically during PHI extraction (Task 3.9)
when NHS numbers are found in clinical documents.
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, String, DateTime, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Patient(Base):
    """
    Patient model for aggregated patient records.

    Patient records are automatically created/updated during PHI extraction
    when NHS numbers are identified in clinical documents. Demographics (name,
    DOB, address) are extracted from PHI entities.

    NHS number serves as the natural key for patient identity. Multiple documents
    can reference the same patient via NHS number.

    Attributes:
        id: Unique patient identifier (UUID)
        nhs_number: NHS number (unique, indexed, 10 digits with spaces: "123 456 7890")
        full_name: Patient full name (extracted from PHI entities)
        date_of_birth: Patient date of birth (extracted from PHI entities)
        address: Patient address (extracted from PHI entities, nullable)
        first_seen_at: Timestamp of first document containing this patient
        last_seen_at: Timestamp of most recent document containing this patient
        document_count: Number of documents referencing this patient
        created_at: Record creation timestamp
        updated_at: Record last updated timestamp

    Relationships:
        extracted_entities: All entities associated with this patient (back-populated)

    Indexes:
        - nhs_number (unique): For fast patient lookup by NHS number

    Example:
        >>> # Patient record created during PHI extraction
        >>> patient = Patient(
        ...     nhs_number="123 456 7890",
        ...     full_name="John Doe",
        ...     date_of_birth=date(1980, 1, 1),
        ...     address="123 Main Street, London",
        ...     first_seen_at=datetime.utcnow(),
        ...     last_seen_at=datetime.utcnow(),
        ...     document_count=1
        ... )
        >>>
        >>> # Patient updated when NHS number found in another document
        >>> patient.document_count += 1
        >>> patient.last_seen_at = datetime.utcnow()
    """

    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Patient identification
    nhs_number = Column(
        String(12),  # Format: "123 456 7890" (10 digits + 2 spaces)
        nullable=False,
        unique=True,
        index=True
    )

    # Patient demographics (extracted from PHI entities)
    full_name = Column(String(255), nullable=True)  # May not always be available
    date_of_birth = Column(Date, nullable=True)  # May not always be available
    address = Column(String(500), nullable=True)  # May not always be available

    # Tracking
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    document_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # extracted_entities relationship will be back-populated from ExtractedEntity.patient

    def __repr__(self) -> str:
        return (
            f"<Patient("
            f"id={self.id}, "
            f"nhs_number={self.nhs_number}, "
            f"name={self.full_name}, "
            f"documents={self.document_count}"
            f")>"
        )

    def update_last_seen(self):
        """Update last_seen_at to current time and increment document count."""
        self.last_seen_at = datetime.utcnow()
        self.document_count += 1

    @staticmethod
    def normalize_nhs_number(nhs_number: str) -> str:
        """
        Normalize NHS number to standard format.

        Removes spaces and non-digits, then formats as "XXX XXX XXXX".

        Args:
            nhs_number: NHS number in any format

        Returns:
            str: Normalized NHS number (e.g., "123 456 7890")

        Example:
            >>> Patient.normalize_nhs_number("1234567890")
            '123 456 7890'
            >>> Patient.normalize_nhs_number("123-456-7890")
            '123 456 7890'
        """
        # Remove all non-digits
        digits = ''.join(c for c in nhs_number if c.isdigit())

        # Format as "XXX XXX XXXX"
        if len(digits) == 10:
            return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
        else:
            # Return as-is if not 10 digits (validation should catch this)
            return nhs_number

    @staticmethod
    def validate_nhs_number(nhs_number: str) -> bool:
        """
        Validate NHS number format.

        NHS number should be 10 digits.

        Args:
            nhs_number: NHS number to validate

        Returns:
            bool: True if valid, False otherwise

        Example:
            >>> Patient.validate_nhs_number("123 456 7890")
            True
            >>> Patient.validate_nhs_number("abc")
            False
        """
        # Remove spaces and non-digits
        digits = ''.join(c for c in nhs_number if c.isdigit())

        # Should be exactly 10 digits
        return len(digits) == 10
