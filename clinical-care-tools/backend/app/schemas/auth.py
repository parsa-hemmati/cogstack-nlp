"""
Pydantic schemas for authentication endpoints.

Defines request/response models for auth operations.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User email address (unique identifier)"
    )
    password: str = Field(
        ...,
        min_length=12,
        description="Password (minimum 12 characters)"
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name"
    )
    role: str = Field(
        default="researcher",
        description="User role (admin, clinician, researcher, auditor)"
    )

    @validator("role")
    def validate_role(cls, v):
        """Validate role is allowed."""
        allowed_roles = ["admin", "clinician", "researcher", "auditor"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v

    @validator("password")
    def validate_password(cls, v):
        """Basic password validation (full validation in service)."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@hospital.org",
                "password": "SecureP@ssw0rd123!",
                "full_name": "John Doe",
                "role": "clinician"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(
        ...,
        description="User email address"
    )
    password: str = Field(
        ...,
        description="User password"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@hospital.org",
                "password": "SecureP@ssw0rd123!"
            }
        }


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token (8 hour expiry)"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token (7 day expiry)"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(
        ...,
        description="Valid refresh token"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class UserResponse(BaseModel):
    """Schema for user information response."""

    id: str = Field(
        ...,
        description="User ID"
    )
    email: EmailStr = Field(
        ...,
        description="User email address"
    )
    full_name: str = Field(
        ...,
        description="User's full name"
    )
    role: str = Field(
        ...,
        description="User role"
    )
    is_active: bool = Field(
        ...,
        description="Whether user account is active"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Last login timestamp"
    )
    last_activity: Optional[datetime] = Field(
        None,
        description="Last activity timestamp"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@hospital.org",
                "full_name": "John Doe",
                "role": "clinician",
                "is_active": True,
                "created_at": "2025-01-08T10:00:00Z",
                "last_login": "2025-01-08T14:30:00Z",
                "last_activity": "2025-01-08T15:45:00Z"
            }
        }


class PasswordChange(BaseModel):
    """Schema for password change request."""

    old_password: str = Field(
        ...,
        description="Current password"
    )
    new_password: str = Field(
        ...,
        min_length=12,
        description="New password (minimum 12 characters)"
    )

    @validator("new_password")
    def passwords_different(cls, v, values):
        """Ensure new password is different from old."""
        if "old_password" in values and v == values["old_password"]:
            raise ValueError("New password must be different from current password")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldP@ssw0rd123!",
                "new_password": "NewP@ssw0rd456!"
            }
        }


class PasswordReset(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(
        ...,
        description="Email address for password reset"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@hospital.org"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str = Field(
        ...,
        description="Password reset token"
    )
    new_password: str = Field(
        ...,
        min_length=12,
        description="New password"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_from_email",
                "new_password": "NewSecureP@ssw0rd789!"
            }
        }


class LoginAttemptResponse(BaseModel):
    """Schema for login attempt information."""

    attempts_remaining: int = Field(
        ...,
        description="Number of login attempts remaining"
    )
    lockout_until: Optional[datetime] = Field(
        None,
        description="Account lockout expiry time"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "attempts_remaining": 2,
                "lockout_until": None
            }
        }