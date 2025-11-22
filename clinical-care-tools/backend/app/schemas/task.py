"""
Pydantic schemas for Task models.

Defines request/response schemas for task management endpoints.
"""

from datetime import datetime
from typing import Optional, Literal, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Base task schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Task name")
    description: str = Field("", max_length=2000, description="Task description")
    task_type: Literal[
        "annotation",
        "search",
        "review",
        "validation"
    ] = Field(..., description="Type of task")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    assigned_to: UUID = Field(..., description="User assigned to the task")
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        "medium",
        description="Task priority"
    )
    due_date: Optional[datetime] = Field(None, description="When task is due")
    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task-specific configuration (document IDs, search criteria, etc.)"
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    task_type: Optional[Literal["annotation", "search", "review", "validation"]] = Field(None)
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = Field(None)
    due_date: Optional[datetime] = Field(None)
    configuration: Optional[Dict[str, Any]] = Field(None)


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""

    status: Literal["pending", "in_progress", "complete", "cancelled"] = Field(
        ...,
        description="New task status"
    )


class TaskAssign(BaseModel):
    """Schema for assigning a task to a user."""

    user_id: UUID = Field(..., description="User ID to assign the task to")


class TaskResponse(TaskBase):
    """Schema for task response."""

    id: UUID
    project_id: UUID
    assigned_to: UUID
    assigned_username: Optional[str] = Field(None, description="Username of assigned user")
    assigned_email: Optional[str] = Field(None, description="Email of assigned user")
    status: str
    priority: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    configuration: Dict[str, Any]
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID

    class Config:
        """Pydantic config."""
        from_attributes = True


class TaskList(BaseModel):
    """Schema for paginated task list response."""

    items: list[TaskResponse]
    total: int
    page: int
    per_page: int
    pages: int


class TaskSummary(BaseModel):
    """Schema for task summary (minimal info)."""

    id: UUID
    name: str
    task_type: str
    status: str
    priority: str
    assigned_to: UUID
    due_date: Optional[datetime]
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class TaskStatistics(BaseModel):
    """Schema for project task statistics."""

    total: int
    pending: int
    in_progress: int
    complete: int
    cancelled: int
    overdue: int
    by_priority: Dict[str, int]
    by_type: Dict[str, int]
    by_assignee: Dict[str, int]