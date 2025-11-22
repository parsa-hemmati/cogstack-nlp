"""
Timeline API Router

REST endpoints for patient timeline access, concept details, export functionality,
and filter management.

All endpoints require authentication and clinician/researcher/admin role.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.modules.timeline.service import TimelineService
from app.modules.timeline.repository import ElasticsearchTimelineRepository
from app.modules.timeline.models import (
    TimelineRequest,
    PatientTimeline,
    ExportRequest,
    TimelineExportResponse,
    FilterPresetRequest,
    FilterPresetResponse,
    TimelineConcept
)
from app.services.audit_service import AuditService


router = APIRouter(
    prefix="/api/v1/timeline",
    tags=["timeline"],
    dependencies=[Depends(require_role("clinician", "researcher", "admin"))]
)


def get_timeline_service(
    db: AsyncSession = Depends(get_db)
) -> TimelineService:
    """
    Dependency injection for TimelineService.
    
    Creates service instance with database session, Elasticsearch repository,
    and audit service dependencies.
    """
    es_repo = ElasticsearchTimelineRepository()
    audit_service = AuditService()
    return TimelineService(db=db, es_repo=es_repo, audit_service=audit_service)


@router.get("/{patient_id}", response_model=PatientTimeline)
async def get_patient_timeline(
    patient_id: UUID,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    concept_cuis: Optional[List[str]] = None,
    document_types: Optional[List[str]] = None,
    negation: Optional[str] = None,
    experiencer: Optional[str] = None,
    temporality: Optional[str] = None,
    certainty: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: TimelineService = Depends(get_timeline_service)
) -> PatientTimeline:
    """
    Get patient timeline with documents and medical concepts.
    
    Filters:
    - date_start/date_end: Date range filter (ISO format: YYYY-MM-DD)
    - concept_cuis: Filter by specific SNOMED-CT/UMLS CUIs (comma-separated)
    - document_types: Filter by document types (e.g., "discharge", "clinic_letter")
    - negation: Meta-annotation filter ("Affirmed", "Negated", "Possible")
    - experiencer: Meta-annotation filter ("Patient", "Family", "Other")
    - temporality: Meta-annotation filter ("Current", "Historical", "Future")
    - certainty: Meta-annotation filter ("Certain", "Uncertain", "Conditional")
    
    Returns:
        PatientTimeline with documents, concepts, statistics
    
    Raises:
        HTTPException 404: Patient not found
        HTTPException 403: User lacks access to patient
    """
    # Build timeline request from query parameters
    timeline_request = TimelineRequest(
        patient_id=patient_id,
        date_start=date_start,
        date_end=date_end,
        concept_cuis=concept_cuis,
        document_types=document_types,
        meta_annotations={
            "negation": negation,
            "experiencer": experiencer,
            "temporality": temporality,
            "certainty": certainty
        } if any([negation, experiencer, temporality, certainty]) else None
    )
    
    # Extract IP and user agent for audit logging
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    # Call service
    return await service.get_patient_timeline(
        patient_id=patient_id,
        request=timeline_request,
        user=current_user,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.get("/{patient_id}/concepts/{concept_cui}", response_model=TimelineConcept)
async def get_concept_details(
    patient_id: UUID,
    concept_cui: str,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: TimelineService = Depends(get_timeline_service)
) -> TimelineConcept:
    """
    Get detailed information about a specific concept in patient timeline.
    
    Returns all mentions of the concept with document context,
    meta-annotations, and temporal information.
    
    Args:
        patient_id: Patient UUID
        concept_cui: SNOMED-CT or UMLS CUI (e.g., "C0011860" for diabetes)
        date_start: Optional start date filter
        date_end: Optional end date filter
    
    Returns:
        TimelineConcept with all mentions
    
    Raises:
        HTTPException 404: Patient or concept not found
    """
    # Build request with specific CUI
    timeline_request = TimelineRequest(
        patient_id=patient_id,
        concept_cuis=[concept_cui],
        date_start=date_start,
        date_end=date_end
    )
    
    # Extract IP and user agent
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    # Get full timeline
    timeline = await service.get_patient_timeline(
        patient_id=patient_id,
        request=timeline_request,
        user=current_user,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Find the specific concept
    concept = next((c for c in timeline.concepts if c.cui == concept_cui), None)
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept {concept_cui} not found in patient timeline"
        )
    
    return concept


@router.post("/{patient_id}/export", response_model=TimelineExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    patient_id: UUID,
    export_request: ExportRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: TimelineService = Depends(get_timeline_service)
) -> TimelineExportResponse:
    """
    Create timeline export job (PDF, FHIR, or JSON format).
    
    Export is processed asynchronously. Use GET /exports/{export_id} to check status.
    
    Args:
        patient_id: Patient UUID
        export_request: Export configuration (format, filters, options)
    
    Returns:
        TimelineExportResponse with export_id and status
    
    Raises:
        HTTPException 404: Patient not found
    """
    # Extract IP and user agent
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    # Create export
    return await service.export_timeline(
        patient_id=patient_id,
        export_request=export_request,
        user=current_user,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.get("/exports/{export_id}", response_model=TimelineExportResponse)
async def get_export_status(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TimelineExportResponse:
    """
    Get timeline export status and metadata.
    
    Args:
        export_id: Export UUID
    
    Returns:
        TimelineExportResponse with current status
    
    Raises:
        HTTPException 404: Export not found
        HTTPException 403: User doesn't own export
    """
    from app.models.timeline import TimelineExport
    from sqlalchemy import select
    
    # Query export
    result = await db.execute(
        select(TimelineExport).where(TimelineExport.id == export_id)
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    # Verify ownership (users can only access their own exports)
    if export.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this export"
        )
    
    return TimelineExportResponse.from_orm(export)


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """
    Download completed timeline export file.
    
    Args:
        export_id: Export UUID
    
    Returns:
        FileResponse with export file (PDF, FHIR JSON, or JSON)
    
    Raises:
        HTTPException 404: Export not found or not yet completed
        HTTPException 403: User doesn't own export
    """
    from app.models.timeline import TimelineExport
    from sqlalchemy import select
    import os
    
    # Query export
    result = await db.execute(
        select(TimelineExport).where(TimelineExport.id == export_id)
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    # Verify ownership
    if export.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this export"
        )
    
    # Check if completed
    if export.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export not yet available (status: {export.status})"
        )
    
    # Check if file exists
    if not export.file_path or not os.path.exists(export.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    # Determine content type based on format
    content_type_map = {
        "pdf": "application/pdf",
        "fhir": "application/fhir+json",
        "json": "application/json"
    }
    
    # Increment download count
    export.download_count += 1
    await db.commit()
    
    # Return file
    return FileResponse(
        path=export.file_path,
        media_type=content_type_map.get(export.format, "application/octet-stream"),
        filename=f"timeline-export-{export_id}.{export.format}"
    )


@router.get("/filters", response_model=List[FilterPresetResponse])
async def list_filters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[FilterPresetResponse]:
    """
    List user's saved timeline filter presets.
    
    Returns:
        List of FilterPresetResponse objects
    """
    from app.models.timeline import TimelineFilter
    from sqlalchemy import select
    
    # Query user's filters
    result = await db.execute(
        select(TimelineFilter)
        .where(TimelineFilter.user_id == current_user.id)
        .order_by(TimelineFilter.is_default.desc(), TimelineFilter.name.asc())
    )
    filters = result.scalars().all()
    
    return [FilterPresetResponse.from_orm(f) for f in filters]


@router.post("/filters", response_model=FilterPresetResponse, status_code=status.HTTP_201_CREATED)
async def save_filter(
    filter_request: FilterPresetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FilterPresetResponse:
    """
    Save a new timeline filter preset.
    
    Args:
        filter_request: Filter configuration
    
    Returns:
        FilterPresetResponse with created filter
    
    Raises:
        HTTPException 409: Filter name already exists for user
    """
    from app.models.timeline import TimelineFilter
    from sqlalchemy import select
    from uuid import uuid4
    
    # Check if name already exists
    existing = await db.execute(
        select(TimelineFilter).where(
            TimelineFilter.user_id == current_user.id,
            TimelineFilter.name == filter_request.name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Filter '{filter_request.name}' already exists"
        )
    
    # Create filter
    filter_preset = TimelineFilter(
        id=uuid4(),
        user_id=current_user.id,
        name=filter_request.name,
        description=filter_request.description,
        filters=filter_request.filters,
        is_default=filter_request.is_default
    )
    
    db.add(filter_preset)
    await db.commit()
    await db.refresh(filter_preset)
    
    return FilterPresetResponse.from_orm(filter_preset)
