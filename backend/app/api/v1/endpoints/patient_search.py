"""
Patient Search API endpoints.

Handles patient search by clinical concepts with meta-annotation filtering.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.patient_search import (
    PatientSearchRequest,
    PatientSearchResponse,
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
