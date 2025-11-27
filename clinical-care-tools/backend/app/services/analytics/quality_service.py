"""QualityService for managing quality metrics and scores."""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.analytics.quality_metric import QualityMetric, QualityScore, QualityMetricTemplate

logger = logging.getLogger(__name__)


class QualityService:
    """Service for managing quality metrics and calculating scores.

    Handles metric definitions, automated calculations, and trend analysis.
    """

    def __init__(self, db: Session):
        """Initialize quality service.

        Args:
            db: Database session
        """
        self.db = db

    def create_metric(
        self,
        name: str,
        category: str,
        metric_type: str,
        calculation_method: str,
        created_by: UUID,
        description: Optional[str] = None,
        calculation_query: Optional[str] = None,
        calculation_params: Optional[Dict[str, Any]] = None,
        target_value: Optional[float] = None,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        comparison_operator: str = ">=",
        unit: Optional[str] = None,
        decimal_places: int = 2,
        display_format: Optional[str] = None,
        chart_type: Optional[str] = None,
        calculation_frequency: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityMetric:
        """Create a new quality metric.

        Args:
            name: Metric name
            category: Metric category
            metric_type: Type of metric
            calculation_method: How to calculate
            created_by: User creating the metric
            description: Metric description
            calculation_query: SQL/ES query for automated calculation
            calculation_params: Query parameters
            target_value: Target value to achieve
            warning_threshold: Warning threshold
            critical_threshold: Critical threshold
            comparison_operator: How to compare against thresholds
            unit: Display unit
            decimal_places: Decimal precision
            display_format: Format string
            chart_type: Preferred chart type
            calculation_frequency: How often to calculate
            tags: Organization tags
            metadata: Additional metadata

        Returns:
            Created QualityMetric
        """
        metric = QualityMetric(
            name=name,
            description=description,
            category=category,
            metric_type=metric_type,
            calculation_method=calculation_method,
            calculation_query=calculation_query,
            calculation_params=calculation_params,
            target_value=target_value,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            comparison_operator=comparison_operator,
            unit=unit,
            decimal_places=decimal_places,
            display_format=display_format,
            chart_type=chart_type,
            calculation_frequency=calculation_frequency,
            created_by=created_by,
            tags=tags,
            metadata=metadata
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)

        logger.info(f"Created quality metric: {name} (id={metric.id})")
        return metric

    def create_from_template(
        self,
        template_name: str,
        created_by: UUID,
        **overrides
    ) -> Optional[QualityMetric]:
        """Create a metric from a predefined template.

        Args:
            template_name: Template name (e.g., "nlp_precision")
            created_by: User creating the metric
            **overrides: Override template values

        Returns:
            Created QualityMetric or None if template not found
        """
        template_methods = {
            "nlp_precision": QualityMetricTemplate.nlp_precision,
            "nlp_recall": QualityMetricTemplate.nlp_recall,
            "nlp_f1_score": QualityMetricTemplate.nlp_f1_score,
            "document_completeness": QualityMetricTemplate.document_completeness,
            "processing_success_rate": QualityMetricTemplate.processing_success_rate,
            "average_processing_time": QualityMetricTemplate.average_processing_time,
        }

        if template_name not in template_methods:
            logger.warning(f"Unknown template: {template_name}")
            return None

        template = template_methods[template_name]()
        template.update(overrides)
        template["created_by"] = created_by
        template["calculation_method"] = QualityMetric.METHOD_AUTOMATED

        return self.create_metric(**template)

    def initialize_default_metrics(self, created_by: UUID) -> List[QualityMetric]:
        """Initialize all default quality metrics from templates.

        Args:
            created_by: User creating the metrics

        Returns:
            List of created metrics
        """
        templates = [
            "nlp_precision",
            "nlp_recall",
            "nlp_f1_score",
            "document_completeness",
            "processing_success_rate",
            "average_processing_time"
        ]

        created = []
        for template_name in templates:
            # Check if already exists
            existing = self.db.query(QualityMetric).filter(
                QualityMetric.name == template_name.replace("_", " ").title()
            ).first()

            if not existing:
                metric = self.create_from_template(template_name, created_by)
                if metric:
                    created.append(metric)

        logger.info(f"Initialized {len(created)} default quality metrics")
        return created

    def get_metric(self, metric_id: UUID) -> Optional[QualityMetric]:
        """Get a metric by ID.

        Args:
            metric_id: Metric ID

        Returns:
            QualityMetric or None
        """
        return self.db.query(QualityMetric).filter(
            QualityMetric.id == metric_id
        ).first()

    def get_metric_by_name(self, name: str) -> Optional[QualityMetric]:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            QualityMetric or None
        """
        return self.db.query(QualityMetric).filter(
            QualityMetric.name == name
        ).first()

    def list_metrics(
        self,
        category: Optional[str] = None,
        is_active: bool = True,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[QualityMetric]:
        """List quality metrics with optional filtering.

        Args:
            category: Filter by category
            is_active: Filter by active status
            tags: Filter by tags
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of QualityMetric objects
        """
        query = self.db.query(QualityMetric)

        if category:
            query = query.filter(QualityMetric.category == category)
        if is_active is not None:
            query = query.filter(QualityMetric.is_active == is_active)
        if tags:
            query = query.filter(QualityMetric.tags.overlap(tags))

        return query.order_by(
            QualityMetric.name
        ).offset(offset).limit(limit).all()

    def update_metric(
        self,
        metric_id: UUID,
        **updates
    ) -> Optional[QualityMetric]:
        """Update a quality metric.

        Args:
            metric_id: Metric to update
            **updates: Fields to update

        Returns:
            Updated metric or None
        """
        metric = self.get_metric(metric_id)
        if not metric:
            return None

        allowed_fields = [
            "name", "description", "target_value", "warning_threshold",
            "critical_threshold", "comparison_operator", "unit", "decimal_places",
            "display_format", "chart_type", "calculation_frequency",
            "calculation_query", "calculation_params", "is_active", "is_public", "tags"
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(metric, field, value)

        self.db.commit()
        self.db.refresh(metric)

        return metric

    def delete_metric(self, metric_id: UUID) -> bool:
        """Delete a quality metric.

        Args:
            metric_id: Metric to delete

        Returns:
            True if deleted
        """
        metric = self.get_metric(metric_id)
        if not metric:
            return False

        self.db.delete(metric)
        self.db.commit()

        logger.info(f"Deleted quality metric: {metric.name}")
        return True

    def record_score(
        self,
        metric_id: UUID,
        value: float,
        cohort_id: Optional[UUID] = None,
        time_period: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        breakdown: Optional[Dict[str, Any]] = None,
        sample_size: Optional[int] = None,
        calculation_details: Optional[Dict[str, Any]] = None,
        calculated_by: str = "system"
    ) -> Optional[QualityScore]:
        """Record a quality score for a metric.

        Args:
            metric_id: Metric being scored
            value: Score value
            cohort_id: Optional cohort context
            time_period: Time period label
            period_start: Period start datetime
            period_end: Period end datetime
            breakdown: Score breakdown by dimension
            sample_size: Sample size for calculation
            calculation_details: Raw calculation data
            calculated_by: User or system that calculated

        Returns:
            Created QualityScore or None
        """
        metric = self.get_metric(metric_id)
        if not metric:
            return None

        # Get previous score for change calculation
        previous = self.get_latest_score(metric_id, cohort_id)
        previous_value = previous.value if previous else None

        score = QualityScore.create_score(
            metric=metric,
            value=value,
            previous_value=previous_value,
            cohort_id=cohort_id,
            time_period=time_period,
            period_start=period_start,
            period_end=period_end,
            breakdown=breakdown,
            sample_size=sample_size,
            calculation_details=calculation_details,
            calculated_by=calculated_by
        )

        self.db.add(score)

        # Update metric's last calculated timestamp
        metric.last_calculated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(score)

        logger.debug(f"Recorded score for {metric.name}: {value} ({score.status})")
        return score

    def get_latest_score(
        self,
        metric_id: UUID,
        cohort_id: Optional[UUID] = None
    ) -> Optional[QualityScore]:
        """Get the latest score for a metric.

        Args:
            metric_id: Metric ID
            cohort_id: Optional cohort filter

        Returns:
            Latest QualityScore or None
        """
        query = self.db.query(QualityScore).filter(
            QualityScore.metric_id == metric_id
        )

        if cohort_id:
            query = query.filter(QualityScore.cohort_id == cohort_id)

        return query.order_by(
            QualityScore.calculated_at.desc()
        ).first()

    def get_score_history(
        self,
        metric_id: UUID,
        cohort_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[QualityScore]:
        """Get historical scores for a metric.

        Args:
            metric_id: Metric ID
            cohort_id: Optional cohort filter
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum results

        Returns:
            List of QualityScore objects
        """
        query = self.db.query(QualityScore).filter(
            QualityScore.metric_id == metric_id
        )

        if cohort_id:
            query = query.filter(QualityScore.cohort_id == cohort_id)
        if start_date:
            query = query.filter(QualityScore.calculated_at >= start_date)
        if end_date:
            query = query.filter(QualityScore.calculated_at <= end_date)

        return query.order_by(
            QualityScore.calculated_at.desc()
        ).limit(limit).all()

    def get_all_latest_scores(
        self,
        category: Optional[str] = None,
        cohort_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get latest scores for all metrics.

        Args:
            category: Optional category filter
            cohort_id: Optional cohort filter

        Returns:
            List of metric + score combinations
        """
        metrics = self.list_metrics(category=category, is_active=True)
        results = []

        for metric in metrics:
            score = self.get_latest_score(metric.id, cohort_id)
            results.append({
                "metric": metric.to_dict(),
                "score": score.to_dict() if score else None
            })

        return results

    def calculate_metric(
        self,
        metric_id: UUID,
        cohort_id: Optional[UUID] = None
    ) -> Optional[QualityScore]:
        """Calculate current value for a metric.

        Args:
            metric_id: Metric to calculate
            cohort_id: Optional cohort context

        Returns:
            New QualityScore or None
        """
        metric = self.get_metric(metric_id)
        if not metric:
            return None

        # Placeholder - would execute calculation_query against actual data
        # In production, would:
        # 1. Parse calculation_query (SQL or Elasticsearch DSL)
        # 2. Execute against appropriate data source
        # 3. Process results

        # Simulated calculation
        import random
        base_value = metric.target_value or 90.0
        variation = random.uniform(-10, 5)
        calculated_value = max(0, min(100, base_value + variation))

        return self.record_score(
            metric_id=metric_id,
            value=round(calculated_value, metric.decimal_places or 2),
            cohort_id=cohort_id,
            time_period=datetime.utcnow().strftime("%Y-%m-%d"),
            period_start=datetime.utcnow().replace(hour=0, minute=0, second=0),
            period_end=datetime.utcnow(),
            calculated_by="system"
        )

    def calculate_all_metrics(
        self,
        cohort_id: Optional[UUID] = None
    ) -> List[QualityScore]:
        """Calculate all active automated metrics.

        Args:
            cohort_id: Optional cohort context

        Returns:
            List of new scores
        """
        metrics = self.db.query(QualityMetric).filter(
            QualityMetric.is_active == True,
            QualityMetric.calculation_method == QualityMetric.METHOD_AUTOMATED
        ).all()

        scores = []
        for metric in metrics:
            score = self.calculate_metric(metric.id, cohort_id)
            if score:
                scores.append(score)

        logger.info(f"Calculated {len(scores)} quality metrics")
        return scores

    def get_quality_summary(
        self,
        cohort_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get overall quality summary.

        Args:
            cohort_id: Optional cohort filter

        Returns:
            Summary dictionary
        """
        metrics = self.list_metrics(is_active=True)

        on_target = 0
        warning = 0
        critical = 0
        unknown = 0

        for metric in metrics:
            score = self.get_latest_score(metric.id, cohort_id)
            if score:
                if score.status == QualityScore.STATUS_ON_TARGET:
                    on_target += 1
                elif score.status == QualityScore.STATUS_WARNING:
                    warning += 1
                elif score.status == QualityScore.STATUS_CRITICAL:
                    critical += 1
                else:
                    unknown += 1
            else:
                unknown += 1

        total = len(metrics)
        health_score = (on_target / total * 100) if total > 0 else 0

        return {
            "total_metrics": total,
            "on_target": on_target,
            "warning": warning,
            "critical": critical,
            "unknown": unknown,
            "health_score": round(health_score, 1),
            "by_category": self._get_summary_by_category(cohort_id)
        }

    def _get_summary_by_category(
        self,
        cohort_id: Optional[UUID] = None
    ) -> Dict[str, Dict[str, int]]:
        """Get quality summary grouped by category.

        Args:
            cohort_id: Optional cohort filter

        Returns:
            Summary by category
        """
        result = {}

        categories = self.db.query(
            QualityMetric.category
        ).distinct().all()

        for (category,) in categories:
            metrics = self.list_metrics(category=category, is_active=True)
            counts = {"on_target": 0, "warning": 0, "critical": 0}

            for metric in metrics:
                score = self.get_latest_score(metric.id, cohort_id)
                if score and score.status in counts:
                    counts[score.status] += 1

            result[category] = counts

        return result

    def get_trend_data(
        self,
        metric_ids: List[UUID],
        days: int = 30,
        cohort_id: Optional[UUID] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get trend data for multiple metrics.

        Args:
            metric_ids: Metrics to include
            days: Number of days
            cohort_id: Optional cohort filter

        Returns:
            Trend data by metric
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        result = {}

        for metric_id in metric_ids:
            metric = self.get_metric(metric_id)
            if not metric:
                continue

            scores = self.get_score_history(
                metric_id=metric_id,
                cohort_id=cohort_id,
                start_date=start_date
            )

            result[str(metric_id)] = {
                "metric_name": metric.name,
                "data": [
                    {
                        "timestamp": s.calculated_at.isoformat(),
                        "value": s.value,
                        "status": s.status
                    }
                    for s in reversed(scores)
                ]
            }

        return result

    def get_metrics_needing_calculation(self) -> List[QualityMetric]:
        """Get metrics that are due for recalculation.

        Returns:
            List of metrics needing calculation
        """
        now = datetime.utcnow()

        return self.db.query(QualityMetric).filter(
            QualityMetric.is_active == True,
            QualityMetric.calculation_method == QualityMetric.METHOD_AUTOMATED,
            QualityMetric.next_calculation_at <= now
        ).all()

    def schedule_next_calculation(self, metric: QualityMetric) -> None:
        """Schedule the next calculation time for a metric.

        Args:
            metric: Metric to schedule
        """
        if not metric.calculation_frequency:
            return

        now = datetime.utcnow()
        freq_map = {
            QualityMetric.FREQ_HOURLY: timedelta(hours=1),
            QualityMetric.FREQ_DAILY: timedelta(days=1),
            QualityMetric.FREQ_WEEKLY: timedelta(weeks=1),
            QualityMetric.FREQ_MONTHLY: timedelta(days=30),
        }

        delta = freq_map.get(metric.calculation_frequency)
        if delta:
            metric.next_calculation_at = now + delta
            self.db.commit()
