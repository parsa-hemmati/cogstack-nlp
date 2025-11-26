"""Quality Metric models for tracking NLP and clinical quality."""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, Date
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base

logger = logging.getLogger(__name__)


class QualityMetric(Base):
    """Quality metric definition for tracking various quality measures.

    Supports NLP accuracy, data quality, clinical outcomes, and operational metrics.
    """

    __tablename__ = "quality_metrics"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)

    # Calculation configuration
    calculation_method = Column(String(50), nullable=False)
    calculation_query = Column(Text, nullable=True)
    calculation_params = Column(JSONB, nullable=True)

    # Thresholds and targets
    target_value = Column(Float, nullable=True)
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)
    comparison_operator = Column(String(10), nullable=False, server_default='>=')

    # Display settings
    unit = Column(String(50), nullable=True)
    decimal_places = Column(Integer, nullable=True, server_default='2')
    display_format = Column(String(100), nullable=True)
    chart_type = Column(String(50), nullable=True)

    # Scheduling
    calculation_frequency = Column(String(50), nullable=True)
    last_calculated_at = Column(DateTime(timezone=True), nullable=True)
    next_calculation_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, server_default='true')
    is_public = Column(Boolean, nullable=False, server_default='false')

    # Audit
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Relationships
    scores = relationship("QualityScore", back_populates="metric", lazy="dynamic")

    # Category constants
    CATEGORY_NLP_ACCURACY = "nlp_accuracy"
    CATEGORY_DATA_QUALITY = "data_quality"
    CATEGORY_CLINICAL_OUTCOMES = "clinical_outcomes"
    CATEGORY_OPERATIONAL = "operational"

    # Type constants
    TYPE_PERCENTAGE = "percentage"
    TYPE_COUNT = "count"
    TYPE_RATIO = "ratio"
    TYPE_SCORE = "score"
    TYPE_TIME = "time"

    # Calculation method constants
    METHOD_AUTOMATED = "automated"
    METHOD_MANUAL = "manual"
    METHOD_HYBRID = "hybrid"

    # Frequency constants
    FREQ_HOURLY = "hourly"
    FREQ_DAILY = "daily"
    FREQ_WEEKLY = "weekly"
    FREQ_MONTHLY = "monthly"
    FREQ_ON_DEMAND = "on_demand"

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "metric_type": self.metric_type,
            "calculation_method": self.calculation_method,
            "calculation_frequency": self.calculation_frequency,
            "target_value": self.target_value,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "comparison_operator": self.comparison_operator,
            "unit": self.unit,
            "decimal_places": self.decimal_places,
            "display_format": self.display_format,
            "chart_type": self.chart_type,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "last_calculated_at": self.last_calculated_at.isoformat() if self.last_calculated_at else None,
            "next_calculation_at": self.next_calculation_at.isoformat() if self.next_calculation_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags,
        }

    def evaluate_status(self, value: float) -> str:
        """Evaluate value against thresholds to determine status."""
        if self.comparison_operator == '>=':
            if self.critical_threshold is not None and value < self.critical_threshold:
                return "critical"
            elif self.warning_threshold is not None and value < self.warning_threshold:
                return "warning"
            elif self.target_value is not None and value >= self.target_value:
                return "on_target"
        elif self.comparison_operator == '<=':
            if self.critical_threshold is not None and value > self.critical_threshold:
                return "critical"
            elif self.warning_threshold is not None and value > self.warning_threshold:
                return "warning"
            elif self.target_value is not None and value <= self.target_value:
                return "on_target"
        elif self.comparison_operator == '==':
            if self.target_value is not None and value == self.target_value:
                return "on_target"
            elif self.warning_threshold is not None:
                return "warning"

        return "unknown"

    def format_value(self, value: float) -> str:
        """Format value for display."""
        if self.decimal_places is not None:
            value = round(value, self.decimal_places)

        if self.display_format:
            return self.display_format.format(value=value)
        elif self.unit:
            return f"{value}{self.unit}"
        return str(value)

    @classmethod
    def create_nlp_accuracy_metric(
        cls,
        name: str,
        created_by: UUID,
        description: Optional[str] = None,
        target_value: float = 90.0,
        warning_threshold: float = 85.0,
        critical_threshold: float = 75.0
    ) -> "QualityMetric":
        """Factory method for NLP accuracy metrics."""
        return cls(
            name=name,
            description=description,
            category=cls.CATEGORY_NLP_ACCURACY,
            metric_type=cls.TYPE_PERCENTAGE,
            calculation_method=cls.METHOD_AUTOMATED,
            target_value=target_value,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            comparison_operator=">=",
            unit="%",
            decimal_places=1,
            chart_type="line",
            calculation_frequency=cls.FREQ_DAILY,
            created_by=created_by
        )

    @classmethod
    def create_data_quality_metric(
        cls,
        name: str,
        created_by: UUID,
        description: Optional[str] = None,
        target_value: float = 95.0,
        warning_threshold: float = 90.0,
        critical_threshold: float = 80.0
    ) -> "QualityMetric":
        """Factory method for data quality metrics."""
        return cls(
            name=name,
            description=description,
            category=cls.CATEGORY_DATA_QUALITY,
            metric_type=cls.TYPE_PERCENTAGE,
            calculation_method=cls.METHOD_AUTOMATED,
            target_value=target_value,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            comparison_operator=">=",
            unit="%",
            decimal_places=1,
            chart_type="gauge",
            calculation_frequency=cls.FREQ_HOURLY,
            created_by=created_by
        )


class QualityScore(Base):
    """Time-series quality score for a metric.

    Tracks metric values over time for trend analysis.
    """

    __tablename__ = "quality_scores"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    metric_id = Column(PG_UUID(as_uuid=True), ForeignKey('quality_metrics.id', ondelete='CASCADE'), nullable=False)

    # Score value
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)

    # Status
    status = Column(String(20), nullable=False)

    # Context
    cohort_id = Column(PG_UUID(as_uuid=True), ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True)
    time_period = Column(String(50), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Breakdown
    breakdown = Column(JSONB, nullable=True)
    sample_size = Column(Integer, nullable=True)

    # Calculation details
    calculation_details = Column(JSONB, nullable=True)
    calculated_by = Column(String(50), nullable=False, server_default='system')

    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    metric = relationship("QualityMetric", back_populates="scores")

    # Status constants
    STATUS_ON_TARGET = "on_target"
    STATUS_WARNING = "warning"
    STATUS_CRITICAL = "critical"
    STATUS_UNKNOWN = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary."""
        return {
            "id": str(self.id),
            "metric_id": str(self.metric_id),
            "value": self.value,
            "previous_value": self.previous_value,
            "change_percentage": self.change_percentage,
            "status": self.status,
            "cohort_id": str(self.cohort_id) if self.cohort_id else None,
            "time_period": self.time_period,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "breakdown": self.breakdown,
            "sample_size": self.sample_size,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }

    def calculate_change(self) -> None:
        """Calculate change from previous value."""
        if self.previous_value is not None and self.previous_value != 0:
            self.change_percentage = ((self.value - self.previous_value) / self.previous_value) * 100
        else:
            self.change_percentage = None

    def is_improving(self, comparison_operator: str = '>=') -> Optional[bool]:
        """Check if metric is improving compared to previous."""
        if self.previous_value is None:
            return None

        if comparison_operator in ['>=', '>']:
            return self.value > self.previous_value
        elif comparison_operator in ['<=', '<']:
            return self.value < self.previous_value
        return None

    @classmethod
    def create_score(
        cls,
        metric: QualityMetric,
        value: float,
        previous_value: Optional[float] = None,
        cohort_id: Optional[UUID] = None,
        time_period: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        breakdown: Optional[Dict[str, Any]] = None,
        sample_size: Optional[int] = None,
        calculation_details: Optional[Dict[str, Any]] = None,
        calculated_by: str = "system"
    ) -> "QualityScore":
        """Factory method for creating a quality score with automatic status."""
        status = metric.evaluate_status(value)

        score = cls(
            metric_id=metric.id,
            value=value,
            previous_value=previous_value,
            status=status,
            cohort_id=cohort_id,
            time_period=time_period,
            period_start=period_start,
            period_end=period_end,
            breakdown=breakdown,
            sample_size=sample_size,
            calculation_details=calculation_details,
            calculated_by=calculated_by
        )
        score.calculate_change()
        return score


class QualityMetricTemplate:
    """Predefined quality metric templates for common use cases."""

    @staticmethod
    def nlp_precision() -> Dict[str, Any]:
        """NLP precision metric template."""
        return {
            "name": "NLP Precision",
            "description": "Precision of medical entity extraction",
            "category": QualityMetric.CATEGORY_NLP_ACCURACY,
            "metric_type": QualityMetric.TYPE_PERCENTAGE,
            "target_value": 90.0,
            "warning_threshold": 85.0,
            "critical_threshold": 75.0,
            "unit": "%",
        }

    @staticmethod
    def nlp_recall() -> Dict[str, Any]:
        """NLP recall metric template."""
        return {
            "name": "NLP Recall",
            "description": "Recall of medical entity extraction",
            "category": QualityMetric.CATEGORY_NLP_ACCURACY,
            "metric_type": QualityMetric.TYPE_PERCENTAGE,
            "target_value": 85.0,
            "warning_threshold": 80.0,
            "critical_threshold": 70.0,
            "unit": "%",
        }

    @staticmethod
    def nlp_f1_score() -> Dict[str, Any]:
        """NLP F1 score metric template."""
        return {
            "name": "NLP F1 Score",
            "description": "F1 score of medical entity extraction",
            "category": QualityMetric.CATEGORY_NLP_ACCURACY,
            "metric_type": QualityMetric.TYPE_PERCENTAGE,
            "target_value": 88.0,
            "warning_threshold": 82.0,
            "critical_threshold": 72.0,
            "unit": "%",
        }

    @staticmethod
    def document_completeness() -> Dict[str, Any]:
        """Document completeness metric template."""
        return {
            "name": "Document Completeness",
            "description": "Percentage of documents with complete metadata",
            "category": QualityMetric.CATEGORY_DATA_QUALITY,
            "metric_type": QualityMetric.TYPE_PERCENTAGE,
            "target_value": 98.0,
            "warning_threshold": 95.0,
            "critical_threshold": 90.0,
            "unit": "%",
        }

    @staticmethod
    def processing_success_rate() -> Dict[str, Any]:
        """Processing success rate metric template."""
        return {
            "name": "Processing Success Rate",
            "description": "Percentage of documents successfully processed",
            "category": QualityMetric.CATEGORY_OPERATIONAL,
            "metric_type": QualityMetric.TYPE_PERCENTAGE,
            "target_value": 99.5,
            "warning_threshold": 98.0,
            "critical_threshold": 95.0,
            "unit": "%",
        }

    @staticmethod
    def average_processing_time() -> Dict[str, Any]:
        """Average processing time metric template."""
        return {
            "name": "Average Processing Time",
            "description": "Average time to process a document",
            "category": QualityMetric.CATEGORY_OPERATIONAL,
            "metric_type": QualityMetric.TYPE_TIME,
            "target_value": 2.0,
            "warning_threshold": 5.0,
            "critical_threshold": 10.0,
            "comparison_operator": "<=",
            "unit": "s",
        }

    @classmethod
    def get_all_templates(cls) -> List[Dict[str, Any]]:
        """Get all predefined templates."""
        return [
            cls.nlp_precision(),
            cls.nlp_recall(),
            cls.nlp_f1_score(),
            cls.document_completeness(),
            cls.processing_success_rate(),
            cls.average_processing_time(),
        ]
