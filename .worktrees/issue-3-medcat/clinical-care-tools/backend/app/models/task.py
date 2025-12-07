"""
Task model for project work assignment and tracking.

A Task represents a unit of work within a Project, with assignment, status tracking,
priority levels, and due dates.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """
    Task model for project work assignment.

    Tasks represent units of work within projects, with status tracking,
    priority levels, assignments, and due dates.

    Attributes:
        id: Unique task identifier (UUID)
        project_id: ID of parent project (required)
        title: Task title (required)
        description: Detailed task description (optional)
        assigned_to: User ID of assigned user (optional, null = unassigned)
        status: Task status (pending, in_progress, completed, blocked)
        priority: Task priority (low, medium, high, urgent)
        due_date: Task deadline (optional)
        created_by: User ID who created the task
        created_at: Timestamp when task was created (auto-set)
        updated_at: Timestamp when task was last updated (auto-set)
    """

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL = unassigned

    # Status and priority
    status = Column(
        SQLEnum(TaskStatus, native_enum=False, length=20),
        nullable=False,
        default=TaskStatus.PENDING
    )
    priority = Column(
        SQLEnum(TaskPriority, native_enum=False, length=20),
        nullable=False,
        default=TaskPriority.MEDIUM
    )

    # Scheduling
    due_date = Column(DateTime, nullable=True)

    # Audit fields
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"
