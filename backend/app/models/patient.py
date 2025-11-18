"""
Patient model for aggregated patient records.

Aggregates patient information from extracted PHI across multiple documents.
Patients are linked by NHS number with fuzzy matching fallback.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Patient(Base):
    """
    Patient model for aggregated records across documents.

    Aggregates patient information extracted from multiple clinical documents:
    - Primary matching: NHS number
    - Fallback matching: Fuzzy match on name + date of birth

    Attributes:
        id: Unique patient identifier (UUID)
        nhs_number: UK National Health Service number (10 digits, unique)
        full_name: Patient full name (from PHI extraction)
        date_of_birth: Patient DOB (from PHI extraction)
        address: Patient address (from PHI extraction)
        first_seen_at: Earliest document date for this patient
        last_seen_at: Most recent document date for this patient
        document_count: Number of documents mentioning this patient
        created_at: Record creation timestamp
        updated_at: Record last update timestamp

    Indexes:
        - nhs_number (unique, primary matching key)
        - full_name (fuzzy matching fallback)
        - date_of_birth (fuzzy matching fallback)

    Constraints:
        - Unique constraint on nhs_number (prevents duplicate records)

    Example:
        >>> patient = Patient(
        >>>     nhs_number="1234567890",
        >>>     full_name="John Smith",
        >>>     date_of_birth=date(1980, 1, 15),
        >>>     first_seen_at=datetime.utcnow(),
        >>>     last_seen_at=datetime.utcnow(),
        >>>     document_count=5
        >>> )
    """

    __tablename__ = "patients"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    nhs_number = Column(
        String(10), nullable=False, unique=True, index=True
    )  # UK NHS number (10 digits)
    full_name = Column(String(200), nullable=True, index=True)  # For fuzzy matching
    date_of_birth = Column(Date, nullable=True, index=True)  # For fuzzy matching
    address = Column(String(500), nullable=True)

    # Timeline tracking
    first_seen_at = Column(DateTime, nullable=False)  # Earliest document date
    last_seen_at = Column(DateTime, nullable=False)  # Most recent document date
    document_count = Column(
        Integer, nullable=False, default=1
    )  # Number of documents

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    # entities relationship will be added when ExtractedEntity backref is configured

    # Indexes for performance
    __table_args__ = (
        Index("ix_patients_nhs_number", "nhs_number", unique=True),  # Primary key for matching
        Index("ix_patients_full_name", "full_name"),  # Fuzzy matching
        Index("ix_patients_date_of_birth", "date_of_birth"),  # Fuzzy matching
        # Composite index for fuzzy matching
        Index("ix_patients_name_dob", "full_name", "date_of_birth"),
        UniqueConstraint("nhs_number", name="uq_patients_nhs_number"),
    )

    def __repr__(self):
        return (
            f"<Patient(id={self.id}, nhs_number={self.nhs_number}, "
            f"name={self.full_name}, documents={self.document_count})>"
        )

    def update_from_new_document(
        self,
        document_date: datetime,
        new_name: Optional[str] = None,
        new_dob: Optional[date] = None,
        new_address: Optional[str] = None,
    ) -> None:
        """
        Update patient record when processing a new document.

        Args:
            document_date: Date of the new document
            new_name: Updated name (if more recent/complete)
            new_dob: Updated DOB (if found)
            new_address: Updated address (if found)

        Example:
            >>> patient.update_from_new_document(
            >>>     document_date=datetime(2025, 6, 15),
            >>>     new_name="John A. Smith"  # More complete name
            >>> )
        """
        # Update timeline
        if document_date < self.first_seen_at:
            self.first_seen_at = document_date
        if document_date > self.last_seen_at:
            self.last_seen_at = document_date

        # Increment document count
        self.document_count += 1

        # Update fields if newer/better data available
        # (Logic: prefer longer/more complete values)
        if new_name and (not self.full_name or len(new_name) > len(self.full_name)):
            self.full_name = new_name

        if new_dob and not self.date_of_birth:
            self.date_of_birth = new_dob

        if new_address and (
            not self.address or len(new_address) > len(self.address)
        ):
            self.address = new_address

    def get_age(self) -> Optional[int]:
        """Calculate patient age in years."""
        if not self.date_of_birth:
            return None

        today = date.today()
        age = (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )
        return age
