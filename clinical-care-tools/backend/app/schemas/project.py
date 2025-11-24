"""
Pydantic schemas for Project API endpoints.

Schemas:
- ProjectCreate: Creating new projects
- ProjectUpdate: Updating existing projects
- ProjectResponse: Project data in responses
- ProjectMemberAdd: Adding members to projects
- ProjectMemberResponse: Project member data in responses
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ProjectMemberRole(str, Enum):
    """Project member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectCreate(BaseModel):
    """Schema for creating new project."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Project name"
    )
    description: Optional[str] = Field(
        None,
        description="Project description"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Clinical Research Project",
                    "description": "Research project for patient cohort analysis"
                }
            ]
        }
    }


class ProjectUpdate(BaseModel):
    """Schema for updating existing project."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Project name"
    )
    description: Optional[str] = Field(
        None,
        description="Project description"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Project Name",
                    "description": "Updated description"
                }
            ]
        }
    }


class ProjectMemberResponse(BaseModel):
    """Schema for project member data in responses."""

    user_id: str
    role: str
    added_at: datetime
    added_by: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "role": "owner",
                    "added_at": "2025-01-08T12:34:56",
                    "added_by": "550e8400-e29b-41d4-a716-446655440001"
                }
            ]
        }
    }


class ProjectResponse(BaseModel):
    """Schema for project data in API responses."""

    id: str
    name: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    members: List[ProjectMemberResponse] = []

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Clinical Research Project",
                    "description": "Research project for patient cohort analysis",
                    "created_by": "550e8400-e29b-41d4-a716-446655440001",
                    "created_at": "2025-01-08T12:34:56",
                    "updated_at": "2025-01-08T12:34:56",
                    "members": [
                        {
                            "user_id": "550e8400-e29b-41d4-a716-446655440001",
                            "role": "owner",
                            "added_at": "2025-01-08T12:34:56",
                            "added_by": "550e8400-e29b-41d4-a716-446655440001"
                        }
                    ]
                }
            ]
        }
    }


class ProjectMemberAdd(BaseModel):
    """Schema for adding member to project."""

    user_id: str = Field(
        ...,
        description="User ID to add as project member"
    )
    role: ProjectMemberRole = Field(
        default=ProjectMemberRole.MEMBER,
        description="Member role (owner, admin, member, viewer)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440002",
                    "role": "member"
                }
            ]
        }
    }
