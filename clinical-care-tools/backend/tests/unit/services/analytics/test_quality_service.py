"""Unit tests for Quality Service."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.analytics.quality_service import QualityService
from app.models.analytics.quality_metric import (
    QualityMetric,
    QualityScore,
    QualityMetricTemplate,
)
from app.schemas.analytics.quality import (
    QualityMetricCreate,
    QualityMetricUpdate,
    QualityScoreCreate,
)


class TestQualityService:
    """Test suite for QualityService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create QualityService instance."""
        return QualityService(mock_db)

    @pytest.fixture
    def sample_metric(self):
        """Create sample quality metric."""
        return QualityMetric(
            id=uuid4(),
            name="NLP Precision",
            description="Precision of NLP entity extraction",
            category="nlp_accuracy",
            metric_type="percentage",
            calculation_method="automated",
            target_value=90.0,
            warning_threshold=85.0,
            critical_threshold=80.0,
            comparison_operator=">=",
            unit="%",
            decimal_places=2,
            is_active=True,
            is_public=True,
            created_at=datetime.utcnow(),
        )

    @pytest.fixture
    def sample_score(self, sample_metric):
        """Create sample quality score."""
        return QualityScore(
            id=uuid4(),
            metric_id=sample_metric.id,
            value=92.5,
            previous_value=91.0,
            change_percentage=1.65,
            status="on_target",
            calculated_at=datetime.utcnow(),
        )

    async def test_create_metric(self, service, mock_db):
        """Test creating a quality metric."""
        metric_data = QualityMetricCreate(
            name="Test Metric",
            category="nlp_accuracy",
            metric_type="percentage",
            calculation_method="automated",
            target_value=90.0,
            description="Test description",
        )

        # Configure mock to return the added metric
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.create_metric(metric_data)

        assert mock_db.add.called
        assert mock_db.commit.called
        # The refresh would update the result object

    async def test_metric_status_evaluation_on_target(self, sample_metric):
        """Test metric status is on_target when value meets target."""
        sample_metric.target_value = 90.0
        sample_metric.comparison_operator = ">="

        status = sample_metric.evaluate_status(92.0)
        assert status == "on_target"

    async def test_metric_status_evaluation_warning(self, sample_metric):
        """Test metric status is warning when value is below target but above warning threshold."""
        sample_metric.target_value = 90.0
        sample_metric.warning_threshold = 85.0
        sample_metric.critical_threshold = 80.0
        sample_metric.comparison_operator = ">="

        status = sample_metric.evaluate_status(87.0)
        assert status == "warning"

    async def test_metric_status_evaluation_critical(self, sample_metric):
        """Test metric status is critical when value is below critical threshold."""
        sample_metric.target_value = 90.0
        sample_metric.warning_threshold = 85.0
        sample_metric.critical_threshold = 80.0
        sample_metric.comparison_operator = ">="

        status = sample_metric.evaluate_status(78.0)
        assert status == "critical"

    async def test_metric_format_value_percentage(self, sample_metric):
        """Test metric value formatting for percentage type."""
        sample_metric.metric_type = "percentage"
        sample_metric.decimal_places = 2
        sample_metric.unit = "%"

        formatted = sample_metric.format_value(92.567)
        assert formatted == "92.57%"

    async def test_metric_format_value_with_unit(self, sample_metric):
        """Test metric value formatting with custom unit."""
        sample_metric.metric_type = "time"
        sample_metric.decimal_places = 1
        sample_metric.unit = "ms"

        formatted = sample_metric.format_value(125.789)
        assert formatted == "125.8ms"

    async def test_template_nlp_precision(self):
        """Test NLP precision template creation."""
        template = QualityMetricTemplate.nlp_precision()

        assert template["name"] == "NLP Precision"
        assert template["category"] == "nlp_accuracy"
        assert template["target_value"] == 95.0
        assert template["warning_threshold"] == 90.0
        assert template["critical_threshold"] == 85.0

    async def test_template_nlp_recall(self):
        """Test NLP recall template creation."""
        template = QualityMetricTemplate.nlp_recall()

        assert template["name"] == "NLP Recall"
        assert template["category"] == "nlp_accuracy"
        assert template["target_value"] == 90.0

    async def test_template_document_completeness(self):
        """Test document completeness template creation."""
        template = QualityMetricTemplate.document_completeness()

        assert template["name"] == "Document Completeness"
        assert template["category"] == "data_quality"

    async def test_get_all_templates(self):
        """Test getting all metric templates."""
        templates = QualityMetricTemplate.get_all_templates()

        assert len(templates) == 4
        template_names = [t["name"] for t in templates]
        assert "NLP Precision" in template_names
        assert "NLP Recall" in template_names
        assert "Document Completeness" in template_names
        assert "Average Processing Time" in template_names


class TestQualityMetricModel:
    """Test suite for QualityMetric model."""

    @pytest.fixture
    def metric(self):
        """Create test metric."""
        return QualityMetric(
            id=uuid4(),
            name="Test Metric",
            category="nlp_accuracy",
            metric_type="percentage",
            calculation_method="automated",
            comparison_operator=">=",
            target_value=90.0,
            warning_threshold=85.0,
            critical_threshold=80.0,
            is_active=True,
            is_public=True,
            created_at=datetime.utcnow(),
        )

    def test_evaluate_status_greater_than_equal(self, metric):
        """Test status evaluation with >= operator."""
        metric.comparison_operator = ">="

        assert metric.evaluate_status(95.0) == "on_target"
        assert metric.evaluate_status(90.0) == "on_target"
        assert metric.evaluate_status(87.0) == "warning"
        assert metric.evaluate_status(82.0) == "warning"
        assert metric.evaluate_status(78.0) == "critical"

    def test_evaluate_status_less_than_equal(self, metric):
        """Test status evaluation with <= operator (lower is better)."""
        metric.comparison_operator = "<="
        metric.target_value = 100.0
        metric.warning_threshold = 150.0
        metric.critical_threshold = 200.0

        # For <= operator: lower values are better
        assert metric.evaluate_status(80.0) == "on_target"
        assert metric.evaluate_status(100.0) == "on_target"
        assert metric.evaluate_status(120.0) == "warning"
        assert metric.evaluate_status(180.0) == "warning"
        assert metric.evaluate_status(250.0) == "critical"

    def test_evaluate_status_without_thresholds(self, metric):
        """Test status evaluation without warning/critical thresholds."""
        metric.warning_threshold = None
        metric.critical_threshold = None

        assert metric.evaluate_status(95.0) == "on_target"
        assert metric.evaluate_status(85.0) == "warning"

    def test_evaluate_status_without_target(self, metric):
        """Test status evaluation without target value."""
        metric.target_value = None

        assert metric.evaluate_status(95.0) == "unknown"

    def test_factory_nlp_accuracy(self):
        """Test factory method for NLP accuracy metric."""
        metric = QualityMetric.create_nlp_accuracy_metric(
            name="Entity Extraction F1",
            target_value=92.0,
        )

        assert metric.name == "Entity Extraction F1"
        assert metric.category == "nlp_accuracy"
        assert metric.target_value == 92.0
        assert metric.comparison_operator == ">="

    def test_factory_data_quality(self):
        """Test factory method for data quality metric."""
        metric = QualityMetric.create_data_quality_metric(
            name="Data Completeness",
            target_value=98.0,
        )

        assert metric.name == "Data Completeness"
        assert metric.category == "data_quality"
        assert metric.metric_type == "percentage"


class TestQualityScoreModel:
    """Test suite for QualityScore model."""

    @pytest.fixture
    def score(self):
        """Create test score."""
        return QualityScore(
            id=uuid4(),
            metric_id=uuid4(),
            value=92.5,
            status="on_target",
            calculated_at=datetime.utcnow(),
        )

    def test_calculate_change_from_previous(self, score):
        """Test change calculation from previous value."""
        score.previous_value = 90.0
        expected_change = ((92.5 - 90.0) / 90.0) * 100

        score.calculate_change()

        assert score.change_percentage is not None
        assert abs(score.change_percentage - expected_change) < 0.01

    def test_calculate_change_no_previous(self, score):
        """Test change calculation without previous value."""
        score.previous_value = None

        score.calculate_change()

        assert score.change_percentage is None
