"""
Pydantic schemas for Task API endpoints.

Schemas:
- TaskCreate: Creating new tasks
- TaskUpdate: Updating existing tasks
- TaskResponse: Task data in responses
- TaskStatus/TaskPriority: Enum values for validation
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCreate(BaseModel):
    """Schema for creating new task."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task title"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed task description"
    )
    assigned_to: Optional[str] = Field(
        None,
        description="User ID to assign task to (UUID)"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Task status"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority"
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Task deadline"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Implement user authentication",
                    "description": "Add JWT-based authentication system",
                    "assigned_to": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "pending",
                    "priority": "high",
                    "due_date": "2025-12-31T23:59:59"
                }
            ]
        }
    }


class TaskUpdate(BaseModel):
    """Schema for updating existing task."""

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Task title"
    )
    description: Optional[str] = Field(
        None,
        description="Task description"
    )
    assigned_to: Optional[str] = Field(
        None,
        description="User ID to assign task to"
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="Task status"
    )
    priority: Optional[TaskPriority] = Field(
        None,
        description="Task priority"
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Task deadline"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "in_progress",
                    "priority": "urgent"
                }
            ]
        }
    }


class TaskResponse(BaseModel):
    """Schema for task data in API responses."""

    id: str
    project_id: str
    title: str
    description: Optional[str]
    assigned_to: Optional[str]
    status: str
    priority: str
    due_date: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "project_id": "550e8400-e29b-41d4-a716-446655440001",
                    "title": "Implement user authentication",
                    "description": "Add JWT-based authentication system",
                    "assigned_to": "550e8400-e29b-41d4-a716-446655440002",
                    "status": "in_progress",
                    "priority": "high",
                    "due_date": "2025-12-31T23:59:59",
                    "created_by": "550e8400-e29b-41d4-a716-446655440003",
                    "created_at": "2025-01-08T12:34:56",
                    "updated_at": "2025-01-08T13:00:00"
                }
            ]
        }
    }
