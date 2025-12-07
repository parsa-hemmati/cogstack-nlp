"""De-identification API Endpoints (Sprint 4, Phase 4.2)

Public API for de-identifying clinical documents.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.deidentification import (
    DeidentificationPreviewRequest,
    DeidentificationPreviewResponse,
    DeidentificationApplyRequest,
    DeidentificationApplyResponse,
    BatchDeidentificationRequest,
    BatchDeidentificationResponse
)
from app.services.deidentification import DeidentificationService
from app.core.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/deidentify", tags=["De-identification"])


def get_deidentification_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> DeidentificationService:
    """Dependency: Get de-identification service"""
    return DeidentificationService(db=db)


@router.post(
    "/preview",
    response_model=DeidentificationPreviewResponse,
    summary="Preview de-identification",
    description="""
    Preview what will be redacted before applying de-identification.

    Shows:
    - Original text
    - Detected PHI entities with positions
    - Preview of redacted text

    Does NOT modify documents.

    **HIPAA Compliance**: All operations are audit logged.
    """,
    status_code=status.HTTP_200_OK
)
async def preview_deidentification(
    request: DeidentificationPreviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DeidentificationService, Depends(get_deidentification_service)]
) -> DeidentificationPreviewResponse:
    """Preview de-identification

    Args:
        request: Documents and redaction mode
        current_user: Authenticated user
        service: De-identification service

    Returns:
        Previews for each document

    Raises:
        HTTPException: 404 if documents not found, 500 if preview fails
    """
    try:
        previews = await service.preview_deidentification(
            document_ids=request.document_ids,
            redaction_mode=request.redaction_mode,
            user_id=current_user.id
        )

        if not previews:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents found"
            )

        return DeidentificationPreviewResponse(
            previews=previews,
            total_documents=len(previews)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


@router.post(
    "/apply",
    response_model=DeidentificationApplyResponse,
    summary="Apply de-identification",
    description="""
    Apply de-identification to documents (creates de-identified copies).

    - Original documents are NOT modified
    - De-identified documents are created as new entities
    - Re-identification mapping optionally stored (encrypted)
    - All operations are audit logged

    **HIPAA Compliance**: PHI access and de-identification are audit logged.
    """,
    status_code=status.HTTP_201_CREATED
)
async def apply_deidentification(
    request: DeidentificationApplyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DeidentificationService, Depends(get_deidentification_service)]
) -> DeidentificationApplyResponse:
    """Apply de-identification

    Args:
        request: Documents, redaction mode, and options
        current_user: Authenticated user
        service: De-identification service

    Returns:
        Results for each document

    Raises:
        HTTPException: 404 if documents not found, 500 if de-identification fails
    """
    try:
        results = await service.apply_deidentification(
            document_ids=request.document_ids,
            redaction_mode=request.redaction_mode,
            store_mapping=request.store_mapping,
            user_id=current_user.id
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents found or de-identification failed"
            )

        total_entities = sum(r.entities_redacted for r in results)

        return DeidentificationApplyResponse(
            deidentified_documents=results,
            total_documents=len(results),
            total_entities_redacted=total_entities
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"De-identification failed: {str(e)}"
        )


@router.post(
    "/batch",
    response_model=BatchDeidentificationResponse,
    summary="Batch de-identify documents (async)",
    description="""
    Queue batch de-identification job for asynchronous processing.

    Use for large document sets (100+ documents).

    - Job is queued and processed in background
    - Returns job ID for status tracking
    - Use GET /api/v1/deidentify/batch/{job_id} to check status

    **Maximum**: 10,000 documents per batch
    """,
    status_code=status.HTTP_202_ACCEPTED
)
async def batch_deidentify(
    request: BatchDeidentificationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DeidentificationService, Depends(get_deidentification_service)]
) -> BatchDeidentificationResponse:
    """Queue batch de-identification job

    Args:
        request: Documents and redaction mode
        current_user: Authenticated user
        service: De-identification service

    Returns:
        Job ID and status

    Raises:
        HTTPException: 400 if too many documents, 500 if queueing fails
    """
    # TODO: Implement batch processing in Phase 4.4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Batch de-identification will be implemented in Phase 4.4"
    )
