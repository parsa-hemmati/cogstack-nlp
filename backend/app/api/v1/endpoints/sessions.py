"""Sessions Management API endpoints.

Endpoints for managing user sessions:
- List active sessions
- Revoke session (logout from specific device)
- Revoke all sessions (logout from all devices)

All operations include audit logging.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.session import SessionInfo, SessionListResponse
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.session_service import session_service

router = APIRouter()
audit_service = AuditService()
auth_service = AuthService()


@router.get("/me", response_model=SessionListResponse, status_code=status.HTTP_200_OK)
async def get_my_sessions(
    authorization: str = Header(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active sessions for the current user.

    Args:
        authorization: Authorization header (to identify current session)
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of active sessions
    """
    # Get current session ID from token
    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_token(token)
    current_token_jti = payload.get("jti")

    # Get all sessions for this user
    sessions = await session_service.list_user_sessions(user_id=str(current_user.id))

    # Convert to response format
    session_infos = [
        SessionInfo(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            is_current=(session.token_jti == current_token_jti),
        )
        for session in sessions
    ]

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="VIEW_MY_SESSIONS",
        resource_type="session",
        details={"sessions_count": len(session_infos)},
    )

    return SessionListResponse(
        sessions=session_infos,
        total=len(session_infos),
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a specific session (logout from a specific device).

    Users can only revoke their own sessions.

    Args:
        session_id: Session ID to revoke
        current_user: Current authenticated user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 403 if session doesn't belong to user, 404 if session not found
    """
    # Get session to verify ownership
    session = await session_service.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already expired",
        )

    # Verify ownership
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only revoke your own sessions",
        )

    # Revoke session
    await session_service.delete_session(session_id)

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="REVOKE_SESSION",
        resource_type="session",
        resource_id=session_id,
        details={"ip_address": session.ip_address, "user_agent": session.user_agent},
    )

    return None


@router.delete("/me/all", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_sessions(
    authorization: str = Header(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all sessions except the current one (logout from all other devices).

    Args:
        authorization: Authorization header (to preserve current session)
        current_user: Current authenticated user
        db: Database session

    Returns:
        None (204 No Content)
    """
    # Get current session ID from token
    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_token(token)
    current_token_jti = payload.get("jti")

    # Get all sessions
    sessions = await session_service.list_user_sessions(user_id=str(current_user.id))

    # Revoke all sessions except current
    revoked_count = 0
    for session in sessions:
        if session.token_jti != current_token_jti:
            await session_service.delete_session(session.session_id)
            revoked_count += 1

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="REVOKE_ALL_SESSIONS",
        resource_type="session",
        details={"revoked_count": revoked_count, "preserved_current": True},
    )

    return None
