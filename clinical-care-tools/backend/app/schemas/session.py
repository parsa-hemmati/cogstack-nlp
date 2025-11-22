"""
Pydantic schemas for session management.

Defines request/response models for session operations.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for session creation (internal use)."""

    device_name: Optional[str] = Field(
        None,
        description="Optional device name for identification"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "John's MacBook Pro"
            }
        }


class SessionResponse(BaseModel):
    """Schema for session information response."""

    id: str = Field(
        ...,
        description="Session ID"
    )
    user_id: str = Field(
        ...,
        description="User ID owning this session"
    )
    device_name: str = Field(
        ...,
        description="Device name"
    )
    created_at: datetime = Field(
        ...,
        description="Session creation time"
    )
    last_activity: datetime = Field(
        ...,
        description="Last activity timestamp"
    )
    expires_at: datetime = Field(
        ...,
        description="Session expiration time"
    )
    is_active: bool = Field(
        ...,
        description="Whether session is active"
    )
    is_current: bool = Field(
        default=False,
        description="Whether this is the current session"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "sess_abc123def456",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "device_name": "iPhone",
                "created_at": "2025-01-08T10:00:00Z",
                "last_activity": "2025-01-08T10:30:00Z",
                "expires_at": "2025-01-09T10:00:00Z",
                "is_active": True,
                "is_current": True
            }
        }


class SessionListResponse(BaseModel):
    """Schema for list of sessions."""

    sessions: List[SessionResponse] = Field(
        ...,
        description="List of user sessions"
    )
    total: int = Field(
        ...,
        description="Total number of sessions"
    )
    active_count: int = Field(
        ...,
        description="Number of active sessions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": "sess_abc123def456",
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "device_name": "iPhone",
                        "created_at": "2025-01-08T10:00:00Z",
                        "last_activity": "2025-01-08T10:30:00Z",
                        "expires_at": "2025-01-09T10:00:00Z",
                        "is_active": True,
                        "is_current": True
                    }
                ],
                "total": 1,
                "active_count": 1
            }
        }


class SessionInvalidateRequest(BaseModel):
    """Schema for session invalidation request."""

    session_id: str = Field(
        ...,
        description="Session ID to invalidate"
    )
    reason: Optional[str] = Field(
        None,
        description="Optional reason for invalidation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123def456",
                "reason": "Suspicious activity detected"
            }
        }


class SessionInvalidateAllRequest(BaseModel):
    """Schema for invalidating all sessions."""

    except_current: bool = Field(
        default=True,
        description="Whether to keep current session active"
    )
    reason: Optional[str] = Field(
        None,
        description="Optional reason for invalidation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "except_current": True,
                "reason": "Password changed"
            }
        }


class SessionSecurityInfo(BaseModel):
    """Schema for session security information."""

    session_binding_enabled: bool = Field(
        ...,
        description="Whether session binding is enabled"
    )
    hijack_detection_enabled: bool = Field(
        ...,
        description="Whether hijack detection is enabled"
    )
    idle_timeout_minutes: int = Field(
        ...,
        description="Session idle timeout in minutes"
    )
    absolute_timeout_hours: int = Field(
        ...,
        description="Session absolute timeout in hours"
    )
    max_concurrent_sessions: int = Field(
        ...,
        description="Maximum concurrent sessions allowed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_binding_enabled": True,
                "hijack_detection_enabled": True,
                "idle_timeout_minutes": 15,
                "absolute_timeout_hours": 24,
                "max_concurrent_sessions": 2
            }
        }


class BreakGlassRequest(BaseModel):
    """Schema for break-glass access request."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Detailed reason for emergency access"
    )
    duration_minutes: int = Field(
        default=60,
        ge=5,
        le=120,
        description="Duration of elevated access in minutes (5-120)"
    )
    patient_id: Optional[str] = Field(
        None,
        description="Specific patient ID if accessing patient data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Emergency surgery requires immediate access to patient history",
                "duration_minutes": 60,
                "patient_id": "PAT-123456"
            }
        }


class BreakGlassResponse(BaseModel):
    """Schema for break-glass access response."""

    grant_id: str = Field(
        ...,
        description="Break-glass grant ID"
    )
    user_id: str = Field(
        ...,
        description="User granted access"
    )
    granted_at: datetime = Field(
        ...,
        description="When access was granted"
    )
    expires_at: datetime = Field(
        ...,
        description="When elevated access expires"
    )
    reason: str = Field(
        ...,
        description="Reason for emergency access"
    )
    review_required_by: datetime = Field(
        ...,
        description="Deadline for post-access review"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "grant_id": "break_glass_789xyz",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "granted_at": "2025-01-08T15:00:00Z",
                "expires_at": "2025-01-08T16:00:00Z",
                "reason": "Emergency surgery requires immediate access",
                "review_required_by": "2025-01-09T15:00:00Z"
            }
        }