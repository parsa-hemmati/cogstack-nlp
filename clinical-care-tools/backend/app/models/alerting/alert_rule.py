"""AlertRule model for configurable alert conditions."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AlertRule(Base):
    """Alert rule configuration model.

    Defines conditions that trigger alerts and notification settings.

    Attributes:
        id: Unique identifier
        name: Human-readable rule name
        description: Detailed description of the rule
        conditions: JSON structure defining trigger conditions
        severity: Alert severity (critical, high, medium, low)
        notification_channels: List of channels (email, sms, in_app)
        escalation_minutes: Minutes before escalating unacknowledged alerts
        enabled: Whether the rule is active
        created_by: User who created the rule
    """
    __tablename__ = "alert_rules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    conditions = Column(JSONB, nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    notification_channels = Column(ARRAY(String), nullable=False, server_default='{}')
    escalation_minutes = Column(Integer, nullable=True)
    enabled = Column(Boolean, nullable=False, server_default='true')
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    versions = relationship("AlertRuleVersion", back_populates="rule", cascade="all, delete-orphan")
    triggered_alerts = relationship("TriggeredAlert", back_populates="rule")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "severity": self.severity,
            "notification_channels": self.notification_channels,
            "escalation_minutes": self.escalation_minutes,
            "enabled": self.enabled,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AlertRuleVersion(Base):
    """Version history for alert rules.

    Tracks changes to alert rules for auditing and rollback.
    """
    __tablename__ = "alert_rule_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    rule_id = Column(PG_UUID(as_uuid=True), ForeignKey('alert_rules.id', ondelete='CASCADE'), nullable=False)
    version = Column(Integer, nullable=False)
    conditions = Column(JSONB, nullable=False)
    changed_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    change_reason = Column(Text, nullable=True)

    # Relationships
    rule = relationship("AlertRule", back_populates="versions")
    changer = relationship("User", foreign_keys=[changed_by])
