"""Population metrics model for aggregated statistics."""
from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PopulationMetric(Base):
    """Population metric model for aggregated statistics.

    Stores calculated metrics for cohorts or the entire population.

    Attributes:
        id: Unique identifier
        cohort_id: Reference to cohort (NULL for global metrics)
        metric_name: Name of the metric (e.g., "diabetes_prevalence")
        metric_type: Type (count, percentage, average, distribution)
        value: Numeric value for simple metrics
        value_json: Complex values like distributions
        dimension: Grouping dimension (age_group, gender, etc.)
        dimension_value: Value within dimension
        period_start: Start of measurement period
        period_end: End of measurement period
        calculated_at: When metric was calculated
    """
    __tablename__ = "population_metrics"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    cohort_id = Column(PG_UUID(as_uuid=True), ForeignKey('cohort_definitions.id', ondelete='CASCADE'), nullable=True)
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=True)
    value_json = Column(JSONB, nullable=True)
    dimension = Column(String(100), nullable=True)
    dimension_value = Column(String(255), nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cohort = relationship("CohortDefinition", back_populates="metrics")

    # Common metric types
    METRIC_TYPES = ["count", "percentage", "average", "median", "distribution", "trend"]

    # Common dimensions
    DIMENSIONS = ["age_group", "gender", "ethnicity", "location", "diagnosis", "medication"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "cohort_id": str(self.cohort_id) if self.cohort_id else None,
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "value": self.value,
            "value_json": self.value_json,
            "dimension": self.dimension,
            "dimension_value": self.dimension_value,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }

    @classmethod
    def create_count_metric(
        cls,
        metric_name: str,
        value: int,
        cohort_id: Optional[UUID] = None,
        dimension: Optional[str] = None,
        dimension_value: Optional[str] = None
    ) -> "PopulationMetric":
        """Create a count metric."""
        return cls(
            cohort_id=cohort_id,
            metric_name=metric_name,
            metric_type="count",
            value=float(value),
            dimension=dimension,
            dimension_value=dimension_value
        )

    @classmethod
    def create_percentage_metric(
        cls,
        metric_name: str,
        value: float,
        cohort_id: Optional[UUID] = None,
        dimension: Optional[str] = None,
        dimension_value: Optional[str] = None
    ) -> "PopulationMetric":
        """Create a percentage metric."""
        return cls(
            cohort_id=cohort_id,
            metric_name=metric_name,
            metric_type="percentage",
            value=value,
            dimension=dimension,
            dimension_value=dimension_value
        )

    @classmethod
    def create_distribution_metric(
        cls,
        metric_name: str,
        distribution: Dict[str, Any],
        cohort_id: Optional[UUID] = None,
        dimension: Optional[str] = None
    ) -> "PopulationMetric":
        """Create a distribution metric."""
        return cls(
            cohort_id=cohort_id,
            metric_name=metric_name,
            metric_type="distribution",
            value_json=distribution,
            dimension=dimension
        )
