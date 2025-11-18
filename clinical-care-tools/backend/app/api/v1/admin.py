"""Admin API endpoints for system administration and compliance."""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.data_retention_service import DataRetentionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Schemas
class LegalHoldRequest(BaseModel):
    """Request to place legal hold on document."""

    reason: str = Field(..., min_length=20, description="Reason for legal hold")


class LegalHoldResponse(BaseModel):
    """Response after placing/removing legal hold."""

    id: UUID
    legal_hold: bool
    legal_hold_reason: str | None
    legal_hold_by: UUID | None
    legal_hold_at: datetime | None

    class Config:
        """Pydantic config."""

        from_attributes = True


class DataRetentionStats(BaseModel):
    """Data retention statistics."""

    documents: dict
    audit_logs: dict
    sessions: dict


class DataRetentionResults(BaseModel):
    """Results of data retention purge."""

    documents_deleted: int
    audit_logs_deleted: int
    sessions_deleted: int


# Endpoints


@router.post(
    "/documents/{document_id}/legal-hold",
    response_model=LegalHoldResponse,
    status_code=status.HTTP_200_OK,
)
async def place_legal_hold(
    document_id: UUID,
    request: LegalHoldRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """
    Place legal hold on document.

    Legal hold prevents document from being deleted per retention policy.
    Used for litigation holds, regulatory investigations, audits.

    **Requires**: Admin role

    **Audit**: LEGAL_HOLD_PLACED
    """
    # Get document
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Check if already on legal hold
    if document.legal_hold:
        logger.warning(
            f"Document {document_id} already on legal hold "
            f"(placed by user {document.legal_hold_by})"
        )
        return document

    # Place legal hold
    document.legal_hold = True
    document.legal_hold_reason = request.reason
    document.legal_hold_by = current_user.id
    document.legal_hold_at = datetime.utcnow()

    await db.commit()
    await db.refresh(document)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="LEGAL_HOLD_PLACED",
        resource_type="document",
        resource_id=str(document_id),
        details={
            "reason": request.reason,
            "patient_id": str(document.patient_id),
        },
    )

    logger.info(
        f"Legal hold placed on document {document_id} by user {current_user.id} "
        f"(reason: {request.reason})"
    )

    return document


@router.delete(
    "/documents/{document_id}/legal-hold",
    response_model=LegalHoldResponse,
    status_code=status.HTTP_200_OK,
)
async def remove_legal_hold(
    document_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """
    Remove legal hold from document.

    Document will become eligible for deletion per retention policy.

    **Requires**: Admin role

    **Audit**: LEGAL_HOLD_REMOVED
    """
    # Get document
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Check if not on legal hold
    if not document.legal_hold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not on legal hold",
        )

    # Store reason for audit
    previous_reason = document.legal_hold_reason

    # Remove legal hold
    document.legal_hold = False
    document.legal_hold_reason = None
    document.legal_hold_by = None
    document.legal_hold_at = None

    await db.commit()
    await db.refresh(document)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="LEGAL_HOLD_REMOVED",
        resource_type="document",
        resource_id=str(document_id),
        details={
            "previous_reason": previous_reason,
            "patient_id": str(document.patient_id),
        },
    )

    logger.info(
        f"Legal hold removed from document {document_id} by user {current_user.id}"
    )

    return document


@router.get(
    "/data-retention/stats",
    response_model=DataRetentionStats,
    status_code=status.HTTP_200_OK,
)
async def get_data_retention_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DataRetentionStats:
    """
    Get data retention statistics.

    Shows how many records are eligible for deletion per retention policy.

    **Requires**: Admin role
    """
    service = DataRetentionService(db)
    stats = await service.get_retention_stats()

    return DataRetentionStats(**stats)


@router.post(
    "/data-retention/purge",
    response_model=DataRetentionResults,
    status_code=status.HTTP_200_OK,
)
async def run_data_retention_purge(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DataRetentionResults:
    """
    Manually trigger data retention purge.

    Deletes data per retention policies:
    - Documents >8 years (respects legal holds)
    - Audit logs >7 years
    - Sessions >90 days

    **Requires**: Admin role

    **Audit**: DATA_RETENTION_PURGE

    **Warning**: This operation cannot be undone!
    """
    logger.info(f"Manual data retention purge triggered by user {current_user.id}")

    service = DataRetentionService(db)
    results = await service.purge_old_data()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DATA_RETENTION_PURGE",
        resource_type="system",
        resource_id="data_retention",
        details=results,
    )

    return DataRetentionResults(**results)
