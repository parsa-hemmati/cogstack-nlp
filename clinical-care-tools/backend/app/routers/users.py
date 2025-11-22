"""
User Management API Router.

Provides CRUD operations for user management (admin-only access).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_admin
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserList,
    UserMe
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=UserList)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
) -> UserList:
    """
    List all users (admin only).

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        search: Optional search term for username/email
        role: Optional filter by role
        is_active: Optional filter by active status

    Returns:
        Paginated list of users

    Raises:
        HTTPException: 403 if not admin
    """
    service = UserService(db)
    return await service.get_users(
        page=page,
        per_page=per_page,
        search=search,
        role=role,
        is_active=is_active
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Create a new user (admin only).

    Args:
        user_data: User creation data

    Returns:
        Created user

    Raises:
        HTTPException:
            - 400 if username/email already exists or password is weak
            - 403 if not admin
    """
    service = UserService(db)
    user = await service.create_user(
        user_data=user_data,
        created_by=UUID(current_user["id"])
    )
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserMe)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserMe:
    """
    Get current user information.

    Returns:
        Current user details with statistics
    """
    service = UserService(db)
    stats = await service.get_user_stats(UUID(current_user["id"]))
    return UserMe(**stats)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID

    Returns:
        User details

    Raises:
        HTTPException:
            - 403 if not admin
            - 404 if user not found
    """
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update user information (admin only).

    Args:
        user_id: User ID to update
        user_data: Update data (only provided fields will be updated)

    Returns:
        Updated user

    Raises:
        HTTPException:
            - 400 if duplicate username/email
            - 403 if not admin
            - 404 if user not found
    """
    service = UserService(db)
    user = await service.update_user(
        user_id=user_id,
        user_data=user_data,
        updated_by=UUID(current_user["id"])
    )
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Soft delete a user (admin only).

    Sets the user's is_active flag to False rather than removing from database.

    Args:
        user_id: User ID to delete

    Raises:
        HTTPException:
            - 400 if trying to delete self
            - 403 if not admin
            - 404 if user not found
    """
    service = UserService(db)
    await service.delete_user(
        user_id=user_id,
        deleted_by=UUID(current_user["id"])
    )
    return None