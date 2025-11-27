"""
Authentication Schemas
Pydantic models for authentication request/response
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request body schema."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")


class LoginResponse(BaseModel):
    """Login response schema with JWT token."""

    access_token: str
    token_type: str
    expires_at: str
    user: dict  # User information (without password_hash!)


class UserResponse(BaseModel):
    """User information response schema."""

    id: str
    username: str
    email: str
    role: str
    is_active: bool
    can_break_glass: bool
    created_at: str
    updated_at: str
