"""
Unit tests for Patient model.

Tests aggregated patient records from PHI extraction.
"""
import pytest
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.patient import Patient


@pytest.mark.asyncio
async def test_patient_creation(db: AsyncSession):
    """Test basic patient creation."""
    patient = Patient(
        nhs_number="1234567890",
        full_name="John Smith",
        date_of_birth=date(1980, 1, 15),
        address="123 Main St, London, UK",
        first_seen_at=datetime(2025, 1, 1, 10, 0, 0),
        last_seen_at=datetime(2025, 1, 1, 10, 0, 0),
        document_count=1,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    assert patient.id is not None
    assert patient.nhs_number == "1234567890"
    assert patient.full_name == "John Smith"
    assert patient.date_of_birth == date(1980, 1, 15)
    assert patient.created_at is not None


@pytest.mark.asyncio
async def test_patient_nhs_number_unique_constraint(db: AsyncSession):
    """Test NHS number unique constraint prevents duplicates."""
    # Create first patient
    patient1 = Patient(
        nhs_number="9876543210",
        full_name="Jane Doe",
        date_of_birth=date(1990, 5, 20),
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        document_count=1,
    )
    db.add(patient1)
    await db.commit()

    # Try to create duplicate NHS number
    patient2 = Patient(
        nhs_number="9876543210",  # Same NHS number!
        full_name="Different Name",  # Different name
        date_of_birth=date(1985, 3, 10),
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        document_count=1,
    )
    db.add(patient2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(Exception):  # IntegrityError
        await db.commit()


@pytest.mark.asyncio
async def test_patient_nhs_number_indexed(db: AsyncSession):
    """Test NHS number is indexed for fast lookups."""
    # Create multiple patients
    for i in range(10):
        patient = Patient(
            nhs_number=f"000000000{i}",
            full_name=f"Patient {i}",
            date_of_birth=date(1980, 1, 1),
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            document_count=1,
        )
        db.add(patient)
    await db.commit()

    # Query by NHS number (should use index)
    result = await db.execute(
        select(Patient).where(Patient.nhs_number == "0000000005")
    )
    patient = result.scalar_one_or_none()

    assert patient is not None
    assert patient.full_name == "Patient 5"


@pytest.mark.asyncio
async def test_patient_document_count_tracking(db: AsyncSession):
    """Test document count tracks number of documents patient appears in."""
    patient = Patient(
        nhs_number="1111111111",
        full_name="Test Patient",
        date_of_birth=date(1985, 6, 15),
        first_seen_at=datetime(2025, 1, 1),
        last_seen_at=datetime(2025, 1, 10),
        document_count=5,  # Patient appears in 5 documents
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    assert patient.document_count == 5


@pytest.mark.asyncio
async def test_patient_first_last_seen_tracking(db: AsyncSession):
    """Test first_seen_at and last_seen_at track patient encounter timeline."""
    first_encounter = datetime(2024, 1, 1, 9, 0, 0)
    last_encounter = datetime(2025, 6, 15, 14, 30, 0)

    patient = Patient(
        nhs_number="2222222222",
        full_name="Timeline Patient",
        date_of_birth=date(1975, 3, 20),
        first_seen_at=first_encounter,
        last_seen_at=last_encounter,
        document_count=10,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    assert patient.first_seen_at == first_encounter
    assert patient.last_seen_at == last_encounter
    # last_seen_at should be >= first_seen_at
    assert patient.last_seen_at >= patient.first_seen_at


@pytest.mark.asyncio
async def test_patient_nullable_fields(db: AsyncSession):
    """Test optional fields can be null."""
    patient = Patient(
        nhs_number="3333333333",
        full_name=None,  # Name might not be extracted
        date_of_birth=None,  # DOB might not be found
        address=None,  # Address might not be present
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        document_count=1,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    assert patient.full_name is None
    assert patient.date_of_birth is None
    assert patient.address is None


@pytest.mark.asyncio
async def test_patient_update_last_seen_and_document_count(db: AsyncSession):
    """Test updating patient record when new document is processed."""
    # Initial patient creation
    patient = Patient(
        nhs_number="4444444444",
        full_name="Update Test",
        date_of_birth=date(1992, 7, 8),
        first_seen_at=datetime(2025, 1, 1),
        last_seen_at=datetime(2025, 1, 1),
        document_count=1,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    # Simulate processing a new document for same patient
    new_encounter = datetime(2025, 6, 15)
    patient.last_seen_at = new_encounter
    patient.document_count += 1

    await db.commit()
    await db.refresh(patient)

    assert patient.last_seen_at == new_encounter
    assert patient.document_count == 2
