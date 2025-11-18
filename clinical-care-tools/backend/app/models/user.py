"""User model for authentication and authorization."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, PyEnum):
    """User roles for role-based access control (RBAC)."""

    ADMIN = "admin"  # Full system access
    CLINICIAN = "clinician"  # Access to patient data for assigned patients
    RESEARCHER = "researcher"  # Access to de-identified data only
    AUDITOR = "auditor"  # Read-only access to audit logs
    VIEWER = "viewer"  # Read-only access to non-PHI data


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        username: Unique username for login
        email: User's email address
        password_hash: Bcrypt hashed password
        full_name: User's full name
        role: User role for RBAC
        is_active: Whether account is active
        is_verified: Whether email is verified
        can_break_glass: Emergency access permission (HIPAA Break-the-Glass)
        failed_login_attempts: Counter for failed logins
        locked_until: Account lockout timestamp
        last_login_at: Last successful login timestamp
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.VIEWER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    can_break_glass: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="HIPAA Break-the-Glass emergency access permission",
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    locked_until: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        default=None,
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        default=None,
    )

    def set_password(self, password: str) -> None:
        """Hash and set password."""
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(password, self.password_hash)

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def increment_failed_login(self) -> None:
        """Increment failed login attempts."""
        self.failed_login_attempts += 1

    def reset_failed_login(self) -> None:
        """Reset failed login attempts and unlock account."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role}')>"
