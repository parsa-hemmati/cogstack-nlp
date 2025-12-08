"""AnalyticsDashboardService for managing analytics dashboards."""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_, func, case, desc, select

from app.models.analytics.dashboard import AnalyticsDashboard
from app.models.patient import Patient
from app.models.document import Document, ProcessingStatus

logger = logging.getLogger(__name__)


class AnalyticsDashboardService:
    """Service for managing analytics dashboard configurations.

    Handles dashboard CRUD, widget management, and data aggregation.
    """

    def __init__(self, db: Session):
        """Initialize dashboard service.

        Args:
            db: Database session
        """
        self.db = db

    def create_dashboard(
        self,
        name: str,
        dashboard_type: str,
        created_by: UUID,
        description: Optional[str] = None,
        layout: Optional[Dict[str, Any]] = None,
        widgets: Optional[List[Dict[str, Any]]] = None,
        theme: str = "default",
        default_filters: Optional[Dict[str, Any]] = None,
        default_date_range: Optional[str] = None,
        default_cohort_id: Optional[UUID] = None,
        auto_refresh: bool = False,
        refresh_interval_seconds: Optional[int] = None,
        is_public: bool = False,
        allowed_roles: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalyticsDashboard:
        """Create a new analytics dashboard."""
        # Use default layouts/widgets based on type if not provided
        if layout is None:
            layout = AnalyticsDashboard.create_default_quality_layout()

        if widgets is None:
            if dashboard_type == AnalyticsDashboard.TYPE_QUALITY:
                widgets = AnalyticsDashboard.create_default_quality_widgets()
            elif dashboard_type == AnalyticsDashboard.TYPE_PREDICTIVE:
                widgets = AnalyticsDashboard.create_default_predictive_widgets()
            else:
                widgets = []

        dashboard = AnalyticsDashboard(
            name=name,
            description=description,
            dashboard_type=dashboard_type,
            layout=layout,
            widgets=widgets,
            theme=theme,
            default_filters=default_filters,
            default_date_range=default_date_range,
            default_cohort_id=default_cohort_id,
            auto_refresh=auto_refresh,
            refresh_interval_seconds=refresh_interval_seconds,
            is_public=is_public,
            allowed_roles=allowed_roles,
            created_by=created_by,
            tags=tags,
            metadata=metadata
        )

        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)

        logger.info(f"Created analytics dashboard: {name} (id={dashboard.id})")
        return dashboard

    def get_dashboard(self, dashboard_id: UUID) -> Optional[AnalyticsDashboard]:
        """Get a dashboard by ID."""
        return self.db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.id == dashboard_id
        ).first()

    def list_dashboards(
        self,
        user_id: Optional[UUID] = None,
        dashboard_type: Optional[str] = None,
        include_public: bool = True,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalyticsDashboard]:
        """List dashboards with optional filtering."""
        query = self.db.query(AnalyticsDashboard)

        if user_id:
            if include_public:
                query = query.filter(or_(
                    AnalyticsDashboard.created_by == user_id,
                    AnalyticsDashboard.is_public == True
                ))
            else:
                query = query.filter(AnalyticsDashboard.created_by == user_id)

        if dashboard_type:
            query = query.filter(AnalyticsDashboard.dashboard_type == dashboard_type)

        if tags:
            query = query.filter(AnalyticsDashboard.tags.overlap(tags))

        return query.order_by(
            AnalyticsDashboard.created_at.desc()
        ).offset(offset).limit(limit).all()

    def update_dashboard(
        self,
        dashboard_id: UUID,
        updated_by: UUID,
        **updates
    ) -> Optional[AnalyticsDashboard]:
        """Update a dashboard."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        allowed_fields = [
            "name", "description", "layout", "widgets", "theme",
            "default_filters", "default_date_range", "default_cohort_id",
            "auto_refresh", "refresh_interval_seconds", "is_public",
            "allowed_roles", "tags", "metadata"
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(dashboard, field, value)

        dashboard.updated_by = updated_by
        self.db.commit()
        self.db.refresh(dashboard)

        return dashboard

    def delete_dashboard(self, dashboard_id: UUID) -> bool:
        """Delete a dashboard."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        self.db.delete(dashboard)
        self.db.commit()

        logger.info(f"Deleted analytics dashboard: {dashboard.name}")
        return True

    def duplicate_dashboard(
        self,
        dashboard_id: UUID,
        new_name: str,
        created_by: UUID
    ) -> Optional[AnalyticsDashboard]:
        """Duplicate an existing dashboard."""
        source = self.get_dashboard(dashboard_id)
        if not source:
            return None

        return self.create_dashboard(
            name=new_name,
            dashboard_type=source.dashboard_type,
            created_by=created_by,
            description=source.description,
            layout=source.layout,
            widgets=source.widgets,
            theme=source.theme,
            default_filters=source.default_filters,
            default_date_range=source.default_date_range,
            auto_refresh=source.auto_refresh,
            refresh_interval_seconds=source.refresh_interval_seconds,
            is_public=False  # New copy is always private
        )

    def set_default_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID
    ) -> bool:
        """Set a dashboard as the default for a user."""
        # Clear existing default
        self.db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.created_by == user_id,
            AnalyticsDashboard.is_default == True
        ).update({"is_default": False})

        # Set new default
        dashboard = self.get_dashboard(dashboard_id)
        if dashboard and dashboard.created_by == user_id:
            dashboard.is_default = True
            self.db.commit()
            return True

        return False

    def get_default_dashboard(
        self,
        user_id: UUID
    ) -> Optional[AnalyticsDashboard]:
        """Get the default dashboard for a user."""
        return self.db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.created_by == user_id,
            AnalyticsDashboard.is_default == True
        ).first()

    def add_widget(
        self,
        dashboard_id: UUID,
        widget_config: Dict[str, Any],
        updated_by: UUID
    ) -> Optional[AnalyticsDashboard]:
        """Add a widget to a dashboard."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        widgets = list(dashboard.widgets or [])
        widgets.append(widget_config)

        return self.update_dashboard(
            dashboard_id=dashboard_id,
            updated_by=updated_by,
            widgets=widgets
        )

    def remove_widget(
        self,
        dashboard_id: UUID,
        widget_id: str,
        updated_by: UUID
    ) -> Optional[AnalyticsDashboard]:
        """Remove a widget from a dashboard."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        widgets = [w for w in (dashboard.widgets or []) if w.get("id") != widget_id]

        return self.update_dashboard(
            dashboard_id=dashboard_id,
            updated_by=updated_by,
            widgets=widgets
        )

    def update_widget(
        self,
        dashboard_id: UUID,
        widget_id: str,
        widget_config: Dict[str, Any],
        updated_by: UUID
    ) -> Optional[AnalyticsDashboard]:
        """Update a specific widget on a dashboard."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        widgets = []
        for w in (dashboard.widgets or []):
            if w.get("id") == widget_id:
                # Preserve ID and merge config
                updated = {**w, **widget_config}
                updated["id"] = widget_id
                widgets.append(updated)
            else:
                widgets.append(w)

        return self.update_dashboard(
            dashboard_id=dashboard_id,
            updated_by=updated_by,
            widgets=widgets
        )

    def update_layout(
        self,
        dashboard_id: UUID,
        layout: Dict[str, Any],
        updated_by: UUID
    ) -> Optional[AnalyticsDashboard]:
        """Update dashboard layout."""
        return self.update_dashboard(
            dashboard_id=dashboard_id,
            updated_by=updated_by,
            layout=layout
        )

    def get_widget_data(
        self,
        widget_config: Dict[str, Any],
        cohort_id: Optional[UUID] = None,
        date_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get data for a specific widget."""
        widget_type = widget_config.get("type")
        config = widget_config.get("config", {})

        # Dispatch to appropriate data fetcher
        if widget_type == "gauge":
            return self._get_gauge_data(config, cohort_id)
        elif widget_type == "metric":
            return self._get_metric_data(config, cohort_id)
        elif widget_type == "line_chart":
            return self._get_line_chart_data(config, cohort_id, date_range)
        elif widget_type == "bar_chart":
            return self._get_bar_chart_data(config, cohort_id)
        elif widget_type == "pie_chart":
            return self._get_pie_chart_data(config, cohort_id)
        elif widget_type == "table":
            return self._get_table_data(config, cohort_id)
        elif widget_type == "alert_list":
            return self._get_alert_list_data(config, cohort_id)
        else:
            return {"error": f"Unknown widget type: {widget_type}"}

    def _get_gauge_data(
        self,
        config: Dict[str, Any],
        cohort_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Get data for gauge widget."""
        metric = config.get("metric")
        
        if metric == "processing_success_rate":
            # Calculate success rate from Documents
            total = self.db.query(Document).count()
            if total == 0:
                value = 100
            else:
                success = self.db.query(Document).filter(
                    Document.processing_status == ProcessingStatus.COMPLETED
                ).count()
                value = (success / total) * 100
                
            return {
                "value": round(value, 1),
                "target": 98.0,
                "min": 0,
                "max": 100,
                "status": "on_target" if value >= 98 else "warning" if value >= 90 else "critical",
                "trend": "neutral",
                "change": 0
            }
            
        # Default/Mock fallback for other metrics (like 'nlp_f1_score' which needs quality tables)
        return {
            "value": 87.5,
            "target": 90.0,
            "min": 0,
            "max": 100,
            "status": "warning",
            "trend": "up",
            "change": 2.3
        }

    def _get_metric_data(
        self,
        config: Dict[str, Any],
        cohort_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Get data for single metric widget."""
        metric = config.get("metric")
        
        if metric == "total_patients":
            value = self.db.query(Patient).count()
            return {
                "value": value,
                "formatted": f"{value}",
                "trend": "neutral",
                "change": 0
            }
            
        if metric == "total_documents":
            value = self.db.query(Document).count()
            return {
                "value": value,
                "formatted": f"{value}",
                "trend": "up",
                "change": 0
            }

        return {
            "value": 1.8,
            "formatted": "1.8s",
            "trend": "down",
            "change": -0.2,
            "sparkline": [2.1, 2.0, 1.9, 1.8, 1.7, 1.8]
        }

    def _get_line_chart_data(
        self,
        config: Dict[str, Any],
        cohort_id: Optional[UUID],
        date_range: Optional[str]
    ) -> Dict[str, Any]:
        """Get data for line chart widget."""
        # TODO: Implement real time-series queries
        return {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "datasets": [
                {
                    "label": "Precision",
                    "data": [85, 87, 86, 88]
                },
                {
                    "label": "Recall",
                    "data": [82, 83, 85, 84]
                },
                {
                    "label": "F1 Score",
                    "data": [83, 85, 85, 86]
                }
            ]
        }

    def _get_bar_chart_data(
        self,
        config: Dict[str, Any],
        cohort_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Get data for bar chart widget."""
        group_by = config.get("groupBy")
        metric = config.get("metric")
        
        if group_by == "gender":
            # Query patient gender distribution
            results = self.db.query(
                Patient.gender, 
                func.count(Patient.id)
            ).group_by(Patient.gender).all()
            
            labels = [r[0] or "Unknown" for r in results]
            data = [r[1] for r in results]
            
            return {
                "labels": labels,
                "datasets": [{
                    "label": "Patients by Gender",
                    "data": data
                }]
            }
            
        return {
            "labels": ["NLP Accuracy", "Data Quality", "Operational", "Clinical"],
            "datasets": [
                {
                    "label": "Average Score",
                    "data": [87, 94, 98, 82]
                }
            ]
        }

    def _get_pie_chart_data(
        self,
        config: Dict[str, Any],
        cohort_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Get data for pie chart widget."""
        group_by = config.get("groupBy")
        
        if group_by == "processing_status":
             results = self.db.query(
                Document.processing_status, 
                func.count(Document.id)
            ).group_by(Document.processing_status).all()
            
             labels = [str(r[0]) for r in results]
             data = [r[1] for r in results]
             
             return {
                "labels": labels,
                "datasets": [{
                    "data": data
                }]
            }

        return {
            "labels": ["Low", "Medium", "High", "Critical"],
            "datasets": [
                {
                    "data": [450, 230, 80, 15]
                }
            ]
        }

    def _get_table_data(
        self,
        config: Dict[str, Any],
        cohort_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Get data for table widget."""
        return {
            "headers": ["Metric", "Value", "Status", "Change"],
            "rows": [
                ["NLP Precision", "88.5%", "on_target", "+1.2%"],
                ["NLP Recall", "84.2%", "warning", "-0.5%"],
                ["F1 Score", "86.3%", "on_target", "+0.3%"]
            ],
            "total": 10,
            "page": 1
        }

    def _get_alert_list_data(
        self,
        config: Dict[str, Any],
        cohort_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Get data for alert list widget."""
        return {
            "alerts": [
                {
                    "id": "1",
                    "title": "NLP Recall Below Threshold",
                    "severity": "warning",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metric": "nlp_recall",
                    "value": 84.2
                }
            ],
            "total": 3,
            "critical_count": 0,
            "warning_count": 3
        }

    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Get dashboard usage statistics."""
        total = self.db.query(AnalyticsDashboard).count()

        by_type = self.db.query(
            AnalyticsDashboard.dashboard_type,
            func.count(AnalyticsDashboard.id)
        ).group_by(AnalyticsDashboard.dashboard_type).all()

        public_count = self.db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.is_public == True
        ).count()

        return {
            "total_dashboards": total,
            "by_type": {dtype: count for dtype, count in by_type},
            "public_dashboards": public_count,
            "private_dashboards": total - public_count
        }

