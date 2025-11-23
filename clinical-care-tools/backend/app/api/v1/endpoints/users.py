"""
User Management API endpoints.

Provides:
- GET /api/v1/users - List all users (admin only)
- POST /api/v1/users - Create new user (admin only)
- PATCH /api/v1/users/{user_id} - Update user (admin only)

All endpoints require admin permission and create audit logs.
"""

from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services import user_service
from app.services.audit_service import log_action


router = APIRouter()


@router.get(
    "/users",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Retrieve list of all users. Requires admin permission."
)
async def get_users(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[UserResponse]:
    """
    Retrieve all users.

    **Permission**: Admin only

    **Returns**: List of all users with id, username, full_name, role, is_active, must_change_password

    **Example**:
    ```bash
    curl -X GET http://localhost:8000/api/v1/users \
      -H "Authorization: Bearer <admin_token>"
    ```
    """
    users = await user_service.get_all_users(db)
    return [UserResponse.model_validate(user) for user in users]


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create new user with hashed password. Requires admin permission."
)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    """
    Create new user.

    **Permission**: Admin only

    **Request Body**:
    - username: Unique username (3-50 characters)
    - full_name: User's full name
    - password: Password (min 8 characters, must contain letter and number)
    - role: User role (admin, clinician, researcher, viewer)

    **Returns**: Created user object

    **Audit**: Creates CREATE_USER audit log entry

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/users \
      -H "Authorization: Bearer <admin_token>" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "john_doe",
        "full_name": "John Doe",
        "password": "SecurePass123!",
        "role": "clinician"
      }'
    ```
    """
    # Create user
    new_user = await user_service.create_user(db, user_data)

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_admin.id),
        username=current_admin.username,
        action="CREATE_USER",
        resource_type="user",
        resource_id=str(new_user.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "created_username": new_user.username,
            "created_role": new_user.role
        }
    )

    return UserResponse.model_validate(new_user)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update existing user. Requires admin permission."
)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    request: Request,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    """
    Update existing user.

    **Permission**: Admin only

    **Path Parameters**:
    - user_id: User ID (UUID)

    **Request Body** (all fields optional):
    - full_name: New full name
    - role: New role
    - is_active: Active status
    - must_change_password: Whether user must change password

    **Returns**: Updated user object

    **Audit**: Creates UPDATE_USER audit log entry

    **Example**:
    ```bash
    curl -X PATCH http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440000 \
      -H "Authorization: Bearer <admin_token>" \
      -H "Content-Type: application/json" \
      -d '{
        "full_name": "John Doe Updated",
        "is_active": false
      }'
    ```
    """
    # Update user
    updated_user = await user_service.update_user(db, user_id, update_data)

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_admin.id),
        username=current_admin.username,
        action="UPDATE_USER",
        resource_type="user",
        resource_id=str(updated_user.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "updated_username": updated_user.username,
            "updated_fields": update_data.model_dump(exclude_unset=True)
        }
    )

    return UserResponse.model_validate(updated_user)
