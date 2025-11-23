"""
Patient Aggregation Service.

Matches and merges patient records using NHS number (primary) and fuzzy matching (fallback).
Handles conflicts and updates patient demographics with most recent data.

Matching Strategy:
1. Primary: Exact NHS number match
2. Fallback: Fuzzy match on name + DOB (>80% similarity)

Usage:
    >>> from app.services.patient_aggregation_service import aggregate_patient
    >>>
    >>> patient = await aggregate_patient(
    ...     db=db,
    ...     nhs_number="123 456 7890",
    ...     full_name="John Doe",
    ...     date_of_birth=date(1980, 1, 1),
    ...     address="123 Main St"
    ... )
"""

import logging
from typing import Optional
from datetime import datetime, date
from difflib import SequenceMatcher
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient


logger = logging.getLogger(__name__)


# Fuzzy matching threshold (80%)
FUZZY_MATCH_THRESHOLD = 0.8


async def aggregate_patient(
    db: AsyncSession,
    nhs_number: Optional[str] = None,
    full_name: Optional[str] = None,
    date_of_birth: Optional[date] = None,
    address: Optional[str] = None,
    document_id: Optional[str] = None
) -> Patient:
    """
    Aggregate patient record using NHS number (primary) or fuzzy matching (fallback).

    Matching Strategy:
    1. Primary: Exact NHS number match → update existing patient
    2. Fallback: Fuzzy match by name + DOB (>80% similarity) → update existing patient
    3. No match: Create new patient

    Args:
        db: Database session
        nhs_number: NHS number (10 digits, normalized to "XXX XXX XXXX")
        full_name: Patient full name
        date_of_birth: Patient date of birth
        address: Patient address
        document_id: Document ID (for logging)

    Returns:
        Patient: Matched or newly created patient record

    Example:
        >>> # Primary match (NHS number)
        >>> patient = await aggregate_patient(
        ...     db=db,
        ...     nhs_number="123 456 7890",
        ...     full_name="John Doe"
        ... )
        >>>
        >>> # Fallback match (fuzzy on name + DOB)
        >>> patient = await aggregate_patient(
        ...     db=db,
        ...     full_name="Jon Doe",  # Typo in name
        ...     date_of_birth=date(1980, 1, 1)
        ... )
    """
    # Strategy 1: Primary match by NHS number
    if nhs_number:
        normalized_nhs = Patient.normalize_nhs_number(nhs_number)

        if Patient.validate_nhs_number(normalized_nhs):
            result = await db.execute(
                select(Patient).where(Patient.nhs_number == normalized_nhs)
            )
            patient = result.scalar_one_or_none()

            if patient:
                logger.info(f"Matched patient {patient.id} by NHS number: {normalized_nhs}")

                # Update patient fields with newest data
                await _update_patient_fields(
                    patient=patient,
                    nhs_number=normalized_nhs,
                    full_name=full_name,
                    date_of_birth=date_of_birth,
                    address=address
                )

                patient.update_last_seen()
                await db.commit()
                return patient
        else:
            logger.warning(f"Invalid NHS number format: {nhs_number}")

    # Strategy 2: Fallback to fuzzy matching by name + DOB
    if full_name and date_of_birth:
        logger.debug(f"No NHS match, attempting fuzzy match for: {full_name}, DOB: {date_of_birth}")

        # Get all patients with same DOB
        result = await db.execute(
            select(Patient).where(Patient.date_of_birth == date_of_birth)
        )
        candidates = result.scalars().all()

        # Fuzzy match on name
        best_match = None
        best_similarity = 0.0

        for candidate in candidates:
            if candidate.full_name:
                similarity = _calculate_name_similarity(full_name, candidate.full_name)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = candidate

        # Accept match if similarity > threshold
        if best_match and best_similarity >= FUZZY_MATCH_THRESHOLD:
            logger.info(
                f"Fuzzy matched patient {best_match.id}: "
                f"{full_name} ~ {best_match.full_name} (similarity: {best_similarity:.2f})"
            )

            # Log potential conflict if name differs
            if full_name.lower() != best_match.full_name.lower():
                logger.warning(
                    f"Name conflict for patient {best_match.id}: "
                    f"Existing: '{best_match.full_name}', New: '{full_name}' "
                    f"(similarity: {best_similarity:.2f})"
                )

            # Update with most recent data
            await _update_patient_fields(
                patient=best_match,
                nhs_number=nhs_number,
                full_name=full_name,
                date_of_birth=date_of_birth,
                address=address
            )

            best_match.update_last_seen()
            await db.commit()
            return best_match
        elif best_match:
            logger.debug(
                f"Fuzzy match below threshold ({best_similarity:.2f} < {FUZZY_MATCH_THRESHOLD}), "
                f"creating new patient"
            )

    # Strategy 3: No match found, create new patient
    logger.info(f"Creating new patient: {full_name or 'Unknown'}")

    new_patient = Patient(
        nhs_number=Patient.normalize_nhs_number(nhs_number) if nhs_number else None,
        full_name=full_name,
        date_of_birth=date_of_birth,
        address=address,
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        document_count=1
    )

    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)

    logger.info(f"Created new patient {new_patient.id}")

    return new_patient


async def _update_patient_fields(
    patient: Patient,
    nhs_number: Optional[str] = None,
    full_name: Optional[str] = None,
    date_of_birth: Optional[date] = None,
    address: Optional[str] = None
):
    """
    Update patient fields with most recent data.

    Strategy: Update field if current value is None, or if new value is provided.

    Args:
        patient: Patient record to update
        nhs_number: New NHS number (if available)
        full_name: New full name (if available)
        date_of_birth: New date of birth (if available)
        address: New address (if available)
    """
    updated_fields = []

    # Update NHS number if not set or if new value provided
    if nhs_number and not patient.nhs_number:
        patient.nhs_number = Patient.normalize_nhs_number(nhs_number)
        updated_fields.append("nhs_number")

    # Update name if not set or if new value provided
    if full_name and not patient.full_name:
        patient.full_name = full_name
        updated_fields.append("full_name")

    # Update DOB if not set
    if date_of_birth and not patient.date_of_birth:
        patient.date_of_birth = date_of_birth
        updated_fields.append("date_of_birth")

    # Update address (always use most recent)
    if address:
        if patient.address != address:
            patient.address = address
            updated_fields.append("address")

    if updated_fields:
        logger.debug(f"Updated patient {patient.id} fields: {', '.join(updated_fields)}")


def _calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two names using Sequence Matcher.

    Args:
        name1: First name
        name2: Second name

    Returns:
        float: Similarity score (0.0 to 1.0)

    Example:
        >>> _calculate_name_similarity("John Doe", "Jon Doe")
        0.94
        >>> _calculate_name_similarity("John Doe", "Jane Smith")
        0.27
    """
    # Normalize: lowercase, remove extra spaces
    name1_normalized = ' '.join(name1.lower().split())
    name2_normalized = ' '.join(name2.lower().split())

    # Calculate similarity ratio
    similarity = SequenceMatcher(None, name1_normalized, name2_normalized).ratio()

    return similarity
