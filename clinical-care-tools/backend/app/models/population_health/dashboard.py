"""Dashboard and report models for population health visualization."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DashboardConfiguration(Base):
    """Dashboard configuration model for saved layouts.

    Stores custom dashboard layouts with widgets and filters.

    Attributes:
        id: Unique identifier
        name: Dashboard name
        description: Dashboard description
        layout: Widget positions and sizes (grid layout)
        widgets: Widget configurations
        filters: Default dashboard filters
        refresh_interval_seconds: Auto-refresh interval
        is_default: Whether this is the default dashboard
        is_public: Visible to all users
        created_by: User who created the dashboard
    """
    __tablename__ = "dashboard_configurations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    layout = Column(JSONB, nullable=False)
    widgets = Column(JSONB, nullable=False)
    filters = Column(JSONB, nullable=True)
    refresh_interval_seconds = Column(Integer, nullable=True)
    is_default = Column(Boolean, nullable=False, server_default='false')
    is_public = Column(Boolean, nullable=False, server_default='false')
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    # Widget types
    WIDGET_TYPES = [
        "cohort_summary",      # Basic cohort statistics
        "condition_prevalence", # Condition breakdown chart
        "age_distribution",    # Age pyramid/histogram
        "gender_breakdown",    # Gender pie chart
        "trend_chart",         # Time series chart
        "medication_usage",    # Top medications
        "alert_summary",       # Active alerts count
        "metric_card",         # Single metric display
        "table",               # Data table
        "map",                 # Geographic distribution
    ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "layout": self.layout,
            "widgets": self.widgets,
            "filters": self.filters,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "is_default": self.is_default,
            "is_public": self.is_public,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_default_layout(cls) -> Dict[str, Any]:
        """Create a default dashboard layout."""
        return {
            "columns": 12,
            "row_height": 80,
            "items": [
                {"i": "cohort_summary", "x": 0, "y": 0, "w": 4, "h": 2},
                {"i": "condition_prevalence", "x": 4, "y": 0, "w": 4, "h": 2},
                {"i": "alert_summary", "x": 8, "y": 0, "w": 4, "h": 2},
                {"i": "age_distribution", "x": 0, "y": 2, "w": 6, "h": 3},
                {"i": "trend_chart", "x": 6, "y": 2, "w": 6, "h": 3},
            ]
        }

    @classmethod
    def create_default_widgets(cls) -> List[Dict[str, Any]]:
        """Create default widget configurations."""
        return [
            {
                "id": "cohort_summary",
                "type": "cohort_summary",
                "title": "Cohort Overview",
                "config": {}
            },
            {
                "id": "condition_prevalence",
                "type": "condition_prevalence",
                "title": "Top Conditions",
                "config": {"limit": 10}
            },
            {
                "id": "alert_summary",
                "type": "alert_summary",
                "title": "Active Alerts",
                "config": {}
            },
            {
                "id": "age_distribution",
                "type": "age_distribution",
                "title": "Age Distribution",
                "config": {"bin_size": 10}
            },
            {
                "id": "trend_chart",
                "type": "trend_chart",
                "title": "Patient Volume Trend",
                "config": {"metric": "patient_count", "period": "month"}
            }
        ]


class SavedReport(Base):
    """Saved report model for generated exports.

    Tracks generated reports (PDF, Excel, CSV) for download.

    Attributes:
        id: Unique identifier
        name: Report name
        report_type: Type of report
        cohort_id: Associated cohort (if applicable)
        parameters: Report generation parameters
        file_path: Path to generated file
        file_format: pdf, xlsx, csv
        file_size_bytes: File size
        status: Generation status
        error_message: Error if generation failed
        generated_by: User who requested the report
        generated_at: When generation completed
        expires_at: When to auto-delete
    """
    __tablename__ = "saved_reports"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    cohort_id = Column(PG_UUID(as_uuid=True), ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True)
    parameters = Column(JSONB, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_format = Column(String(20), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    status = Column(String(20), nullable=False, server_default='pending')
    error_message = Column(Text, nullable=True)
    generated_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    cohort = relationship("CohortDefinition", back_populates="reports")
    generator = relationship("User", foreign_keys=[generated_by])

    # Report types
    REPORT_TYPES = [
        "cohort_summary",      # Overview of cohort characteristics
        "condition_analysis",  # Detailed condition breakdown
        "trend_analysis",      # Time series analysis
        "medication_report",   # Medication usage report
        "demographic_report",  # Age, gender, ethnicity analysis
        "custom",              # Custom report with parameters
    ]

    # Statuses
    STATUSES = ["pending", "generating", "completed", "failed"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "report_type": self.report_type,
            "cohort_id": str(self.cohort_id) if self.cohort_id else None,
            "parameters": self.parameters,
            "file_path": self.file_path,
            "file_format": self.file_format,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "error_message": self.error_message,
            "generated_by": str(self.generated_by),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def mark_generating(self) -> None:
        """Mark report as currently generating."""
        self.status = "generating"

    def mark_completed(self, file_path: str, file_size: int) -> None:
        """Mark report as completed."""
        self.status = "completed"
        self.file_path = file_path
        self.file_size_bytes = file_size
        self.generated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark report as failed."""
        self.status = "failed"
        self.error_message = error_message
