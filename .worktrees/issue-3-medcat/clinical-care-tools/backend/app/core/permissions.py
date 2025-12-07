"""
Role-Based Access Control (RBAC) system.

Defines permissions for each role and provides decorators for enforcement.
"""

from typing import List, Callable
from functools import wraps
from fastapi import HTTPException, status


# Role permission definitions
# Format: "resource:action" where action can be * (wildcard) or specific
ROLE_PERMISSIONS = {
    "admin": [
        # Admin has full access to all resources
        "user:*",
        "project:*",
        "task:*",
        "document:*",
        "module:*",
        "patient:*",
        "audit:*",
    ],
    "clinician": [
        # Clinician has full patient access and limited document/module access
        "patient:*",
        "document:read",
        "document:write",
        "module:patient-search",
        "module:patient-timeline",
        "module:concept-extraction",
    ],
    "researcher": [
        # Researcher has read-only access to patients and documents
        "patient:read",
        "document:read",
        "module:analytics",
        "module:cohort-builder",
    ],
    "viewer": [
        # Viewer has minimal read-only access
        "document:read",
    ],
}


def has_permission(role: str, required_permission: str) -> bool:
    """
    Check if a role has a specific permission.

    Supports wildcard matching (e.g., "user:*" grants "user:read", "user:write").

    Args:
        role: User role (admin, clinician, researcher, viewer)
        required_permission: Permission to check (format: "resource:action")

    Returns:
        True if role has permission, False otherwise

    Examples:
        >>> has_permission("admin", "user:read")
        True  # Admin has user:*

        >>> has_permission("clinician", "patient:write")
        True  # Clinician has patient:*

        >>> has_permission("researcher", "patient:write")
        False  # Researcher only has patient:read
    """
    # Get permissions for role
    role_perms = ROLE_PERMISSIONS.get(role, [])

    # Check for exact match
    if required_permission in role_perms:
        return True

    # Check for wildcard match
    # Example: user:* grants user:read, user:write, user:delete
    resource, action = required_permission.split(":", 1)
    wildcard_perm = f"{resource}:*"

    return wildcard_perm in role_perms


def require_permission(*permissions: str):
    """
    Decorator to enforce permission requirements on endpoints.

    Checks that current user has ALL specified permissions.
    Raises 403 Forbidden if any permission is missing.

    Args:
        *permissions: One or more required permissions (format: "resource:action")

    Returns:
        Decorated function that checks permissions before execution

    Usage:
        @router.get("/api/v1/users")
        @require_permission("user:read")
        async def list_users(current_user: User = Depends(get_current_user)):
            # Only users with user:read permission can access this
            return await get_all_users()

        @router.post("/api/v1/patients")
        @require_permission("patient:write")
        async def create_patient(current_user: User = Depends(get_current_user)):
            # Only users with patient:write permission can access this
            return await create_new_patient()

        @router.get("/api/v1/analytics")
        @require_permission("patient:read", "module:analytics")
        async def get_analytics(current_user: User = Depends(get_current_user)):
            # Requires BOTH patient:read AND module:analytics
            return await get_patient_analytics()

    Raises:
        HTTPException: 403 Forbidden if user lacks required permission
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                # Try positional args (for testing)
                if args and hasattr(args[0], "role"):
                    current_user = args[0]

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Check all required permissions
            user_role = current_user.role
            for perm in permissions:
                if not has_permission(user_role, perm):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required: {', '.join(permissions)}",
                    )

            # All permissions granted, call function
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                # Try positional args (for testing)
                if args and hasattr(args[0], "role"):
                    current_user = args[0]

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Check all required permissions
            user_role = current_user.role
            for perm in permissions:
                if not has_permission(user_role, perm):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required: {', '.join(permissions)}",
                    )

            # All permissions granted, call function
            return await func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_user_permissions(role: str) -> List[str]:
    """
    Get all permissions for a role.

    Args:
        role: User role

    Returns:
        List of permissions for the role

    Example:
        >>> get_user_permissions("admin")
        ['user:*', 'project:*', 'task:*', 'document:*', 'module:*', 'patient:*', 'audit:*']
    """
    return ROLE_PERMISSIONS.get(role, [])


def check_permissions(role: str, required_permissions: List[str]) -> bool:
    """
    Check if a role has ALL specified permissions.

    Args:
        role: User role
        required_permissions: List of required permissions

    Returns:
        True if role has all permissions, False otherwise

    Example:
        >>> check_permissions("researcher", ["patient:read", "document:read"])
        True

        >>> check_permissions("researcher", ["patient:read", "patient:write"])
        False  # Researcher doesn't have patient:write
    """
    return all(has_permission(role, perm) for perm in required_permissions)
