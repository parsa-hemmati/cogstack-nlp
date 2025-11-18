"""User CRUD API endpoints.

Endpoints for user management:
- List users (paginated)
- Get user by ID
- Create user (admin only)
- Update user (admin only)
- Delete user (soft delete, admin only)

All operations include RBAC protection and audit logging.
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()


@router.get("", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination (admin only).

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        role: Optional filter by role
        is_active: Optional filter by active status
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Paginated list of users

    Raises:
        HTTPException: 403 if not admin
    """
    # Build query with filters
    query = select(User)

    if role is not None:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="LIST_USERS",
        resource_type="user",
        details={"page": page, "page_size": page_size, "filters": {"role": role, "is_active": is_active}},
    )

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID (admin only).

    Args:
        user_id: User UUID
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        User details

    Raises:
        HTTPException: 404 if user not found, 403 if not admin
    """
    # Query user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="VIEW_USER",
        resource_type="user",
        resource_id=str(user_id),
    )

    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only).

    Args:
        user_data: User creation data
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Created user details

    Raises:
        HTTPException: 400 if username/email exists, 403 if not admin
    """
    # Check for duplicate username
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists",
        )

    # Check for duplicate email
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_email = result.scalar_one_or_none()

    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' already exists",
        )

    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        role=user_data.role,
        is_active=user_data.is_active,
        can_break_glass=user_data.can_break_glass,
    )
    new_user.set_password(user_data.password)

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="CREATE_USER",
        resource_type="user",
        resource_id=str(new_user.id),
        details={
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
        },
    )

    return UserResponse.model_validate(new_user)


@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update user (admin only).

    Args:
        user_id: User UUID
        user_data: User update data
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated user details

    Raises:
        HTTPException: 404 if user not found, 403 if not admin
    """
    # Query user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Track changes for audit log
    changes = {}

    # Update fields if provided
    if user_data.email is not None:
        changes["email"] = {"old": user.email, "new": user_data.email}
        user.email = user_data.email

    if user_data.role is not None:
        changes["role"] = {"old": user.role, "new": user_data.role}
        user.role = user_data.role

    if user_data.is_active is not None:
        changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}
        user.is_active = user_data.is_active

    if user_data.can_break_glass is not None:
        changes["can_break_glass"] = {
            "old": user.can_break_glass,
            "new": user_data.can_break_glass,
        }
        user.can_break_glass = user_data.can_break_glass

    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="UPDATE_USER",
        resource_type="user",
        resource_id=str(user_id),
        details={"changes": changes},
    )

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete user (soft delete by setting is_active=False, admin only).

    Args:
        user_id: User UUID
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 404 if user not found, 400 if self-delete, 403 if not admin
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Query user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Soft delete (set is_active = False)
    user.is_active = False

    await db.commit()

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="DELETE_USER",
        resource_type="user",
        resource_id=str(user_id),
        details={"username": user.username, "soft_delete": True},
    )

    return None
