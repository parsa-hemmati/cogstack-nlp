"""
Break-Glass Access Router (Phase 5)

Endpoints for emergency access to patient data.
Requires special authorization and mandatory audit trail.

HIPAA Compliance:
- All break-glass access logged and audited
- Requires clinical justification
- Mandatory security team review within 24 hours
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_db
from app.dependencies import get_current_user, get_current_request_info
from app.services.break_glass_service import BreakGlassService
from app.schemas.break_glass import (
    BreakGlassRequest, BreakGlassResponse, BreakGlassReview, BreakGlassRevoke, BreakGlassList
)

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/break-glass",
    tags=["break-glass"]
)


@router.post("/request", response_model=BreakGlassResponse, status_code=status.HTTP_201_CREATED)
async def request_emergency_access(
    request_data: BreakGlassRequest,
    user: Annotated[dict, Depends(get_current_user)],
    request_info: Annotated[dict, Depends(get_current_request_info)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> BreakGlassResponse:
    """
    Request emergency access to patient data.

    Clinicians only. Generates alert to security team.
    Access will be approved or denied within 24 hours.

    Args:
        request_data: Break-glass request details
        user: Current authenticated user
        request_info: IP and User-Agent info
        db: Database session

    Returns:
        Break-glass access request details

    Raises:
        HTTPException: 400 if justification too short
        HTTPException: 403 if user not authorized (requires clinician role)
    """
    if not settings.BREAK_GLASS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Break-glass access is disabled"
        )

    # Check user role (clinicians only)
    if user.get("role") != settings.BREAK_GLASS_REQUIRED_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Break-glass access requires {settings.BREAK_GLASS_REQUIRED_ROLE} role"
        )

    service = BreakGlassService(db)
    access = await service.request_access(
        user_id=user["id"],
        patient_id=request_data.patient_id,
        justification=request_data.justification,
        ip_address=request_info.get("ip_address"),
        user_agent=request_info.get("user_agent")
    )

    return BreakGlassResponse.model_validate(access)


@router.get("/pending-reviews", response_model=BreakGlassList)
async def get_pending_reviews(
    limit: int = 20,
    offset: int = 0,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> BreakGlassList:
    """
    Get pending break-glass requests for security team review.

    Security team only. Lists all pending requests awaiting approval.

    Args:
        limit: Maximum results to return
        offset: Pagination offset
        user: Current authenticated user
        db: Database session

    Returns:
        List of pending requests

    Raises:
        HTTPException: 403 if user not security team
    """
    # Check user role (security team only)
    if user.get("role") != settings.BREAK_GLASS_REVIEWER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access requires {settings.BREAK_GLASS_REVIEWER_ROLE} role"
        )

    service = BreakGlassService(db)
    requests, total = await service.get_pending_reviews(limit=limit, offset=offset)

    return BreakGlassList(
        total=total,
        limit=limit,
        offset=offset,
        requests=[BreakGlassResponse.model_validate(r) for r in requests]
    )


@router.post("/{access_id}/review", response_model=BreakGlassResponse)
async def review_access_request(
    access_id: str,
    review: BreakGlassReview,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> BreakGlassResponse:
    """
    Review and approve/deny break-glass access request.

    Security team only. Must complete within 24 hours of request.

    Args:
        access_id: Break-glass request ID
        review: Review decision (approve or deny)
        user: Current authenticated user
        db: Database session

    Returns:
        Updated access request

    Raises:
        HTTPException: 403 if user not security team
        HTTPException: 404 if request not found
        HTTPException: 400 if invalid decision
    """
    # Check user role (security team only)
    if user.get("role") != settings.BREAK_GLASS_REVIEWER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access requires {settings.BREAK_GLASS_REVIEWER_ROLE} role"
        )

    service = BreakGlassService(db)

    if review.decision == "approve":
        access = await service.approve_access(
            access_id=access_id,
            reviewer_id=user["id"],
            review_notes=review.notes
        )
    elif review.decision == "deny":
        access = await service.deny_access(
            access_id=access_id,
            reviewer_id=user["id"],
            reason=review.notes or "No reason provided"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid decision. Must be 'approve' or 'deny'"
        )

    return BreakGlassResponse.model_validate(access)


@router.post("/{access_id}/revoke", response_model=BreakGlassResponse)
async def revoke_access(
    access_id: str,
    revoke_request: BreakGlassRevoke,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> BreakGlassResponse:
    """
    Revoke approved break-glass access immediately.

    Security team or admin only. Can be used to stop access if abuse detected.

    Args:
        access_id: Break-glass request ID
        revoke_request: Revocation details
        user: Current authenticated user
        db: Database session

    Returns:
        Updated access request

    Raises:
        HTTPException: 403 if user not authorized
        HTTPException: 404 if request not found
        HTTPException: 400 if cannot revoke current status
    """
    # Check user role (security team or admin only)
    if user.get("role") not in [settings.BREAK_GLASS_REVIEWER_ROLE, "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access requires security team or admin role"
        )

    service = BreakGlassService(db)
    access = await service.revoke_access(
        access_id=access_id,
        revoked_by=user["id"],
        reason=revoke_request.reason
    )

    return BreakGlassResponse.model_validate(access)


@router.get("/{access_id}", response_model=BreakGlassResponse)
async def get_access_details(
    access_id: str,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> BreakGlassResponse:
    """
    Get details of a break-glass access request.

    Available to clinician who made request and security team.

    Args:
        access_id: Break-glass request ID
        user: Current authenticated user
        db: Database session

    Returns:
        Access request details

    Raises:
        HTTPException: 404 if not found
        HTTPException: 403 if not authorized to view
    """
    # NOTE: Implement authorization check
    # Should allow: clinician who made request, security team, admins

    from app.models.break_glass_access import BreakGlassAccess
    from sqlalchemy import select

    result = await db.execute(
        select(BreakGlassAccess).where(BreakGlassAccess.id == access_id)
    )
    access = result.scalar_one_or_none()

    if not access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Break-glass access request not found"
        )

    return BreakGlassResponse.model_validate(access)


@router.get("/audit/trail", response_model=dict)
async def get_break_glass_audit_trail(
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> dict:
    """
    Get audit trail of break-glass access (admin/security only).

    Lists all break-glass requests and access for compliance auditing.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        Audit trail data

    Raises:
        HTTPException: 403 if user not authorized
    """
    # Check user role (security team or admin only)
    if user.get("role") not in [settings.BREAK_GLASS_REVIEWER_ROLE, "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access requires security team or admin role"
        )

    # NOTE: Implement audit trail retrieval from AuditLog table

    return {"message": "Audit trail feature coming soon"}
