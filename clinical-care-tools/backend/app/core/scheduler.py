"""Task scheduler for automated background jobs."""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.services.data_retention_service import DataRetentionService

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Background task scheduler using APScheduler.

    Manages automated tasks:
    - Data retention/purging (daily at 2 AM)
    - Future: Report generation, backups, etc.
    """

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler: Optional[AsyncIOScheduler] = None

    def start(self) -> None:
        """Start the scheduler and register jobs."""
        if self.scheduler is not None:
            logger.warning("Scheduler already started")
            return

        self.scheduler = AsyncIOScheduler()

        # Register jobs
        self._register_data_retention_job()

        # Start scheduler
        self.scheduler.start()
        logger.info("Task scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler is None:
            return

        self.scheduler.shutdown(wait=True)
        self.scheduler = None
        logger.info("Task scheduler stopped")

    def _register_data_retention_job(self) -> None:
        """
        Register data retention/purging job.

        Runs daily at 2:00 AM to purge old data per retention policies.
        """
        self.scheduler.add_job(
            func=self._run_data_retention_purge,
            trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM daily
            id="data_retention_purge",
            name="Data Retention Purge",
            replace_existing=True,
            max_instances=1,  # Only one instance at a time
        )
        logger.info("Registered data retention purge job (daily at 2:00 AM)")

    async def _run_data_retention_purge(self) -> None:
        """
        Run data retention purge job.

        Creates a database session and executes the purge.
        """
        logger.info("Starting scheduled data retention purge")

        async with SessionLocal() as db:
            try:
                service = DataRetentionService(db)
                results = await service.purge_old_data()

                logger.info(
                    f"Data retention purge completed successfully: "
                    f"{results['documents_deleted']} documents, "
                    f"{results['audit_logs_deleted']} audit logs, "
                    f"{results['sessions_deleted']} sessions deleted"
                )

            except Exception as e:
                logger.error(f"Data retention purge failed: {str(e)}", exc_info=True)
                # Don't raise - we want the scheduler to continue

    def run_job_now(self, job_id: str) -> None:
        """
        Manually trigger a scheduled job immediately.

        Useful for testing or manual administration.

        Args:
            job_id: Job identifier (e.g., "data_retention_purge")

        Raises:
            ValueError: If job not found
        """
        if self.scheduler is None:
            raise ValueError("Scheduler not started")

        job = self.scheduler.get_job(job_id)
        if job is None:
            raise ValueError(f"Job '{job_id}' not found")

        job.modify(next_run_time=None)  # Trigger immediately
        logger.info(f"Manually triggered job: {job_id}")


# Global scheduler instance
scheduler = TaskScheduler()
