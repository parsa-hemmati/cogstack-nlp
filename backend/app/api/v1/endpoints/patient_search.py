"""
Patient Search API endpoints.

Handles patient search by clinical concepts with meta-annotation filtering.
"""
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient_search import (
    ConceptHighlightResponse,
    PatientSearchRequest,
    PatientSearchResponse,
    SearchFilters,
)
from app.services.audit_service import AuditService
from app.services.patient_search_service import PatientSearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/search", response_model=PatientSearchResponse, status_code=status.HTTP_200_OK)
async def search_patients(
    request: PatientSearchRequest,
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for patients by clinical concept with meta-annotation filtering.

    **Authorization**: Requires one of: clinician, researcher, admin

    **Workflow**:
    1. Validate search request (Pydantic validation)
    2. Execute search query with meta-annotation filters
    3. Apply pagination and sorting
    4. Log audit trail (HIPAA compliance)
    5. Return paginated results with query time

    **Search Query Types**:
    - Concept name: "diabetes", "atrial flutter", "myocardial infarction"
    - SNOMED-CT CUI: "C0011849", "C0004238", "C0027051"

    **Meta-Annotation Filters**:
    - Negation: Affirmed (default) | Negated | Any
    - Temporality: Current (default) | Historical | Any
    - Experiencer: Patient (default) | Family | Other | Any
    - Certainty: Confirmed | Suspected | Any (default)

    **Sort Options**:
    - relevance: By concept document count (most mentions first)
    - name: Alphabetical by patient name
    - last_updated: By most recent document

    **Performance**: Target <500ms for 10,000 patients (with database indexes)

    Args:
        request: PatientSearchRequest with query, filters, pagination
        current_user: Authenticated user (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        PatientSearchResponse with results, total_count, pagination, query_time_ms

    Raises:
        HTTPException 400: Invalid request (validation error)
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 403: Forbidden (insufficient role permissions)
        HTTPException 500: Internal server error

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/patients/search" \\
          -H "Authorization: Bearer $TOKEN" \\
          -H "Content-Type: application/json" \\
          -d '{
            "query": "diabetes",
            "filters": {
              "negation": "Affirmed",
              "temporality": "Current",
              "experiencer": "Patient"
            },
            "sort_by": "relevance",
            "page": 1,
            "page_size": 20
          }'
        ```

    Response:
        ```json
        {
          "results": [
            {
              "patient_id": "uuid-here",
              "nhs_number": "XXX-XXX-1234",
              "full_name": "John Doe",
              "date_of_birth": "1980-05-15",
              "age": 44,
              "document_count": 25,
              "concept_document_count": 8,
              "last_updated": "2025-11-18T10:30:00Z"
            }
          ],
          "total_count": 150,
          "page": 1,
          "page_size": 20,
          "query_time_ms": 245
        }
        ```
    """
    try:
        # Initialize services
        search_service = PatientSearchService(db)
        audit_service = AuditService()

        # Execute search
        response = await search_service.search(
            concept=request.concept,
            filters=request.filters,
            page=request.pagination.page,
            page_size=request.pagination.pageSize,
            sort=request.sort,
        )

        # Log audit trail (HIPAA compliance - PHI access)
        # NOTE: Audit logging must not abort the search if it fails
        try:
            await audit_service.log_action(
                db=db,
                user=current_user,
                action="SEARCH_PATIENTS",
                resource_type="patient",
                resource_id=None,  # No specific patient (cohort search)
                details={
                    "concept": request.concept,
                    "filters": request.filters.dict(),
                    "result_count": response.total,
                    "query_time_ms": response.queryTimeMs,
                },
            )
        except Exception as audit_error:
            # Log failure but don't break the search response
            logger.error(
                f"Failed to log audit trail for patient search: {audit_error}",
                exc_info=True,
                extra={
                    "user_id": current_user.id,
                    "concept": request.concept,
                    "result_count": response.total,
                }
            )

        logger.info(
            f"Patient search completed: user={current_user.username}, "
            f"concept='{request.concept}', results={response.total}, "
            f"time={response.queryTimeMs}ms"
        )

        return response

    except ValueError as e:
        # Invalid input (e.g., invalid filter values)
        logger.warning(f"Invalid patient search request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search request: {str(e)}",
        )
    except Exception as e:
        # Unexpected error
        logger.error(f"Patient search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient search failed. Please try again.",
        )


@router.get("/{patient_id}/concept-highlights", response_model=ConceptHighlightResponse, status_code=status.HTTP_200_OK)
async def get_concept_highlights(
    patient_id: UUID,
    cui: str = Query(..., description="SNOMED-CT CUI or concept name"),
    temporal: Optional[str] = Query(None, description="Temporal filter (current, historical, future, any)"),
    include_negated: Optional[bool] = Query(False, description="Include negated mentions"),
    include_family: Optional[bool] = Query(False, description="Include family history"),
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
    db: AsyncSession = Depends(get_db),
) -> ConceptHighlightResponse:
    """
    Get concept highlights for a specific patient.

    Retrieves all documents containing the specified concept for a patient,
    with document snippets showing context (100 chars before/after concept),
    meta-annotations, and document metadata.

    **Authentication**: Required (JWT token)
    **Authorization**: Clinician, Researcher, or Admin role

    **Performance**: <300ms target for typical cases

    **Audit Logging**: Creates audit log for document views (PHI access)

    Args:
        patient_id: Patient UUID
        cui: SNOMED-CT CUI (e.g., "C0004238") or concept name (e.g., "diabetes")
        temporal: Filter by temporal context (current, historical, future, any)
        include_negated: Include negated mentions (e.g., "no chest pain")
        include_family: Include family history mentions
        current_user: Authenticated user (dependency injection)
        db: Database session (dependency injection)

    Returns:
        ConceptHighlightResponse with document highlights and total count

    Raises:
        400: Invalid request (e.g., invalid patient_id)
        401: Unauthorized (no JWT token)
        403: Forbidden (insufficient role)
        404: Patient not found
        500: Internal server error

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/patients/{patient_id}/concept-highlights?cui=C0004238" \\
             -H "Authorization: Bearer <token>"
        ```
    """
    try:
        # Validate patient exists and user has access
        patient_query = await db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = patient_query.scalar_one_or_none()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found",
            )

        # Build filters from query parameters
        filters = None
        if temporal or include_negated or include_family:
            filters = SearchFilters(
                temporal=temporal or "current",
                includeNegated=include_negated or False,
                includeFamily=include_family or False,
            )

        # Get concept highlights
        search_service = PatientSearchService(db)
        response = await search_service.get_concept_highlights(
            patient_id=patient_id,
            cui=cui,
            filters=filters,
        )

        # Audit logging (non-blocking)
        try:
            audit_service = AuditService(db)
            await audit_service.log(
                user_id=current_user.id,
                action="VIEW_CONCEPT_HIGHLIGHTS",
                resource_type="patient",
                resource_id=str(patient_id),
                details={
                    "cui": cui,
                    "document_count": response.totalCount,
                    "filters": filters.dict() if filters else {},
                },
            )
        except Exception as audit_error:
            # Log failure but don't abort the request
            logger.error(
                f"Audit logging failed for concept highlights: {audit_error}",
                exc_info=True,
                extra={
                    "user_id": current_user.id,
                    "patient_id": str(patient_id),
                    "cui": cui,
                }
            )

        logger.info(
            f"Concept highlights retrieved: user={current_user.username}, "
            f"patient={patient_id}, cui='{cui}', documents={response.totalCount}"
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions (404, etc.)
        raise
    except ValueError as e:
        # Invalid input
        logger.warning(f"Invalid concept highlights request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    except Exception as e:
        # Unexpected error
        logger.error(f"Concept highlights failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve concept highlights. Please try again.",
        )
