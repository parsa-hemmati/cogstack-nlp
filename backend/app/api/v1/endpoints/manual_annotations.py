"""
Manual Annotation API Endpoints

REST API for creating, reading, updating, deleting manual PHI annotations.
Supports human-in-the-loop workflow for catching missed PHI.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.manual_annotation import ManualAnnotation
from app.models.deidentification_job import DeidentificationJob
from app.models.phi_entity import PHIEntity
from app.schemas.manual_annotation import (
    ManualAnnotationCreate,
    ManualAnnotationUpdate,
    ManualAnnotationResponse,
    ManualAnnotationList,
    JobAnalytics,
)
from app.services.audit_service import audit_service


router = APIRouter()


@router.post("/annotations", response_model=ManualAnnotationResponse, status_code=201)
async def create_annotation(
    request: ManualAnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new manual PHI annotation.

    **Args**:
    - note_id: Note identifier
    - text: Annotated PHI text (max 500 chars)
    - start_offset: Character start position
    - end_offset: Character end position
    - entity_type: PHI category (NAME, DOB, MRN, etc.)
    - confidence: Annotator confidence (0.0-1.0)

    **Returns**:
    - Created annotation with annotation_id

    **Security**:
    - Requires authentication
    - Audit log entry created for annotation creation
    """
    # Create annotation
    annotation = ManualAnnotation(
        annotation_id=uuid.uuid4(),
        note_id=request.note_id,
        user_id=current_user.id,
        text=request.text,
        start_offset=request.start_offset,
        end_offset=request.end_offset,
        entity_type=request.entity_type,
        confidence=request.confidence,
    )

    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)

    # Log annotation creation
    await audit_service.log_access(
        db=db,
        user=current_user,
        action="CREATE_ANNOTATION",
        resource_id=str(annotation.annotation_id),
        details={
            "note_id": request.note_id,
            "entity_type": request.entity_type,
            "text_length": len(request.text),
        }
    )

    return ManualAnnotationResponse.from_orm(annotation)


@router.get("/annotations/{note_id}", response_model=ManualAnnotationList)
async def get_annotations_for_note(
    note_id: str,
    include_inactive: bool = Query(False, description="Include soft-deleted annotations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all manual annotations for a specific note.

    **Args**:
    - note_id: Note identifier
    - include_inactive: Include soft-deleted annotations (default: False)

    **Returns**:
    - List of annotations with total count
    """
    # Build query
    query = select(ManualAnnotation).where(ManualAnnotation.note_id == note_id)

    if not include_inactive:
        query = query.where(ManualAnnotation.is_active == True)

    query = query.order_by(ManualAnnotation.start_offset)

    # Execute query
    result = await db.execute(query)
    annotations = result.scalars().all()

    # Log access
    await audit_service.log_access(
        db=db,
        user=current_user,
        action="VIEW_ANNOTATIONS",
        resource_id=note_id,
        details={"count": len(annotations)}
    )

    return ManualAnnotationList(
        annotations=[ManualAnnotationResponse.from_orm(a) for a in annotations],
        total=len(annotations)
    )


@router.put("/annotations/{annotation_id}", response_model=ManualAnnotationResponse)
async def update_annotation(
    annotation_id: str,
    request: ManualAnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing manual annotation.

    **Args**:
    - annotation_id: Annotation identifier
    - text: Updated PHI text (optional)
    - entity_type: Updated entity type (optional)
    - confidence: Updated confidence (optional)

    **Returns**:
    - Updated annotation

    **Security**:
    - Users can only update their own annotations
    - Admins can update any annotation
    """
    # Parse annotation ID
    try:
        annotation_uuid = uuid.UUID(annotation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid annotation_id format")

    # Fetch annotation
    query = select(ManualAnnotation).where(ManualAnnotation.annotation_id == annotation_uuid)
    result = await db.execute(query)
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    # Verify ownership
    if annotation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    if request.text is not None:
        annotation.text = request.text
    if request.entity_type is not None:
        annotation.entity_type = request.entity_type
    if request.confidence is not None:
        annotation.confidence = request.confidence

    annotation.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(annotation)

    # Log update
    await audit_service.log_access(
        db=db,
        user=current_user,
        action="UPDATE_ANNOTATION",
        resource_id=annotation_id,
        details={"updated_fields": request.dict(exclude_unset=True)}
    )

    return ManualAnnotationResponse.from_orm(annotation)


@router.delete("/annotations/{annotation_id}", status_code=200)
async def delete_annotation(
    annotation_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a manual annotation.

    **Args**:
    - annotation_id: Annotation identifier
    - hard_delete: Permanently delete (default: False, soft delete)

    **Returns**:
    - Deletion confirmation

    **Security**:
    - Users can only delete their own annotations
    - Admins can delete any annotation
    - Hard delete requires admin role
    """
    # Parse annotation ID
    try:
        annotation_uuid = uuid.UUID(annotation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid annotation_id format")

    # Fetch annotation
    query = select(ManualAnnotation).where(ManualAnnotation.annotation_id == annotation_uuid)
    result = await db.execute(query)
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    # Verify ownership
    if annotation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Hard delete requires admin
    if hard_delete and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Hard delete requires admin role")

    # Delete
    if hard_delete:
        await db.delete(annotation)
        delete_type = "HARD_DELETE"
    else:
        annotation.is_active = False
        annotation.updated_at = datetime.utcnow()
        delete_type = "SOFT_DELETE"

    await db.commit()

    # Log deletion
    await audit_service.log_access(
        db=db,
        user=current_user,
        action=f"{delete_type}_ANNOTATION",
        resource_id=annotation_id,
        details={"note_id": annotation.note_id}
    )

    return {
        "message": f"Annotation {'permanently deleted' if hard_delete else 'soft deleted'}",
        "annotation_id": annotation_id,
        "delete_type": delete_type
    }


@router.get("/analytics", response_model=JobAnalytics, dependencies=[Depends(require_role("admin"))])
async def get_job_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Get de-identification job analytics.

    **Args**:
    - start_date: Start date for analytics (default: 30 days ago)
    - end_date: End date for analytics (default: today)

    **Returns**:
    - total_jobs: Total number of jobs
    - success_rate: Percentage of successful jobs
    - avg_processing_time: Average processing time (seconds)
    - total_notes: Total notes processed
    - jobs_over_time: Daily job counts
    - phi_distribution: PHI entity type counts
    - confidence_by_type: Average confidence by entity type

    **Security**:
    - Requires admin role
    """
    # Default date range: last 30 days
    if not end_date:
        end_dt = datetime.utcnow()
    else:
        end_dt = datetime.fromisoformat(end_date)

    if not start_date:
        start_dt = end_dt - timedelta(days=30)
    else:
        start_dt = datetime.fromisoformat(start_date)

    # Total jobs
    total_jobs_query = select(func.count(DeidentificationJob.job_id)).where(
        DeidentificationJob.created_at.between(start_dt, end_dt)
    )
    result = await db.execute(total_jobs_query)
    total_jobs = result.scalar() or 0

    # Success rate
    completed_jobs_query = select(func.count(DeidentificationJob.job_id)).where(
        and_(
            DeidentificationJob.created_at.between(start_dt, end_dt),
            DeidentificationJob.status == "completed"
        )
    )
    result = await db.execute(completed_jobs_query)
    completed_jobs = result.scalar() or 0
    success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

    # Average processing time
    avg_time_query = select(
        func.avg(
            func.extract('epoch', DeidentificationJob.completed_at - DeidentificationJob.created_at)
        )
    ).where(
        and_(
            DeidentificationJob.created_at.between(start_dt, end_dt),
            DeidentificationJob.status == "completed",
            DeidentificationJob.completed_at.isnot(None)
        )
    )
    result = await db.execute(avg_time_query)
    avg_processing_time = result.scalar() or 0

    # Total notes
    total_notes_query = select(func.sum(DeidentificationJob.total_notes)).where(
        DeidentificationJob.created_at.between(start_dt, end_dt)
    )
    result = await db.execute(total_notes_query)
    total_notes = result.scalar() or 0

    # Jobs over time (daily counts)
    jobs_over_time_query = select(
        func.date(DeidentificationJob.created_at).label('date'),
        func.count(DeidentificationJob.job_id).label('count')
    ).where(
        DeidentificationJob.created_at.between(start_dt, end_dt)
    ).group_by(
        func.date(DeidentificationJob.created_at)
    ).order_by('date')

    result = await db.execute(jobs_over_time_query)
    jobs_over_time = [
        {"date": str(row.date), "count": row.count}
        for row in result.all()
    ]

    # PHI distribution
    phi_dist_query = select(
        PHIEntity.entity_type,
        func.count(PHIEntity.entity_id).label('count')
    ).where(
        PHIEntity.created_at.between(start_dt, end_dt)
    ).group_by(PHIEntity.entity_type).order_by(func.count(PHIEntity.entity_id).desc())

    result = await db.execute(phi_dist_query)
    phi_distribution = [
        {"entity_type": row.entity_type, "count": row.count}
        for row in result.all()
    ]

    # Confidence by type
    confidence_query = select(
        PHIEntity.entity_type,
        func.avg(PHIEntity.confidence).label('avg_confidence')
    ).where(
        PHIEntity.created_at.between(start_dt, end_dt)
    ).group_by(PHIEntity.entity_type).order_by('avg_confidence')

    result = await db.execute(confidence_query)
    confidence_by_type = [
        {"entity_type": row.entity_type, "avg_confidence": round(float(row.avg_confidence), 3)}
        for row in result.all()
    ]

    return JobAnalytics(
        total_jobs=total_jobs,
        success_rate=round(success_rate, 2),
        avg_processing_time=round(avg_processing_time, 2),
        total_notes=total_notes,
        jobs_over_time=jobs_over_time,
        phi_distribution=phi_distribution,
        confidence_by_type=confidence_by_type
    )
