"""Pydantic schemas for alert statistics."""
from typing import Dict, Any
from pydantic import BaseModel, Field


class AlertStatisticsResponse(BaseModel):
    """Schema for alert statistics response."""
    total_alerts: int = Field(..., description="Total number of alerts in period")
    by_status: Dict[str, int] = Field(
        ...,
        description="Count by status (new, acknowledged, dismissed, snoozed)"
    )
    by_severity: Dict[str, int] = Field(
        ...,
        description="Count by severity (critical, high, medium, low)"
    )
    avg_response_time_seconds: float = Field(
        ...,
        description="Average time to acknowledge alerts (seconds)"
    )
    unacknowledged_count: int = Field(
        ...,
        description="Number of alerts still in 'new' status"
    )
    critical_unacknowledged: int = Field(
        ...,
        description="Number of critical alerts still unacknowledged"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_alerts": 150,
                "by_status": {
                    "new": 12,
                    "acknowledged": 98,
                    "dismissed": 35,
                    "snoozed": 5
                },
                "by_severity": {
                    "critical": 8,
                    "high": 42,
                    "medium": 75,
                    "low": 25
                },
                "avg_response_time_seconds": 180.5,
                "unacknowledged_count": 12,
                "critical_unacknowledged": 2
            }
        }


class AlertTrendPoint(BaseModel):
    """Single point in alert trend data."""
    timestamp: str
    count: int
    severity_breakdown: Dict[str, int]


class AlertTrendResponse(BaseModel):
    """Schema for alert trend data over time."""
    period: str  # "hour", "day", "week"
    data_points: list[AlertTrendPoint]
