"""NotificationPreferences model for user notification settings."""
from datetime import time
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Boolean, Time, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class NotificationPreferences(Base):
    """User notification preferences for alert delivery.

    Stores per-user settings for how they want to receive alerts.

    Attributes:
        id: Unique identifier
        user_id: Reference to the user
        email_enabled: Whether to receive email notifications
        sms_enabled: Whether to receive SMS notifications
        in_app_enabled: Whether to receive in-app notifications
        quiet_hours_start: Start of quiet hours (no notifications)
        quiet_hours_end: End of quiet hours
        min_severity: Minimum severity to receive (medium = medium and above)
        phone_number: Phone number for SMS (if enabled)
        updated_at: Last update timestamp
    """
    __tablename__ = "notification_preferences"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    email_enabled = Column(Boolean, nullable=False, server_default='true')
    sms_enabled = Column(Boolean, nullable=False, server_default='false')
    in_app_enabled = Column(Boolean, nullable=False, server_default='true')
    quiet_hours_start = Column(Time, nullable=True)  # e.g., 22:00
    quiet_hours_end = Column(Time, nullable=True)    # e.g., 07:00
    min_severity = Column(String(20), nullable=False, server_default='medium')  # critical, high, medium, low
    phone_number = Column(String(20), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    # Severity ranking for comparison
    SEVERITY_RANKS = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "in_app_enabled": self.in_app_enabled,
            "quiet_hours_start": self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            "quiet_hours_end": self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            "min_severity": self.min_severity,
            "phone_number": self.phone_number,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_in_quiet_hours(self, current_time: time) -> bool:
        """Check if current time is within quiet hours.

        Args:
            current_time: Time to check

        Returns:
            True if in quiet hours, False otherwise
        """
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        # Handle overnight quiet hours (e.g., 22:00 to 07:00)
        if self.quiet_hours_start > self.quiet_hours_end:
            # Overnight period
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        else:
            # Same day period
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end

    def should_receive_alert(self, severity: str, current_time: Optional[time] = None) -> bool:
        """Check if user should receive an alert based on preferences.

        Args:
            severity: Alert severity level
            current_time: Optional time to check quiet hours (uses now if not provided)

        Returns:
            True if alert should be delivered, False otherwise
        """
        from datetime import datetime

        # Check severity threshold
        alert_rank = self.SEVERITY_RANKS.get(severity, 0)
        min_rank = self.SEVERITY_RANKS.get(self.min_severity, 0)

        if alert_rank < min_rank:
            return False

        # Check quiet hours (unless critical - critical alerts always go through)
        if severity != "critical" and current_time is not None:
            if self.is_in_quiet_hours(current_time):
                return False

        return True

    def get_enabled_channels(self) -> list:
        """Get list of enabled notification channels.

        Returns:
            List of channel names that are enabled
        """
        channels = []
        if self.email_enabled:
            channels.append("email")
        if self.sms_enabled and self.phone_number:
            channels.append("sms")
        if self.in_app_enabled:
            channels.append("in_app")
        return channels
