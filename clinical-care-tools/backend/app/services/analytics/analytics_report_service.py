"""AnalyticsReportService for generating analytics reports."""
import logging
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.analytics.dashboard import AnalyticsReport, AnalyticsDashboard

logger = logging.getLogger(__name__)


class AnalyticsReportService:
    """Service for generating and managing analytics reports.

    Handles report creation, generation, scheduling, and distribution.
    """

    REPORT_DIR = "reports/analytics"  # Would be configured from settings
    REPORT_EXPIRY_DAYS = 30

    def __init__(self, db: Session):
        """Initialize report service.

        Args:
            db: Database session
        """
        self.db = db

    def create_report(
        self,
        name: str,
        report_type: str,
        file_format: str,
        created_by: UUID,
        description: Optional[str] = None,
        dashboard_id: Optional[UUID] = None,
        metrics: Optional[List[UUID]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        date_range_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        relative_period: Optional[str] = None,
        cohort_id: Optional[UUID] = None,
        include_charts: bool = True,
        include_raw_data: bool = False,
        is_scheduled: bool = False,
        schedule_cron: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
        auto_send: bool = False,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalyticsReport:
        """Create a new analytics report.

        Args:
            name: Report name
            report_type: Type of report
            file_format: Output format
            created_by: User creating the report
            description: Report description
            dashboard_id: Source dashboard
            metrics: Selected metric IDs
            parameters: Report parameters
            date_range_type: Fixed or relative
            start_date: Start date for fixed range
            end_date: End date for fixed range
            relative_period: Period for relative range
            cohort_id: Cohort filter
            include_charts: Include visualizations
            include_raw_data: Include raw data tables
            is_scheduled: Enable scheduling
            schedule_cron: Cron expression
            email_recipients: Distribution list
            auto_send: Auto-send on generation
            tags: Organization tags
            metadata: Additional metadata

        Returns:
            Created AnalyticsReport
        """
        report = AnalyticsReport(
            name=name,
            description=description,
            report_type=report_type,
            dashboard_id=dashboard_id,
            metrics=metrics,
            parameters=parameters,
            date_range_type=date_range_type,
            start_date=start_date,
            end_date=end_date,
            relative_period=relative_period,
            cohort_id=cohort_id,
            file_format=file_format,
            include_charts=include_charts,
            include_raw_data=include_raw_data,
            is_scheduled=is_scheduled,
            schedule_cron=schedule_cron,
            email_recipients=email_recipients,
            auto_send=auto_send,
            created_by=created_by,
            tags=tags,
            metadata=metadata
        )

        # Calculate next run time for scheduled reports
        if is_scheduled and schedule_cron:
            report.next_run_at = self._calculate_next_run(schedule_cron)

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.info(f"Created analytics report: {name} (id={report.id})")
        return report

    def get_report(self, report_id: UUID) -> Optional[AnalyticsReport]:
        """Get a report by ID.

        Args:
            report_id: Report ID

        Returns:
            AnalyticsReport or None
        """
        return self.db.query(AnalyticsReport).filter(
            AnalyticsReport.id == report_id
        ).first()

    def list_reports(
        self,
        user_id: Optional[UUID] = None,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        dashboard_id: Optional[UUID] = None,
        is_scheduled: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalyticsReport]:
        """List reports with optional filtering.

        Args:
            user_id: Filter by creator
            report_type: Filter by type
            status: Filter by status
            dashboard_id: Filter by dashboard
            is_scheduled: Filter by scheduled
            tags: Filter by tags
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AnalyticsReport objects
        """
        query = self.db.query(AnalyticsReport)

        if user_id:
            query = query.filter(AnalyticsReport.created_by == user_id)
        if report_type:
            query = query.filter(AnalyticsReport.report_type == report_type)
        if status:
            query = query.filter(AnalyticsReport.status == status)
        if dashboard_id:
            query = query.filter(AnalyticsReport.dashboard_id == dashboard_id)
        if is_scheduled is not None:
            query = query.filter(AnalyticsReport.is_scheduled == is_scheduled)
        if tags:
            query = query.filter(AnalyticsReport.tags.overlap(tags))

        return query.order_by(
            AnalyticsReport.created_at.desc()
        ).offset(offset).limit(limit).all()

    def update_report(
        self,
        report_id: UUID,
        **updates
    ) -> Optional[AnalyticsReport]:
        """Update a report configuration.

        Args:
            report_id: Report to update
            **updates: Fields to update

        Returns:
            Updated report or None
        """
        report = self.get_report(report_id)
        if not report:
            return None

        allowed_fields = [
            "name", "description", "metrics", "parameters",
            "date_range_type", "start_date", "end_date", "relative_period",
            "cohort_id", "include_charts", "include_raw_data",
            "is_scheduled", "schedule_cron", "email_recipients", "auto_send",
            "tags", "metadata"
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(report, field, value)

        # Recalculate next run time if schedule changed
        if "schedule_cron" in updates and report.is_scheduled:
            report.next_run_at = self._calculate_next_run(report.schedule_cron)

        self.db.commit()
        self.db.refresh(report)

        return report

    def delete_report(self, report_id: UUID) -> bool:
        """Delete a report and its file.

        Args:
            report_id: Report to delete

        Returns:
            True if deleted
        """
        report = self.get_report(report_id)
        if not report:
            return False

        # Delete file if exists
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except OSError as e:
                logger.warning(f"Failed to delete report file: {e}")

        self.db.delete(report)
        self.db.commit()

        logger.info(f"Deleted analytics report: {report.name}")
        return True

    async def generate_report(self, report_id: UUID) -> bool:
        """Generate a report asynchronously.

        Args:
            report_id: Report to generate

        Returns:
            True if generation successful
        """
        report = self.get_report(report_id)
        if not report:
            return False

        report.mark_generating()
        self.db.commit()

        try:
            # Generate based on report type
            if report.report_type == AnalyticsReport.TYPE_QUALITY_SUMMARY:
                file_path, file_size = await self._generate_quality_summary(report)
            elif report.report_type == AnalyticsReport.TYPE_TREND_ANALYSIS:
                file_path, file_size = await self._generate_trend_analysis(report)
            elif report.report_type == AnalyticsReport.TYPE_MODEL_PERFORMANCE:
                file_path, file_size = await self._generate_model_performance(report)
            else:
                file_path, file_size = await self._generate_custom_report(report)

            report.mark_completed(file_path, file_size)

            # Update scheduling
            if report.is_scheduled:
                report.last_run_at = datetime.utcnow()
                report.next_run_at = self._calculate_next_run(report.schedule_cron)

            self.db.commit()

            # Send notifications if configured
            if report.auto_send and report.email_recipients:
                await self._send_report_email(report)

            logger.info(f"Generated analytics report: {report.name}")
            return True

        except Exception as e:
            report.mark_failed(str(e))
            self.db.commit()
            logger.error(f"Failed to generate report {report_id}: {e}")
            return False

    async def _generate_quality_summary(self, report: AnalyticsReport) -> tuple:
        """Generate a quality summary report.

        Args:
            report: Report configuration

        Returns:
            (file_path, file_size) tuple
        """
        # Placeholder - would generate actual report
        # Would use libraries like:
        # - reportlab for PDF
        # - openpyxl for Excel
        # - csv module for CSV

        os.makedirs(self.REPORT_DIR, exist_ok=True)
        file_path = f"{self.REPORT_DIR}/{report.id}.{report.file_format}"
        file_size = 0

        # In production:
        # 1. Fetch quality metrics data
        # 2. Generate charts using matplotlib/plotly
        # 3. Create formatted output
        # 4. Save to storage

        return file_path, file_size

    async def _generate_trend_analysis(self, report: AnalyticsReport) -> tuple:
        """Generate a trend analysis report."""
        os.makedirs(self.REPORT_DIR, exist_ok=True)
        file_path = f"{self.REPORT_DIR}/{report.id}.{report.file_format}"
        return file_path, 0

    async def _generate_model_performance(self, report: AnalyticsReport) -> tuple:
        """Generate a model performance report."""
        os.makedirs(self.REPORT_DIR, exist_ok=True)
        file_path = f"{self.REPORT_DIR}/{report.id}.{report.file_format}"
        return file_path, 0

    async def _generate_custom_report(self, report: AnalyticsReport) -> tuple:
        """Generate a custom report based on parameters."""
        os.makedirs(self.REPORT_DIR, exist_ok=True)
        file_path = f"{self.REPORT_DIR}/{report.id}.{report.file_format}"
        return file_path, 0

    async def _send_report_email(self, report: AnalyticsReport) -> bool:
        """Send report via email.

        Args:
            report: Report to send

        Returns:
            True if sent successfully
        """
        # Placeholder - would integrate with email service
        logger.info(f"Would send report {report.name} to {report.email_recipients}")
        return True

    def _calculate_next_run(self, cron_expression: Optional[str]) -> Optional[datetime]:
        """Calculate next run time from cron expression.

        Args:
            cron_expression: Cron expression

        Returns:
            Next run datetime
        """
        if not cron_expression:
            return None

        # Simplified - would use croniter library
        # For now, schedule for next day at midnight
        next_run = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        return next_run

    def get_download_url(self, report_id: UUID) -> Optional[str]:
        """Get download URL for a completed report.

        Args:
            report_id: Report ID

        Returns:
            Download URL or None
        """
        report = self.get_report(report_id)
        if not report or report.status != AnalyticsReport.STATUS_COMPLETED:
            return None

        if report.is_expired():
            return None

        # In production, would generate presigned URL for S3
        return f"/api/v1/analytics/reports/{report_id}/download"

    def regenerate_report(self, report_id: UUID) -> Optional[AnalyticsReport]:
        """Regenerate an existing report.

        Args:
            report_id: Report to regenerate

        Returns:
            Updated report or None
        """
        report = self.get_report(report_id)
        if not report or not report.can_regenerate():
            return None

        report.status = AnalyticsReport.STATUS_PENDING
        report.progress_percentage = None
        report.error_message = None
        self.db.commit()

        return report

    def get_scheduled_reports(self) -> List[AnalyticsReport]:
        """Get reports that are due for scheduled generation.

        Returns:
            List of reports due for generation
        """
        now = datetime.utcnow()

        return self.db.query(AnalyticsReport).filter(
            AnalyticsReport.is_scheduled == True,
            AnalyticsReport.next_run_at <= now
        ).all()

    def cleanup_expired_reports(self) -> int:
        """Delete expired reports.

        Returns:
            Number of reports deleted
        """
        expired = self.db.query(AnalyticsReport).filter(
            AnalyticsReport.expires_at < datetime.utcnow()
        ).all()

        count = 0
        for report in expired:
            if self.delete_report(report.id):
                count += 1

        logger.info(f"Cleaned up {count} expired analytics reports")
        return count

    def get_report_statistics(
        self,
        user_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get report generation statistics.

        Args:
            user_id: Optional filter by user
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(AnalyticsReport).filter(
            AnalyticsReport.created_at >= start_date
        )

        if user_id:
            query = query.filter(AnalyticsReport.created_by == user_id)

        total = query.count()

        by_status = self.db.query(
            AnalyticsReport.status,
            func.count(AnalyticsReport.id)
        ).filter(
            AnalyticsReport.created_at >= start_date
        )
        if user_id:
            by_status = by_status.filter(AnalyticsReport.created_by == user_id)
        by_status = by_status.group_by(AnalyticsReport.status).all()

        by_type = self.db.query(
            AnalyticsReport.report_type,
            func.count(AnalyticsReport.id)
        ).filter(
            AnalyticsReport.created_at >= start_date
        )
        if user_id:
            by_type = by_type.filter(AnalyticsReport.created_by == user_id)
        by_type = by_type.group_by(AnalyticsReport.report_type).all()

        by_format = self.db.query(
            AnalyticsReport.file_format,
            func.count(AnalyticsReport.id)
        ).filter(
            AnalyticsReport.created_at >= start_date
        )
        if user_id:
            by_format = by_format.filter(AnalyticsReport.created_by == user_id)
        by_format = by_format.group_by(AnalyticsReport.file_format).all()

        scheduled_count = self.db.query(AnalyticsReport).filter(
            AnalyticsReport.is_scheduled == True
        ).count()

        return {
            "period_days": days,
            "total_reports": total,
            "by_status": {status: count for status, count in by_status},
            "by_type": {rtype: count for rtype, count in by_type},
            "by_format": {fmt: count for fmt, count in by_format},
            "scheduled_reports": scheduled_count,
            "success_rate": self._calculate_success_rate(by_status)
        }

    def _calculate_success_rate(
        self,
        status_counts: List[tuple]
    ) -> Optional[float]:
        """Calculate report generation success rate.

        Args:
            status_counts: List of (status, count) tuples

        Returns:
            Success rate percentage or None
        """
        status_dict = {status: count for status, count in status_counts}

        completed = status_dict.get(AnalyticsReport.STATUS_COMPLETED, 0)
        failed = status_dict.get(AnalyticsReport.STATUS_FAILED, 0)
        total = completed + failed

        if total == 0:
            return None

        return round((completed / total) * 100, 1)
