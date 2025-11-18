"""Patient management endpoints."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_clinician
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientSearchRequest,
    PatientUpdate,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    patient_data: PatientCreate,
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new patient.

    Requires: Clinician or Admin role

    Args:
        request: FastAPI request
        patient_data: Patient data
        current_user: Authenticated user
        db: Database session

    Returns:
        Created patient
    """
    audit_service = AuditService(db)

    # Check if patient_id already exists
    result = await db.execute(
        select(Patient).where(Patient.patient_id == patient_data.patient_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with ID {patient_data.patient_id} already exists",
        )

    # Create patient
    patient = Patient(**patient_data.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    # Audit log
    await audit_service.log(
        user=current_user,
        action=AuditAction.CREATE_RECORD,
        resource_type="Patient",
        resource_id=str(patient.id),
        patient_id=patient.patient_id,
        ip_address=request.client.host if request.client else None,
        success=True,
    )

    logger.info(f"Patient created: {patient.patient_id} by {current_user.username}")

    return patient


@router.get("/", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all patients (paginated).

    Requires: Clinician or Admin role

    Args:
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        db: Database session

    Returns:
        Paginated list of patients
    """
    # Get total count
    count_result = await db.execute(select(Patient))
    total = len(count_result.scalars().all())

    # Get paginated results
    offset = (page - 1) * page_size
    result = await db.execute(select(Patient).offset(offset).limit(page_size))
    patients = result.scalars().all()

    return {
        "patients": patients,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get patient by ID.

    Requires: Clinician or Admin role

    Args:
        request: FastAPI request
        patient_id: Patient UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Patient details
    """
    audit_service = AuditService(db)

    # Get patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Audit log - PHI access
    await audit_service.log_phi_access(
        user=current_user,
        action=AuditAction.VIEW_PATIENT,
        patient_id=patient.patient_id,
        resource_type="Patient",
        resource_id=str(patient.id),
        ip_address=request.client.host if request.client else None,
    )

    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    request: Request,
    patient_id: UUID,
    patient_data: PatientUpdate,
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update patient.

    Requires: Clinician or Admin role

    Args:
        request: FastAPI request
        patient_id: Patient UUID
        patient_data: Updated patient data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated patient
    """
    audit_service = AuditService(db)

    # Get patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Update fields
    for field, value in patient_data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)

    await db.commit()
    await db.refresh(patient)

    # Audit log
    await audit_service.log(
        user=current_user,
        action=AuditAction.UPDATE_RECORD,
        resource_type="Patient",
        resource_id=str(patient.id),
        patient_id=patient.patient_id,
        ip_address=request.client.host if request.client else None,
        success=True,
    )

    logger.info(f"Patient updated: {patient.patient_id} by {current_user.username}")

    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete patient.

    Requires: Clinician or Admin role

    Args:
        request: FastAPI request
        patient_id: Patient UUID
        current_user: Authenticated user
        db: Database session
    """
    audit_service = AuditService(db)

    # Get patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    patient_id_str = patient.patient_id

    # Delete patient (cascade deletes documents)
    await db.delete(patient)
    await db.commit()

    # Audit log
    await audit_service.log(
        user=current_user,
        action=AuditAction.DELETE_RECORD,
        resource_type="Patient",
        resource_id=str(patient_id),
        patient_id=patient_id_str,
        ip_address=request.client.host if request.client else None,
        success=True,
    )

    logger.warning(f"Patient deleted: {patient_id_str} by {current_user.username}")
