"""
Pydantic schemas for Project models.

Defines request/response schemas for project management endpoints.
"""

from datetime import datetime
from typing import Optional, Literal, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProjectBase(BaseModel):
    """Base project schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: str = Field("", max_length=2000, description="Project description")
    project_type: Literal[
        "patient_search",
        "timeline",
        "cds",
        "cohort",
        "annotation"
    ] = Field(..., description="Type of project")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    status: Literal["active", "complete", "archived"] = Field(
        "active",
        description="Initial project status"
    )
    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Project-specific configuration"
    )
    dataset_id: Optional[UUID] = Field(None, description="Reference to shared dataset")
    medcat_model_id: Optional[UUID] = Field(None, description="Reference to MedCAT model")


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[Literal["active", "complete", "archived"]] = Field(None)
    configuration: Optional[Dict[str, Any]] = Field(None)
    dataset_id: Optional[UUID] = Field(None)
    medcat_model_id: Optional[UUID] = Field(None)


class ProjectMemberBase(BaseModel):
    """Base schema for project member."""

    user_id: UUID = Field(..., description="User ID")
    role: Literal["owner", "member", "viewer"] = Field(
        "member",
        description="Role in the project"
    )


class ProjectMemberAdd(BaseModel):
    """Schema for adding a project member."""

    user_id: UUID = Field(..., description="User ID to add")
    role: Literal["member", "viewer"] = Field(
        "member",
        description="Role in the project (cannot add as owner)"
    )


class ProjectMemberResponse(ProjectMemberBase):
    """Schema for project member response."""

    id: UUID
    project_id: UUID
    username: Optional[str] = Field(None, description="Username from user relation")
    email: Optional[str] = Field(None, description="Email from user relation")
    joined_at: datetime
    added_by: UUID

    class Config:
        """Pydantic config."""
        from_attributes = True


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: UUID
    status: str
    dataset_id: Optional[UUID]
    medcat_model_id: Optional[UUID]
    configuration: Dict[str, Any]
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    members: list[ProjectMemberResponse] = Field(
        default_factory=list,
        description="Project members"
    )
    tasks_count: int = Field(0, description="Number of tasks in project")
    documents_count: int = Field(0, description="Number of documents in project")

    class Config:
        """Pydantic config."""
        from_attributes = True


class ProjectList(BaseModel):
    """Schema for paginated project list response."""

    items: list[ProjectResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ProjectSummary(BaseModel):
    """Schema for project summary (minimal info)."""

    id: UUID
    name: str
    project_type: str
    status: str
    members_count: int
    tasks_count: int
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class ProjectStatistics(BaseModel):
    """Schema for project statistics."""

    id: UUID
    name: str
    members_count: int
    tasks_total: int
    tasks_pending: int
    tasks_in_progress: int
    tasks_complete: int
    documents_count: int
    entities_extracted: int
    last_activity: Optional[datetime]