"""Timeline API endpoints."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.models.patient import Patient
from app.models.user import User
from app.schemas.timeline import TimelineResponse
from app.services.audit_service import AuditService
from app.services.timeline_service import TimelineService
from app.services.timeline_export_service import TimelineExportService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{patient_id}", response_model=TimelineResponse)
async def get_patient_timeline(
    request: Request,
    patient_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter end date (ISO 8601)"),
    document_types: Optional[str] = Query(None, description="Comma-separated document types"),
    concept_types: Optional[str] = Query(None, description="Comma-separated concept types"),
    include_negated: bool = Query(False, description="Include negated concepts"),
    include_family: bool = Query(False, description="Include family history"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get timeline for a patient.

    Retrieves chronological timeline of documents and clinical concepts.

    Args:
        request: FastAPI request
        patient_id: Patient UUID
        start_date: Filter start date (optional)
        end_date: Filter end date (optional)
        document_types: Comma-separated list of document types (optional)
        concept_types: Comma-separated list of concept types (optional)
        include_negated: Include negated concepts (default: False)
        include_family: Include family history (default: False)
        current_user: Authenticated user
        db: Database session

    Returns:
        TimelineResponse with documents, concepts, and metadata

    Raises:
        HTTPException: 404 if patient not found, 403 if not authorized
    """
    audit_service = AuditService(db)
    timeline_service = TimelineService(db)

    # Verify patient exists
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )

    # Parse comma-separated lists
    doc_types_list = None
    if document_types:
        doc_types_list = [dt.strip() for dt in document_types.split(",")]

    concept_types_list = None
    if concept_types:
        concept_types_list = [ct.strip() for ct in concept_types.split(",")]

    # Get timeline
    try:
        timeline_response = await timeline_service.get_patient_timeline(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            document_types=doc_types_list,
            concept_types=concept_types_list,
            include_negated=include_negated,
            include_family=include_family,
        )
    except Exception as e:
        logger.error(f"Error retrieving timeline for patient {patient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving timeline: {str(e)}",
        )

    # Audit log (PHI access)
    await audit_service.log(
        user=current_user,
        action=AuditAction.VIEW_RECORD,
        resource_type="Timeline",
        resource_id=str(patient_id),
        patient_id=patient.patient_id,  # MRN for audit trail
        ip_address=request.client.host if request.client else None,
        details={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "document_types": doc_types_list,
            "concept_types": concept_types_list,
            "include_negated": include_negated,
            "include_family": include_family,
            "document_count": timeline_response.metadata["document_count"],
            "concept_count": timeline_response.metadata["concept_count"],
        },
        success=True,
    )

    logger.info(
        f"Timeline retrieved for patient {patient.patient_id} by {current_user.username}: "
        f"{timeline_response.metadata['document_count']} docs, "
        f"{timeline_response.metadata['concept_count']} concepts"
    )

    return timeline_response


@router.post("/{patient_id}/export")
async def export_patient_timeline(
    request: Request,
    patient_id: UUID,
    format: Literal["pdf", "json", "fhir"] = Query("pdf", description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Filter start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter end date (ISO 8601)"),
    document_types: Optional[str] = Query(None, description="Comma-separated document types"),
    concept_types: Optional[str] = Query(None, description="Comma-separated concept types"),
    include_negated: bool = Query(False, description="Include negated concepts"),
    include_family: bool = Query(False, description="Include family history"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Export patient timeline to specified format.

    Generates an export file in PDF, JSON, or FHIR format and returns it for download.

    Args:
        request: FastAPI request
        patient_id: Patient UUID
        format: Export format (pdf, json, or fhir)
        start_date: Filter start date (optional)
        end_date: Filter end date (optional)
        document_types: Comma-separated list of document types (optional)
        concept_types: Comma-separated list of concept types (optional)
        include_negated: Include negated concepts (default: False)
        include_family: Include family history (default: False)
        current_user: Authenticated user
        db: Database session

    Returns:
        FileResponse with the exported file

    Raises:
        HTTPException: 404 if patient not found, 403 if not authorized
    """
    audit_service = AuditService(db)
    timeline_service = TimelineService(db)
    export_service = TimelineExportService()

    # Verify patient exists
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )

    # Parse comma-separated lists
    doc_types_list = None
    if document_types:
        doc_types_list = [dt.strip() for dt in document_types.split(",")]

    concept_types_list = None
    if concept_types:
        concept_types_list = [ct.strip() for ct in concept_types.split(",")]

    # Get timeline data
    try:
        timeline_response = await timeline_service.get_patient_timeline(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            document_types=doc_types_list,
            concept_types=concept_types_list,
            include_negated=include_negated,
            include_family=include_family,
        )
    except Exception as e:
        logger.error(f"Error retrieving timeline for export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving timeline: {str(e)}",
        )

    # Generate export based on format
    try:
        patient_name = f"{patient.first_name} {patient.last_name}" if hasattr(patient, 'first_name') else None

        if format == "pdf":
            export_path = export_service.export_to_pdf(timeline_response, patient_name)
            media_type = "application/pdf"
            filename = f"timeline_{patient.patient_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        elif format == "json":
            export_path = export_service.export_to_json(timeline_response)
            media_type = "application/json"
            filename = f"timeline_{patient.patient_id}_{datetime.now().strftime('%Y%m%d')}.json"
        elif format == "fhir":
            export_path = export_service.export_to_fhir(timeline_response)
            media_type = "application/fhir+json"
            filename = f"timeline_{patient.patient_id}_{datetime.now().strftime('%Y%m%d')}_fhir.json"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid export format: {format}",
            )

    except Exception as e:
        logger.error(f"Error generating export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating export: {str(e)}",
        )

    # Audit log (PHI export)
    await audit_service.log(
        user=current_user,
        action=AuditAction.EXPORT_RECORD,
        resource_type="Timeline",
        resource_id=str(patient_id),
        patient_id=patient.patient_id,
        ip_address=request.client.host if request.client else None,
        details={
            "export_format": format,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "document_types": doc_types_list,
            "concept_types": concept_types_list,
            "include_negated": include_negated,
            "include_family": include_family,
            "document_count": timeline_response.metadata["document_count"],
            "concept_count": timeline_response.metadata["concept_count"],
            "filename": filename,
        },
        success=True,
    )

    logger.info(
        f"Timeline exported for patient {patient.patient_id} by {current_user.username} "
        f"in {format} format: {filename}"
    )

    return FileResponse(
        path=str(export_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/documents/{document_id}")
async def get_document_details(
    request: Request,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get document details with content and annotations for preview.

    Returns document text with annotation highlights for timeline document preview.

    Args:
        request: FastAPI request
        document_id: Document UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Document with decrypted content and annotations

    Raises:
        HTTPException: 404 if document not found
    """
    from app.models.document import Document
    from app.models.annotation import Annotation
    from app.services.encryption_service import decrypt_content

    audit_service = AuditService(db)

    # Get document
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Get annotations for this document
    annotations_result = await db.execute(
        select(Annotation).where(Annotation.document_id == document_id)
    )
    annotations = annotations_result.scalars().all()

    # Decrypt document content
    try:
        content = decrypt_content(document.encrypted_content)
        content_text = content.decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Error decrypting document {document_id}: {e}")
        content_text = "[Unable to decrypt document content]"

    # Build annotations list
    annotations_list = [
        {
            "id": str(ann.id),
            "cui": ann.cui,
            "preferredName": ann.preferred_name,
            "conceptType": ann.concept_type or "unknown",
            "startChar": ann.start_char,
            "endChar": ann.end_char,
            "text": ann.text,
            "metaAnnotations": {
                "negation": ann.negation,
                "temporality": ann.temporality,
                "experiencer": ann.experiencer,
                "certainty": getattr(ann, 'certainty', None),
            }
        }
        for ann in annotations
    ]

    # Audit log (PHI access)
    patient_id = document.patient_id if hasattr(document, 'patient_id') else None
    await audit_service.log(
        user=current_user,
        action=AuditAction.VIEW_RECORD,
        resource_type="Document",
        resource_id=str(document_id),
        patient_id=str(patient_id) if patient_id else None,
        ip_address=request.client.host if request.client else None,
        details={
            "document_title": document.title if hasattr(document, 'title') else document.filename,
            "annotation_count": len(annotations_list),
        },
        success=True,
    )

    logger.info(
        f"Document {document_id} retrieved by {current_user.username}: "
        f"{len(annotations_list)} annotations"
    )

    return {
        "id": str(document.id),
        "title": document.title if hasattr(document, 'title') else document.filename,
        "documentType": document.document_type.value if hasattr(document, 'document_type') else "unknown",
        "date": document.document_date.isoformat() + "Z" if hasattr(document, 'document_date') and document.document_date else document.created_at.isoformat() + "Z",
        "author": document.author if hasattr(document, 'author') else None,
        "content": content_text,
        "annotations": annotations_list,
    }
