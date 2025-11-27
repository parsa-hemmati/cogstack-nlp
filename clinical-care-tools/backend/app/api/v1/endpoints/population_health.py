"""Population Health API endpoints for Sprint 8 - Population Health Dashboards.

Provides REST API for cohort management, metrics, dashboards, and reports.
"""
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.population_health.cohort_service import CohortService
from app.services.population_health.metrics_service import MetricsService
from app.services.population_health.dashboard_service import DashboardService
from app.services.population_health.report_service import ReportService

router = APIRouter(prefix="/population-health", tags=["Population Health"])


def get_cohort_service(db: Session = Depends(get_db)) -> CohortService:
    return CohortService(db)


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    return MetricsService(db)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


# ==================== Cohorts ====================

@router.post("/cohorts", status_code=status.HTTP_201_CREATED)
async def create_cohort(
    name: str,
    query_definition: dict,
    description: Optional[str] = None,
    inclusion_criteria: Optional[dict] = None,
    exclusion_criteria: Optional[dict] = None,
    is_dynamic: bool = True,
    is_public: bool = False,
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new patient cohort."""
    cohort = service.create_cohort(
        name=name,
        query_definition=query_definition,
        created_by=current_user.id,
        description=description,
        inclusion_criteria=inclusion_criteria,
        exclusion_criteria=exclusion_criteria,
        is_dynamic=is_dynamic,
        is_public=is_public
    )
    return cohort.to_dict()


@router.get("/cohorts")
async def list_cohorts(
    include_public: bool = True,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """List available cohorts."""
    cohorts = service.list_cohorts(
        user_id=current_user.id,
        include_public=include_public,
        limit=limit,
        offset=offset
    )
    return [c.to_dict() for c in cohorts]


@router.get("/cohorts/{cohort_id}")
async def get_cohort(
    cohort_id: UUID,
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific cohort."""
    cohort = service.get_cohort(cohort_id)
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return cohort.to_dict()


@router.put("/cohorts/{cohort_id}")
async def update_cohort(
    cohort_id: UUID,
    updates: dict,
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Update a cohort definition."""
    cohort = service.update_cohort(cohort_id, **updates)
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return cohort.to_dict()


@router.delete("/cohorts/{cohort_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cohort(
    cohort_id: UUID,
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Delete a cohort."""
    if not service.delete_cohort(cohort_id):
        raise HTTPException(status_code=404, detail="Cohort not found")


@router.post("/cohorts/{cohort_id}/refresh")
async def refresh_cohort(
    cohort_id: UUID,
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Refresh cohort membership."""
    count = service.refresh_cohort(cohort_id)
    return {"patient_count": count}


@router.get("/cohorts/{cohort_id}/patients")
async def get_cohort_patients(
    cohort_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Get patients in a cohort."""
    memberships = service.get_cohort_patients(cohort_id, limit, offset)
    return [m.to_dict() for m in memberships]


@router.post("/cohorts/{cohort_id}/patients/{patient_id}")
async def add_patient_to_cohort(
    cohort_id: UUID,
    patient_id: UUID,
    metadata: Optional[dict] = None,
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Manually add a patient to a cohort."""
    membership = service.add_patient_to_cohort(
        cohort_id, patient_id, current_user.id, metadata
    )
    if not membership:
        raise HTTPException(status_code=400, detail="Failed to add patient")
    return membership.to_dict()


@router.delete("/cohorts/{cohort_id}/patients/{patient_id}")
async def remove_patient_from_cohort(
    cohort_id: UUID,
    patient_id: UUID,
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Remove a patient from a cohort."""
    if not service.remove_patient_from_cohort(cohort_id, patient_id):
        raise HTTPException(status_code=404, detail="Membership not found")
    return {"status": "removed"}


@router.get("/cohorts/compare")
async def compare_cohorts(
    cohort_a: UUID = Query(...),
    cohort_b: UUID = Query(...),
    service: CohortService = Depends(get_cohort_service),
    current_user: User = Depends(get_current_user)
):
    """Compare two cohorts."""
    return service.compare_cohorts(cohort_a, cohort_b)


# ==================== Metrics ====================

@router.post("/cohorts/{cohort_id}/metrics/calculate")
async def calculate_cohort_metrics(
    cohort_id: UUID,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """Calculate metrics for a cohort."""
    metrics = service.calculate_cohort_metrics(cohort_id)
    return [m.to_dict() for m in metrics]


@router.get("/cohorts/{cohort_id}/summary")
async def get_cohort_summary(
    cohort_id: UUID,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics for a cohort."""
    return service.get_cohort_summary(cohort_id)


@router.get("/metrics/trend")
async def get_metric_trend(
    metric_name: str,
    cohort_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """Get historical trend for a metric."""
    return service.get_metric_trend(metric_name, cohort_id, start_date, end_date)


@router.get("/metrics/comparison")
async def compare_cohort_metrics(
    cohort_ids: List[UUID] = Query(...),
    metric_names: List[str] = Query(...),
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """Compare metrics across cohorts."""
    return service.get_comparison_metrics(cohort_ids, metric_names)


# ==================== Dashboards ====================

@router.post("/dashboards", status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    name: str,
    layout: Optional[dict] = None,
    widgets: Optional[List[dict]] = None,
    description: Optional[str] = None,
    filters: Optional[dict] = None,
    refresh_interval_seconds: Optional[int] = None,
    is_public: bool = False,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new dashboard."""
    dashboard = service.create_dashboard(
        name=name,
        created_by=current_user.id,
        layout=layout,
        widgets=widgets,
        description=description,
        filters=filters,
        refresh_interval_seconds=refresh_interval_seconds,
        is_public=is_public
    )
    return dashboard.to_dict()


@router.get("/dashboards")
async def list_dashboards(
    include_public: bool = True,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """List available dashboards."""
    dashboards = service.list_dashboards(
        user_id=current_user.id,
        include_public=include_public,
        limit=limit,
        offset=offset
    )
    return [d.to_dict() for d in dashboards]


@router.get("/dashboards/default")
async def get_default_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Get the user's default dashboard."""
    dashboard = service.get_default_dashboard(current_user.id)
    if not dashboard:
        from app.models.population_health.dashboard import DashboardConfiguration
        return {
            "layout": DashboardConfiguration.create_default_layout(),
            "widgets": DashboardConfiguration.create_default_widgets()
        }
    return dashboard.to_dict()


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific dashboard."""
    dashboard = service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard.to_dict()


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: UUID,
    updates: dict,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Update a dashboard configuration."""
    dashboard = service.update_dashboard(dashboard_id, **updates)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard.to_dict()


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Delete a dashboard."""
    if not service.delete_dashboard(dashboard_id):
        raise HTTPException(status_code=404, detail="Dashboard not found")


@router.post("/dashboards/{dashboard_id}/set-default")
async def set_default_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Set a dashboard as the default."""
    if not service.set_default_dashboard(dashboard_id, current_user.id):
        raise HTTPException(status_code=400, detail="Failed to set default")
    return {"status": "set"}


@router.post("/dashboards/{dashboard_id}/duplicate")
async def duplicate_dashboard(
    dashboard_id: UUID,
    new_name: str,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Duplicate a dashboard."""
    dashboard = service.duplicate_dashboard(dashboard_id, new_name, current_user.id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard.to_dict()


@router.post("/dashboards/widget-data")
async def get_widget_data(
    widget_config: dict,
    cohort_id: Optional[UUID] = None,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """Get data for a specific widget."""
    return service.get_widget_data(widget_config, cohort_id)


# ==================== Reports ====================

@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_report(
    name: str,
    report_type: str,
    file_format: str,
    cohort_id: Optional[UUID] = None,
    parameters: Optional[dict] = None,
    background_tasks: BackgroundTasks = None,
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user)
):
    """Create and generate a report."""
    report = service.create_report(
        name=name,
        report_type=report_type,
        file_format=file_format,
        generated_by=current_user.id,
        cohort_id=cohort_id,
        parameters=parameters
    )

    if background_tasks:
        background_tasks.add_task(service.generate_report, report.id)

    return report.to_dict()


@router.get("/reports")
async def list_reports(
    cohort_id: Optional[UUID] = None,
    report_status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user)
):
    """List generated reports."""
    reports = service.list_reports(
        user_id=current_user.id,
        cohort_id=cohort_id,
        status=report_status,
        limit=limit,
        offset=offset
    )
    return [r.to_dict() for r in reports]


@router.get("/reports/{report_id}")
async def get_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report."""
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report.to_dict()


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user)
):
    """Get download URL for a report."""
    url = service.get_download_url(report_id)
    if not url:
        raise HTTPException(status_code=404, detail="Report not available")
    return {"download_url": url}


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user)
):
    """Delete a report."""
    if not service.delete_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found")
