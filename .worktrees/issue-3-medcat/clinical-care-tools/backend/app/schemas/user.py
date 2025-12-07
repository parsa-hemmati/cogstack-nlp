"""
Pydantic schemas for User API endpoints.

Schemas:
- UserCreate: Creating new users
- UserUpdate: Updating existing users
- UserResponse: User data in responses (excludes sensitive fields)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class UserRole(str, Enum):
    """Allowed user roles."""
    ADMIN = "admin"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


class UserCreate(BaseModel):
    """Schema for creating new user."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 characters)"
    )
    role: UserRole = Field(
        ...,
        description="User role (admin, clinician, researcher, viewer)"
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum strength requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_letter and has_digit):
            raise ValueError('Password must contain at least one letter and one number')

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "john_doe",
                    "full_name": "John Doe",
                    "password": "SecurePass123!",
                    "role": "clinician"
                }
            ]
        }
    }


class UserUpdate(BaseModel):
    """Schema for updating existing user."""

    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's full name"
    )
    role: Optional[UserRole] = Field(
        None,
        description="User role"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether user account is active"
    )
    must_change_password: Optional[bool] = Field(
        None,
        description="Whether user must change password on next login"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "John Doe Updated",
                    "is_active": False
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: str
    username: str
    full_name: str
    role: str
    is_active: bool
    must_change_password: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "john_doe",
                    "full_name": "John Doe",
                    "role": "clinician",
                    "is_active": True,
                    "must_change_password": False,
                    "created_at": "2025-01-08T12:34:56"
                }
            ]
        }
    }
