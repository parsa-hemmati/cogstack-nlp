"""CDS Rules model for storing business rules in IF-THEN format."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base_class import Base


class CDSRule(Base):
    """Clinical decision support business rule with IF-THEN logic.

    Rules are defined with:
    - Conditions (IF part): JSONB array of condition objects (field, operator, value)
    - Actions (THEN part): JSONB array of action objects (type, parameters)

    Rules are evaluated against patient data in priority order (highest first).
    Only active rules are evaluated.

    Attributes:
        id: Unique rule ID
        rule_name: Unique rule identifier/name
        description: Human-readable description of what the rule does
        priority: Rule priority (higher = more urgent, evaluated first)
        conditions: IF conditions (JSONB array of condition objects)
        actions: THEN actions (JSONB array of action objects)
        active: Whether rule is currently active
        created_at: Creation timestamp
        updated_at: Last update timestamp (auto-updated by trigger)
    """

    __tablename__ = "cds_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), nullable=False, unique=True, comment='Unique rule name/identifier')
    description = Column(Text, nullable=False, comment='Human-readable rule description')
    priority = Column(Integer, nullable=False, default=0, comment='Rule priority (higher = more urgent)')
    conditions = Column(JSONB, nullable=False, comment='IF conditions (JSONB array of condition objects)')
    actions = Column(JSONB, nullable=False, comment='THEN actions (JSONB array of action objects)')
    active = Column(Boolean, nullable=False, default=True, comment='Whether rule is currently active')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, comment='Date rule was created')
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, comment='Date rule was last updated')

    # Indexes and trigger are defined in Alembic migration 016
    # This __table_args__ is just for documentation (actual constraints are in DB)
    __table_args__ = (
        # Unique constraint on rule_name
        Index('uq_cds_rules_name', 'rule_name', unique=True),

        # Index for filtering by active rules
        Index('ix_cds_rules_active', 'active'),

        # Index for ordering by priority DESC
        Index('ix_cds_rules_priority_desc', 'priority', postgresql_ops={'priority': 'DESC'}),
    )

    def __repr__(self):
        return f"<CDSRule(id={self.id}, name={self.rule_name}, priority={self.priority}, active={self.active})>"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "rule_name": self.rule_name,
            "description": self.description,
            "priority": self.priority,
            "conditions": self.conditions,  # Already dict from JSONB
            "actions": self.actions,        # Already dict from JSONB
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CDSRule":
        """Create CDSRule from dictionary.

        Args:
            data: Dictionary with rule fields

        Returns:
            CDSRule instance
        """
        return cls(
            rule_name=data["rule_name"],
            description=data["description"],
            priority=data.get("priority", 0),
            conditions=data["conditions"],
            actions=data["actions"],
            active=data.get("active", True),
        )

    def evaluate_conditions(self, patient_data: dict) -> bool:
        """Evaluate rule conditions against patient data.

        This is a simple implementation. For production, use business-rules library
        or integrate with a rules engine.

        Args:
            patient_data: Dictionary of patient attributes

        Returns:
            True if all conditions are met, False otherwise
        """
        if not self.conditions:
            return True

        for condition in self.conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            expected_value = condition.get("value")

            actual_value = patient_data.get(field)

            # Evaluate condition based on operator
            if operator == "equals":
                if actual_value != expected_value:
                    return False
            elif operator == "not_equals":
                if actual_value == expected_value:
                    return False
            elif operator == "greater_than":
                if not (actual_value is not None and actual_value > expected_value):
                    return False
            elif operator == "less_than":
                if not (actual_value is not None and actual_value < expected_value):
                    return False
            elif operator == "greater_than_or_equal":
                if not (actual_value is not None and actual_value >= expected_value):
                    return False
            elif operator == "less_than_or_equal":
                if not (actual_value is not None and actual_value <= expected_value):
                    return False
            elif operator == "in":
                if actual_value not in expected_value:
                    return False
            elif operator == "contains":
                if expected_value not in (actual_value or ""):
                    return False
            else:
                # Unknown operator - skip this condition
                continue

        # All conditions met
        return True
