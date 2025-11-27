"""Role Management API endpoints.

Endpoints for managing roles and permissions:
- List available roles and their permissions
- Get user's effective permissions
- Assign role to user (semantic wrapper around user update)

All operations include RBAC protection and audit logging.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.role import (
    Permission,
    RoleEnum,
    get_all_roles,
    get_role_permissions,
    user_has_permission,
)
from app.models.user import User
from app.schemas.role import (
    RoleAssignRequest,
    RoleInfo,
    RoleListResponse,
    UserPermissionsResponse,
)
from app.services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()


@router.get("", response_model=RoleListResponse, status_code=status.HTTP_200_OK)
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available roles with their permissions.

    Available to all authenticated users (for viewing role descriptions).

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of all roles with descriptions and permissions
    """
    # Get all roles
    all_roles = get_all_roles()

    # Convert to response format
    role_infos = [
        RoleInfo(
            role=role.role, description=role.description, permissions=role.permissions
        )
        for role in all_roles
    ]

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="LIST_ROLES",
        resource_type="role",
        details={"count": len(role_infos)},
    )

    return RoleListResponse(roles=role_infos)


@router.get(
    "/{role}",
    response_model=RoleInfo,
    status_code=status.HTTP_200_OK,
)
async def get_role(
    role: RoleEnum,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details about a specific role.

    Args:
        role: Role to query
        current_user: Current authenticated user
        db: Database session

    Returns:
        Role details with permissions

    Raises:
        HTTPException: 404 if role not found
    """
    try:
        role_perms = get_role_permissions(role)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role}' not found",
        )

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="VIEW_ROLE",
        resource_type="role",
        resource_id=role.value,
    )

    return RoleInfo(
        role=role_perms.role,
        description=role_perms.description,
        permissions=role_perms.permissions,
    )


@router.get(
    "/users/{user_id}/permissions",
    response_model=UserPermissionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get effective permissions for a user based on their role.

    Args:
        user_id: User UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        User's effective permissions

    Raises:
        HTTPException: 404 if user not found, 403 if not authorized
    """
    # Users can view their own permissions, admins can view anyone's
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own permissions unless admin",
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

    # Get role permissions
    role_enum = RoleEnum(user.role)
    role_perms = get_role_permissions(role_enum)
    permissions = list(role_perms.permissions)

    # Add break-glass permission if user has it
    if user.can_break_glass:
        permissions.append(Permission.BREAK_GLASS)

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="VIEW_USER_PERMISSIONS",
        resource_type="user",
        resource_id=str(user_id),
    )

    return UserPermissionsResponse(
        user_id=str(user.id),
        username=user.username,
        role=role_enum,
        can_break_glass=user.can_break_glass,
        permissions=permissions,
    )


@router.put(
    "/users/{user_id}/role",
    response_model=UserPermissionsResponse,
    status_code=status.HTTP_200_OK,
)
async def assign_role(
    user_id: UUID,
    role_data: RoleAssignRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Assign a role to a user (admin only).

    Semantic wrapper around user update for role assignment.

    Args:
        user_id: User UUID
        role_data: Role to assign and reason
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated user permissions

    Raises:
        HTTPException: 404 if user not found, 403 if not admin, 400 if self-role-change
    """
    # Prevent admins from changing their own role (security)
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role. Another admin must do this.",
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

    # Store old role for audit
    old_role = user.role

    # Update role
    user.role = role_data.role.value

    await db.commit()
    await db.refresh(user)

    # Audit log with reason
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="ASSIGN_ROLE",
        resource_type="user",
        resource_id=str(user_id),
        details={
            "old_role": old_role,
            "new_role": role_data.role.value,
            "reason": role_data.reason,
        },
    )

    # Get updated permissions
    role_enum = RoleEnum(user.role)
    role_perms = get_role_permissions(role_enum)
    permissions = list(role_perms.permissions)

    if user.can_break_glass:
        permissions.append(Permission.BREAK_GLASS)

    return UserPermissionsResponse(
        user_id=str(user.id),
        username=user.username,
        role=role_enum,
        can_break_glass=user.can_break_glass,
        permissions=permissions,
    )
