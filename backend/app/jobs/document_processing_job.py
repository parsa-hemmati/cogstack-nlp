"""
Background job for processing pending documents.

Runs periodically to extract PHI and entities from uploaded documents.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.services.document_processing_service import DocumentProcessingService

logger = logging.getLogger(__name__)


class DocumentProcessingJob:
    """
    Background job for document processing.

    Features:
        - Periodic execution (configurable interval)
        - Batch processing (configurable batch size)
        - Error handling and logging
        - Graceful shutdown

    Usage:
        >>> job = DocumentProcessingJob(interval_seconds=60, batch_size=10)
        >>> await job.start()  # Start background processing
    """

    def __init__(self, interval_seconds: int = 60, batch_size: int = 10):
        """
        Initialize document processing job.

        Args:
            interval_seconds: Seconds between processing runs (default 60)
            batch_size: Maximum documents to process per run (default 10)
        """
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self.processing_service = DocumentProcessingService()
        self._running = False
        self._task = None

    async def start(self):
        """
        Start background job.

        Runs in background loop, processing pending documents every interval.
        """
        if self._running:
            logger.warning("Document processing job already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"Document processing job started (interval={self.interval_seconds}s, "
            f"batch_size={self.batch_size})"
        )

    async def stop(self):
        """
        Stop background job.

        Gracefully shuts down the processing loop.
        """
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Document processing job stopped")

    async def _run_loop(self):
        """
        Main processing loop.

        Runs continuously, processing pending documents every interval.
        """
        logger.info("Document processing loop starting...")

        while self._running:
            try:
                # Process pending documents
                async with async_session_maker() as db:
                    count = await self.processing_service.process_pending_documents(
                        db, batch_size=self.batch_size
                    )

                    if count > 0:
                        logger.info(f"Processed {count} documents")

            except Exception as e:
                logger.error(f"Error in document processing loop: {e}", exc_info=True)

            # Wait for next interval
            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

        logger.info("Document processing loop stopped")

    async def run_once(self):
        """
        Run processing job once (for testing or manual execution).

        Returns:
            Number of documents processed
        """
        async with async_session_maker() as db:
            count = await self.processing_service.process_pending_documents(
                db, batch_size=self.batch_size
            )
            logger.info(f"Manual processing run: {count} documents processed")
            return count


# Global job instance
_job_instance = None


def get_job_instance(interval_seconds: int = 60, batch_size: int = 10) -> DocumentProcessingJob:
    """
    Get singleton job instance.

    Args:
        interval_seconds: Processing interval (default 60)
        batch_size: Batch size (default 10)

    Returns:
        DocumentProcessingJob instance
    """
    global _job_instance
    if _job_instance is None:
        _job_instance = DocumentProcessingJob(interval_seconds, batch_size)
    return _job_instance


async def start_background_job(interval_seconds: int = 60, batch_size: int = 10):
    """
    Start background document processing job.

    Called from FastAPI startup event.

    Args:
        interval_seconds: Processing interval (default 60)
        batch_size: Batch size (default 10)
    """
    job = get_job_instance(interval_seconds, batch_size)
    await job.start()


async def stop_background_job():
    """
    Stop background document processing job.

    Called from FastAPI shutdown event.
    """
    job = get_job_instance()
    await job.stop()
