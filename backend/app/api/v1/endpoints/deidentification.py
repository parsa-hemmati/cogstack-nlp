"""
De-identification API Endpoints

REST API for single note and batch de-identification.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.deidentification_job import DeidentificationJob
from app.schemas.deidentification import (
    DeidentificationRequest,
    DeidentificationResult,
)
from app.schemas.deidentification_api import (
    DeidentifyBatchRequest,
    DeidentifyBatchResponse,
    JobStatus,
)
from app.services.deidentification_service import DeidentificationService
from app.services.phi_detection_service import PHIDetectionService
from app.services.audit_service import audit_service
from app.tasks.deidentification_tasks import process_batch_deidentification


router = APIRouter()


@router.post("/deidentify", response_model=DeidentificationResult)
async def deidentify_single_note(
    request: DeidentificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    De-identify a single clinical note.

    **Args**:
    - text: Clinical note text (max 50,000 characters)
    - method: De-identification method (removal, replacement, generalization)
    - confidence_threshold: Minimum confidence for PHI detection (0.0-1.0, default 0.7)

    **Returns**:
    - original_text: Original text (for review)
    - deidentified_text: De-identified text
    - entities_removed: List of PHI entities removed
    - method_used: Method used
    - confidence_score: Average confidence of detected PHI
    - review_required: True if manual review recommended

    **Security**:
    - Requires authentication
    - Audit log entry created for PHI access
    - Original text NOT stored (only de-identified text stored if exported)
    """
    # Initialize services
    phi_service = PHIDetectionService()
    deid_service = DeidentificationService()

    # Detect PHI entities
    entities = await phi_service.detect_phi(request.text, request.confidence_threshold)

    # De-identify note
    result = await deid_service.deidentify(
        text=request.text,
        method=request.method,
        entities=entities,
    )

    # Log de-identification action
    await audit_service.log_deidentification(
        db=db,
        user=current_user,
        job_id=str(uuid.uuid4()),  # Single note gets unique job ID
        note_id="single_note",
        entities_detected=len(entities),
        entities_removed=len(result.entities_removed),
        method=request.method,
    )

    return result


@router.post("/deidentify/batch", response_model=DeidentifyBatchResponse)
async def create_batch_job(
    request: DeidentifyBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a batch de-identification job.

    **Args**:
    - note_ids: List of note IDs to process (max 10,000)
    - method: De-identification method
    - notify_email: Optional email for completion notification

    **Returns**:
    - job_id: Batch job ID (use to poll status)
    - status: Job status (pending)
    - total_notes: Total notes to process
    - estimated_completion: Estimated completion time

    **Process**:
    1. Job created in database (status: pending)
    2. Celery task queued for background processing
    3. Client polls GET /deidentify/job/{job_id} for status
    4. When completed, download results via GET /deidentify/job/{job_id}/download

    **Performance**:
    - Processes ~100 notes per minute
    - Max 10,000 notes per job
    - Supports concurrent jobs (up to 10 workers)
    """
    # Validate request
    if len(request.notes) > 10000:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10,000 notes per batch job"
        )

    # Extract note IDs and texts
    note_ids = [note.id for note in request.notes]

    # Create job in database
    job = DeidentificationJob(
        job_id=uuid.uuid4(),
        user_id=current_user.id,
        status="pending",
        method=request.method,
        total_notes=len(request.notes),
        notify_email=request.notify_email,
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Log job creation
    await audit_service.log_job_created(
        db=db,
        user=current_user,
        job_id=str(job.job_id),
        total_notes=len(request.notes),
        method=request.method,
    )

    # Queue Celery task
    process_batch_deidentification.delay(
        job_id=str(job.job_id),
        user_id=str(current_user.id),
        note_ids=note_ids,
        method=request.method,
        notify_email=request.notify_email,
    )

    # Calculate estimated completion time (100 notes/minute)
    estimated_minutes = len(request.notes) / 100
    estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_minutes)

    return DeidentifyBatchResponse(
        job_id=job.job_id,
        status=job.status,
        total_notes=job.total_notes,
        created_at=job.created_at,
        estimated_completion=estimated_completion,
    )


@router.get("/deidentify/job/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get batch job status.

    **Args**:
    - job_id: Batch job ID

    **Returns**:
    - job_id: Job ID
    - status: Current status (pending, processing, completed, failed, cancelled)
    - total_notes: Total notes to process
    - processed_notes: Notes processed so far
    - error_count: Number of errors
    - progress_percentage: Progress (0-100)
    - created_at: Job creation time
    - completed_at: Job completion time (if completed)

    **Polling**:
    - Poll every 5 seconds for updates
    - Stop polling when status is completed, failed, or cancelled
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    # Fetch job
    query = select(DeidentificationJob).where(DeidentificationJob.job_id == job_uuid)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify ownership
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        total_notes=job.total_notes,
        processed_notes=job.processed_notes,
        progress_percentage=job.progress_percentage,
        created_at=job.created_at,
        updated_at=job.updated_at,
        estimated_completion=None,
        errors=[],
    )


@router.post("/deidentify/job/{job_id}/cancel", status_code=200)
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel a running batch job.

    **Args**:
    - job_id: Batch job ID

    **Returns**:
    - message: Cancellation confirmation
    - job_id: Job ID
    - status: Updated status (cancelled)

    **Note**:
    - Only pending or processing jobs can be cancelled
    - Partially processed results are preserved
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    # Fetch job
    query = select(DeidentificationJob).where(DeidentificationJob.job_id == job_uuid)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify ownership
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if cancellable
    if job.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in status: {job.status}"
        )

    # Update status
    job.status = "cancelled"
    job.completed_at = datetime.utcnow()
    await db.commit()

    # Log cancellation
    await audit_service.log_job_cancelled(
        db=db,
        user=current_user,
        job_id=job_id,
        reason="User cancelled",
    )

    # Revoke Celery task
    from app.celery_app import celery_app
    celery_app.control.revoke(str(job_uuid), terminate=True)

    return {
        "message": "Job cancelled successfully",
        "job_id": job_id,
        "status": "cancelled",
    }


@router.get("/deidentify/job/{job_id}/download")
async def download_results(
    job_id: str,
    format: str = "csv",  # csv, json, txt
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download de-identified notes from completed job.

    **Args**:
    - job_id: Batch job ID
    - format: Download format (csv, json, txt)

    **Returns**:
    - File download (streaming response)

    **Formats**:
    - csv: CSV with columns (note_id, deidentified_text, entities_removed, confidence_score)
    - json: JSON array of de-identified notes
    - txt: Plain text (one note per line)

    **Security**:
    - Only completed jobs can be downloaded
    - User must own the job or be admin
    - Download action is logged in audit trail
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    # Fetch job
    query = select(DeidentificationJob).where(DeidentificationJob.job_id == job_uuid)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify ownership
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if completed
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot download results from job in status: {job.status}"
        )

    # Log download action
    await audit_service.log_access(
        db=db,
        user=current_user,
        action="DOWNLOAD",
        resource_id=job_id,
    )

    # TODO: Fetch de-identified notes from Elasticsearch and generate file
    # For now, return placeholder
    content = f"De-identified notes for job {job_id}\n(Implementation pending)"

    return StreamingResponse(
        iter([content]),
        media_type=f"text/{format}",
        headers={"Content-Disposition": f"attachment; filename=deidentified_{job_id}.{format}"}
    )
