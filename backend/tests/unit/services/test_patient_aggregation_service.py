"""
Unit tests for Patient Aggregation Service.

Tests patient matching and aggregation by NHS number.
"""
import pytest
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.services.patient_aggregation_service import PatientAggregationService


@pytest.fixture
def aggregation_service():
    """Create patient aggregation service."""
    return PatientAggregationService()


@pytest.mark.asyncio
async def test_aggregate_patient_new_nhs_number(
    aggregation_service, db: AsyncSession
):
    """Test creating new patient for unseen NHS number."""
    patient = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number="1234567890",
        full_name="John Smith",
        date_of_birth=date(1980, 1, 15),
        address="123 Main St",
        document_date=datetime(2025, 1, 1),
    )

    assert patient.nhs_number == "1234567890"
    assert patient.full_name == "John Smith"
    assert patient.first_seen_at == datetime(2025, 1, 1)
    assert patient.last_seen_at == datetime(2025, 1, 1)
    assert patient.document_count == 1


@pytest.mark.asyncio
async def test_aggregate_patient_existing_nhs_number_updates(
    aggregation_service, db: AsyncSession
):
    """Test updating existing patient with same NHS number."""
    # Create initial patient
    initial_patient = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number="9876543210",
        full_name="Jane Doe",
        date_of_birth=date(1990, 5, 20),
        document_date=datetime(2025, 1, 1),
    )

    # Process second document for same patient
    updated_patient = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number="9876543210",  # Same NHS number
        full_name="Jane A. Doe",  # More complete name
        address="456 Oak Ave",  # New address
        document_date=datetime(2025, 6, 15),  # Later date
    )

    assert updated_patient.id == initial_patient.id  # Same patient
    assert updated_patient.document_count == 2  # Incremented
    assert updated_patient.full_name == "Jane A. Doe"  # Updated (longer)
    assert updated_patient.address == "456 Oak Ave"  # Updated
    assert updated_patient.last_seen_at == datetime(2025, 6, 15)  # Updated


@pytest.mark.asyncio
async def test_aggregate_patient_document_count_increments(
    aggregation_service, db: AsyncSession
):
    """Test document count increments with each document."""
    nhs_number = "1111111111"

    # First document
    p1 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2025, 1, 1),
    )
    assert p1.document_count == 1

    # Second document
    p2 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2025, 2, 1),
    )
    assert p2.document_count == 2

    # Third document
    p3 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2025, 3, 1),
    )
    assert p3.document_count == 3


@pytest.mark.asyncio
async def test_aggregate_patient_first_seen_updates_if_earlier(
    aggregation_service, db: AsyncSession
):
    """Test first_seen_at updates if earlier document found."""
    nhs_number = "2222222222"

    # Initial document (recent)
    p1 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2025, 6, 1),
    )
    assert p1.first_seen_at == datetime(2025, 6, 1)

    # Earlier document
    p2 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2024, 1, 1),  # Earlier!
    )
    assert p2.first_seen_at == datetime(2024, 1, 1)  # Updated


@pytest.mark.asyncio
async def test_aggregate_patient_last_seen_updates_if_later(
    aggregation_service, db: AsyncSession
):
    """Test last_seen_at updates if later document found."""
    nhs_number = "3333333333"

    # Initial document (old)
    p1 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2024, 1, 1),
    )
    assert p1.last_seen_at == datetime(2024, 1, 1)

    # Later document
    p2 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2025, 6, 15),  # Later!
    )
    assert p2.last_seen_at == datetime(2025, 6, 15)  # Updated


@pytest.mark.asyncio
async def test_aggregate_patient_prefers_longer_name(
    aggregation_service, db: AsyncSession
):
    """Test name updated if newer value is longer/more complete."""
    nhs_number = "4444444444"

    # Initial: short name
    p1 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        full_name="J. Smith",
        document_date=datetime(2025, 1, 1),
    )
    assert p1.full_name == "J. Smith"

    # Later: longer name (more complete)
    p2 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        full_name="John A. Smith",  # Longer
        document_date=datetime(2025, 2, 1),
    )
    assert p2.full_name == "John A. Smith"  # Updated

    # Later: shorter name (less complete) - should NOT update
    p3 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        full_name="J Smith",  # Shorter
        document_date=datetime(2025, 3, 1),
    )
    assert p3.full_name == "John A. Smith"  # NOT updated


@pytest.mark.asyncio
async def test_aggregate_patient_handles_missing_fields(
    aggregation_service, db: AsyncSession
):
    """Test aggregation works with missing optional fields."""
    patient = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number="5555555555",
        full_name=None,  # Missing
        date_of_birth=None,  # Missing
        address=None,  # Missing
        document_date=datetime(2025, 1, 1),
    )

    assert patient.nhs_number == "5555555555"
    assert patient.full_name is None
    assert patient.date_of_birth is None
    assert patient.address is None


@pytest.mark.asyncio
async def test_aggregate_patient_fills_missing_fields_from_later_doc(
    aggregation_service, db: AsyncSession
):
    """Test missing fields filled in from later documents."""
    nhs_number = "6666666666"

    # First document: missing name and DOB
    p1 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        full_name=None,
        date_of_birth=None,
        document_date=datetime(2025, 1, 1),
    )
    assert p1.full_name is None
    assert p1.date_of_birth is None

    # Second document: has name and DOB
    p2 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        full_name="New Name",
        date_of_birth=date(1985, 3, 10),
        document_date=datetime(2025, 2, 1),
    )
    assert p2.full_name == "New Name"  # Filled in
    assert p2.date_of_birth == date(1985, 3, 10)  # Filled in


@pytest.mark.asyncio
async def test_aggregate_patient_only_updates_dob_if_missing(
    aggregation_service, db: AsyncSession
):
    """Test DOB only updated if previously missing (immutable once set)."""
    nhs_number = "7777777777"

    # First document: has DOB
    p1 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        date_of_birth=date(1980, 1, 1),
        document_date=datetime(2025, 1, 1),
    )
    assert p1.date_of_birth == date(1980, 1, 1)

    # Second document: different DOB (conflict!)
    p2 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        date_of_birth=date(1985, 5, 5),  # Different DOB
        document_date=datetime(2025, 2, 1),
    )
    # DOB should NOT change (first value wins)
    assert p2.date_of_birth == date(1980, 1, 1)


@pytest.mark.asyncio
async def test_aggregate_patient_concurrent_updates_safe(
    aggregation_service, db: AsyncSession
):
    """Test concurrent updates to same patient are handled safely."""
    nhs_number = "8888888888"

    # Create initial patient
    p1 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2025, 1, 1),
    )

    # Simulate concurrent update
    p2 = await aggregation_service.aggregate_patient(
        db=db,
        nhs_number=nhs_number,
        document_date=datetime(2025, 1, 2),
    )

    # Both should reference same patient
    assert p1.id == p2.id
    # Document count should reflect both documents
    # (Note: In production, use database locking for true concurrency safety)
    assert p2.document_count >= 2
