"""
Project Models

Represents projects (shared workspaces) and their members and tasks.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func, JSON, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import Base


class Project(Base):
    """
    Project model representing a shared workspace.

    Attributes:
        id: Unique project identifier (UUID)
        name: Project name (unique)
        description: Project description
        project_type: Type of project (patient_search, timeline, cds, cohort, annotation)
        status: Project status (active, complete, archived)
        dataset_id: Reference to shared dataset (future)
        medcat_model_id: Reference to MedCAT model (future)
        configuration: Project-specific configuration as JSON
        created_at: When project was created
        created_by: User who created project
        updated_at: When project was last updated
        updated_by: User who last updated project

    Relationships:
        creator: Reference to User who created project
        members: Project members
        tasks: Project tasks
        documents: Documents in project
        extracted_entities: Extracted entities from documents
    """

    __tablename__ = "projects"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Project Details
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    project_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="'patient_search', 'timeline', 'cds', 'cohort', 'annotation'",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        comment="'active', 'complete', 'archived'",
    )

    # References to shared resources (future)
    dataset_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    medcat_model_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    # Configuration
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Project-specific configuration",
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    created_by: Mapped[UUID] = mapped_column(nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )
    updated_by: Mapped[UUID] = mapped_column(nullable=False)

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="projects_created",
        foreign_keys=[created_by],
    )

    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    extracted_entities: Mapped[list["ExtractedEntity"]] = relationship(
        "ExtractedEntity",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_projects_name", "name"),
        Index("idx_projects_type", "project_type"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_created_by", "created_by"),
    )

    def __repr__(self) -> str:
        """String representation of Project."""
        return f"<Project(id={self.id}, name={self.name}, type={self.project_type}, status={self.status})>"


class ProjectMember(Base):
    """
    Project membership model.

    Attributes:
        id: Unique membership identifier (UUID)
        project_id: Reference to project
        user_id: Reference to user
        role: Role in project (owner, member, viewer)
        joined_at: When user joined project
        added_by: User who added this member

    Relationships:
        project: Reference to Project
        user: Reference to User
    """

    __tablename__ = "project_members"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    project_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    added_by: Mapped[UUID] = mapped_column(nullable=False)

    # Membership Details
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="member",
        index=True,
        comment="'owner', 'member', 'viewer'",
    )

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members",
        foreign_keys=[project_id],
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="project_members",
        foreign_keys=[user_id],
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="unique_project_member"),
        Index("idx_project_members_project", "project_id"),
        Index("idx_project_members_user", "user_id"),
        Index("idx_project_members_role", "role"),
    )

    def __repr__(self) -> str:
        """String representation of ProjectMember."""
        return f"<ProjectMember(project={self.project_id}, user={self.user_id}, role={self.role})>"


class Task(Base):
    """
    Task model for project assignments.

    Attributes:
        id: Unique task identifier (UUID)
        project_id: Reference to project
        assigned_to: User assigned to task
        name: Task name
        description: Task description
        task_type: Type of task (annotation, search, review, validation)
        status: Task status (pending, in_progress, complete, cancelled)
        priority: Task priority (low, medium, high, urgent)
        due_date: When task is due
        completed_at: When task was completed
        configuration: Task-specific configuration as JSON
        created_at: When task was created
        created_by: User who created task
        updated_at: When task was last updated
        updated_by: User who last updated task

    Relationships:
        project: Reference to Project
        assignee: Reference to User assigned to task
    """

    __tablename__ = "tasks"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    project_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    assigned_to: Mapped[UUID] = mapped_column(nullable=False, index=True)
    created_by: Mapped[UUID] = mapped_column(nullable=False, index=True)
    updated_by: Mapped[UUID] = mapped_column(nullable=False)

    # Task Details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    task_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="'annotation', 'search', 'review', 'validation'",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="'pending', 'in_progress', 'complete', 'cancelled'",
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
        index=True,
        comment="'low', 'medium', 'high', 'urgent'",
    )

    # Task Configuration
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Task-specific config (document IDs, search criteria, etc.)",
    )

    # Dates
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="tasks",
        foreign_keys=[project_id],
    )

    assignee: Mapped["User"] = relationship(
        "User",
        back_populates="tasks_assigned",
        foreign_keys=[assigned_to],
    )

    # Indexes
    __table_args__ = (
        Index("idx_tasks_project", "project_id"),
        Index("idx_tasks_assigned_to", "assigned_to"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_priority", "priority"),
        Index("idx_tasks_due_date", "due_date"),
        Index("idx_tasks_created_by", "created_by"),
    )

    def __repr__(self) -> str:
        """String representation of Task."""
        return f"<Task(id={self.id}, name={self.name}, assigned_to={self.assigned_to}, status={self.status})>"
