"""
Project model for organizing work and managing team collaboration.

A Project represents a container for related tasks and team members.
Projects have owners, admins, members, and viewers with different permission levels.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProjectMemberRole(str, enum.Enum):
    """Project member roles with different permission levels."""
    OWNER = "owner"  # Full control, can delete project
    ADMIN = "admin"  # Can manage members and tasks
    MEMBER = "member"  # Can create and edit tasks
    VIEWER = "viewer"  # Read-only access


class Project(Base):
    """
    Project model for organizing work.

    Projects group related tasks and define team membership.
    Each project has a creator and can have multiple members with different roles.

    Attributes:
        id: Unique project identifier (UUID)
        name: Project name (required)
        description: Optional project description
        created_by: User ID of project creator
        created_at: Timestamp when project was created (auto-set)
        updated_at: Timestamp when project was last updated (auto-set)
        members: Relationship to ProjectMember (team members)
    """

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"  # Eager load members
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"


class ProjectMember(Base):
    """
    ProjectMember model for project team membership.

    Links users to projects with specific roles and permissions.
    Tracks who added each member and when.

    Attributes:
        project_id: ID of the project
        user_id: ID of the user (team member)
        role: Member role (owner, admin, member, viewer)
        added_by: User ID who added this member
        added_at: Timestamp when member was added (auto-set)
    """

    __tablename__ = "project_members"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    role = Column(
        SQLEnum(ProjectMemberRole, native_enum=False, length=20),
        nullable=False,
        default=ProjectMemberRole.MEMBER
    )

    # Audit fields
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    added_by_user = relationship("User", foreign_keys=[added_by])

    def __repr__(self) -> str:
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"
