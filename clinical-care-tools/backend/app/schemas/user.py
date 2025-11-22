"""
Pydantic schemas for User models.

Defines request/response schemas for user management endpoints.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    role: Literal["admin", "clinician", "researcher"] = Field(
        "researcher",
        description="User role in the system"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=12, description="User password")
    is_active: bool = Field(True, description="Whether user is active")
    must_change_password: bool = Field(False, description="Force password change on next login")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )

        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = Field(None)
    password: Optional[str] = Field(None, min_length=12)
    role: Optional[Literal["admin", "clinician", "researcher"]] = Field(None)
    is_active: Optional[bool] = Field(None)
    must_change_password: Optional[bool] = Field(None)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        """Validate password meets security requirements if provided."""
        if v is None:
            return v

        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )

        return v


class UserResponse(UserBase):
    """Schema for user response (without sensitive fields)."""

    id: UUID
    is_active: bool
    must_change_password: bool
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login: Optional[datetime]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]

    class Config:
        """Pydantic config."""
        from_attributes = True


class UserList(BaseModel):
    """Schema for paginated user list response."""

    items: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


class UserPasswordReset(BaseModel):
    """Schema for password reset request."""

    new_password: str = Field(..., min_length=12, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )

        return v


class UserMe(BaseModel):
    """Schema for current user info."""

    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    projects_count: int = Field(0, description="Number of projects user is member of")
    tasks_assigned: int = Field(0, description="Number of tasks assigned to user")

    class Config:
        """Pydantic config."""
        from_attributes = True