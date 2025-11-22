"""
Clinical Safety Router (Phase 6)

Endpoints for clinical data safety validation and warning management.

Safety Checks:
- NLP confidence thresholds
- Critical concept detection
- Duplicate patient detection
- Date validation
- Required field validation
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.services.clinical_safety_service import ClinicalSafetyService
from app.schemas.safety import (
    SafetyCheckRequest, SafetyCheckResponse, SafetyWarningResponse, SafetyDismiss, SafetyOverride,
    SafetyWarningsList, SafetyStatistics
)

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/safety",
    tags=["safety"]
)


@router.post("/validate", response_model=SafetyCheckResponse)
async def validate_clinical_data(
    check_request: SafetyCheckRequest,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> SafetyCheckResponse:
    """
    Validate clinical data before saving.

    Performs safety checks and returns warnings if issues found.
    Clinicians should address warnings before proceeding.

    Args:
        check_request: Data to validate
        user: Current authenticated user
        db: Database session

    Returns:
        Validation result with warning details if applicable

    Raises:
        HTTPException: 400 if invalid check type
    """
    if not settings.CLINICAL_SAFETY_ENABLED:
        return SafetyCheckResponse(
            has_warning=False,
            message="Clinical safety checks disabled"
        )

    service = ClinicalSafetyService(db)
    warning = None

    # Dispatch to appropriate check based on type
    if check_request.data_type == "nlp_confidence":
        warning = await service.check_nlp_confidence(
            user_id=user["id"],
            patient_id=check_request.patient_id,
            concept=check_request.data.get("concept"),
            confidence=check_request.data.get("confidence", 0)
        )

    elif check_request.data_type == "critical_concept":
        warning = await service.check_critical_concept(
            user_id=user["id"],
            patient_id=check_request.patient_id,
            concept=check_request.data.get("concept"),
            concept_type=check_request.data.get("concept_type")
        )

    elif check_request.data_type == "duplicate_patient":
        warning = await service.check_duplicate_patient(
            user_id=user["id"],
            first_name=check_request.data.get("first_name"),
            last_name=check_request.data.get("last_name"),
            date_of_birth=check_request.data.get("date_of_birth")
        )

    elif check_request.data_type == "required_fields":
        warning = await service.check_required_fields(
            user_id=user["id"],
            patient_data=check_request.data
        )

    elif check_request.data_type == "future_date":
        from datetime import datetime
        warning = await service.check_future_date(
            user_id=user["id"],
            field_name=check_request.data.get("field_name"),
            date_value=datetime.fromisoformat(check_request.data.get("date_value")),
            patient_id=check_request.patient_id
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown check type: {check_request.data_type}"
        )

    return SafetyCheckResponse(
        has_warning=warning is not None,
        warning=SafetyWarningResponse.model_validate(warning) if warning else None,
        message="Safety check completed" + (" with warnings" if warning else " - no issues found")
    )


@router.get("/warnings", response_model=SafetyWarningsList)
async def get_active_warnings(
    patient_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> SafetyWarningsList:
    """
    Get active safety warnings.

    Returns warnings for current clinician and optional patient.
    Allows clinician to see what issues need to be addressed.

    Args:
        patient_id: Optional filter by patient
        limit: Maximum results
        offset: Pagination offset
        user: Current authenticated user
        db: Database session

    Returns:
        List of active warnings

    Raises:
        HTTPException: 401 if not authenticated
    """
    service = ClinicalSafetyService(db)
    warnings = await service.get_active_warnings(
        user_id=user["id"],
        patient_id=patient_id,
        limit=limit
    )

    return SafetyWarningsList(
        total=len(warnings),
        limit=limit,
        offset=offset,
        warnings=[SafetyWarningResponse.model_validate(w) for w in warnings]
    )


@router.post("/warnings/{warning_id}/dismiss", response_model=SafetyWarningResponse)
async def dismiss_warning(
    warning_id: str,
    dismiss_request: SafetyDismiss,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> SafetyWarningResponse:
    """
    Dismiss a safety warning.

    Clinician acknowledges the warning but doesn't override it.
    Warning is marked inactive.

    Args:
        warning_id: Warning ID to dismiss
        dismiss_request: Dismissal details
        user: Current authenticated user
        db: Database session

    Returns:
        Updated warning

    Raises:
        HTTPException: 404 if warning not found
    """
    service = ClinicalSafetyService(db)
    warning = await service.dismiss_warning(
        warning_id=warning_id,
        user_id=user["id"],
        reason=dismiss_request.reason
    )

    if not warning:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warning not found"
        )

    return SafetyWarningResponse.model_validate(warning)


@router.post("/warnings/{warning_id}/override", response_model=dict)
async def override_warning(
    warning_id: str,
    override_request: SafetyOverride,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> dict:
    """
    Override a safety warning with clinical justification.

    Requires manager approval for high-severity overrides.
    Clinician provides clinical reason for overriding warning.

    Args:
        warning_id: Warning ID to override
        override_request: Override justification
        user: Current authenticated user
        db: Database session

    Returns:
        Override record

    Raises:
        HTTPException: 404 if warning not found
        HTTPException: 400 if justification too short
    """
    service = ClinicalSafetyService(db)
    override = await service.override_warning(
        warning_id=warning_id,
        user_id=user["id"],
        justification=override_request.justification,
        severity=override_request.severity
    )

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warning not found"
        )

    return {
        "id": override.id,
        "warning_id": override.warning_id,
        "user_id": override.user_id,
        "severity": override.severity,
        "created_at": override.created_at.isoformat(),
        "status": "pending_approval" if override.severity == "high" else "approved",
        "message": f"Override {'requires manager approval' if override.severity == 'high' else 'recorded'}"
    }


@router.get("/statistics", response_model=SafetyStatistics)
async def get_safety_statistics(
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> SafetyStatistics:
    """
    Get clinical safety statistics.

    Admin/manager only. Shows safety metrics and trends.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        Safety statistics

    Raises:
        HTTPException: 403 if user not authorized
    """
    # Check user role (admin or manager only)
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access requires admin or manager role"
        )

    # NOTE: Implement statistics aggregation from database
    # Query:
    # - Total warnings by type
    # - Active warnings count
    # - Dismissed warnings count
    # - Override count
    # - Critical alerts count

    return SafetyStatistics(
        total_warnings=0,
        active_warnings=0,
        dismissed_warnings=0,
        overrides=0,
        critical_alerts=0,
        warnings_by_type={}
    )


@router.get("/audit/trail", response_model=dict)
async def get_safety_audit_trail(
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> dict:
    """
    Get safety warning audit trail.

    Admin only. Complete audit of all safety actions for compliance.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        Audit trail data

    Raises:
        HTTPException: 403 if user not admin
    """
    # Check user role (admin only)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access requires admin role"
        )

    # NOTE: Query AuditLog table for CLINICAL_SAFETY actions

    return {
        "status": "pending",
        "message": "Audit trail feature coming soon"
    }
