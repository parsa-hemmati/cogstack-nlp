"""MetricsService for calculating population health metrics.

Provides aggregated statistics for cohorts and the overall population.
"""
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.population_health.metrics import PopulationMetric
from app.models.population_health.cohort import CohortDefinition, CohortMembership

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for calculating and managing population metrics.

    Calculates various statistics for cohorts and the overall population.
    """

    def __init__(self, db: Session):
        """Initialize metrics service.

        Args:
            db: Database session
        """
        self.db = db

    def calculate_cohort_metrics(self, cohort_id: UUID) -> List[PopulationMetric]:
        """Calculate all standard metrics for a cohort.

        Args:
            cohort_id: Cohort to calculate metrics for

        Returns:
            List of calculated metrics
        """
        cohort = self.db.query(CohortDefinition).filter(
            CohortDefinition.id == cohort_id
        ).first()

        if not cohort:
            return []

        metrics = []

        # Calculate standard metrics
        metrics.append(self._calculate_patient_count(cohort_id))
        metrics.extend(self._calculate_age_distribution(cohort_id))
        metrics.extend(self._calculate_gender_distribution(cohort_id))
        metrics.extend(self._calculate_condition_prevalence(cohort_id))

        # Save all metrics
        for metric in metrics:
            self.db.add(metric)

        self.db.commit()

        logger.info(f"Calculated {len(metrics)} metrics for cohort {cohort_id}")
        return metrics

    def _calculate_patient_count(self, cohort_id: UUID) -> PopulationMetric:
        """Calculate total patient count for cohort."""
        count = self.db.query(func.count(CohortMembership.id)).filter(
            CohortMembership.cohort_id == cohort_id
        ).scalar() or 0

        return PopulationMetric.create_count_metric(
            metric_name="patient_count",
            value=count,
            cohort_id=cohort_id
        )

    def _calculate_age_distribution(self, cohort_id: UUID) -> List[PopulationMetric]:
        """Calculate age distribution for cohort."""
        # This would query patient demographics
        # Placeholder implementation
        age_groups = {
            "0-17": 0,
            "18-34": 0,
            "35-49": 0,
            "50-64": 0,
            "65-79": 0,
            "80+": 0
        }

        metrics = []
        total = sum(age_groups.values()) or 1  # Avoid division by zero

        for age_group, count in age_groups.items():
            metrics.append(PopulationMetric(
                cohort_id=cohort_id,
                metric_name="age_distribution",
                metric_type="count",
                value=float(count),
                dimension="age_group",
                dimension_value=age_group
            ))

        # Also create the full distribution
        metrics.append(PopulationMetric.create_distribution_metric(
            metric_name="age_distribution_full",
            distribution=age_groups,
            cohort_id=cohort_id,
            dimension="age_group"
        ))

        return metrics

    def _calculate_gender_distribution(self, cohort_id: UUID) -> List[PopulationMetric]:
        """Calculate gender distribution for cohort."""
        # Placeholder - would query patient demographics
        genders = {"male": 0, "female": 0, "other": 0, "unknown": 0}

        metrics = []
        total = sum(genders.values()) or 1

        for gender, count in genders.items():
            metrics.append(PopulationMetric(
                cohort_id=cohort_id,
                metric_name="gender_distribution",
                metric_type="percentage",
                value=(count / total) * 100,
                dimension="gender",
                dimension_value=gender
            ))

        return metrics

    def _calculate_condition_prevalence(self, cohort_id: UUID) -> List[PopulationMetric]:
        """Calculate top condition prevalence for cohort."""
        # Placeholder - would query patient conditions from NLP results
        conditions = {}  # Would be populated from actual data

        metrics = []
        for condition, count in list(conditions.items())[:20]:
            metrics.append(PopulationMetric(
                cohort_id=cohort_id,
                metric_name="condition_prevalence",
                metric_type="count",
                value=float(count),
                dimension="condition",
                dimension_value=condition
            ))

        return metrics

    def get_cohort_summary(self, cohort_id: UUID) -> Dict[str, Any]:
        """Get summary statistics for a cohort.

        Args:
            cohort_id: Cohort ID

        Returns:
            Summary dictionary
        """
        cohort = self.db.query(CohortDefinition).filter(
            CohortDefinition.id == cohort_id
        ).first()

        if not cohort:
            return {}

        # Get latest metrics
        patient_count = self.db.query(PopulationMetric).filter(
            PopulationMetric.cohort_id == cohort_id,
            PopulationMetric.metric_name == "patient_count"
        ).order_by(PopulationMetric.calculated_at.desc()).first()

        age_dist = self.db.query(PopulationMetric).filter(
            PopulationMetric.cohort_id == cohort_id,
            PopulationMetric.metric_name == "age_distribution_full"
        ).order_by(PopulationMetric.calculated_at.desc()).first()

        return {
            "cohort_id": str(cohort_id),
            "cohort_name": cohort.name,
            "patient_count": patient_count.value if patient_count else cohort.patient_count,
            "age_distribution": age_dist.value_json if age_dist else None,
            "last_refreshed": cohort.last_refreshed.isoformat() if cohort.last_refreshed else None,
        }

    def get_metric_trend(
        self,
        metric_name: str,
        cohort_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get historical trend for a metric.

        Args:
            metric_name: Name of metric
            cohort_id: Optional cohort filter
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of metric values over time
        """
        query = self.db.query(PopulationMetric).filter(
            PopulationMetric.metric_name == metric_name
        )

        if cohort_id:
            query = query.filter(PopulationMetric.cohort_id == cohort_id)

        if start_date:
            query = query.filter(PopulationMetric.calculated_at >= start_date)

        if end_date:
            query = query.filter(PopulationMetric.calculated_at <= end_date)

        metrics = query.order_by(PopulationMetric.calculated_at).all()

        return [
            {
                "timestamp": m.calculated_at.isoformat() if m.calculated_at else None,
                "value": m.value,
                "dimension": m.dimension,
                "dimension_value": m.dimension_value
            }
            for m in metrics
        ]

    def calculate_global_metrics(self) -> List[PopulationMetric]:
        """Calculate metrics for the entire patient population.

        Returns:
            List of global metrics
        """
        metrics = []

        # Total patients
        # Would query actual patient table
        total_patients = 0  # Placeholder

        metrics.append(PopulationMetric.create_count_metric(
            metric_name="total_patients",
            value=total_patients
        ))

        # Active cohorts count
        cohort_count = self.db.query(func.count(CohortDefinition.id)).scalar() or 0
        metrics.append(PopulationMetric.create_count_metric(
            metric_name="total_cohorts",
            value=cohort_count
        ))

        for metric in metrics:
            self.db.add(metric)

        self.db.commit()
        return metrics

    def get_comparison_metrics(
        self,
        cohort_ids: List[UUID],
        metric_names: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get metrics for comparing multiple cohorts.

        Args:
            cohort_ids: Cohorts to compare
            metric_names: Metrics to compare

        Returns:
            Comparison data by cohort
        """
        result = {}

        for cohort_id in cohort_ids:
            cohort = self.db.query(CohortDefinition).filter(
                CohortDefinition.id == cohort_id
            ).first()

            if not cohort:
                continue

            cohort_metrics = {}
            for metric_name in metric_names:
                metric = self.db.query(PopulationMetric).filter(
                    PopulationMetric.cohort_id == cohort_id,
                    PopulationMetric.metric_name == metric_name
                ).order_by(PopulationMetric.calculated_at.desc()).first()

                if metric:
                    cohort_metrics[metric_name] = metric.value or metric.value_json

            result[str(cohort_id)] = {
                "name": cohort.name,
                "metrics": cohort_metrics
            }

        return result
