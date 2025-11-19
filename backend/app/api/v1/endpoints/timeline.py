"""
Timeline API endpoints.

Provides patient timeline view with documents and clinical concepts.
"""
import logging
from typing import Annotated, Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.timeline import (
    PatientTimeline,
    TimelineFilters,
    DateRange,
    TimelineExportRequest,
    TimelineExportResponse,
)
from app.services.timeline_service import TimelineService
from app.services.timeline_export_service import TimelineExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/{patient_id}", response_model=PatientTimeline, status_code=status.HTTP_200_OK)
async def get_patient_timeline(
    patient_id: UUID,
    request: Request,
    concepts: Annotated[Optional[str], Query(
        description="Comma-separated SNOMED CUIs to filter by",
        example="C0011849,C0020538"
    )] = None,
    date_start: Annotated[Optional[datetime], Query(
        description="Start date for timeline (ISO 8601 format)",
        example="2023-01-01T00:00:00Z"
    )] = None,
    date_end: Annotated[Optional[datetime], Query(
        description="End date for timeline (ISO 8601 format)",
        example="2023-12-31T23:59:59Z"
    )] = None,
    meta_negation: Annotated[Optional[str], Query(
        description="Filter by Negation meta-annotation",
        example="Affirmed"
    )] = "Affirmed",
    meta_experiencer: Annotated[Optional[str], Query(
        description="Filter by Experiencer meta-annotation",
        example="Patient"
    )] = "Patient",
    meta_temporality: Annotated[Optional[str], Query(
        description="Comma-separated Temporality values (OR logic)",
        example="Current,Recent"
    )] = "Current,Recent",
    meta_certainty: Annotated[Optional[str], Query(
        description="Filter by Certainty meta-annotation",
        example="High"
    )] = None,
    document_types: Annotated[Optional[str], Query(
        description="Comma-separated document types to filter by",
        example="clinical_note,lab_result"
    )] = None,
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get patient timeline with documents and clinical concepts.

    **Authorization**: Requires one of: clinician, researcher, admin

    **Workflow**:
    1. Validate patient_id and filters
    2. Query documents from PostgreSQL
    3. Query concepts from Elasticsearch with meta-annotation filters
    4. Aggregate concepts by CUI (first mention, count)
    5. Log audit trail (HIPAA compliance)
    6. Return timeline with documents, concepts, and date range

    **Meta-Annotation Filtering**:
    - **Negation**: "Affirmed" (default) or "Negated"
      - Affirmed: Patient HAS the condition
      - Negated: Patient denies/doesn't have the condition
    - **Experiencer**: "Patient" (default), "Family", or "Other"
      - Patient: Condition applies to patient
      - Family: Family history (not patient's condition)
    - **Temporality**: "Current,Recent" (default), "Historical"
      - Current: Currently active condition
      - Recent: Recently mentioned condition
      - Historical: Past condition (may not be active)
    - **Certainty**: "High", "Medium", "Low" (optional filter)

    **Default Filters** (safe for clinical use):
    - Negation: "Affirmed" (excludes "patient denies chest pain")
    - Experiencer: "Patient" (excludes family history)
    - Temporality: "Current,Recent" (excludes historical conditions)

    **Example Requests**:

    1. Basic timeline (all concepts, default filters):
       ```
       GET /api/v1/timeline/patient-uuid-123
       ```

    2. Timeline for diabetes management (last 6 months):
       ```
       GET /api/v1/timeline/patient-uuid-123?concepts=C0011849&date_start=2023-06-01&date_end=2023-12-31
       ```

    3. Timeline including historical conditions:
       ```
       GET /api/v1/timeline/patient-uuid-123?meta_temporality=Current,Recent,Historical
       ```

    **Response**:
    - **documents**: List of clinical documents (title, type, date, concepts)
    - **concepts**: List of aggregated concepts (CUI, name, first mention, count, all mentions)
    - **date_range**: Overall date range (min/max dates from documents + concepts)
    - **filters_applied**: Filters that were applied to generate this timeline

    **Security**:
    - Audit log entry created for every timeline access (HIPAA requirement)
    - Logs include: user, patient, filters, IP address, timestamp
    """
    logger.info(f"Timeline request: patient_id={patient_id}, user={current_user.username}")

    # Parse filters from query parameters
    filters = _parse_timeline_filters(
        concepts=concepts,
        date_start=date_start,
        date_end=date_end,
        meta_negation=meta_negation,
        meta_experiencer=meta_experiencer,
        meta_temporality=meta_temporality,
        meta_certainty=meta_certainty,
        document_types=document_types
    )

    # Get timeline from service
    async with TimelineService(db) as service:
        try:
            timeline = await service.get_patient_timeline(
                patient_id=patient_id,
                filters=filters,
                user=current_user,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as e:
            logger.error(
                f"Timeline retrieval failed: patient_id={patient_id}, "
                f"user={current_user.username}, error={str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve patient timeline. Please try again later."
            )

    logger.info(
        f"Timeline retrieved: patient_id={patient_id}, "
        f"documents={len(timeline.documents)}, concepts={len(timeline.concepts)}"
    )

    return timeline


def _parse_timeline_filters(
    concepts: Optional[str],
    date_start: Optional[datetime],
    date_end: Optional[datetime],
    meta_negation: Optional[str],
    meta_experiencer: Optional[str],
    meta_temporality: Optional[str],
    meta_certainty: Optional[str],
    document_types: Optional[str]
) -> TimelineFilters:
    """Parse query parameters into TimelineFilters object.

    Args:
        concepts: Comma-separated concept CUIs
        date_start: Start date for timeline
        date_end: End date for timeline
        meta_negation: Negation filter value
        meta_experiencer: Experiencer filter value
        meta_temporality: Comma-separated Temporality values (OR logic)
        meta_certainty: Certainty filter value
        document_types: Comma-separated document types

    Returns:
        TimelineFilters object

    Raises:
        HTTPException: If date_start provided without date_end (or vice versa)
    """
    # Parse concept list
    concept_list = None
    if concepts:
        concept_list = [c.strip() for c in concepts.split(",") if c.strip()]

    # Parse date range
    date_range = None
    if date_start and date_end:
        date_range = DateRange(start=date_start, end=date_end)
    elif date_start or date_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both date_start and date_end must be provided together"
        )

    # Parse meta-annotations
    meta_annotations = {}

    if meta_negation:
        meta_annotations["Negation"] = meta_negation

    if meta_experiencer:
        meta_annotations["Experiencer"] = meta_experiencer

    if meta_temporality:
        # Parse comma-separated values for OR logic
        temporality_values = [t.strip() for t in meta_temporality.split(",") if t.strip()]
        if len(temporality_values) == 1:
            meta_annotations["Temporality"] = temporality_values[0]
        elif len(temporality_values) > 1:
            meta_annotations["Temporality"] = temporality_values

    if meta_certainty:
        meta_annotations["Certainty"] = meta_certainty

    # Parse document types
    doc_types_list = None
    if document_types:
        doc_types_list = [d.strip() for d in document_types.split(",") if d.strip()]

    return TimelineFilters(
        concepts=concept_list,
        date_range=date_range,
        meta_annotations=meta_annotations if meta_annotations else None,
        document_types=doc_types_list
    )

# ========================================
# Export Endpoints
# ========================================

@router.post(
    "/{patient_id}/export",
    response_model=TimelineExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export patient timeline",
    description="Export patient timeline to PDF, FHIR R4, or JSON format"
)
async def export_timeline(
    patient_id: UUID,
    export_request: TimelineExportRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export patient timeline to specified format.

    **Formats**:
    - **PDF**: Visual clinical summary for referrals/audits
    - **FHIR**: FHIR R4 Composition for EHR interoperability
    - **JSON**: Machine-readable data for research/analysis

    **Options**:
    - `watermark`: Add "Confidential" watermark (PDF only)
    - `de_identified`: Remove patient PII
    - `apply_filters`: Use filters from export_request.filters

    **Audit Logging**: All exports are logged for HIPAA compliance.

    **Returns**: Export response with download URL or inline data.
    """
    try:
        # Initialize services
        timeline_service = TimelineService(db)
        export_service = TimelineExportService()

        # Parse filters if provided
        filters = None
        if export_request.filters:
            # Convert dict to TimelineFilters
            filters = TimelineFilters(**export_request.filters)

        # Fetch timeline data
        timeline_data = await timeline_service.get_patient_timeline(
            patient_id=patient_id,
            filters=filters
        )

        # Audit log: Export initiated
        logger.info(
            f"Timeline export initiated: user={current_user.id}, "
            f"patient={patient_id}, format={export_request.format}, "
            f"ip={request.client.host}"
        )

        # Generate export based on format
        export_result = None
        content_type = None

        if export_request.format == "pdf":
            export_bytes = await export_service.export_to_pdf(
                patient_id=patient_id,
                timeline_data=timeline_data,
                options=export_request.options
            )
            export_result = export_bytes
            content_type = "application/pdf"

        elif export_request.format == "fhir":
            export_dict = await export_service.export_to_fhir(
                patient_id=patient_id,
                timeline_data=timeline_data
            )
            export_result = export_dict
            content_type = "application/fhir+json"

        elif export_request.format == "json":
            export_dict = await export_service.export_to_json(
                timeline_data=timeline_data
            )
            export_result = export_dict
            content_type = "application/json"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {export_request.format}"
            )

        # Audit log: Export completed
        logger.info(
            f"Timeline export completed: user={current_user.id}, "
            f"patient={patient_id}, format={export_request.format}, "
            f"size={len(export_result) if isinstance(export_result, bytes) else 'N/A'}"
        )

        # Return response
        # For PDF: return base64-encoded bytes
        # For JSON/FHIR: return dict directly
        if isinstance(export_result, bytes):
            import base64
            return TimelineExportResponse(
                export_id=str(UUID(int=0)),  # Placeholder for sync export
                status="completed",
                format=export_request.format,
                content_type=content_type,
                data=base64.b64encode(export_result).decode('utf-8'),
                created_at=datetime.now(),
                expires_at=None  # No expiration for sync export
            )
        else:
            return TimelineExportResponse(
                export_id=str(UUID(int=0)),  # Placeholder for sync export
                status="completed",
                format=export_request.format,
                content_type=content_type,
                data=export_result,
                created_at=datetime.now(),
                expires_at=None  # No expiration for sync export
            )

    except Exception as e:
        logger.error(
            f"Timeline export failed: user={current_user.id}, "
            f"patient={patient_id}, format={export_request.format}, "
            f"error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
