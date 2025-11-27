"""
FastAPI dependencies for authentication and authorization.

Provides reusable dependencies for endpoints requiring authentication.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import verify_token


async def get_current_user(
    authorization: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Dependency for FastAPI endpoints requiring authentication.
    Extracts user from Authorization header, verifies JWT token,
    and returns User object from database.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: 401 if token invalid, expired, or user not found

    Usage:
        @router.get("/api/v1/profile")
        async def get_profile(
            current_user: User = Depends(get_current_user)
        ):
            return {"username": current_user.username}

        @router.post("/api/v1/patients")
        @require_permission("patient:write")
        async def create_patient(
            current_user: User = Depends(get_current_user)
        ):
            # Only authenticated users with patient:write can access
            return await create_new_patient(current_user)
    """
    # Extract token from Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    # Verify token
    try:
        payload = verify_token(token)
    except HTTPException:
        # Re-raise token verification errors (expired, invalid, etc.)
        raise

    # Extract user ID from token payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user (convenience dependency).

    Same as get_current_user but with explicit active check emphasis.
    Useful for endpoints that specifically require active users.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Active User object

    Raises:
        HTTPException: 401 if user is inactive

    Usage:
        @router.get("/api/v1/protected")
        async def protected_endpoint(
            current_user: User = Depends(get_current_active_user)
        ):
            # Only active users can access
            return {"message": "Protected resource"}
    """
    # get_current_user already checks is_active, so just return
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current user and verify they have admin role.

    Dependency for admin-only endpoints.
    Requires authenticated user with 'admin' role.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Admin User object

    Raises:
        HTTPException: 403 if user is not admin

    Usage:
        @router.get("/api/v1/admin/users")
        async def get_all_users(
            current_admin: User = Depends(get_current_admin_user)
        ):
            # Only admins can access
            return await fetch_all_users()
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required. Only users with admin role can access this resource."
        )

    return current_user
