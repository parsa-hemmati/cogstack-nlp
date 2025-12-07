"""PHI Detection API Endpoints (Sprint 4, Phase 4.1, Task 4.1.7)

Internal API for PHI detection (not exposed publicly).
Used by de-identification service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.schemas.phi import (
    PHIDetectionRequest,
    PHIDetectionResponse,
    DetectedEntity
)
from app.services.phi import PHIDetectionService
from app.core.audit import audit_log
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/internal/phi", tags=["PHI Detection (Internal)"])


def get_phi_service() -> PHIDetectionService:
    """Dependency: Get PHI detection service"""
    return PHIDetectionService(use_mock=True)


@router.post(
    "/detect",
    response_model=PHIDetectionResponse,
    summary="Detect PHI in text (Internal)",
    description="""
    Detect Protected Health Information (PHI) in clinical text using NER model.

    **Internal API**: This endpoint is for internal service use only.

    Detects:
    - PERSON: Patient names, doctor names
    - DATE: Birth dates, admission dates
    - ID: SSN, MRN, insurance numbers
    - LOCATION: Addresses, cities, states
    - PHONE: Phone numbers
    - EMAIL: Email addresses
    - AGE: Ages over 89

    **HIPAA Compliance**: All PHI detection operations are audit logged.
    """
)
async def detect_phi(
    request: PHIDetectionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PHIDetectionService, Depends(get_phi_service)]
) -> PHIDetectionResponse:
    """Detect PHI entities in text

    Args:
        request: Text to analyze
        current_user: Authenticated user (for audit logging)
        service: PHI detection service

    Returns:
        Detected PHI entities with positions and confidence scores

    Raises:
        HTTPException: 400 if text is empty, 500 if detection fails
    """
    try:
        # Detect PHI
        entities = await service.detect_phi(request.text)

        # Audit log (PHI access)
        audit_log(
            user_id=current_user.id,
            action="PHI_DETECTION",
            resource_type="clinical_text",
            resource_id=None,
            details={
                "text_length": len(request.text),
                "entities_detected": len(entities),
                "entity_types": list({e.label.value for e in entities})
            }
        )

        return PHIDetectionResponse(
            entities=entities,
            total_entities=len(entities)
        )

    except Exception as e:
        # Log error (but not PHI text!)
        audit_log(
            user_id=current_user.id,
            action="PHI_DETECTION_FAILED",
            resource_type="clinical_text",
            resource_id=None,
            details={"error": str(e), "text_length": len(request.text)}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PHI detection failed: {str(e)}"
        )
