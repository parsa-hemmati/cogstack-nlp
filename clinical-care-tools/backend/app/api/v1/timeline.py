"""Timeline API endpoints."""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.models.patient import Patient
from app.models.user import User
from app.schemas.timeline import TimelineResponse
from app.services.audit_service import AuditService
from app.services.timeline_service import TimelineService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{patient_id}", response_model=TimelineResponse)
async def get_patient_timeline(
    request: Request,
    patient_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter end date (ISO 8601)"),
    document_types: Optional[str] = Query(None, description="Comma-separated document types"),
    concept_types: Optional[str] = Query(None, description="Comma-separated concept types"),
    include_negated: bool = Query(False, description="Include negated concepts"),
    include_family: bool = Query(False, description="Include family history"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get timeline for a patient.

    Retrieves chronological timeline of documents and clinical concepts.

    Args:
        request: FastAPI request
        patient_id: Patient UUID
        start_date: Filter start date (optional)
        end_date: Filter end date (optional)
        document_types: Comma-separated list of document types (optional)
        concept_types: Comma-separated list of concept types (optional)
        include_negated: Include negated concepts (default: False)
        include_family: Include family history (default: False)
        current_user: Authenticated user
        db: Database session

    Returns:
        TimelineResponse with documents, concepts, and metadata

    Raises:
        HTTPException: 404 if patient not found, 403 if not authorized
    """
    audit_service = AuditService(db)
    timeline_service = TimelineService(db)

    # Verify patient exists
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )

    # Parse comma-separated lists
    doc_types_list = None
    if document_types:
        doc_types_list = [dt.strip() for dt in document_types.split(",")]

    concept_types_list = None
    if concept_types:
        concept_types_list = [ct.strip() for ct in concept_types.split(",")]

    # Get timeline
    try:
        timeline_response = await timeline_service.get_patient_timeline(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            document_types=doc_types_list,
            concept_types=concept_types_list,
            include_negated=include_negated,
            include_family=include_family,
        )
    except Exception as e:
        logger.error(f"Error retrieving timeline for patient {patient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving timeline: {str(e)}",
        )

    # Audit log (PHI access)
    await audit_service.log(
        user=current_user,
        action=AuditAction.VIEW_RECORD,
        resource_type="Timeline",
        resource_id=str(patient_id),
        patient_id=patient.patient_id,  # MRN for audit trail
        ip_address=request.client.host if request.client else None,
        details={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "document_types": doc_types_list,
            "concept_types": concept_types_list,
            "include_negated": include_negated,
            "include_family": include_family,
            "document_count": timeline_response.metadata["document_count"],
            "concept_count": timeline_response.metadata["concept_count"],
        },
        success=True,
    )

    logger.info(
        f"Timeline retrieved for patient {patient.patient_id} by {current_user.username}: "
        f"{timeline_response.metadata['document_count']} docs, "
        f"{timeline_response.metadata['concept_count']} concepts"
    )

    return timeline_response
