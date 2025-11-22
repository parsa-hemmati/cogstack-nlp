"""
Celery tasks for batch de-identification processing.

Background tasks for processing large batches of clinical notes (1,000-10,000 notes).
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.deidentification_job import DeidentificationJob
from app.models.phi_entity import PHIEntity
from app.models.user import User
from app.services.deidentification_service import DeidentificationService
from app.services.phi_detection_service import PHIDetectionService
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.deidentification_tasks.process_batch_deidentification")
def process_batch_deidentification(
    self,
    job_id: str,
    user_id: str,
    note_ids: List[str],
    method: str,
    notify_email: str = None
):
    """
    Process batch de-identification job.

    Args:
        job_id: De-identification job ID
        user_id: User who created the job
        note_ids: List of note IDs to process
        method: De-identification method (removal, replacement, generalization)
        notify_email: Optional email for completion notification

    Celery Configuration:
        - Runs in 'deidentification' queue
        - Max runtime: 1 hour per task
        - Retries: 3 times with exponential backoff
    """
    async def _process_batch():
        async with AsyncSessionLocal() as db:
            try:
                # Update job status to processing
                await _update_job_status(db, job_id, "processing")

                # Fetch user
                user = await db.get(User, uuid.UUID(user_id))
                if not user:
                    raise ValueError(f"User {user_id} not found")

                # Initialize services
                phi_service = PHIDetectionService()
                deid_service = DeidentificationService()

                # Process each note
                processed_count = 0
                error_count = 0

                for note_id in note_ids:
                    try:
                        # Fetch note content (would come from documents table or external source)
                        note_text = await _fetch_note(db, note_id)

                        # Detect PHI entities
                        entities = await phi_service.detect_phi(note_text)

                        # De-identify note
                        result = await deid_service.deidentify(
                            text=note_text,
                            method=method,
                            entities=entities
                        )

                        # Store de-identified note and entities
                        await _store_deidentified_note(db, job_id, note_id, result, entities)

                        # Store PHI entities
                        for entity in entities:
                            phi_entity = PHIEntity(
                                job_id=uuid.UUID(job_id),
                                note_id=note_id,
                                entity_type=entity.type,
                                start_offset=entity.start,
                                end_offset=entity.end,
                                confidence=entity.confidence,
                                action=_get_action_from_method(method),
                            )
                            db.add(phi_entity)

                        # Log de-identification action
                        await audit_service.log_deidentification(
                            db=db,
                            user=user,
                            job_id=job_id,
                            note_id=note_id,
                            entities_detected=len(entities),
                            entities_removed=len(result.entities_removed),
                            method=method,
                        )

                        processed_count += 1

                        # Update progress every 10 notes
                        if processed_count % 10 == 0:
                            await _update_job_progress(db, job_id, processed_count, error_count)
                            self.update_state(
                                state="PROGRESS",
                                meta={"processed": processed_count, "total": len(note_ids)}
                            )

                    except Exception as e:
                        logger.error(f"Error processing note {note_id}: {e}")
                        error_count += 1
                        # Continue processing other notes

                # Mark job as completed
                await _update_job_status(
                    db, job_id, "completed", processed_count, error_count
                )

                # Log job completion
                await audit_service.log_job_completed(
                    db=db,
                    user=user,
                    job_id=job_id,
                    processed_notes=processed_count,
                    error_count=error_count,
                )

                # Send notification email if requested
                if notify_email:
                    await _send_completion_email(notify_email, job_id, processed_count, error_count)

                return {
                    "job_id": job_id,
                    "processed": processed_count,
                    "errors": error_count,
                    "status": "completed"
                }

            except Exception as e:
                logger.error(f"Batch de-identification job {job_id} failed: {e}")
                await _update_job_status(db, job_id, "failed")
                raise

    # Run async function in sync context
    import asyncio
    try:
        return asyncio.run(_process_batch())
    except Exception as e:
        logger.exception(f"Fatal error in batch de-identification job {job_id}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(name="app.tasks.deidentification_tasks.cleanup_old_jobs")
def cleanup_old_jobs():
    """
    Clean up old de-identification jobs (older than 30 days).

    Runs daily via Celery Beat schedule.
    Deletes completed jobs and their associated PHI entities.
    """
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            # Find old completed jobs
            query = select(DeidentificationJob).where(
                DeidentificationJob.status == "completed",
                DeidentificationJob.completed_at < cutoff_date
            )

            result = await db.execute(query)
            old_jobs = result.scalars().all()

            deleted_count = 0
            for job in old_jobs:
                # Delete job (PHI entities cascade delete)
                await db.delete(job)
                deleted_count += 1

            await db.commit()

            logger.info(f"Cleaned up {deleted_count} old de-identification jobs")
            return {"deleted": deleted_count}

    import asyncio
    return asyncio.run(_cleanup())


# Helper functions

async def _update_job_status(
    db: AsyncSession,
    job_id: str,
    status: str,
    processed_notes: int = None,
    error_count: int = None
):
    """Update job status in database."""
    update_data = {"status": status, "updated_at": datetime.utcnow()}

    if processed_notes is not None:
        update_data["processed_notes"] = processed_notes
    if error_count is not None:
        update_data["error_count"] = error_count
    if status == "completed":
        update_data["completed_at"] = datetime.utcnow()

    query = update(DeidentificationJob).where(
        DeidentificationJob.job_id == uuid.UUID(job_id)
    ).values(**update_data)

    await db.execute(query)
    await db.commit()


async def _update_job_progress(db: AsyncSession, job_id: str, processed: int, errors: int):
    """Update job progress."""
    await _update_job_status(db, job_id, "processing", processed, errors)


async def _fetch_note(db: AsyncSession, note_id: str) -> str:
    """
    Fetch note content from database.

    TODO: Implement actual note fetching from documents table.
    For now, returns placeholder.
    """
    # In real implementation, would query documents table
    # For now, placeholder
    return f"Sample clinical note {note_id}"


async def _store_deidentified_note(
    db: AsyncSession,
    job_id: str,
    note_id: str,
    result: Dict,
    entities: List
):
    """
    Store de-identified note in Elasticsearch.

    TODO: Implement Elasticsearch storage.
    """
    # Would store to Elasticsearch 'deidentified_notes' index
    pass


async def _send_completion_email(email: str, job_id: str, processed: int, errors: int):
    """
    Send job completion notification email.

    TODO: Implement email sending.
    """
    logger.info(f"Would send email to {email}: Job {job_id} completed ({processed} processed, {errors} errors)")


def _get_action_from_method(method: str) -> str:
    """Map de-identification method to entity action."""
    mapping = {
        "removal": "remove",
        "replacement": "replace",
        "generalization": "generalize",
    }
    return mapping.get(method, "remove")
