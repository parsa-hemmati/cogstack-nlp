"""Advanced Analytics API (Sprint 9).

This module provides comprehensive analytics endpoints for:
- ML Model registry and lifecycle management
- Predictions with risk scoring
- Quality metrics and scores
- Analytics dashboards with widgets
- Report generation and scheduling
"""

from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
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
from app.services.analytics.model_service import ModelService
from app.services.analytics.prediction_service import PredictionService
from app.services.analytics.quality_service import QualityService
from app.services.analytics.analytics_dashboard_service import AnalyticsDashboardService
from app.services.analytics.analytics_report_service import AnalyticsReportService

router = APIRouter(prefix="/analytics", tags=["Advanced Analytics"])


# =============================================================================
# ML Model Endpoints
# =============================================================================

@router.post("/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Create a new ML model in the registry."""
    service = ModelService(db)
    model = await service.create_model(model_data, current_user.id)
    return model


@router.get("/models", response_model=List[ModelResponse])
async def list_models(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[ModelResponse]:
    """List ML models with optional filtering."""
    service = ModelService(db)
    models = await service.list_models(
        model_type=model_type,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return models


@router.get("/models/statistics", response_model=ModelStatisticsResponse)
async def get_model_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelStatisticsResponse:
    """Get statistics about ML models in the registry."""
    service = ModelService(db)
    stats = await service.get_statistics()
    return stats


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Get a specific ML model by ID."""
    service = ModelService(db)
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.patch("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: UUID,
    model_data: ModelUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Update an ML model."""
    service = ModelService(db)
    model = await service.update_model(model_id, model_data)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete an ML model."""
    service = ModelService(db)
    deleted = await service.delete_model(model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")


@router.post("/models/{model_id}/train", response_model=ModelResponse)
async def start_model_training(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Start training an ML model."""
    service = ModelService(db)
    model = await service.start_training(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/{model_id}/training-complete", response_model=ModelResponse)
async def complete_model_training(
    model_id: UUID,
    training_data: ModelTrainingComplete,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Mark model training as complete with metrics."""
    service = ModelService(db)
    model = await service.complete_training(model_id, training_data)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/{model_id}/activate", response_model=ModelResponse)
async def activate_model(
    model_id: UUID,
    activation_data: Optional[ModelActivate] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelResponse:
    """Activate a trained model for predictions."""
    service = ModelService(db)
    model = await service.activate_model(
        model_id,
        endpoint_url=activation_data.endpoint_url if activation_data else None,
    )
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/{model_id}/deprecate", response_model=ModelResponse)
async def deprecate_model(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Deprecate an active model."""
    service = ModelService(db)
    model = await service.deprecate_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/{model_id}/archive", response_model=ModelResponse)
async def archive_model(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelResponse:
    """Archive a deprecated model."""
    service = ModelService(db)
    model = await service.archive_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/models/{model_id}/versions", response_model=List[ModelResponse])
async def get_model_versions(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[ModelResponse]:
    """Get all versions of a model by name."""
    service = ModelService(db)
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    versions = await service.get_model_versions(model.name)
    return versions


@router.post("/models/compare", response_model=ModelComparisonResponse)
async def compare_models(
    model_ids: List[UUID],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelComparisonResponse:
    """Compare multiple models."""
    if len(model_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 models required for comparison")
    service = ModelService(db)
    comparison = await service.compare_models(model_ids)
    return comparison


# =============================================================================
# Prediction Endpoints
# =============================================================================

@router.post("/predictions", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    prediction_data: PredictionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PredictionResponse:
    """Create a new prediction record."""
    service = PredictionService(db)
    prediction = await service.create_prediction(prediction_data)
    return prediction


@router.post("/models/{model_id}/predict", response_model=PredictionResponse)
async def execute_prediction(
    model_id: UUID,
    prediction_input: PredictionExecute,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PredictionResponse:
    """Execute a prediction using a model."""
    service = PredictionService(db)
    prediction = await service.execute_prediction(model_id, prediction_input)
    if not prediction:
        raise HTTPException(status_code=404, detail="Model not found or not active")
    return prediction


@router.get("/predictions", response_model=List[PredictionResponse])
async def list_predictions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    risk_level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[PredictionResponse]:
    """List predictions with optional filtering."""
    service = PredictionService(db)
    predictions = await service.list_predictions(
        model_id=model_id,
        patient_id=patient_id,
        risk_level=risk_level,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return predictions


@router.get("/predictions/statistics", response_model=PredictionStatisticsResponse)
async def get_prediction_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_id: Optional[UUID] = None,
    days: int = Query(30, ge=1, le=365),
) -> PredictionStatisticsResponse:
    """Get prediction statistics."""
    service = PredictionService(db)
    stats = await service.get_statistics(model_id=model_id, days=days)
    return stats


@router.get("/predictions/high-risk", response_model=List[PredictionResponse])
async def get_high_risk_predictions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_id: Optional[UUID] = None,
    limit: int = Query(20, ge=1, le=100),
) -> List[PredictionResponse]:
    """Get recent high-risk predictions."""
    service = PredictionService(db)
    predictions = await service.get_high_risk_predictions(model_id=model_id, limit=limit)
    return predictions


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PredictionResponse:
    """Get a specific prediction by ID."""
    service = PredictionService(db)
    prediction = await service.get_prediction(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@router.post("/predictions/{prediction_id}/feedback", response_model=PredictionResponse)
async def add_prediction_feedback(
    prediction_id: UUID,
    feedback: PredictionFeedback,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PredictionResponse:
    """Add feedback to a prediction."""
    service = PredictionService(db)
    prediction = await service.add_feedback(prediction_id, feedback)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@router.get("/patients/{patient_id}/risk-summary", response_model=PatientRiskSummary)
async def get_patient_risk_summary(
    patient_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PatientRiskSummary:
    """Get risk summary for a patient."""
    service = PredictionService(db)
    summary = await service.get_patient_risk_summary(patient_id)
    return summary


@router.get("/models/{model_id}/accuracy", response_model=ModelAccuracyResponse)
async def get_model_accuracy(
    model_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ModelAccuracyResponse:
    """Get model accuracy based on feedback."""
    service = PredictionService(db)
    accuracy = await service.get_model_accuracy(model_id)
    return accuracy


# =============================================================================
# Quality Metric Endpoints
# =============================================================================

@router.post("/quality/metrics", response_model=QualityMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_quality_metric(
    metric_data: QualityMetricCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QualityMetricResponse:
    """Create a new quality metric."""
    service = QualityService(db)
    metric = await service.create_metric(metric_data)
    return metric


@router.get("/quality/metrics", response_model=List[QualityMetricResponse])
async def list_quality_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[QualityMetricResponse]:
    """List quality metrics with optional filtering."""
    service = QualityService(db)
    metrics = await service.list_metrics(
        category=category,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return metrics


@router.get("/quality/metrics/with-scores", response_model=List[MetricWithLatestScore])
async def list_metrics_with_scores(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    category: Optional[str] = None,
) -> List[MetricWithLatestScore]:
    """List quality metrics with their latest scores."""
    service = QualityService(db)
    metrics = await service.list_metrics_with_latest_scores(category=category)
    return metrics


@router.get("/quality/summary", response_model=QualitySummaryResponse)
async def get_quality_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cohort_id: Optional[UUID] = None,
) -> QualitySummaryResponse:
    """Get overall quality summary."""
    service = QualityService(db)
    summary = await service.get_quality_summary(cohort_id=cohort_id)
    return summary


@router.get("/quality/metrics/{metric_id}", response_model=QualityMetricResponse)
async def get_quality_metric(
    metric_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QualityMetricResponse:
    """Get a specific quality metric by ID."""
    service = QualityService(db)
    metric = await service.get_metric(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Quality metric not found")
    return metric


@router.patch("/quality/metrics/{metric_id}", response_model=QualityMetricResponse)
async def update_quality_metric(
    metric_id: UUID,
    metric_data: QualityMetricUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QualityMetricResponse:
    """Update a quality metric."""
    service = QualityService(db)
    metric = await service.update_metric(metric_id, metric_data)
    if not metric:
        raise HTTPException(status_code=404, detail="Quality metric not found")
    return metric


@router.delete("/quality/metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quality_metric(
    metric_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a quality metric."""
    service = QualityService(db)
    deleted = await service.delete_metric(metric_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quality metric not found")


@router.post("/quality/metrics/{metric_id}/calculate", response_model=QualityScoreResponse)
async def calculate_quality_metric(
    metric_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    cohort_id: Optional[UUID] = None,
) -> QualityScoreResponse:
    """Calculate and record a quality score."""
    service = QualityService(db)
    score = await service.calculate_metric(metric_id, cohort_id=cohort_id)
    if not score:
        raise HTTPException(status_code=404, detail="Quality metric not found")
    return score


@router.post("/quality/scores", response_model=QualityScoreResponse, status_code=status.HTTP_201_CREATED)
async def record_quality_score(
    score_data: QualityScoreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QualityScoreResponse:
    """Manually record a quality score."""
    service = QualityService(db)
    score = await service.record_score(score_data)
    return score


@router.get("/quality/metrics/{metric_id}/scores", response_model=List[QualityScoreResponse])
async def get_metric_scores(
    metric_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
) -> List[QualityScoreResponse]:
    """Get historical scores for a metric."""
    service = QualityService(db)
    scores = await service.get_metric_scores(
        metric_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return scores


@router.get("/quality/metrics/{metric_id}/trend", response_model=QualityTrendResponse)
async def get_metric_trend(
    metric_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=7, le=365),
) -> QualityTrendResponse:
    """Get trend data for a metric."""
    service = QualityService(db)
    trend = await service.get_metric_trend(metric_id, days=days)
    if not trend:
        raise HTTPException(status_code=404, detail="Quality metric not found")
    return trend


@router.post("/quality/initialize-templates", response_model=List[QualityMetricResponse])
async def initialize_quality_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[QualityMetricResponse]:
    """Initialize default quality metric templates."""
    service = QualityService(db)
    metrics = await service.initialize_templates()
    return metrics


# =============================================================================
# Analytics Dashboard Endpoints
# =============================================================================

@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Create a new analytics dashboard."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.create_dashboard(dashboard_data, current_user.id)
    return dashboard


@router.get("/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[DashboardResponse]:
    """List analytics dashboards with optional filtering."""
    service = AnalyticsDashboardService(db)
    dashboards = await service.list_dashboards(
        user_id=current_user.id,
        dashboard_type=dashboard_type,
        is_public=is_public,
        skip=skip,
        limit=limit,
    )
    return dashboards


@router.get("/dashboards/statistics", response_model=DashboardStatisticsResponse)
async def get_dashboard_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardStatisticsResponse:
    """Get dashboard statistics."""
    service = AnalyticsDashboardService(db)
    stats = await service.get_statistics(current_user.id)
    return stats


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Get a specific dashboard by ID."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.get_dashboard(dashboard_id, current_user.id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.patch("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    dashboard_data: DashboardUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Update a dashboard."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.update_dashboard(dashboard_id, dashboard_data, current_user.id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a dashboard."""
    service = AnalyticsDashboardService(db)
    deleted = await service.delete_dashboard(dashboard_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dashboard not found")


@router.post("/dashboards/{dashboard_id}/duplicate", response_model=DashboardResponse)
async def duplicate_dashboard(
    dashboard_id: UUID,
    duplicate_data: DuplicateDashboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Duplicate a dashboard."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.duplicate_dashboard(
        dashboard_id,
        duplicate_data.new_name,
        current_user.id,
    )
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("/dashboards/{dashboard_id}/set-default", response_model=DashboardResponse)
async def set_default_dashboard(
    dashboard_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Set a dashboard as default for its type."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.set_default(dashboard_id, current_user.id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("/dashboards/{dashboard_id}/widgets", response_model=DashboardResponse)
async def add_widget_to_dashboard(
    dashboard_id: UUID,
    widget_data: AddWidgetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Add a widget to a dashboard."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.add_widget(
        dashboard_id,
        widget_data.widget_config,
        current_user.id,
    )
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.patch("/dashboards/{dashboard_id}/widgets/{widget_id}", response_model=DashboardResponse)
async def update_dashboard_widget(
    dashboard_id: UUID,
    widget_id: str,
    widget_data: UpdateWidgetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Update a widget in a dashboard."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.update_widget(
        dashboard_id,
        widget_id,
        widget_data.widget_config,
        current_user.id,
    )
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard or widget not found")
    return dashboard


@router.delete("/dashboards/{dashboard_id}/widgets/{widget_id}", response_model=DashboardResponse)
async def remove_widget_from_dashboard(
    dashboard_id: UUID,
    widget_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Remove a widget from a dashboard."""
    service = AnalyticsDashboardService(db)
    dashboard = await service.remove_widget(dashboard_id, widget_id, current_user.id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard or widget not found")
    return dashboard


@router.post("/dashboards/{dashboard_id}/widgets/{widget_id}/data", response_model=WidgetDataResponse)
async def get_widget_data(
    dashboard_id: UUID,
    widget_id: str,
    request_data: WidgetDataRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WidgetDataResponse:
    """Get data for a specific widget."""
    service = AnalyticsDashboardService(db)
    data = await service.get_widget_data(
        dashboard_id,
        widget_id,
        request_data,
        current_user.id,
    )
    if not data:
        raise HTTPException(status_code=404, detail="Dashboard or widget not found")
    return data


# =============================================================================
# Analytics Report Endpoints
# =============================================================================

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportResponse:
    """Create a new analytics report."""
    service = AnalyticsReportService(db)
    report = await service.create_report(report_data, current_user.id)
    return report


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    report_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[ReportResponse]:
    """List analytics reports with optional filtering."""
    service = AnalyticsReportService(db)
    reports = await service.list_reports(
        user_id=current_user.id,
        report_type=report_type,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return reports


@router.get("/reports/statistics", response_model=ReportStatisticsResponse)
async def get_report_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=365),
) -> ReportStatisticsResponse:
    """Get report statistics."""
    service = AnalyticsReportService(db)
    stats = await service.get_statistics(current_user.id, days=days)
    return stats


@router.get("/reports/scheduled", response_model=List[ReportResponse])
async def list_scheduled_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[ReportResponse]:
    """List scheduled reports."""
    service = AnalyticsReportService(db)
    reports = await service.list_scheduled_reports(current_user.id)
    return reports


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportResponse:
    """Get a specific report by ID."""
    service = AnalyticsReportService(db)
    report = await service.get_report(report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID,
    report_data: ReportUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportResponse:
    """Update a report."""
    service = AnalyticsReportService(db)
    report = await service.update_report(report_id, report_data, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a report."""
    service = AnalyticsReportService(db)
    deleted = await service.delete_report(report_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")


@router.post("/reports/{report_id}/generate", response_model=ReportResponse)
async def generate_report(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportResponse:
    """Generate a report."""
    service = AnalyticsReportService(db)
    report = await service.generate_report(report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/reports/{report_id}/download", response_model=ReportDownloadResponse)
async def download_report(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportDownloadResponse:
    """Get download URL for a generated report."""
    service = AnalyticsReportService(db)
    download_info = await service.get_download_url(report_id, current_user.id)
    if not download_info:
        raise HTTPException(status_code=404, detail="Report not found or not generated")
    return download_info


@router.post("/reports/{report_id}/cancel", response_model=ReportResponse)
async def cancel_report_generation(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportResponse:
    """Cancel a report generation."""
    service = AnalyticsReportService(db)
    report = await service.cancel_generation(report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
