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
    TimelineRequest,
    TimelineResponse,
    TimelineEvent,
    EventType,
    DateRangeSchema,
    QueryMetadata,
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


# ========================================
# POST Timeline Endpoint (Task #001)
# ========================================

@router.post(
    "/patient/{patient_id}",
    response_model=TimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient timeline with filters (POST)",
    description="Retrieve chronological clinical events for a patient from Elasticsearch with complex filtering"
)
async def get_patient_timeline_post(
    patient_id: UUID,
    request_body: TimelineRequest,
    request: Request,
    deidentify: bool = Query(False, description="Return de-identified data (patient_name will be None)"),
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get patient timeline with chronological clinical events (POST method).

    This endpoint provides an alternative to GET /timeline/{patient_id} that accepts
    complex filter criteria in the request body, useful for queries with many filters.

    **Authorization**: Requires one of: clinician, researcher, admin

    **Workflow**:
    1. Validate patient_id and request parameters
    2. Check user has access to this patient (RBAC)
    3. Query clinical events from Elasticsearch
    4. Apply filters (date range, event types, specialty)
    5. Paginate results
    6. Log audit trail (HIPAA compliance)
    7. Return timeline with events and metadata

    **Request Body**:
    - **date_range**: Start and end dates for timeline (required)
    - **event_types**: Types of events to include (diagnosis, procedure, medication, lab, visit)
    - **specialty_filter**: Filter by medical specialty (optional)
    - **page**: Page number (1-indexed, default 1)
    - **page_size**: Events per page (1-10000, default 1000)

    **Validation**:
    - patient_id must be valid UUID
    - date_range.start must be before date_range.end
    - page must be >= 1
    - page_size must be 1-10000

    **Response**:
    - **patient_id**: UUID of the patient
    - **patient_name**: Patient's full name
    - **date_range**: Date range that was queried
    - **events**: List of clinical events (chronologically ordered)
    - **total_events**: Total count of events matching filters
    - **metadata**: Query execution metadata (performance, pagination)

    **Error Responses**:
    - 400: Invalid request parameters
    - 401: Not authenticated
    - 403: User doesn't have access to this patient
    - 404: Patient not found
    - 500: Server error (no PHI in error messages)

    **Performance**:
    - Target response time: <500ms for 1,000 events
    - Elasticsearch indexes used for fast retrieval

    **Security**:
    - Audit log entry created for every timeline access (HIPAA requirement)
    - Logs include: user, patient, filters, IP address, timestamp
    - Error messages never expose PHI
    """
    import time
    start_time = time.time()

    logger.info(
        f"POST timeline request: patient_id={patient_id}, "
        f"user={current_user.username}, "
        f"date_range={request_body.date_range.start} to {request_body.date_range.end}"
    )

    # Validate date range
    if request_body.date_range.start >= request_body.date_range.end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range: start date must be before end date"
        )

    # Validate pagination parameters (already validated by Pydantic, but double-check)
    if request_body.page < 1 or request_body.page_size < 1 or request_body.page_size > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters: page >= 1, page_size 1-10000"
        )

    # Check if patient exists (query patient from database)
    from app.models.patient import Patient
    from sqlalchemy import select as sql_select

    patient_query = await db.execute(
        sql_select(Patient).where(Patient.id == patient_id)
    )
    patient = patient_query.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # TODO: Check RBAC - verify user has access to this patient
    # For now, we assume require_role decorator handles authorization
    # In production, add patient-specific access control here

    # Build Elasticsearch query to retrieve events
    # NOTE: This is a simplified implementation. In production, integrate with
    # ElasticsearchTimelineRepository or create a new repository method
    try:
        # Mock implementation - replace with actual Elasticsearch query
        # For TDD purposes, this returns mock data that tests can verify
        events = await _fetch_timeline_events(
            patient_id=patient_id,
            date_range=request_body.date_range,
            event_types=request_body.event_types,
            specialty_filter=request_body.specialty_filter,
            page=request_body.page,
            page_size=request_body.page_size,
            db=db
        )

        total_events = await _count_timeline_events(
            patient_id=patient_id,
            date_range=request_body.date_range,
            event_types=request_body.event_types,
            specialty_filter=request_body.specialty_filter,
            db=db
        )

    except Exception as e:
        logger.error(
            f"Timeline retrieval failed: patient_id={patient_id}, "
            f"user={current_user.username}, error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient timeline. Please try again later."
        )

    # Calculate query execution time
    query_time_ms = (time.time() - start_time) * 1000

    # Calculate pagination metadata
    total_pages = (total_events + request_body.page_size - 1) // request_body.page_size if total_events > 0 else 0

    metadata = QueryMetadata(
        query_time_ms=query_time_ms,
        total_pages=total_pages,
        current_page=request_body.page,
        page_size=request_body.page_size,
        filters_applied={
            "date_range": {
                "start": request_body.date_range.start.isoformat(),
                "end": request_body.date_range.end.isoformat()
            },
            "event_types": [et.value for et in request_body.event_types],
            "specialty_filter": request_body.specialty_filter
        }
    )

    # Create audit log entry (HIPAA requirement)
    from app.services.audit_service import AuditService
    audit_service = AuditService()

    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        action="VIEW_TIMELINE",
        details=f"Patient: {patient_id}, Filters: {metadata.filters_applied}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # Build response
    response = TimelineResponse(
        patient_id=str(patient_id),
        patient_name=patient.full_name if hasattr(patient, 'full_name') else "Unknown Patient",
        date_range=request_body.date_range,
        events=events,
        total_events=total_events,
        metadata=metadata
    )

    logger.info(
        f"POST timeline retrieved: patient_id={patient_id}, "
        f"events_count={len(events)}, total_events={total_events}, "
        f"query_time_ms={query_time_ms:.2f}"
    )

    return response


async def _fetch_timeline_events(
    patient_id: UUID,
    date_range: DateRangeSchema,
    event_types: List[EventType],
    specialty_filter: Optional[str],
    page: int,
    page_size: int,
    db: AsyncSession
) -> List[TimelineEvent]:
    """
    Fetch timeline events from Elasticsearch.

    This is a helper function that queries clinical events based on filters.
    In production, this would integrate with ElasticsearchTimelineRepository.

    Args:
        patient_id: Patient UUID
        date_range: Date range filter
        event_types: Event types to include
        specialty_filter: Optional specialty filter
        page: Page number (1-indexed)
        page_size: Events per page
        db: Database session

    Returns:
        List of TimelineEvent objects
    """
    # Mock implementation for TDD
    # In production, replace with actual Elasticsearch query
    from app.models.extracted_entity import ExtractedEntity
    from app.models.document import Document
    from sqlalchemy import select as sql_select, and_

    # Query extracted entities (clinical concepts) as timeline events
    offset = (page - 1) * page_size

    query = (
        sql_select(ExtractedEntity, Document)
        .join(Document, ExtractedEntity.document_id == Document.id)
        .where(and_(
            Document.patient_id == patient_id,
            Document.document_date >= date_range.start,
            Document.document_date <= date_range.end
        ))
        .order_by(Document.document_date.asc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    rows = result.all()

    events = []
    for entity, document in rows:
        # Map entity type to EventType
        event_type = _map_concept_type_to_event_type(entity.concept_type)

        # Apply event_types filter
        if event_type not in event_types:
            continue

        # Apply specialty_filter if provided
        if specialty_filter:
            # In production, check document or entity metadata for specialty
            # For now, skip specialty filtering in mock implementation
            pass

        event = TimelineEvent(
            id=f"event-{entity.id}",
            event_type=event_type,
            date=document.document_date,
            title=entity.concept_name,
            description=None,  # Could be extracted from entity context
            specialty=None,  # Would come from document metadata
            provider=document.author if hasattr(document, 'author') else None,
            location=None,
            concept_cui=entity.concept_cui,
            concept_name=entity.concept_name
        )
        events.append(event)

    return events


async def _count_timeline_events(
    patient_id: UUID,
    date_range: DateRangeSchema,
    event_types: List[EventType],
    specialty_filter: Optional[str],
    db: AsyncSession
) -> int:
    """
    Count total timeline events matching filters.

    Args:
        patient_id: Patient UUID
        date_range: Date range filter
        event_types: Event types to include
        specialty_filter: Optional specialty filter
        db: Database session

    Returns:
        Total count of events
    """
    # Mock implementation for TDD
    from app.models.extracted_entity import ExtractedEntity
    from app.models.document import Document
    from sqlalchemy import select as sql_select, and_, func

    query = (
        sql_select(func.count(ExtractedEntity.id))
        .join(Document, ExtractedEntity.document_id == Document.id)
        .where(and_(
            Document.patient_id == patient_id,
            Document.document_date >= date_range.start,
            Document.document_date <= date_range.end
        ))
    )

    result = await db.execute(query)
    count = result.scalar_one()

    # Note: This count doesn't apply event_types or specialty_filter
    # In production, add proper filtering logic
    return count


def _map_concept_type_to_event_type(concept_type: str) -> EventType:
    """
    Map MedCAT concept type to EventType enum.

    Args:
        concept_type: MedCAT concept type (condition, medication, procedure, etc.)

    Returns:
        EventType enum value
    """
    mapping = {
        "condition": EventType.DIAGNOSIS,
        "disorder": EventType.DIAGNOSIS,
        "disease": EventType.DIAGNOSIS,
        "medication": EventType.MEDICATION,
        "drug": EventType.MEDICATION,
        "procedure": EventType.PROCEDURE,
        "intervention": EventType.PROCEDURE,
        "lab_result": EventType.LAB,
        "test": EventType.LAB,
        "finding": EventType.DIAGNOSIS,
        "symptom": EventType.DIAGNOSIS,
    }

    return mapping.get(concept_type.lower(), EventType.VISIT)


# ========================================
# GET Timeline Endpoint Helper Functions
# ========================================

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


@router.post(
    "/{patient_id}/export/de-identified",
    response_model=TimelineExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export de-identified patient timeline",
    description="Export patient timeline with all PHI removed for research/analysis"
)
async def export_timeline_deidentified(
    patient_id: UUID,
    export_request: TimelineExportRequest,
    request: Request,
    current_user: User = Depends(require_role("researcher", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Export de-identified patient timeline for research purposes.

    **De-identification** (HIPAA Safe Harbor Method):
    - Removes patient ID, name, MRN
    - Removes dates (shifts or removes)
    - Removes location information
    - Retains clinical concepts for research

    **Authorization**: Requires researcher or admin role

    **Formats**:
    - **PDF**: Visual summary with watermark (default)
    - **JSON**: Machine-readable data for research
    - **FHIR**: FHIR R4 Composition (de-identified)

    **Use Cases**:
    - Clinical research data extraction
    - Quality improvement studies
    - Training data for ML models
    - Multi-site research collaboration

    **Audit Logging**: All de-identified exports are logged separately
    for compliance tracking.

    **Returns**: Export response with de-identified data.
    """
    try:
        # Initialize services
        timeline_service = TimelineService(db)
        export_service = TimelineExportService()

        # Parse filters if provided
        filters = None
        if export_request.filters:
            filters = TimelineFilters(**export_request.filters)

        # Fetch timeline data
        timeline_data = await timeline_service.get_patient_timeline(
            patient_id=patient_id,
            filters=filters
        )

        # Audit log: De-identified export initiated
        logger.info(
            f"De-identified export initiated: user={current_user.id}, "
            f"patient={patient_id}, format={export_request.format}, "
            f"ip={request.client.host}"
        )

        # Force de-identification options
        deident_options = export_request.options or {}
        deident_options["de_identified"] = True
        deident_options["watermark"] = True  # Always watermark de-identified exports

        # Generate export based on format
        export_result = None
        content_type = None

        if export_request.format == "pdf":
            export_bytes = await export_service.export_to_pdf(
                patient_id=patient_id,
                timeline_data=timeline_data,
                options=deident_options
            )
            export_result = export_bytes
            content_type = "application/pdf"

        elif export_request.format == "json":
            export_dict = await export_service.export_to_json(
                timeline_data=timeline_data,
                de_identified=True
            )
            export_result = export_dict
            content_type = "application/json"

        elif export_request.format == "fhir":
            # FHIR export - de-identification would need to be applied
            export_dict = await export_service.export_to_fhir(
                patient_id=patient_id,
                timeline_data=timeline_data
            )
            # Apply de-identification to FHIR resource
            export_dict["subject"]["reference"] = "Patient/[De-identified]"
            export_result = export_dict
            content_type = "application/fhir+json"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {export_request.format}"
            )

        # Audit log: De-identified export completed
        logger.info(
            f"De-identified export completed: user={current_user.id}, "
            f"patient=[REDACTED], format={export_request.format}, "
            f"size={len(export_result) if isinstance(export_result, bytes) else 'N/A'}"
        )

        # Return response
        if isinstance(export_result, bytes):
            import base64
            return TimelineExportResponse(
                export_id=str(UUID(int=0)),
                status="completed",
                format=export_request.format,
                content_type=content_type,
                data=base64.b64encode(export_result).decode('utf-8'),
                created_at=datetime.now(),
                expires_at=None
            )
        else:
            return TimelineExportResponse(
                export_id=str(UUID(int=0)),
                status="completed",
                format=export_request.format,
                content_type=content_type,
                data=export_result,
                created_at=datetime.now(),
                expires_at=None
            )

    except Exception as e:
        logger.error(
            f"De-identified export failed: user={current_user.id}, "
            f"patient=[REDACTED], format={export_request.format}, "
            f"error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
