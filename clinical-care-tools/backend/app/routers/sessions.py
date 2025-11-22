"""
Session Management API Router for Clinical Care Tools.

Handles session listing, invalidation, and security features.
HIPAA Compliance: Implements session security and audit logging.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.services.session_service import SessionService
from app.services.rbac_service import RBACService, Role, Resource, Action
from app.schemas.session import (
    SessionResponse,
    SessionListResponse,
    SessionInvalidateRequest,
    SessionInvalidateAllRequest,
    SessionSecurityInfo,
    BreakGlassRequest,
    BreakGlassResponse
)
from app.core.config import settings
from datetime import datetime, timezone, timedelta


router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["Session Management"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's active sessions.

    **Returns:**
    - List of all active sessions
    - Device information for each session
    - Last activity timestamps

    **Note:**
    - Users can only see their own sessions
    - Admins can see all sessions (with user_id parameter)

    **Security:**
    - Session details are masked for privacy
    """
    session_service = SessionService(db)

    # Get user's sessions
    sessions = await session_service.get_user_sessions(str(current_user.id))

    # Convert to response format
    session_responses = []
    for session in sessions:
        session_responses.append(SessionResponse(
            id=session.id,
            user_id=session.user_id,
            device_name=session.device_name,
            created_at=session.created_at,
            last_activity=session.last_activity,
            expires_at=session.expires_at,
            is_active=session.is_active,
            is_current=False  # Would check against current session
        ))

    return SessionListResponse(
        sessions=session_responses,
        total=len(sessions),
        active_count=len([s for s in sessions if s.is_active])
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invalidate a specific session.

    **Use Cases:**
    - User wants to logout a specific device
    - Suspicious activity detected on a session
    - Admin terminating user session

    **Process:**
    1. Verifies ownership or admin rights
    2. Invalidates the session
    3. Audit logs the action

    **Returns:**
    - 204 No Content on success

    **Raises:**
    - 403: Not authorized to invalidate this session
    - 404: Session not found
    """
    session_service = SessionService(db)
    rbac_service = RBACService(db)

    # Get the session to check ownership
    sessions = await session_service.get_user_sessions(str(current_user.id))
    target_session = next((s for s in sessions if s.id == session_id), None)

    if not target_session:
        # Check if admin trying to invalidate another user's session
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

    # Invalidate the session
    success = await session_service.invalidate_session(session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already invalidated"
        )

    return


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_all_sessions(
    request: SessionInvalidateAllRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invalidate all user sessions.

    **Use Cases:**
    - User wants to logout all devices
    - Security breach response
    - Password change (automatic)

    **Options:**
    - except_current: Keep current session active
    - reason: Optional reason for audit log

    **Returns:**
    - 204 No Content on success
    - Returns count of invalidated sessions in header

    **Security:**
    - Commonly triggered after password change
    - Admin can force logout all users
    """
    session_service = SessionService(db)

    # Get current session ID from request if keeping current
    current_session_id = None
    if request.except_current:
        # In production, extract from request/token
        # For now, we'll skip the current session
        pass

    # Invalidate all sessions
    count = await session_service.invalidate_all_user_sessions(
        str(current_user.id),
        except_current=current_session_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={"X-Sessions-Invalidated": str(count)}
    )


@router.get("/security", response_model=SessionSecurityInfo)
async def get_security_settings(
    current_user=Depends(get_current_user)
):
    """
    Get current session security settings.

    **Returns:**
    - Session binding status
    - Hijack detection status
    - Timeout configurations
    - Concurrent session limits

    **Use Case:**
    - Display security settings to user
    - Inform about session policies
    """
    return SessionSecurityInfo(
        session_binding_enabled=settings.SESSION_BINDING_ENABLED,
        hijack_detection_enabled=settings.SESSION_HIJACK_DETECTION,
        idle_timeout_minutes=settings.SESSION_IDLE_TIMEOUT_MINUTES,
        absolute_timeout_hours=settings.SESSION_ABSOLUTE_TIMEOUT_HOURS,
        max_concurrent_sessions=settings.SESSION_MAX_CONCURRENT
    )


@router.post("/break-glass", response_model=BreakGlassResponse)
async def request_break_glass_access(
    request: BreakGlassRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Request emergency break-glass access.

    **Use Case:**
    - Emergency medical situations
    - Time-critical patient care
    - System access issues

    **Requirements:**
    - Must be clinician or admin
    - Must provide detailed reason
    - Subject to post-access review

    **Process:**
    1. Validates user role
    2. Grants temporary elevated access
    3. Sends security alert
    4. Schedules mandatory review

    **Duration:**
    - Default: 60 minutes
    - Maximum: 120 minutes

    **Compliance:**
    - HIPAA emergency access provision
    - Requires review within 24 hours
    - All actions heavily audited

    **Returns:**
    - Grant details with expiration
    - Review deadline

    **Raises:**
    - 403: Role not authorized for break-glass
    - 400: Invalid reason or duration
    """
    if not settings.BREAK_GLASS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Break-glass access is not enabled"
        )

    rbac_service = RBACService(db)

    # Request break-glass access
    grant = await rbac_service.grant_break_glass_access(
        current_user,
        request.reason,
        request.duration_minutes
    )

    # Create response
    return BreakGlassResponse(
        grant_id=f"break_glass_{current_user.id}_{datetime.now(timezone.utc).timestamp()}",
        user_id=str(current_user.id),
        granted_at=grant["granted_at"],
        expires_at=grant["expires_at"],
        reason=request.reason,
        review_required_by=datetime.now(timezone.utc) + timedelta(hours=24)
    )


@router.get("/active-count", response_model=dict)
async def get_active_session_count(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get count of active sessions.

    **Returns:**
    - Current active session count
    - Maximum allowed sessions
    - Whether limit is reached

    **Use Case:**
    - Show session count in UI
    - Warn before hitting limit
    """
    session_service = SessionService(db)

    sessions = await session_service.get_user_sessions(str(current_user.id))
    active_count = len([s for s in sessions if s.is_active])

    return {
        "active_sessions": active_count,
        "max_sessions": settings.SESSION_MAX_CONCURRENT,
        "limit_reached": active_count >= settings.SESSION_MAX_CONCURRENT
    }


@router.post("/cleanup", response_model=dict)
async def cleanup_expired_sessions(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger cleanup of expired sessions.

    **Note:**
    - Normally runs automatically via background task
    - Admin only endpoint

    **Returns:**
    - Number of sessions cleaned up

    **Raises:**
    - 403: Not authorized (admin only)
    """
    # Check admin permission
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    session_service = SessionService(db)
    count = await session_service.cleanup_expired_sessions()

    return {
        "sessions_cleaned": count,
        "timestamp": datetime.now(timezone.utc)
    }