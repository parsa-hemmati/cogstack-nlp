"""
Authentication request/response schemas.

Pydantic models for login, token responses, and user information.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid


class LoginRequest(BaseModel):
    """
    Login request schema.

    Example:
        {
            "username": "john_doe",
            "password": "SecurePassword123!"
        }
    """

    username: str = Field(
        ..., min_length=3, max_length=50, description="Username for login"
    )
    password: str = Field(
        ..., min_length=8, max_length=100, description="User password"
    )


class UserResponse(BaseModel):
    """
    User information in responses (no password).

    Example:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "john_doe",
            "email": "john@example.com",
            "role": "clinician",
            "is_active": true,
            "created_at": "2025-01-01T00:00:00"
        }
    """

    id: uuid.UUID = Field(..., description="User unique identifier")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description="User role (admin, clinician, researcher, viewer)")
    is_active: bool = Field(..., description="Whether user account is active")
    can_break_glass: bool = Field(
        ..., description="Whether user can trigger break-glass access"
    )
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True  # For SQLAlchemy ORM compatibility


class LoginResponse(BaseModel):
    """
    Login success response schema.

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_at": "2025-01-01T08:00:00",
            "user": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "john_doe",
                "email": "john@example.com",
                "role": "clinician",
                "is_active": true,
                "created_at": "2025-01-01T00:00:00"
            }
        }
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    user: UserResponse = Field(..., description="Authenticated user information")
