"""Critical finding alert API endpoints."""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_clinician_user
from app.core.database import get_db
from app.models.critical_finding_alert import CriticalFindingAlert, FindingSeverity
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.critical_finding_service import CriticalFindingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/critical-findings", tags=["critical-findings"])


# Schemas
class CriticalFindingResponse(BaseModel):
    """Critical finding alert response."""

    id: UUID
    patient_id: UUID
    concept_cui: str
    concept_name: str
    severity: FindingSeverity
    document_id: UUID | None
    acknowledged_by: UUID | None
    acknowledged_at: datetime | None
    notification_sent_at: datetime | None
    created_at: datetime
    is_acknowledged: bool

    class Config:
        """Pydantic config."""

        from_attributes = True


# Endpoints


@router.get(
    "",
    response_model=List[CriticalFindingResponse],
    status_code=status.HTTP_200_OK,
)
async def list_critical_findings(
    patient_id: UUID | None = None,
    severity: FindingSeverity | None = None,
    unacknowledged_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    List critical finding alerts.

    **Requires**: Clinician role or higher

    **Query params**:
    - patient_id: Filter by patient
    - severity: Filter by severity (low, medium, high, critical)
    - unacknowledged_only: Show only unacknowledged alerts (default: true)
    - skip: Pagination offset
    - limit: Pagination limit (max 100)
    """
    service = CriticalFindingService(db)

    if unacknowledged_only:
        # Get unacknowledged alerts
        alerts = await service.get_unacknowledged_alerts(
            patient_id=patient_id,
            severity=severity,
        )

        # Apply pagination manually
        alerts = alerts[skip : skip + min(limit, 100)]

    else:
        # Get all alerts (need to implement this query)
        from sqlalchemy import select

        query = select(CriticalFindingAlert)

        if patient_id:
            query = query.where(CriticalFindingAlert.patient_id == patient_id)

        if severity:
            query = query.where(CriticalFindingAlert.severity == severity)

        # Order by severity (critical first) then creation date
        query = query.order_by(
            CriticalFindingAlert.severity.desc(),
            CriticalFindingAlert.created_at.desc(),
        )

        query = query.offset(skip).limit(min(limit, 100))

        result = await db.execute(query)
        alerts = result.scalars().all()

    # Convert to dicts with is_acknowledged property
    return [
        {
            "id": alert.id,
            "patient_id": alert.patient_id,
            "concept_cui": alert.concept_cui,
            "concept_name": alert.concept_name,
            "severity": alert.severity,
            "document_id": alert.document_id,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at,
            "notification_sent_at": alert.notification_sent_at,
            "created_at": alert.created_at,
            "is_acknowledged": alert.is_acknowledged,
        }
        for alert in alerts
    ]


@router.get(
    "/{alert_id}",
    response_model=CriticalFindingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_critical_finding(
    alert_id: UUID,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get critical finding alert by ID.

    **Requires**: Clinician role or higher
    """
    from sqlalchemy import select

    query = select(CriticalFindingAlert).where(CriticalFindingAlert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Critical finding alert {alert_id} not found",
        )

    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "concept_cui": alert.concept_cui,
        "concept_name": alert.concept_name,
        "severity": alert.severity,
        "document_id": alert.document_id,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledged_at": alert.acknowledged_at,
        "notification_sent_at": alert.notification_sent_at,
        "created_at": alert.created_at,
        "is_acknowledged": alert.is_acknowledged,
    }


@router.post(
    "/{alert_id}/acknowledge",
    response_model=CriticalFindingResponse,
    status_code=status.HTTP_200_OK,
)
async def acknowledge_critical_finding(
    alert_id: UUID,
    current_user: User = Depends(get_current_clinician_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Acknowledge a critical finding alert.

    Marks the alert as reviewed by the clinician.

    **Requires**: Clinician role or higher

    **Audit**: CRITICAL_FINDING_ACKNOWLEDGED
    """
    service = CriticalFindingService(db)

    try:
        alert = await service.acknowledge_alert(
            alert_id=alert_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CRITICAL_FINDING_ACKNOWLEDGED",
        resource_type="critical_finding_alert",
        resource_id=str(alert_id),
        details={
            "patient_id": str(alert.patient_id),
            "concept_cui": alert.concept_cui,
            "concept_name": alert.concept_name,
            "severity": alert.severity.value,
        },
    )

    logger.info(
        f"Critical finding alert {alert_id} acknowledged by user {current_user.id}"
    )

    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "concept_cui": alert.concept_cui,
        "concept_name": alert.concept_name,
        "severity": alert.severity,
        "document_id": alert.document_id,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledged_at": alert.acknowledged_at,
        "notification_sent_at": alert.notification_sent_at,
        "created_at": alert.created_at,
        "is_acknowledged": alert.is_acknowledged,
    }
