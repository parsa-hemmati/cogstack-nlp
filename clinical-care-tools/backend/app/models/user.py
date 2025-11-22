"""
User model for authentication and authorization.

Supports RBAC with roles: admin, clinician, researcher, viewer.
Includes break-glass access control for emergency access.
"""

from datetime import datetime
import uuid
import bcrypt
from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Unique user identifier (UUID)
        username: Unique username for login
        email: User email address
        password_hash: Bcrypt hashed password
        role: User role (admin, clinician, researcher, viewer)
        is_active: Whether user account is active
        can_break_glass: Whether user can trigger break-glass access
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique user identifier"
    )
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for login"
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User email address"
    )
    password_hash = Column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )
    role = Column(
        String(20),
        nullable=False,
        doc="User role (admin, clinician, researcher, viewer)"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether user account is active"
    )
    can_break_glass = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether user can trigger break-glass access"
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp of user creation"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp of last update"
    )

    def __init__(self, **kwargs):
        """
        Initialize User with Python-level defaults.

        Sets defaults for is_active and can_break_glass at Python level,
        so they're available before database insertion.
        """
        # Set defaults if not provided
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'can_break_glass' not in kwargs:
            kwargs['can_break_glass'] = False

        super().__init__(**kwargs)

    def set_password(self, password: str) -> None:
        """
        Hash and set user password using bcrypt.

        Args:
            password: Plaintext password to hash

        Example:
            user = User(username="john", email="john@example.com", role="clinician")
            user.set_password("SecurePassword123!")
        """
        # Hash password with bcrypt (automatically salted)
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        self.password_hash = hashed.decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plaintext password to verify

        Returns:
            True if password matches, False otherwise

        Example:
            if user.verify_password("SecurePassword123!"):
                print("Login successful")
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(username='{self.username}', role='{self.role}', is_active={self.is_active})>"
