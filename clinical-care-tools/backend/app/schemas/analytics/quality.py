"""Quality Metric schemas for analytics API."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QualityMetricCreate(BaseModel):
    """Schema for creating a quality metric."""

    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., description="nlp_accuracy, data_quality, clinical_outcomes, operational")
    metric_type: str = Field(..., description="percentage, count, ratio, score, time")
    calculation_method: str = Field(..., description="automated, manual, hybrid")
    description: Optional[str] = None
    calculation_query: Optional[str] = None
    calculation_params: Optional[Dict[str, Any]] = None
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison_operator: str = Field(default=">=", description=">=, <=, ==, >, <")
    unit: Optional[str] = None
    decimal_places: int = Field(default=2, ge=0, le=6)
    display_format: Optional[str] = None
    chart_type: Optional[str] = None
    calculation_frequency: Optional[str] = Field(
        None, description="hourly, daily, weekly, monthly, on_demand"
    )
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class QualityMetricUpdate(BaseModel):
    """Schema for updating a quality metric."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison_operator: Optional[str] = None
    unit: Optional[str] = None
    decimal_places: Optional[int] = Field(None, ge=0, le=6)
    display_format: Optional[str] = None
    chart_type: Optional[str] = None
    calculation_frequency: Optional[str] = None
    calculation_query: Optional[str] = None
    calculation_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class QualityMetricResponse(BaseModel):
    """Schema for quality metric response."""

    id: UUID
    name: str
    description: Optional[str]
    category: str
    metric_type: str
    calculation_method: str
    calculation_frequency: Optional[str]
    target_value: Optional[float]
    warning_threshold: Optional[float]
    critical_threshold: Optional[float]
    comparison_operator: str
    unit: Optional[str]
    decimal_places: Optional[int]
    display_format: Optional[str]
    chart_type: Optional[str]
    is_active: bool
    is_public: bool
    last_calculated_at: Optional[datetime]
    next_calculation_at: Optional[datetime]
    created_at: datetime
    tags: Optional[List[str]]

    class Config:
        from_attributes = True


class QualityScoreCreate(BaseModel):
    """Schema for recording a quality score."""

    metric_id: UUID
    value: float
    cohort_id: Optional[UUID] = None
    time_period: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    breakdown: Optional[Dict[str, Any]] = None
    sample_size: Optional[int] = None
    calculation_details: Optional[Dict[str, Any]] = None


class QualityScoreResponse(BaseModel):
    """Schema for quality score response."""

    id: UUID
    metric_id: UUID
    value: float
    previous_value: Optional[float]
    change_percentage: Optional[float]
    status: str
    cohort_id: Optional[UUID]
    time_period: Optional[str]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    breakdown: Optional[Dict[str, Any]]
    sample_size: Optional[int]
    calculated_at: datetime

    class Config:
        from_attributes = True


class QualitySummaryResponse(BaseModel):
    """Schema for quality summary response."""

    total_metrics: int
    on_target: int
    warning: int
    critical: int
    unknown: int
    health_score: float
    by_category: Dict[str, Dict[str, int]]


class QualityTrendResponse(BaseModel):
    """Schema for quality trend response."""

    metric_id: str
    metric_name: str
    data: List[Dict[str, Any]]


class MetricWithLatestScore(BaseModel):
    """Schema for metric with its latest score."""

    metric: QualityMetricResponse
    score: Optional[QualityScoreResponse]
