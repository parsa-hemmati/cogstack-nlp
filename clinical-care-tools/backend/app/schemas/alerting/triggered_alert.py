"""Pydantic schemas for triggered alerts."""
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class TriggeredAlertResponse(BaseModel):
    """Schema for triggered alert API responses."""
    id: UUID
    rule_id: UUID
    rule_name: Optional[str] = None
    patient_id: Optional[UUID]
    severity: str
    status: str
    trigger_data: Optional[Dict[str, Any]]
    triggered_at: datetime
    acknowledged_by: Optional[UUID]
    acknowledged_at: Optional[datetime]
    dismissed_by: Optional[UUID]
    dismissed_at: Optional[datetime]
    snooze_until: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    """Schema for acknowledging an alert."""
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes about the acknowledgment"
    )


class AlertDismissRequest(BaseModel):
    """Schema for dismissing an alert."""
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Reason for dismissing the alert"
    )


class AlertSnoozeRequest(BaseModel):
    """Schema for snoozing an alert."""
    snooze_minutes: int = Field(
        ...,
        ge=5,
        le=1440,  # Max 24 hours
        description="Minutes to snooze the alert"
    )


class BulkAcknowledgeRequest(BaseModel):
    """Schema for bulk acknowledging alerts."""
    alert_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of alert IDs to acknowledge"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes for all acknowledgments"
    )


class BulkAcknowledgeResponse(BaseModel):
    """Schema for bulk acknowledge response."""
    acknowledged_count: int
    failed_ids: List[UUID] = []


class AlertListFilters(BaseModel):
    """Schema for filtering alert list."""
    status: Optional[Literal["new", "acknowledged", "dismissed", "snoozed"]] = None
    severity: Optional[Literal["critical", "high", "medium", "low"]] = None
    patient_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    rule_id: Optional[UUID] = None


class AlertListResponse(BaseModel):
    """Schema for paginated alert list response."""
    alerts: List[TriggeredAlertResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
