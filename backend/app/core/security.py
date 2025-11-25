"""
Security Module
JWT dependencies, RBAC permission checking, current user extraction
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import auth_service


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extract current user from JWT token in Authorization header.

    Args:
        authorization: Authorization header (Bearer <token>)
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException(401): If token is missing or invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Query user from database
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def require_role(*allowed_roles: str):
    """
    Dependency to require specific roles (RBAC).

    Args:
        *allowed_roles: Roles that are allowed (e.g., "admin", "clinician")

    Returns:
        Dependency function

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            return {"message": "Admin access granted"}
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


def require_active_user():
    """Dependency to require active user (simplified version of get_current_user)."""
    return Depends(get_current_user)
