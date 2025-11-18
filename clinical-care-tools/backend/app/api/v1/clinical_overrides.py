"""Clinical override API endpoints."""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_clinician_user
from app.core.database import get_db
from app.models.clinical_override import ClinicalOverride
from app.models.patient import Patient
from app.models.user import User
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clinical-overrides", tags=["clinical-overrides"])


# Schemas
class ClinicalOverrideCreate(BaseModel):
    """Request to create clinical override."""

    patient_id: UUID
    recommendation_type: str = Field(
        ..., description="Type of recommendation (e.g., 'critical_alert', 'dosage_warning')"
    )
    recommendation_value: str = Field(..., description="Original system recommendation")
    override_value: str = Field(..., description="Clinician's override decision")
    justification: str = Field(
        ..., min_length=20, description="Required justification (min 20 characters)"
    )
    severity: str = Field(
        default="medium", description="Severity: low, medium, high"
    )


class ClinicalOverrideResponse(BaseModel):
    """Clinical override response."""

    id: UUID
    user_id: UUID
    patient_id: UUID
    recommendation_type: str
    recommendation_value: str
    override_value: str
    justification: str
    severity: str
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Endpoints


@router.post(
    "",
    response_model=ClinicalOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_override(
    override: ClinicalOverrideCreate,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalOverride:
    """
    Create clinical override.

    Records when a clinician overrides a system recommendation or alert.
    Critical for patient safety monitoring and system improvement.

    **Requires**: Clinician role or higher

    **Audit**: CLINICAL_OVERRIDE
    """
    # Validate severity
    if override.severity not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Severity must be one of: low, medium, high",
        )

    # Verify patient exists
    patient_query = select(Patient).where(Patient.id == override.patient_id)
    result = await db.execute(patient_query)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {override.patient_id} not found",
        )

    # Create override
    db_override = ClinicalOverride(
        user_id=current_user.id,
        patient_id=override.patient_id,
        recommendation_type=override.recommendation_type,
        recommendation_value=override.recommendation_value,
        override_value=override.override_value,
        justification=override.justification,
        severity=override.severity,
    )

    db.add(db_override)
    await db.commit()
    await db.refresh(db_override)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CLINICAL_OVERRIDE",
        resource_type="clinical_override",
        resource_id=str(db_override.id),
        details={
            "patient_id": str(override.patient_id),
            "recommendation_type": override.recommendation_type,
            "severity": override.severity,
            "justification": override.justification,
        },
    )

    logger.warning(
        f"Clinical override created by user {current_user.id} "
        f"for patient {override.patient_id} "
        f"(type: {override.recommendation_type}, severity: {override.severity})"
    )

    return db_override


@router.get(
    "",
    response_model=List[ClinicalOverrideResponse],
    status_code=status.HTTP_200_OK,
)
async def list_overrides(
    patient_id: UUID | None = None,
    severity: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> List[ClinicalOverride]:
    """
    List clinical overrides.

    **Requires**: Clinician role or higher

    **Query params**:
    - patient_id: Filter by patient
    - severity: Filter by severity (low, medium, high)
    - skip: Pagination offset
    - limit: Pagination limit (max 100)
    """
    query = select(ClinicalOverride)

    # Apply filters
    if patient_id:
        query = query.where(ClinicalOverride.patient_id == patient_id)

    if severity:
        if severity not in ["low", "medium", "high"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Severity must be one of: low, medium, high",
            )
        query = query.where(ClinicalOverride.severity == severity)

    # Order by creation date (newest first)
    query = query.order_by(ClinicalOverride.created_at.desc())

    # Apply pagination
    query = query.offset(skip).limit(min(limit, 100))

    result = await db.execute(query)
    overrides = result.scalars().all()

    return overrides


@router.get(
    "/{override_id}",
    response_model=ClinicalOverrideResponse,
    status_code=status.HTTP_200_OK,
)
async def get_override(
    override_id: UUID,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalOverride:
    """
    Get clinical override by ID.

    **Requires**: Clinician role or higher
    """
    query = select(ClinicalOverride).where(ClinicalOverride.id == override_id)
    result = await db.execute(query)
    override = result.scalar_one_or_none()

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clinical override {override_id} not found",
        )

    return override
