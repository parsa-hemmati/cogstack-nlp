"""
Authentication endpoints.

Handles user login, logout, and token management.
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse, LogoutResponse
from app.services.auth_service import create_access_token, verify_token
from app.services.session_service import invalidate_session


router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Login endpoint.

    Authenticates user with username and password, returns JWT access token.

    Args:
        credentials: LoginRequest with username and password
        db: Database session

    Returns:
        LoginResponse with access token, expiry, and user information

    Raises:
        HTTPException: 401 if credentials invalid or user inactive

    Example:
        POST /api/v1/auth/login
        {
            "username": "john_doe",
            "password": "SecurePassword123!"
        }

        Response (200):
        {
            "access_token": "eyJhbGci...",
            "token_type": "bearer",
            "expires_at": "2025-01-01T08:00:00",
            "user": {...}
        }
    """
    # Query user by username
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    # Verify user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    token_result = create_access_token(
        user_id=str(user.id), role=user.role
    )

    # Calculate expiration time (8 hours from now)
    expires_at = datetime.utcnow() + timedelta(hours=8)

    # Return login response
    return LoginResponse(
        access_token=token_result["access_token"],
        token_type=token_result["token_type"],
        expires_at=expires_at,
        user=UserResponse.from_orm(user),
    )


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    authorization: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Logout endpoint.

    Invalidates the current session by marking it as expired.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        LogoutResponse with success message

    Raises:
        HTTPException: 401 if token invalid or missing

    Example:
        POST /api/v1/auth/logout
        Headers: Authorization: Bearer eyJhbGci...

        Response (200):
        {
            "message": "Logged out successfully"
        }
    """
    # Extract token from Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    # Verify token and extract JTI
    try:
        payload = verify_token(token)
        token_jti = payload.get("jti")

        if not token_jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        # Re-raise token verification errors
        raise

    # Invalidate session
    invalidated = await invalidate_session(db, token_jti)

    if not invalidated:
        # Session not found - token might be valid but no session exists
        # This is acceptable (logout is idempotent)
        pass

    return LogoutResponse(message="Logged out successfully")
