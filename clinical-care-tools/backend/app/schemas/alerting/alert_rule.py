"""Pydantic schemas for alert rules."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, validator


class ConditionSchema(BaseModel):
    """Single condition in an alert rule."""
    field: str = Field(..., description="Field path to evaluate (e.g., 'lab_results.potassium')")
    operator: Literal[
        "equals", "not_equals", "greater_than", "less_than",
        "greater_than_or_equals", "less_than_or_equals",
        "contains", "not_contains", "in", "not_in",
        "is_null", "is_not_null", "starts_with", "ends_with", "regex_match"
    ] = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "lab_results.potassium",
                "operator": "greater_than",
                "value": 5.5
            }
        }


class RuleConditionsSchema(BaseModel):
    """Container for rule conditions with match type."""
    match_type: Literal["all", "any"] = Field(
        default="all",
        description="'all' = all conditions must match (AND), 'any' = at least one must match (OR)"
    )
    conditions: List[ConditionSchema] = Field(
        ...,
        min_length=1,
        description="List of conditions to evaluate"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "match_type": "all",
                "conditions": [
                    {"field": "lab_results.potassium", "operator": "greater_than", "value": 5.5},
                    {"field": "medications", "operator": "contains", "value": "potassium"}
                ]
            }
        }


class AlertRuleCreate(BaseModel):
    """Schema for creating a new alert rule."""
    name: str = Field(..., min_length=1, max_length=255, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    conditions: RuleConditionsSchema = Field(..., description="Rule conditions")
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Alert severity level"
    )
    notification_channels: List[Literal["email", "sms", "in_app"]] = Field(
        default=["in_app"],
        description="Channels to send notifications"
    )
    escalation_minutes: Optional[int] = Field(
        None,
        ge=1,
        le=10080,  # Max 1 week
        description="Minutes before escalating unacknowledged alert"
    )
    enabled: bool = Field(default=True, description="Whether rule is active")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "High Potassium Alert",
                "description": "Alert when potassium > 5.5 mmol/L",
                "conditions": {
                    "match_type": "all",
                    "conditions": [
                        {"field": "lab_results.potassium", "operator": "greater_than", "value": 5.5}
                    ]
                },
                "severity": "high",
                "notification_channels": ["email", "in_app"],
                "escalation_minutes": 30,
                "enabled": True
            }
        }


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Optional[RuleConditionsSchema] = None
    severity: Optional[Literal["critical", "high", "medium", "low"]] = None
    notification_channels: Optional[List[Literal["email", "sms", "in_app"]]] = None
    escalation_minutes: Optional[int] = Field(None, ge=1, le=10080)
    enabled: Optional[bool] = None
    change_reason: Optional[str] = Field(
        None,
        description="Reason for the change (for audit trail)"
    )


class AlertRuleResponse(BaseModel):
    """Schema for alert rule API responses."""
    id: UUID
    name: str
    description: Optional[str]
    conditions: Dict[str, Any]
    severity: str
    notification_channels: List[str]
    escalation_minutes: Optional[int]
    enabled: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertRuleVersionResponse(BaseModel):
    """Schema for alert rule version history."""
    id: UUID
    rule_id: UUID
    version: int
    conditions: Dict[str, Any]
    changed_by: UUID
    changed_at: datetime
    change_reason: Optional[str]

    class Config:
        from_attributes = True


class RuleTestRequest(BaseModel):
    """Schema for testing a rule against sample data."""
    test_data: Dict[str, Any] = Field(
        ...,
        description="Sample data to test the rule against"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "test_data": {
                    "lab_results": {
                        "potassium": 6.2,
                        "sodium": 140
                    },
                    "medications": ["lisinopril", "potassium supplement"]
                }
            }
        }


class RuleTestResponse(BaseModel):
    """Schema for rule test results."""
    rule_id: str
    rule_name: str
    matched: bool
    match_type: str
    condition_results: List[Dict[str, Any]]
