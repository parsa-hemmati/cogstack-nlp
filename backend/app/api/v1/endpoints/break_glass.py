"""Break-Glass API endpoints for emergency PHI access.

Endpoints for break-glass workflow:
- Request emergency access (requires can_break_glass permission)
- View break-glass audit logs (admin only)

All break-glass operations are heavily audit logged.
"""
import math
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.break_glass import (
    BreakGlassLogEntry,
    BreakGlassLogListResponse,
    BreakGlassRequest,
    BreakGlassResponse,
)
from app.services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()


@router.post("/access", response_model=BreakGlassResponse, status_code=status.HTTP_200_OK)
async def request_break_glass_access(
    break_glass_request: BreakGlassRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request emergency break-glass access to PHI.

    Requires can_break_glass permission. All access is audit logged.

    Args:
        break_glass_request: Break-glass access request with justification
        request: HTTP request (for IP, user agent)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Break-glass access grant with expiration time

    Raises:
        HTTPException: 403 if user doesn't have break-glass permission
    """
    # Check permission
    if not current_user.can_break_glass:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Break-glass access not authorized for this user",
        )

    # Extract IP and user agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Create audit log for break-glass event
    # This is a CRITICAL security event and must be logged
    audit_log = await audit_service.log_action(
        db=db,
        user=current_user,
        action="BREAK_GLASS_ACCESS",
        resource_type=break_glass_request.resource_type,
        resource_id=break_glass_request.resource_id,
        details={
            "patient_id": break_glass_request.patient_id,
            "justification": break_glass_request.justification,
            "granted_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        },
        ip_address=ip_address,
        user_agent=user_agent,
        success="success",
    )

    # Grant access for 24 hours
    expires_at = datetime.utcnow() + timedelta(hours=24)

    return BreakGlassResponse(
        access_granted=True,
        break_glass_id=audit_log.id,
        user_id=current_user.id,
        username=current_user.username,
        timestamp=datetime.utcnow(),
        justification=break_glass_request.justification,
        expires_at=expires_at,
        resource_type=break_glass_request.resource_type,
        resource_id=break_glass_request.resource_id,
        message=(
            "⚠️ EMERGENCY ACCESS GRANTED ⚠️\n"
            "This break-glass access is valid for 24 hours. "
            "All actions are being audit logged. "
            "Unauthorized use may result in disciplinary action."
        ),
    )


@router.get(
    "/logs", response_model=BreakGlassLogListResponse, status_code=status.HTTP_200_OK
)
async def list_break_glass_logs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all break-glass access logs (admin only).

    Critical security audit trail for emergency access events.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        user_id: Optional filter by user ID
        start_date: Optional filter events after this date
        end_date: Optional filter events before this date
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Paginated list of break-glass audit logs

    Raises:
        HTTPException: 403 if not admin
    """
    # Build query for break-glass events
    query = select(AuditLog).where(AuditLog.action == "BREAK_GLASS_ACCESS")

    # Apply filters
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
    if start_date is not None:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date is not None:
        query = query.where(AuditLog.timestamp <= end_date)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(AuditLog.timestamp.desc())

    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()

    # Convert to response format
    log_entries = [
        BreakGlassLogEntry(
            id=log.id,
            user_id=log.user_id,
            username=log.username,
            patient_id=log.details.get("patient_id") if log.details else None,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            justification=log.details.get("justification") if log.details else "",
            timestamp=log.timestamp,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
        )
        for log in logs
    ]

    # Audit log (viewing break-glass logs)
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="VIEW_BREAK_GLASS_LOGS",
        resource_type="audit_log",
        details={"page": page, "page_size": page_size, "filters": {"user_id": user_id}},
    )

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return BreakGlassLogListResponse(
        items=log_entries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
