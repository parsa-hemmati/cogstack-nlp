"""Role and Permission schemas for API.

Pydantic models for role management operations.
"""
from typing import List

from pydantic import BaseModel, Field

from app.models.role import Permission, RoleEnum


class RoleListResponse(BaseModel):
    """Response for listing all available roles."""

    roles: List["RoleInfo"]


class RoleInfo(BaseModel):
    """Information about a role."""

    role: RoleEnum
    description: str
    permissions: List[Permission]

    model_config = {"from_attributes": True}


class UserPermissionsResponse(BaseModel):
    """Response for user permissions query."""

    user_id: str
    username: str
    role: RoleEnum
    can_break_glass: bool
    permissions: List[Permission] = Field(description="Effective permissions based on role")


class RoleAssignRequest(BaseModel):
    """Request to assign a role to a user."""

    role: RoleEnum = Field(description="Role to assign")
    reason: str = Field(description="Reason for role change (for audit)")
