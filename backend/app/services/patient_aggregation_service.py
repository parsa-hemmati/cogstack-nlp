"""
Patient Aggregation Service.

Matches and merges patient records across documents by NHS number.
Handles data quality issues (missing fields, conflicts).
"""
import logging
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient

logger = logging.getLogger(__name__)


class PatientAggregationService:
    """
    Patient aggregation service using NHS number matching.

    Features:
    - Primary matching: NHS number (UK national identifier)
    - Update strategy: Prefer longer/more complete values
    - Immutable fields: DOB (once set, never changed)
    - Timeline tracking: first_seen_at, last_seen_at
    - Document counting: track patient frequency

    Workflow:
        1. Check if NHS number exists in database
        2. If exists: Update existing patient record
        3. If not: Create new patient record
        4. Increment document_count
        5. Update timeline (first_seen_at, last_seen_at)
        6. Fill in missing fields from new data

    Example:
        >>> service = PatientAggregationService()
        >>> patient = await service.aggregate_patient(
        >>>     db=db,
        >>>     nhs_number="1234567890",
        >>>     full_name="John Smith",
        >>>     date_of_birth=date(1980, 1, 15),
        >>>     document_date=datetime(2025, 1, 1)
        >>> )
    """

    async def aggregate_patient(
        self,
        db: AsyncSession,
        nhs_number: str,
        full_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        address: Optional[str] = None,
        document_date: Optional[datetime] = None,
    ) -> Patient:
        """
        Aggregate patient information from document extraction.

        Args:
            db: Database session
            nhs_number: UK NHS number (10 digits, primary key)
            full_name: Patient full name (optional)
            date_of_birth: Patient DOB (optional)
            address: Patient address (optional)
            document_date: Document date for timeline tracking

        Returns:
            Patient record (created or updated)

        Example:
            >>> patient = await service.aggregate_patient(
            >>>     db=db,
            >>>     nhs_number="1234567890",
            >>>     full_name="John Smith",
            >>>     document_date=datetime(2025, 1, 1)
            >>> )
        """
        if document_date is None:
            document_date = datetime.utcnow()

        # Primary matching: NHS number
        result = await db.execute(
            select(Patient).where(Patient.nhs_number == nhs_number)
        )
        existing_patient = result.scalar_one_or_none()

        if existing_patient:
            # Update existing patient
            self._update_patient(
                patient=existing_patient,
                full_name=full_name,
                date_of_birth=date_of_birth,
                address=address,
                document_date=document_date,
            )
            await db.commit()
            await db.refresh(existing_patient)
            return existing_patient
        else:
            # Create new patient
            new_patient = Patient(
                nhs_number=nhs_number,
                full_name=full_name,
                date_of_birth=date_of_birth,
                address=address,
                first_seen_at=document_date,
                last_seen_at=document_date,
                document_count=1,
            )
            db.add(new_patient)
            await db.commit()
            await db.refresh(new_patient)

            logger.info(
                f"Created new patient record: NHS {nhs_number}, "
                f"name={full_name}, first_seen={document_date}"
            )

            return new_patient

    def _update_patient(
        self,
        patient: Patient,
        full_name: Optional[str],
        date_of_birth: Optional[date],
        address: Optional[str],
        document_date: datetime,
    ) -> None:
        """
        Update existing patient with new information.

        Strategy:
        - Timeline: Update first_seen_at if earlier, last_seen_at if later
        - Name: Update if longer/more complete
        - Address: Update if longer/more complete
        - DOB: Update ONLY if previously missing (immutable once set)
        - document_count: Always increment

        Args:
            patient: Existing patient record
            full_name: New name value
            date_of_birth: New DOB value
            address: New address value
            document_date: Document date
        """
        # Update timeline
        if document_date < patient.first_seen_at:
            patient.first_seen_at = document_date

        if document_date > patient.last_seen_at:
            patient.last_seen_at = document_date

        # Increment document count
        patient.document_count += 1

        # Update name if longer (prefer more complete names)
        if full_name:
            if patient.full_name is None or len(full_name) > len(patient.full_name):
                if patient.full_name != full_name:
                    logger.debug(
                        f"Updating patient {patient.nhs_number} name: "
                        f"'{patient.full_name}' → '{full_name}'"
                    )
                patient.full_name = full_name

        # Update DOB ONLY if previously missing (immutable field)
        if date_of_birth and patient.date_of_birth is None:
            patient.date_of_birth = date_of_birth
            logger.debug(
                f"Setting patient {patient.nhs_number} DOB: {date_of_birth}"
            )
        elif date_of_birth and patient.date_of_birth != date_of_birth:
            # Conflict: different DOB values
            logger.warning(
                f"DOB conflict for patient {patient.nhs_number}: "
                f"existing={patient.date_of_birth}, new={date_of_birth}. "
                f"Keeping existing value (immutable field)."
            )

        # Update address if longer (prefer more complete addresses)
        if address:
            if patient.address is None or len(address) > len(patient.address):
                if patient.address != address:
                    logger.debug(
                        f"Updating patient {patient.nhs_number} address: "
                        f"'{patient.address}' → '{address}'"
                    )
                patient.address = address

    async def find_patient_by_nhs_number(
        self, db: AsyncSession, nhs_number: str
    ) -> Optional[Patient]:
        """
        Find patient by NHS number.

        Args:
            db: Database session
            nhs_number: UK NHS number

        Returns:
            Patient if found, None otherwise

        Example:
            >>> patient = await service.find_patient_by_nhs_number(db, "1234567890")
        """
        result = await db.execute(
            select(Patient).where(Patient.nhs_number == nhs_number)
        )
        return result.scalar_one_or_none()

    async def get_patient_stats(
        self, db: AsyncSession, nhs_number: str
    ) -> Optional[dict]:
        """
        Get patient statistics (document count, timeline).

        Args:
            db: Database session
            nhs_number: UK NHS number

        Returns:
            Statistics dictionary or None if patient not found

        Example:
            >>> stats = await service.get_patient_stats(db, "1234567890")
            >>> print(f"Documents: {stats['document_count']}")
        """
        patient = await self.find_patient_by_nhs_number(db, nhs_number)
        if not patient:
            return None

        return {
            "nhs_number": patient.nhs_number,
            "full_name": patient.full_name,
            "document_count": patient.document_count,
            "first_seen_at": patient.first_seen_at,
            "last_seen_at": patient.last_seen_at,
            "age": patient.get_age(),
            "days_span": (patient.last_seen_at - patient.first_seen_at).days,
        }
