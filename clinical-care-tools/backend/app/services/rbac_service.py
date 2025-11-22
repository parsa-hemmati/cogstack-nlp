"""
Role-Based Access Control (RBAC) Service for Clinical Care Tools.

Implements fine-grained permission checking for healthcare compliance.
HIPAA Compliance: Enforces minimum necessary access principle.
"""
from typing import List, Optional, Dict, Set
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.audit_log import AuditLog
from datetime import datetime, timezone


class Role(str, Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    AUDITOR = "auditor"


class Resource(str, Enum):
    """Protected resources in the system."""
    PATIENTS = "patients"
    DOCUMENTS = "documents"
    PROJECTS = "projects"
    USERS = "users"
    AUDIT_LOGS = "audit_logs"
    SESSIONS = "sessions"
    MODULES = "modules"
    SYSTEM = "system"


class Action(str, Enum):
    """Actions that can be performed on resources."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    AUDIT = "audit"
    EXPORT = "export"
    EXECUTE = "execute"  # For module execution
    MANAGE = "manage"    # For administrative actions


class RBACService:
    """Service for managing role-based access control."""

    # Define role hierarchy (higher roles inherit lower role permissions)
    ROLE_HIERARCHY = {
        Role.ADMIN: [Role.CLINICIAN, Role.RESEARCHER, Role.AUDITOR],
        Role.CLINICIAN: [Role.RESEARCHER],
        Role.RESEARCHER: [],
        Role.AUDITOR: []
    }

    # Define base permissions for each role
    ROLE_PERMISSIONS = {
        Role.ADMIN: {
            # Admin has full access to everything
            Resource.USERS: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.MANAGE},
            Resource.PROJECTS: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.MANAGE},
            Resource.DOCUMENTS: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
            Resource.PATIENTS: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
            Resource.AUDIT_LOGS: {Action.READ, Action.AUDIT, Action.EXPORT},
            Resource.SESSIONS: {Action.READ, Action.DELETE, Action.MANAGE},
            Resource.MODULES: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXECUTE, Action.MANAGE},
            Resource.SYSTEM: {Action.READ, Action.UPDATE, Action.MANAGE}
        },
        Role.CLINICIAN: {
            # Clinicians can access patient data and documents
            Resource.PATIENTS: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
            Resource.DOCUMENTS: {Action.CREATE, Action.READ, Action.UPDATE},
            Resource.PROJECTS: {Action.READ, Action.UPDATE},  # Only projects they're assigned to
            Resource.MODULES: {Action.READ, Action.EXECUTE},  # Can use modules
            Resource.AUDIT_LOGS: {Action.READ},  # Only their own audit logs
            Resource.SESSIONS: {Action.READ, Action.DELETE}  # Only their own sessions
        },
        Role.RESEARCHER: {
            # Researchers have limited access, mainly for analysis
            Resource.PATIENTS: {Action.READ},  # De-identified data only
            Resource.DOCUMENTS: {Action.READ},  # De-identified documents
            Resource.PROJECTS: {Action.READ},  # Only assigned projects
            Resource.MODULES: {Action.READ, Action.EXECUTE},  # Can use analysis modules
            Resource.AUDIT_LOGS: {Action.READ},  # Only their own
            Resource.SESSIONS: {Action.READ}  # Only their own
        },
        Role.AUDITOR: {
            # Auditors can view everything but not modify
            Resource.AUDIT_LOGS: {Action.READ, Action.AUDIT, Action.EXPORT},
            Resource.USERS: {Action.READ},
            Resource.PROJECTS: {Action.READ},
            Resource.DOCUMENTS: {Action.READ, Action.AUDIT},
            Resource.PATIENTS: {Action.READ, Action.AUDIT},
            Resource.SESSIONS: {Action.READ},
            Resource.SYSTEM: {Action.READ}
        }
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize RBAC service.

        Args:
            db: Database session for audit logging
        """
        self.db = db

    async def check_permission(
        self,
        user: User,
        resource: Resource,
        action: Action,
        resource_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Check if user has permission to perform action on resource.

        Args:
            user: User object
            resource: Resource type
            action: Action to perform
            resource_id: Optional specific resource ID
            context: Optional context for fine-grained checks

        Returns:
            True if permission granted, False otherwise
        """
        # System users (for background tasks) have full access
        if user.email == "system@clinical-care-tools.local":
            return True

        # Get user's effective permissions
        permissions = self._get_effective_permissions(user.role)

        # Check if user has permission for resource and action
        if resource in permissions and action in permissions[resource]:
            # Additional context-based checks
            if context:
                return await self._check_contextual_permission(
                    user, resource, action, resource_id, context
                )
            return True

        # Log denied access attempt
        await self._audit_log(
            action="PERMISSION_DENIED",
            user_id=str(user.id),
            details={
                "resource": resource.value,
                "action": action.value,
                "resource_id": resource_id
            }
        )

        return False

    def _get_effective_permissions(self, role: str) -> Dict[Resource, Set[Action]]:
        """
        Get all effective permissions for a role (including inherited).

        Args:
            role: User role

        Returns:
            Dictionary of resources and allowed actions
        """
        role_enum = Role(role)
        permissions = {}

        # Start with role's direct permissions
        if role_enum in self.ROLE_PERMISSIONS:
            permissions = self.ROLE_PERMISSIONS[role_enum].copy()

        # Add inherited permissions from lower roles
        for inherited_role in self.ROLE_HIERARCHY.get(role_enum, []):
            if inherited_role in self.ROLE_PERMISSIONS:
                for resource, actions in self.ROLE_PERMISSIONS[inherited_role].items():
                    if resource in permissions:
                        permissions[resource] = permissions[resource].union(actions)
                    else:
                        permissions[resource] = actions.copy()

        return permissions

    async def _check_contextual_permission(
        self,
        user: User,
        resource: Resource,
        action: Action,
        resource_id: Optional[str],
        context: Dict
    ) -> bool:
        """
        Perform context-based permission checks.

        Args:
            user: User object
            resource: Resource type
            action: Action to perform
            resource_id: Specific resource ID
            context: Context information

        Returns:
            True if contextual permission granted
        """
        # Check project membership for non-admins
        if resource in [Resource.PATIENTS, Resource.DOCUMENTS, Resource.PROJECTS]:
            if user.role != Role.ADMIN and "project_id" in context:
                # Check if user is member of the project
                # This would query the project_members table
                is_member = context.get("is_project_member", False)
                if not is_member:
                    return False

        # Check ownership for personal resources
        if resource in [Resource.SESSIONS, Resource.AUDIT_LOGS]:
            if user.role != Role.ADMIN and user.role != Role.AUDITOR:
                # Non-admins and non-auditors can only access their own
                owner_id = context.get("owner_id")
                if owner_id and owner_id != str(user.id):
                    return False

        # Researchers only get de-identified data
        if user.role == Role.RESEARCHER and resource in [Resource.PATIENTS, Resource.DOCUMENTS]:
            if action != Action.READ:
                return False
            # Ensure de-identification flag is set
            if not context.get("is_deidentified", False):
                return False

        # Break-glass access checks
        if context.get("is_break_glass", False):
            # Only clinicians and admins can use break-glass
            if user.role not in [Role.ADMIN, Role.CLINICIAN]:
                return False
            # Must provide reason
            if not context.get("break_glass_reason"):
                return False

        return True

    def get_user_permissions(self, user: User) -> List[str]:
        """
        Get list of all permissions for a user.

        Args:
            user: User object

        Returns:
            List of permission strings (resource:action format)
        """
        permissions = self._get_effective_permissions(user.role)
        permission_list = []

        for resource, actions in permissions.items():
            for action in actions:
                permission_list.append(f"{resource.value}:{action.value}")

        return sorted(permission_list)

    def require_role(self, allowed_roles: List[Role]):
        """
        Dependency function to require specific roles.

        Args:
            allowed_roles: List of allowed roles

        Returns:
            Dependency function for FastAPI

        Usage:
            @router.get("/admin", dependencies=[Depends(rbac.require_role([Role.ADMIN]))])
        """
        def role_checker(current_user: User = Depends(self.get_current_user)):
            if Role(current_user.role) not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {current_user.role} not authorized for this operation"
                )
            return current_user
        return role_checker

    def require_permission(self, resource: Resource, action: Action):
        """
        Dependency function to require specific permission.

        Args:
            resource: Resource type
            action: Action type

        Returns:
            Dependency function for FastAPI

        Usage:
            @router.post("/users", dependencies=[Depends(rbac.require_permission(Resource.USERS, Action.CREATE))])
        """
        async def permission_checker(
            current_user: User = Depends(self.get_current_user)
        ):
            has_permission = await self.check_permission(
                current_user,
                resource,
                action
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied for {action.value} on {resource.value}"
                )
            return current_user
        return permission_checker

    async def check_data_access(
        self,
        user: User,
        data_type: str,
        identifiable: bool = True
    ) -> bool:
        """
        Check if user can access specific type of data.

        Args:
            user: User object
            data_type: Type of data (clinical, demographic, etc.)
            identifiable: Whether data contains PHI

        Returns:
            True if access granted

        HIPAA Note: Implements minimum necessary standard.
        """
        # Researchers only get de-identified data
        if user.role == Role.RESEARCHER and identifiable:
            await self._audit_log(
                action="PHI_ACCESS_DENIED",
                user_id=str(user.id),
                details={
                    "data_type": data_type,
                    "reason": "researcher_identifiable_data"
                }
            )
            return False

        # Auditors can view but not export PHI
        if user.role == Role.AUDITOR and identifiable:
            # They can read for audit purposes but not export
            return True  # Read-only access

        # Clinicians and admins have full access to PHI
        if user.role in [Role.ADMIN, Role.CLINICIAN]:
            await self._audit_log(
                action="PHI_ACCESS_GRANTED",
                user_id=str(user.id),
                details={
                    "data_type": data_type,
                    "identifiable": identifiable
                }
            )
            return True

        return False

    async def grant_break_glass_access(
        self,
        user: User,
        reason: str,
        duration_minutes: int = 60
    ) -> Dict:
        """
        Grant emergency break-glass access.

        Args:
            user: User requesting access
            reason: Reason for emergency access
            duration_minutes: Duration of elevated access

        Returns:
            Access grant details

        Compliance: Requires post-access review within 24 hours.
        """
        # Only clinicians and admins can use break-glass
        if user.role not in [Role.ADMIN, Role.CLINICIAN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Break-glass access not available for this role"
            )

        # Create break-glass grant
        grant = {
            "user_id": str(user.id),
            "granted_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=duration_minutes),
            "reason": reason,
            "status": "active"
        }

        # Audit log with HIGH priority
        await self._audit_log(
            action="BREAK_GLASS_ACTIVATED",
            user_id=str(user.id),
            details={
                "reason": reason,
                "duration_minutes": duration_minutes,
                "alert_level": "HIGH",
                "requires_review": True,
                "review_deadline": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            }
        )

        # NOTE: Send immediate notification to security team
        # await self._notify_security_team(user, reason)

        return grant

    async def _audit_log(
        self,
        action: str,
        user_id: str,
        details: Dict
    ):
        """Create audit log entry for RBAC events."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="RBAC",
            resource_id=details.get("resource_id"),
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)
        await self.db.commit()

    # Placeholder for current user dependency
    async def get_current_user(self):
        """Placeholder - will be replaced with actual implementation."""
        pass