"""Dashboard schemas for analytics API."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WidgetConfig(BaseModel):
    """Schema for widget configuration."""

    id: str
    type: str = Field(..., description="gauge, metric, line_chart, bar_chart, pie_chart, table, alert_list")
    title: str
    config: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None


class DashboardCreate(BaseModel):
    """Schema for creating an analytics dashboard."""

    name: str = Field(..., min_length=1, max_length=255)
    dashboard_type: str = Field(..., description="quality, predictive, operational, custom")
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    theme: str = Field(default="default")
    default_filters: Optional[Dict[str, Any]] = None
    default_date_range: Optional[str] = None
    default_cohort_id: Optional[UUID] = None
    auto_refresh: bool = False
    refresh_interval_seconds: Optional[int] = Field(None, ge=30)
    is_public: bool = False
    allowed_roles: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DashboardUpdate(BaseModel):
    """Schema for updating an analytics dashboard."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    theme: Optional[str] = None
    default_filters: Optional[Dict[str, Any]] = None
    default_date_range: Optional[str] = None
    default_cohort_id: Optional[UUID] = None
    auto_refresh: Optional[bool] = None
    refresh_interval_seconds: Optional[int] = Field(None, ge=30)
    is_public: Optional[bool] = None
    allowed_roles: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DashboardResponse(BaseModel):
    """Schema for analytics dashboard response."""

    id: UUID
    name: str
    description: Optional[str]
    dashboard_type: str
    layout: Optional[Dict[str, Any]]
    widgets: Optional[List[Dict[str, Any]]]
    theme: Optional[str]
    default_filters: Optional[Dict[str, Any]]
    default_date_range: Optional[str]
    default_cohort_id: Optional[UUID]
    auto_refresh: bool
    refresh_interval_seconds: Optional[int]
    is_public: bool
    is_default: bool
    allowed_roles: Optional[List[str]]
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    tags: Optional[List[str]]

    class Config:
        from_attributes = True


class WidgetDataRequest(BaseModel):
    """Schema for requesting widget data."""

    widget_config: Dict[str, Any]
    cohort_id: Optional[UUID] = None
    date_range: Optional[str] = None


class WidgetDataResponse(BaseModel):
    """Schema for widget data response."""

    widget_id: Optional[str] = None
    data: Dict[str, Any]


class DashboardStatisticsResponse(BaseModel):
    """Schema for dashboard statistics."""

    total_dashboards: int
    by_type: Dict[str, int]
    public_dashboards: int
    private_dashboards: int


class AddWidgetRequest(BaseModel):
    """Schema for adding a widget to a dashboard."""

    widget_config: Dict[str, Any]


class UpdateWidgetRequest(BaseModel):
    """Schema for updating a widget."""

    widget_config: Dict[str, Any]


class DuplicateDashboardRequest(BaseModel):
    """Schema for duplicating a dashboard."""

    new_name: str = Field(..., min_length=1, max_length=255)
