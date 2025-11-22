"""
User Model

Represents a user account in the system with authentication and role information.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import Base


class User(Base):
    """
    User account model.

    Attributes:
        id: Unique user identifier (UUID)
        username: Unique username for login
        email: Unique email address
        password_hash: Bcrypt hash of password
        role: User role (admin, clinician, researcher)
        is_active: Whether account is active
        must_change_password: Flag for forced password change on first login
        failed_login_attempts: Count of failed login attempts (for lockout)
        locked_until: Timestamp when account is locked until (for brute force protection)
        last_login: Timestamp of last successful login
        created_at: When account was created
        created_by: ID of user who created this account
        updated_at: When account was last updated
        updated_by: ID of user who last updated this account

    Relationships:
        sessions: User's active sessions
        audit_logs: Audit log entries for this user
        projects_created: Projects created by this user
        project_members: Project memberships
        tasks_assigned: Tasks assigned to this user
        documents_uploaded: Documents uploaded by this user
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Authentication
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Authorization
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Role: 'admin', 'clinician', 'researcher'",
    )

    # Account Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Security: Lockout Policy
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    created_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    projects_created: Mapped[list["Project"]] = relationship(
        "Project",
        foreign_keys="Project.created_by",
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    project_members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    tasks_assigned: Mapped[list["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assigned_to",
        back_populates="assignee",
        cascade="all, delete-orphan",
    )

    documents_uploaded: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="uploader",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        Index("idx_users_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"
