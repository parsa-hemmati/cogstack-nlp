"""Authentication endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, UserCreate, UserResponse
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        can_break_glass=user_data.can_break_glass,
    )
    user.set_password(user_data.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User registered: {user.username}")

    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Login and get access token.

    Args:
        request: FastAPI request
        login_data: Login credentials
        db: Database session

    Returns:
        Login response with tokens

    Raises:
        HTTPException: If credentials are invalid or account is locked
    """
    audit_service = AuditService(db)

    # Get user by username
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user:
        # Log failed login attempt
        logger.warning(f"Login failed: User not found - {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Check if account is locked
    if user.is_locked:
        await audit_service.log(
            user=user,
            action=AuditAction.LOGIN_FAILED,
            ip_address=request.client.host if request.client else None,
            details={"reason": "Account locked"},
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until}",
        )

    # Verify password
    if not user.verify_password(login_data.password):
        # Increment failed login attempts
        user.increment_failed_login()

        # Lock account if too many failed attempts
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=settings.LOCKOUT_DURATION_MINUTES
            )
            logger.warning(f"Account locked: {user.username}")

        await db.commit()

        # Log failed login
        await audit_service.log(
            user=user,
            action=AuditAction.LOGIN_FAILED,
            ip_address=request.client.host if request.client else None,
            details={"attempts": user.failed_login_attempts},
            success=False,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Check if user is active
    if not user.is_active:
        await audit_service.log(
            user=user,
            action=AuditAction.LOGIN_FAILED,
            ip_address=request.client.host if request.client else None,
            details={"reason": "Inactive account"},
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    # Reset failed login attempts
    user.reset_failed_login()
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Log successful login
    await audit_service.log(
        user=user,
        action=AuditAction.LOGIN,
        ip_address=request.client.host if request.client else None,
        success=True,
    )

    logger.info(f"User logged in: {user.username}")

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Logout current user.

    Args:
        request: FastAPI request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    audit_service = AuditService(db)

    # Log logout
    await audit_service.log(
        user=current_user,
        action=AuditAction.LOGOUT,
        ip_address=request.client.host if request.client else None,
        success=True,
    )

    logger.info(f"User logged out: {current_user.username}")

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user data
    """
    return current_user
