"""TriggeredAlert and AlertNotification models for Sprint 7 - Automated Alerting."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TriggeredAlert(Base):
    """Alert that has been triggered by a rule.

    Represents an actual alert instance triggered when rule conditions are met.

    Attributes:
        id: Unique identifier
        rule_id: Reference to the AlertRule that triggered this
        patient_id: Patient this alert relates to (if applicable)
        severity: Alert severity (critical, high, medium, low)
        status: Current status (new, acknowledged, dismissed, snoozed)
        trigger_data: JSON data that caused the trigger
        triggered_at: When the alert was triggered
        acknowledged_by: User who acknowledged the alert
        acknowledged_at: When it was acknowledged
        dismissed_by: User who dismissed the alert
        dismissed_at: When it was dismissed
        snooze_until: If snoozed, when to re-alert
        notes: Additional notes about the alert
    """
    __tablename__ = "triggered_alerts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    rule_id = Column(PG_UUID(as_uuid=True), ForeignKey('alert_rules.id'), nullable=False)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey('patients.id'), nullable=True)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    status = Column(String(20), nullable=False, server_default='new')  # new, acknowledged, dismissed, snoozed
    trigger_data = Column(JSONB, nullable=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    snooze_until = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    rule = relationship("AlertRule", back_populates="triggered_alerts")
    patient = relationship("Patient", foreign_keys=[patient_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    dismisser = relationship("User", foreign_keys=[dismissed_by])
    notifications = relationship("AlertNotification", back_populates="alert", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "rule_id": str(self.rule_id),
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "severity": self.severity,
            "status": self.status,
            "trigger_data": self.trigger_data,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "acknowledged_by": str(self.acknowledged_by) if self.acknowledged_by else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "dismissed_by": str(self.dismissed_by) if self.dismissed_by else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
            "snooze_until": self.snooze_until.isoformat() if self.snooze_until else None,
            "notes": self.notes,
        }

    def acknowledge(self, user_id: UUID, notes: Optional[str] = None) -> None:
        """Mark alert as acknowledged by a user."""
        self.status = "acknowledged"
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now()
        if notes:
            self.notes = notes

    def dismiss(self, user_id: UUID, notes: Optional[str] = None) -> None:
        """Mark alert as dismissed by a user."""
        self.status = "dismissed"
        self.dismissed_by = user_id
        self.dismissed_at = datetime.now()
        if notes:
            self.notes = notes

    def snooze(self, until: datetime) -> None:
        """Snooze alert until specified time."""
        self.status = "snoozed"
        self.snooze_until = until


class AlertNotification(Base):
    """Notification record for alert delivery tracking.

    Tracks the delivery status of notifications across different channels.

    Attributes:
        id: Unique identifier
        alert_id: Reference to the triggered alert
        channel: Notification channel (email, sms, in_app)
        recipient_id: User receiving the notification
        status: Delivery status (pending, sent, delivered, failed)
        sent_at: When the notification was sent
        delivered_at: When delivery was confirmed
        error_message: Error message if delivery failed
        retry_count: Number of retry attempts
    """
    __tablename__ = "alert_notifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    alert_id = Column(PG_UUID(as_uuid=True), ForeignKey('triggered_alerts.id', ondelete='CASCADE'), nullable=False)
    channel = Column(String(20), nullable=False)  # email, sms, in_app
    recipient_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    status = Column(String(20), nullable=False, server_default='pending')  # pending, sent, delivered, failed
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, server_default='0')

    # Relationships
    alert = relationship("TriggeredAlert", back_populates="notifications")
    recipient = relationship("User", foreign_keys=[recipient_id])

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "alert_id": str(self.alert_id),
            "channel": self.channel,
            "recipient_id": str(self.recipient_id),
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }

    def mark_sent(self) -> None:
        """Mark notification as sent."""
        self.status = "sent"
        self.sent_at = datetime.now()

    def mark_delivered(self) -> None:
        """Mark notification as delivered."""
        self.status = "delivered"
        self.delivered_at = datetime.now()

    def mark_failed(self, error_message: str) -> None:
        """Mark notification as failed with error message."""
        self.status = "failed"
        self.error_message = error_message
        self.retry_count += 1
