"""Pydantic schemas for user-related requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=100)
    can_break_glass: bool = False


class UserUpdate(BaseModel):
    """Schema for updating user."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    can_break_glass: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Schema for password update."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    is_active: bool
    is_verified: bool
    can_break_glass: bool
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: UUID  # User ID
    exp: datetime  # Expiration
    iat: datetime  # Issued at


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
