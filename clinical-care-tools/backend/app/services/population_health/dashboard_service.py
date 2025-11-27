"""DashboardService for managing dashboard configurations."""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.population_health.dashboard import DashboardConfiguration

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for managing dashboard configurations.

    Handles CRUD operations for dashboard layouts and widgets.
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
        created_by: UUID,
        layout: Optional[Dict[str, Any]] = None,
        widgets: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        refresh_interval_seconds: Optional[int] = None,
        is_public: bool = False
    ) -> DashboardConfiguration:
        """Create a new dashboard configuration.

        Args:
            name: Dashboard name
            created_by: User creating the dashboard
            layout: Widget layout (or use default)
            widgets: Widget configurations (or use default)
            description: Optional description
            filters: Default filters
            refresh_interval_seconds: Auto-refresh interval
            is_public: Whether visible to all users

        Returns:
            Created DashboardConfiguration
        """
        dashboard = DashboardConfiguration(
            name=name,
            description=description,
            layout=layout or DashboardConfiguration.create_default_layout(),
            widgets=widgets or DashboardConfiguration.create_default_widgets(),
            filters=filters,
            refresh_interval_seconds=refresh_interval_seconds,
            is_public=is_public,
            created_by=created_by
        )

        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)

        logger.info(f"Created dashboard: {name} (id={dashboard.id})")
        return dashboard

    def get_dashboard(self, dashboard_id: UUID) -> Optional[DashboardConfiguration]:
        """Get a dashboard by ID.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            DashboardConfiguration or None
        """
        return self.db.query(DashboardConfiguration).filter(
            DashboardConfiguration.id == dashboard_id
        ).first()

    def list_dashboards(
        self,
        user_id: Optional[UUID] = None,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[DashboardConfiguration]:
        """List dashboard configurations.

        Args:
            user_id: Filter to dashboards created by this user
            include_public: Include public dashboards
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of DashboardConfiguration objects
        """
        query = self.db.query(DashboardConfiguration)

        if user_id:
            if include_public:
                query = query.filter(or_(
                    DashboardConfiguration.created_by == user_id,
                    DashboardConfiguration.is_public == True
                ))
            else:
                query = query.filter(DashboardConfiguration.created_by == user_id)

        return query.offset(offset).limit(limit).all()

    def update_dashboard(
        self,
        dashboard_id: UUID,
        **updates
    ) -> Optional[DashboardConfiguration]:
        """Update a dashboard configuration.

        Args:
            dashboard_id: Dashboard to update
            **updates: Fields to update

        Returns:
            Updated dashboard or None
        """
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        allowed_fields = [
            "name", "description", "layout", "widgets",
            "filters", "refresh_interval_seconds", "is_public"
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(dashboard, field, value)

        self.db.commit()
        self.db.refresh(dashboard)

        return dashboard

    def delete_dashboard(self, dashboard_id: UUID) -> bool:
        """Delete a dashboard configuration.

        Args:
            dashboard_id: Dashboard to delete

        Returns:
            True if deleted, False if not found
        """
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        self.db.delete(dashboard)
        self.db.commit()

        logger.info(f"Deleted dashboard: {dashboard.name}")
        return True

    def set_default_dashboard(self, dashboard_id: UUID, user_id: UUID) -> bool:
        """Set a dashboard as the default for a user.

        Args:
            dashboard_id: Dashboard to set as default
            user_id: User to set default for

        Returns:
            True if set successfully
        """
        # Clear existing default
        self.db.query(DashboardConfiguration).filter(
            DashboardConfiguration.created_by == user_id,
            DashboardConfiguration.is_default == True
        ).update({"is_default": False})

        # Set new default
        dashboard = self.get_dashboard(dashboard_id)
        if dashboard and dashboard.created_by == user_id:
            dashboard.is_default = True
            self.db.commit()
            return True

        return False

    def get_default_dashboard(self, user_id: UUID) -> Optional[DashboardConfiguration]:
        """Get the default dashboard for a user.

        Args:
            user_id: User ID

        Returns:
            Default DashboardConfiguration or None
        """
        return self.db.query(DashboardConfiguration).filter(
            DashboardConfiguration.created_by == user_id,
            DashboardConfiguration.is_default == True
        ).first()

    def duplicate_dashboard(
        self,
        dashboard_id: UUID,
        new_name: str,
        created_by: UUID
    ) -> Optional[DashboardConfiguration]:
        """Duplicate an existing dashboard.

        Args:
            dashboard_id: Dashboard to duplicate
            new_name: Name for the new dashboard
            created_by: User creating the duplicate

        Returns:
            New DashboardConfiguration or None
        """
        source = self.get_dashboard(dashboard_id)
        if not source:
            return None

        return self.create_dashboard(
            name=new_name,
            created_by=created_by,
            layout=source.layout,
            widgets=source.widgets,
            description=source.description,
            filters=source.filters,
            refresh_interval_seconds=source.refresh_interval_seconds,
            is_public=False
        )

    def get_widget_data(
        self,
        widget_config: Dict[str, Any],
        cohort_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get data for a specific widget.

        Args:
            widget_config: Widget configuration
            cohort_id: Optional cohort filter

        Returns:
            Widget data
        """
        widget_type = widget_config.get("type")
        config = widget_config.get("config", {})

        # Dispatch to appropriate data fetcher
        if widget_type == "cohort_summary":
            return self._get_cohort_summary_data(cohort_id)
        elif widget_type == "condition_prevalence":
            return self._get_condition_prevalence_data(cohort_id, config)
        elif widget_type == "age_distribution":
            return self._get_age_distribution_data(cohort_id)
        elif widget_type == "trend_chart":
            return self._get_trend_data(cohort_id, config)
        elif widget_type == "alert_summary":
            return self._get_alert_summary_data(cohort_id)
        else:
            return {"error": f"Unknown widget type: {widget_type}"}

    def _get_cohort_summary_data(self, cohort_id: Optional[UUID]) -> Dict[str, Any]:
        """Get cohort summary widget data."""
        # Would integrate with MetricsService
        return {
            "patient_count": 0,
            "avg_age": 0,
            "gender_split": {"male": 0, "female": 0},
            "active_alerts": 0
        }

    def _get_condition_prevalence_data(
        self,
        cohort_id: Optional[UUID],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get condition prevalence widget data."""
        limit = config.get("limit", 10)
        return {
            "conditions": [],  # Would be populated with actual data
            "total_patients": 0
        }

    def _get_age_distribution_data(self, cohort_id: Optional[UUID]) -> Dict[str, Any]:
        """Get age distribution widget data."""
        return {
            "bins": ["0-17", "18-34", "35-49", "50-64", "65-79", "80+"],
            "counts": [0, 0, 0, 0, 0, 0]
        }

    def _get_trend_data(
        self,
        cohort_id: Optional[UUID],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get trend chart widget data."""
        return {
            "labels": [],
            "values": []
        }

    def _get_alert_summary_data(self, cohort_id: Optional[UUID]) -> Dict[str, Any]:
        """Get alert summary widget data."""
        return {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total_new": 0
        }
