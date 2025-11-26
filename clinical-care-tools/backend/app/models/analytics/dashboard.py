"""Analytics Dashboard and Report models."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, Date, BigInteger
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base

logger = logging.getLogger(__name__)


class AnalyticsDashboard(Base):
    """Custom analytics dashboard configuration.

    Supports quality dashboards, predictive analytics, and custom layouts.
    """

    __tablename__ = "analytics_dashboards"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dashboard_type = Column(String(50), nullable=False)

    # Layout configuration
    layout = Column(JSONB, nullable=True)
    widgets = Column(JSONB, nullable=True)
    theme = Column(String(50), nullable=True, server_default='default')

    # Filters and defaults
    default_filters = Column(JSONB, nullable=True)
    default_date_range = Column(String(50), nullable=True)
    default_cohort_id = Column(PG_UUID(as_uuid=True), ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True)

    # Refresh settings
    auto_refresh = Column(Boolean, nullable=False, server_default='false')
    refresh_interval_seconds = Column(Integer, nullable=True)

    # Access control
    is_public = Column(Boolean, nullable=False, server_default='false')
    is_default = Column(Boolean, nullable=False, server_default='false')
    allowed_roles = Column(ARRAY(String), nullable=True)

    # Audit
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Relationships
    reports = relationship("AnalyticsReport", back_populates="dashboard", lazy="dynamic")

    # Type constants
    TYPE_QUALITY = "quality"
    TYPE_PREDICTIVE = "predictive"
    TYPE_OPERATIONAL = "operational"
    TYPE_CUSTOM = "custom"

    # Theme constants
    THEME_DEFAULT = "default"
    THEME_DARK = "dark"
    THEME_CLINICAL = "clinical"

    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "dashboard_type": self.dashboard_type,
            "layout": self.layout,
            "widgets": self.widgets,
            "theme": self.theme,
            "default_filters": self.default_filters,
            "default_date_range": self.default_date_range,
            "default_cohort_id": str(self.default_cohort_id) if self.default_cohort_id else None,
            "auto_refresh": self.auto_refresh,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "is_public": self.is_public,
            "is_default": self.is_default,
            "allowed_roles": self.allowed_roles,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags,
        }

    @classmethod
    def create_default_quality_layout(cls) -> Dict[str, Any]:
        """Create default layout for quality dashboard."""
        return {
            "columns": 12,
            "rowHeight": 100,
            "margin": [10, 10],
            "containerPadding": [10, 10],
            "isDraggable": True,
            "isResizable": True
        }

    @classmethod
    def create_default_quality_widgets(cls) -> List[Dict[str, Any]]:
        """Create default widgets for quality dashboard."""
        return [
            {
                "id": "nlp-accuracy-gauge",
                "type": "gauge",
                "title": "NLP Accuracy",
                "config": {
                    "metric": "nlp_f1_score",
                    "thresholds": {"warning": 85, "critical": 75}
                },
                "layout": {"x": 0, "y": 0, "w": 3, "h": 2}
            },
            {
                "id": "processing-success-gauge",
                "type": "gauge",
                "title": "Processing Success",
                "config": {
                    "metric": "processing_success_rate",
                    "thresholds": {"warning": 98, "critical": 95}
                },
                "layout": {"x": 3, "y": 0, "w": 3, "h": 2}
            },
            {
                "id": "data-quality-gauge",
                "type": "gauge",
                "title": "Data Quality",
                "config": {
                    "metric": "document_completeness",
                    "thresholds": {"warning": 95, "critical": 90}
                },
                "layout": {"x": 6, "y": 0, "w": 3, "h": 2}
            },
            {
                "id": "avg-processing-time",
                "type": "metric",
                "title": "Avg Processing Time",
                "config": {
                    "metric": "average_processing_time",
                    "format": "{value}s"
                },
                "layout": {"x": 9, "y": 0, "w": 3, "h": 2}
            },
            {
                "id": "quality-trend",
                "type": "line_chart",
                "title": "Quality Trends",
                "config": {
                    "metrics": ["nlp_precision", "nlp_recall", "nlp_f1_score"],
                    "timeRange": "last_30_days"
                },
                "layout": {"x": 0, "y": 2, "w": 8, "h": 3}
            },
            {
                "id": "quality-breakdown",
                "type": "bar_chart",
                "title": "Quality by Category",
                "config": {
                    "groupBy": "category",
                    "metric": "average_score"
                },
                "layout": {"x": 8, "y": 2, "w": 4, "h": 3}
            },
            {
                "id": "recent-scores",
                "type": "table",
                "title": "Recent Scores",
                "config": {
                    "columns": ["metric", "value", "status", "change"],
                    "limit": 10
                },
                "layout": {"x": 0, "y": 5, "w": 6, "h": 3}
            },
            {
                "id": "alerts-summary",
                "type": "alert_list",
                "title": "Quality Alerts",
                "config": {
                    "filter": "critical_and_warning",
                    "limit": 5
                },
                "layout": {"x": 6, "y": 5, "w": 6, "h": 3}
            }
        ]

    @classmethod
    def create_default_predictive_widgets(cls) -> List[Dict[str, Any]]:
        """Create default widgets for predictive analytics dashboard."""
        return [
            {
                "id": "risk-distribution",
                "type": "pie_chart",
                "title": "Risk Distribution",
                "config": {
                    "groupBy": "risk_level",
                    "colors": {
                        "low": "#4CAF50",
                        "medium": "#FFC107",
                        "high": "#FF9800",
                        "critical": "#F44336"
                    }
                },
                "layout": {"x": 0, "y": 0, "w": 4, "h": 3}
            },
            {
                "id": "model-performance",
                "type": "line_chart",
                "title": "Model Performance",
                "config": {
                    "metrics": ["accuracy", "precision", "recall"],
                    "timeRange": "last_30_days"
                },
                "layout": {"x": 4, "y": 0, "w": 8, "h": 3}
            },
            {
                "id": "high-risk-patients",
                "type": "table",
                "title": "High Risk Patients",
                "config": {
                    "filter": {"risk_level": ["high", "critical"]},
                    "columns": ["patient_id", "risk_level", "confidence", "risk_factors"],
                    "limit": 10
                },
                "layout": {"x": 0, "y": 3, "w": 12, "h": 4}
            },
            {
                "id": "prediction-accuracy",
                "type": "gauge",
                "title": "Prediction Accuracy",
                "config": {
                    "metric": "prediction_accuracy",
                    "thresholds": {"warning": 85, "critical": 75}
                },
                "layout": {"x": 0, "y": 7, "w": 3, "h": 2}
            },
            {
                "id": "predictions-today",
                "type": "metric",
                "title": "Predictions Today",
                "config": {
                    "metric": "predictions_count",
                    "timeRange": "today"
                },
                "layout": {"x": 3, "y": 7, "w": 3, "h": 2}
            }
        ]


class AnalyticsReport(Base):
    """Generated analytics report.

    Supports various report types with scheduling and distribution.
    """

    __tablename__ = "analytics_reports"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(50), nullable=False)

    # Report configuration
    dashboard_id = Column(PG_UUID(as_uuid=True), ForeignKey('analytics_dashboards.id', ondelete='SET NULL'), nullable=True)
    metrics = Column(ARRAY(PG_UUID(as_uuid=True)), nullable=True)
    parameters = Column(JSONB, nullable=True)

    # Date range
    date_range_type = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    relative_period = Column(String(50), nullable=True)

    # Cohort filter
    cohort_id = Column(PG_UUID(as_uuid=True), ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True)

    # Output configuration
    file_format = Column(String(20), nullable=False)
    include_charts = Column(Boolean, nullable=False, server_default='true')
    include_raw_data = Column(Boolean, nullable=False, server_default='false')

    # Generation status
    status = Column(String(20), nullable=False, server_default='pending')
    progress_percentage = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Generated file
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Scheduling
    is_scheduled = Column(Boolean, nullable=False, server_default='false')
    schedule_cron = Column(String(100), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    # Distribution
    email_recipients = Column(ARRAY(String), nullable=True)
    auto_send = Column(Boolean, nullable=False, server_default='false')

    # Audit
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Relationships
    dashboard = relationship("AnalyticsDashboard", back_populates="reports")

    # Report type constants
    TYPE_QUALITY_SUMMARY = "quality_summary"
    TYPE_TREND_ANALYSIS = "trend_analysis"
    TYPE_MODEL_PERFORMANCE = "model_performance"
    TYPE_CUSTOM = "custom"

    # Format constants
    FORMAT_PDF = "pdf"
    FORMAT_XLSX = "xlsx"
    FORMAT_CSV = "csv"
    FORMAT_HTML = "html"

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_GENERATING = "generating"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    # Period constants
    PERIOD_LAST_7_DAYS = "last_7_days"
    PERIOD_LAST_30_DAYS = "last_30_days"
    PERIOD_THIS_MONTH = "this_month"
    PERIOD_LAST_MONTH = "last_month"
    PERIOD_THIS_QUARTER = "this_quarter"
    PERIOD_THIS_YEAR = "this_year"

    REPORT_EXPIRY_DAYS = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "report_type": self.report_type,
            "dashboard_id": str(self.dashboard_id) if self.dashboard_id else None,
            "metrics": [str(m) for m in self.metrics] if self.metrics else None,
            "parameters": self.parameters,
            "date_range_type": self.date_range_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "relative_period": self.relative_period,
            "cohort_id": str(self.cohort_id) if self.cohort_id else None,
            "file_format": self.file_format,
            "include_charts": self.include_charts,
            "include_raw_data": self.include_raw_data,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_scheduled": self.is_scheduled,
            "schedule_cron": self.schedule_cron,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "email_recipients": self.email_recipients,
            "auto_send": self.auto_send,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags,
        }

    def mark_generating(self) -> None:
        """Mark report as generating."""
        self.status = self.STATUS_GENERATING
        self.progress_percentage = 0
        self.error_message = None

    def update_progress(self, percentage: int) -> None:
        """Update generation progress."""
        self.progress_percentage = min(max(percentage, 0), 100)

    def mark_completed(self, file_path: str, file_size_bytes: int) -> None:
        """Mark report as completed."""
        self.status = self.STATUS_COMPLETED
        self.progress_percentage = 100
        self.file_path = file_path
        self.file_size_bytes = file_size_bytes
        self.generated_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=self.REPORT_EXPIRY_DAYS)

    def mark_failed(self, error_message: str) -> None:
        """Mark report as failed."""
        self.status = self.STATUS_FAILED
        self.error_message = error_message

    def is_expired(self) -> bool:
        """Check if report has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get_download_filename(self) -> str:
        """Generate download filename."""
        safe_name = self.name.replace(" ", "_").lower()
        date_str = datetime.utcnow().strftime("%Y%m%d")
        return f"{safe_name}_{date_str}.{self.file_format}"

    def can_regenerate(self) -> bool:
        """Check if report can be regenerated."""
        return self.status in [self.STATUS_COMPLETED, self.STATUS_FAILED]
