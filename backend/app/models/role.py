"""Role and Permission definitions.

Static definitions of roles and their permissions for RBAC.
"""
from enum import Enum
from typing import Dict, List

from pydantic import BaseModel


class RoleEnum(str, Enum):
    """Available user roles."""

    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class Permission(str, Enum):
    """Available permissions in the system."""

    # User management
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Patient data access
    PATIENT_READ = "patient:read"
    PATIENT_WRITE = "patient:write"
    PATIENT_DELETE = "patient:delete"

    # Document management
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_DELETE = "document:delete"

    # NLP processing
    NLP_PROCESS = "nlp:process"
    NLP_VIEW_RESULTS = "nlp:view_results"

    # Cohort/Research
    COHORT_CREATE = "cohort:create"
    COHORT_VIEW = "cohort:view"
    COHORT_EXPORT = "cohort:export"

    # Emergency access
    BREAK_GLASS = "break_glass:access"

    # System administration
    SYSTEM_CONFIG = "system:config"
    AUDIT_VIEW = "audit:view"


class RolePermissions(BaseModel):
    """Role with its permissions."""

    role: RoleEnum
    description: str
    permissions: List[Permission]


# Role definitions with permissions
ROLE_PERMISSIONS_MAP: Dict[RoleEnum, RolePermissions] = {
    RoleEnum.CLINICIAN: RolePermissions(
        role=RoleEnum.CLINICIAN,
        description="Clinical staff member with patient care access",
        permissions=[
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_UPLOAD,
            Permission.NLP_PROCESS,
            Permission.NLP_VIEW_RESULTS,
        ],
    ),
    RoleEnum.RESEARCHER: RolePermissions(
        role=RoleEnum.RESEARCHER,
        description="Research staff with cohort identification and analytics access",
        permissions=[
            Permission.PATIENT_READ,  # Read-only for research
            Permission.DOCUMENT_READ,
            Permission.NLP_PROCESS,
            Permission.NLP_VIEW_RESULTS,
            Permission.COHORT_CREATE,
            Permission.COHORT_VIEW,
            Permission.COHORT_EXPORT,
        ],
    ),
    RoleEnum.ADMIN: RolePermissions(
        role=RoleEnum.ADMIN,
        description="System administrator with full access",
        permissions=[
            # User management
            Permission.USER_READ,
            Permission.USER_CREATE,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            # Patient data (full access)
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.PATIENT_DELETE,
            # Document management (full access)
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_UPLOAD,
            Permission.DOCUMENT_DELETE,
            # NLP
            Permission.NLP_PROCESS,
            Permission.NLP_VIEW_RESULTS,
            # Cohort/Research
            Permission.COHORT_CREATE,
            Permission.COHORT_VIEW,
            Permission.COHORT_EXPORT,
            # System
            Permission.SYSTEM_CONFIG,
            Permission.AUDIT_VIEW,
        ],
    ),
}


def get_role_permissions(role: RoleEnum) -> RolePermissions:
    """Get permissions for a role.

    Args:
        role: The role to get permissions for

    Returns:
        RolePermissions object with role details and permissions
    """
    return ROLE_PERMISSIONS_MAP[role]


def user_has_permission(role: RoleEnum, permission: Permission, can_break_glass: bool = False) -> bool:
    """Check if a user with given role has a specific permission.

    Args:
        role: User's role
        permission: Permission to check
        can_break_glass: Whether user has break-glass capability

    Returns:
        True if user has the permission, False otherwise
    """
    role_perms = ROLE_PERMISSIONS_MAP[role]

    # Break-glass users get BREAK_GLASS permission
    if permission == Permission.BREAK_GLASS:
        return can_break_glass

    return permission in role_perms.permissions


def get_all_roles() -> List[RolePermissions]:
    """Get all available roles with their permissions.

    Returns:
        List of all role definitions
    """
    return list(ROLE_PERMISSIONS_MAP.values())
