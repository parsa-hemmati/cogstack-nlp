"""Analytics schemas for Sprint 9 - Advanced Analytics."""

from app.schemas.analytics.ml_model import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelTrainingComplete,
    ModelActivate,
    ModelComparisonResponse,
    ModelStatisticsResponse,
)
from app.schemas.analytics.prediction import (
    PredictionCreate,
    PredictionExecute,
    PredictionResponse,
    PredictionFeedback,
    PredictionStatisticsResponse,
    PatientRiskSummary,
    ModelAccuracyResponse,
)
from app.schemas.analytics.quality import (
    QualityMetricCreate,
    QualityMetricUpdate,
    QualityMetricResponse,
    QualityScoreCreate,
    QualityScoreResponse,
    QualitySummaryResponse,
    QualityTrendResponse,
    MetricWithLatestScore,
)
from app.schemas.analytics.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    WidgetConfig,
    WidgetDataRequest,
    WidgetDataResponse,
    DashboardStatisticsResponse,
    AddWidgetRequest,
    UpdateWidgetRequest,
    DuplicateDashboardRequest,
)
from app.schemas.analytics.report import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportStatisticsResponse,
    ReportDownloadResponse,
)

__all__ = [
    # ML Models
    "ModelCreate",
    "ModelUpdate",
    "ModelResponse",
    "ModelTrainingComplete",
    "ModelActivate",
    "ModelComparisonResponse",
    "ModelStatisticsResponse",
    # Predictions
    "PredictionCreate",
    "PredictionExecute",
    "PredictionResponse",
    "PredictionFeedback",
    "PredictionStatisticsResponse",
    "PatientRiskSummary",
    "ModelAccuracyResponse",
    # Quality Metrics
    "QualityMetricCreate",
    "QualityMetricUpdate",
    "QualityMetricResponse",
    "QualityScoreCreate",
    "QualityScoreResponse",
    "QualitySummaryResponse",
    "QualityTrendResponse",
    "MetricWithLatestScore",
    # Dashboards
    "DashboardCreate",
    "DashboardUpdate",
    "DashboardResponse",
    "WidgetConfig",
    "WidgetDataRequest",
    "WidgetDataResponse",
    "DashboardStatisticsResponse",
    "AddWidgetRequest",
    "UpdateWidgetRequest",
    "DuplicateDashboardRequest",
    # Reports
    "ReportCreate",
    "ReportUpdate",
    "ReportResponse",
    "ReportStatisticsResponse",
    "ReportDownloadResponse",
]
