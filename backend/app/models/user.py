"""
User Model
SQLAlchemy ORM model for users table with password hashing
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from passlib.context import CryptContext
from app.db.base_class import Base


# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: UUID primary key
        username: Unique username (3-50 characters)
        email: Unique email address
        password_hash: Bcrypt hashed password (never store plaintext!)
        role: User role (clinician, researcher, admin)
        is_active: Account active status
        can_break_glass: Emergency PHI access permission
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    # Primary key (UUID for security - no sequential IDs)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Bcrypt hash

    # Authorization fields
    role = Column(
        SQLEnum("clinician", "researcher", "admin", name="user_role"),
        nullable=False,
        default="clinician",
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    can_break_glass = Column(Boolean, nullable=False, default=False)  # Emergency PHI access

    # Audit timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def set_password(self, password: str) -> None:
        """
        Hash password with bcrypt and store in password_hash field.

        Args:
            password: Plaintext password (min 8 characters recommended)

        Security:
            - Uses bcrypt with automatic salt generation
            - Never stores plaintext password
            - Password hash is one-way (cannot be reversed)
        """
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plaintext password to verify

        Returns:
            True if password matches, False otherwise

        Security:
            - Constant-time comparison (prevents timing attacks)
            - Automatically handles bcrypt rounds/salt
        """
        return pwd_context.verify(password, self.password_hash)

    def to_dict(self, include_password_hash: bool = False) -> dict:
        """
        Convert user to dictionary for serialization.

        Args:
            include_password_hash: If True, include password_hash (NEVER send to client!)

        Returns:
            Dictionary representation of user

        Security:
            - By default, excludes password_hash
            - Only include password_hash for internal operations
        """
        data = {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "can_break_glass": self.can_break_glass,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_password_hash:
            data["password_hash"] = self.password_hash

        return data
