"""Pydantic schemas for notification preferences and stats."""
from datetime import datetime, time
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID
from pydantic import BaseModel, Field, validator


class NotificationPreferencesResponse(BaseModel):
    """Schema for notification preferences response."""
    id: UUID
    user_id: UUID
    email_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool
    quiet_hours_start: Optional[str]  # Time as string HH:MM
    quiet_hours_end: Optional[str]
    min_severity: str
    phone_number: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator("quiet_hours_start", "quiet_hours_end", pre=True)
    def time_to_string(cls, v):
        if isinstance(v, time):
            return v.strftime("%H:%M")
        return v


class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences."""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(
        None,
        pattern=r"^\d{2}:\d{2}$",
        description="Quiet hours start time (HH:MM)"
    )
    quiet_hours_end: Optional[str] = Field(
        None,
        pattern=r"^\d{2}:\d{2}$",
        description="Quiet hours end time (HH:MM)"
    )
    min_severity: Optional[Literal["critical", "high", "medium", "low"]] = None
    phone_number: Optional[str] = Field(
        None,
        pattern=r"^\+?[1-9]\d{1,14}$",
        description="Phone number in E.164 format"
    )

    @validator("quiet_hours_start", "quiet_hours_end", pre=True)
    def validate_time_format(cls, v):
        if v is None:
            return v
        try:
            hours, minutes = map(int, v.split(":"))
            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError
            return v
        except (ValueError, AttributeError):
            raise ValueError("Time must be in HH:MM format (00:00-23:59)")

    class Config:
        json_schema_extra = {
            "example": {
                "email_enabled": True,
                "sms_enabled": True,
                "in_app_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "07:00",
                "min_severity": "medium",
                "phone_number": "+447123456789"
            }
        }


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics."""
    total: int
    by_status: Dict[str, int]
    by_channel: Dict[str, int]
    success_rate: float


class AlertNotificationResponse(BaseModel):
    """Schema for individual notification record."""
    id: UUID
    alert_id: UUID
    channel: str
    recipient_id: UUID
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int

    class Config:
        from_attributes = True
