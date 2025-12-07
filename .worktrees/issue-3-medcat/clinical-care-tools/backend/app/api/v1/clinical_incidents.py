"""Clinical incident API endpoints."""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin_user, get_current_clinician_user
from app.core.database import get_db
from app.models.clinical_incident import (
    ClinicalIncident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from app.models.patient import Patient
from app.models.user import User
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clinical-incidents", tags=["clinical-incidents"])


# Schemas
class ClinicalIncidentCreate(BaseModel):
    """Request to create clinical incident."""

    incident_type: IncidentType
    severity: IncidentSeverity
    description: str = Field(..., min_length=20, description="Detailed incident description")
    patient_id: UUID | None = Field(None, description="Patient affected (if applicable)")


class ClinicalIncidentUpdate(BaseModel):
    """Request to update clinical incident."""

    investigated_by: UUID | None = None
    resolution: str | None = Field(None, min_length=20)
    status: IncidentStatus | None = None


class ClinicalIncidentResponse(BaseModel):
    """Clinical incident response."""

    id: UUID
    incident_type: IncidentType
    severity: IncidentSeverity
    description: str
    patient_id: UUID | None
    reported_by: UUID
    investigated_by: UUID | None
    resolution: str | None
    status: IncidentStatus
    created_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None

    class Config:
        """Pydantic config."""

        from_attributes = True


# Endpoints


@router.post(
    "",
    response_model=ClinicalIncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    incident: ClinicalIncidentCreate,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalIncident:
    """
    Create clinical incident.

    Report clinical safety incidents, system errors, data quality issues.

    **Requires**: Clinician role or higher

    **Audit**: INCIDENT_REPORTED
    """
    # Verify patient exists if provided
    if incident.patient_id:
        patient_query = select(Patient).where(Patient.id == incident.patient_id)
        result = await db.execute(patient_query)
        patient = result.scalar_one_or_none()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {incident.patient_id} not found",
            )

    # Create incident
    db_incident = ClinicalIncident(
        incident_type=incident.incident_type,
        severity=incident.severity,
        description=incident.description,
        patient_id=incident.patient_id,
        reported_by=current_user.id,
        status=IncidentStatus.REPORTED,
    )

    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="INCIDENT_REPORTED",
        resource_type="clinical_incident",
        resource_id=str(db_incident.id),
        details={
            "incident_type": incident.incident_type.value,
            "severity": incident.severity.value,
            "patient_id": str(incident.patient_id) if incident.patient_id else None,
        },
    )

    logger.warning(
        f"Clinical incident reported by user {current_user.id} "
        f"(type: {incident.incident_type}, severity: {incident.severity})"
    )

    return db_incident


@router.get(
    "",
    response_model=List[ClinicalIncidentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_incidents(
    incident_type: IncidentType | None = None,
    severity: IncidentSeverity | None = None,
    status_filter: IncidentStatus | None = None,
    patient_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> List[ClinicalIncident]:
    """
    List clinical incidents.

    **Requires**: Clinician role or higher

    **Query params**:
    - incident_type: Filter by incident type
    - severity: Filter by severity
    - status_filter: Filter by status
    - patient_id: Filter by patient
    - skip: Pagination offset
    - limit: Pagination limit (max 100)
    """
    query = select(ClinicalIncident)

    # Apply filters
    if incident_type:
        query = query.where(ClinicalIncident.incident_type == incident_type)

    if severity:
        query = query.where(ClinicalIncident.severity == severity)

    if status_filter:
        query = query.where(ClinicalIncident.status == status_filter)

    if patient_id:
        query = query.where(ClinicalIncident.patient_id == patient_id)

    # Order by severity (critical first) then creation date (newest first)
    query = query.order_by(
        ClinicalIncident.severity.desc(),
        ClinicalIncident.created_at.desc(),
    )

    # Apply pagination
    query = query.offset(skip).limit(min(limit, 100))

    result = await db.execute(query)
    incidents = result.scalars().all()

    return incidents


@router.get(
    "/{incident_id}",
    response_model=ClinicalIncidentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_incident(
    incident_id: UUID,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalIncident:
    """
    Get clinical incident by ID.

    **Requires**: Clinician role or higher
    """
    query = select(ClinicalIncident).where(ClinicalIncident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clinical incident {incident_id} not found",
        )

    return incident


@router.patch(
    "/{incident_id}",
    response_model=ClinicalIncidentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_incident(
    incident_id: UUID,
    update: ClinicalIncidentUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalIncident:
    """
    Update clinical incident.

    Used to assign investigator, add resolution, change status.

    **Requires**: Admin role

    **Audit**: INCIDENT_UPDATED, INCIDENT_RESOLVED (if resolved)
    """
    query = select(ClinicalIncident).where(ClinicalIncident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clinical incident {incident_id} not found",
        )

    # Update fields
    if update.investigated_by is not None:
        incident.investigated_by = update.investigated_by

    if update.resolution is not None:
        incident.resolution = update.resolution

    if update.status is not None:
        # Validate status transitions
        if update.status == IncidentStatus.RESOLVED and not incident.resolution:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark incident as resolved without resolution",
            )

        old_status = incident.status
        incident.status = update.status

        # Set timestamps
        if update.status == IncidentStatus.RESOLVED and old_status != IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.utcnow()

        if update.status == IncidentStatus.CLOSED and old_status != IncidentStatus.CLOSED:
            incident.closed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(incident)

    # Audit log
    audit_service = AuditService(db)
    action = "INCIDENT_RESOLVED" if incident.status == IncidentStatus.RESOLVED else "INCIDENT_UPDATED"

    await audit_service.log(
        user_id=current_user.id,
        action=action,
        resource_type="clinical_incident",
        resource_id=str(incident_id),
        details={
            "status": incident.status.value,
            "resolution": incident.resolution,
        },
    )

    logger.info(
        f"Clinical incident {incident_id} updated by user {current_user.id} "
        f"(status: {incident.status})"
    )

    return incident
