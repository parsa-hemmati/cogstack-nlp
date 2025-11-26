"""Report schemas for analytics API."""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class ReportCreate(BaseModel):
    """Schema for creating an analytics report."""

    name: str = Field(..., min_length=1, max_length=255)
    report_type: str = Field(..., description="quality_summary, trend_analysis, model_performance, custom")
    file_format: str = Field(..., description="pdf, xlsx, csv, html")
    description: Optional[str] = None
    dashboard_id: Optional[UUID] = None
    metrics: Optional[List[UUID]] = None
    parameters: Optional[Dict[str, Any]] = None
    date_range_type: Optional[str] = Field(None, description="fixed, relative")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    relative_period: Optional[str] = Field(
        None, description="last_7_days, last_30_days, this_month, last_month, this_quarter, this_year"
    )
    cohort_id: Optional[UUID] = None
    include_charts: bool = True
    include_raw_data: bool = False
    is_scheduled: bool = False
    schedule_cron: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    auto_send: bool = False
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ReportUpdate(BaseModel):
    """Schema for updating an analytics report."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metrics: Optional[List[UUID]] = None
    parameters: Optional[Dict[str, Any]] = None
    date_range_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    relative_period: Optional[str] = None
    cohort_id: Optional[UUID] = None
    include_charts: Optional[bool] = None
    include_raw_data: Optional[bool] = None
    is_scheduled: Optional[bool] = None
    schedule_cron: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    auto_send: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """Schema for analytics report response."""

    id: UUID
    name: str
    description: Optional[str]
    report_type: str
    dashboard_id: Optional[UUID]
    metrics: Optional[List[UUID]]
    parameters: Optional[Dict[str, Any]]
    date_range_type: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    relative_period: Optional[str]
    cohort_id: Optional[UUID]
    file_format: str
    include_charts: bool
    include_raw_data: bool
    status: str
    progress_percentage: Optional[int]
    error_message: Optional[str]
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    generated_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_scheduled: bool
    schedule_cron: Optional[str]
    next_run_at: Optional[datetime]
    email_recipients: Optional[List[str]]
    auto_send: bool
    created_by: UUID
    created_at: datetime
    tags: Optional[List[str]]

    class Config:
        from_attributes = True


class ReportStatisticsResponse(BaseModel):
    """Schema for report statistics."""

    period_days: int
    total_reports: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    by_format: Dict[str, int]
    scheduled_reports: int
    success_rate: Optional[float]


class ReportDownloadResponse(BaseModel):
    """Schema for report download response."""

    download_url: str
    filename: str
    file_size_bytes: Optional[int]
    expires_at: Optional[datetime]
