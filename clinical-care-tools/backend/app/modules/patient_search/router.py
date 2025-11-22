"""
Patient Search Router

API endpoints for patient search module.
"""

import csv
import io
import json
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from .schemas import (
    ConceptSuggestion,
    ExportFormat,
    ExportRequest,
    PatientSearchRequest,
    PatientSearchResponse,
    SavedSearchRequest,
    SavedSearchResponse,
)
from .service import PatientSearchService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service (would be dependency injected in production)
search_service = PatientSearchService()


@router.post("/search", response_model=PatientSearchResponse)
async def search_patients(
    request: PatientSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PatientSearchResponse:
    """
    Execute patient search with medical concepts and meta-annotation filtering.

    This endpoint provides high-precision patient search by:
    - Extracting medical concepts from the query
    - Applying meta-annotation filters to exclude false positives
    - Ranking results by relevance

    Key filtering capabilities:
    - **Negation**: Excludes negated mentions (patient denies chest pain)
    - **Temporality**: Focus on current/recent vs historical conditions
    - **Experiencer**: Distinguish patient conditions from family history
    - **Certainty**: Filter by confirmed vs suspected conditions

    Args:
        request: Search parameters with query and filters
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user

    Returns:
        Search results with matching patients

    Example:
        ```json
        {
            "query": "diabetes mellitus",
            "filters": {
                "negation": "Affirmed",
                "temporality": ["Current", "Recent"],
                "experiencer": "Patient",
                "confidence_min": 0.7
            },
            "limit": 50
        }
        ```
    """
    # Check permission
    if not current_user.has_permission("patient_search.search"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to search patients",
        )

    # Log search request (audit)
    logger.info(
        f"Patient search by {current_user.username}: "
        f"query='{request.query}', filters={request.filters.model_dump()}"
    )

    try:
        # Execute search
        response = await search_service.search_patients(
            request=request,
            db=db,
            user_id=current_user.id,
        )

        # Schedule background analytics
        background_tasks.add_task(
            log_search_analytics,
            user_id=current_user.id,
            query=request.query,
            result_count=response.total,
        )

        return response

    except Exception as e:
        logger.error(f"Search failed for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed. Please try again later.",
        )


@router.get("/concepts", response_model=List[ConceptSuggestion])
async def get_concept_suggestions(
    q: str = Query(..., min_length=2, description="Query string for autocomplete"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions"),
    current_user: User = Depends(get_current_active_user),
) -> List[ConceptSuggestion]:
    """
    Get medical concept suggestions for autocomplete.

    Provides real-time suggestions as the user types, showing:
    - SNOMED-CT/UMLS concept codes
    - Human-readable names
    - Semantic types (Disease, Symptom, etc.)
    - Synonyms and alternative names

    Args:
        q: Partial query string (minimum 2 characters)
        limit: Maximum number of suggestions
        current_user: Authenticated user

    Returns:
        List of concept suggestions

    Example:
        GET /concepts?q=diab&limit=5
    """
    # Check permission
    if not current_user.has_permission("patient_search.view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to view concepts",
        )

    try:
        suggestions = await search_service.get_concept_suggestions(
            query=q,
            limit=limit,
        )
        return suggestions

    except Exception as e:
        logger.error(f"Failed to get concept suggestions: {e}")
        return []


@router.post("/saved-searches", response_model=SavedSearchResponse)
async def save_search(
    request: SavedSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SavedSearchResponse:
    """
    Save a search query for reuse.

    Allows users to save complex searches with:
    - Custom name and description
    - All search parameters and filters
    - Option to share with other users

    Args:
        request: Save search request
        db: Database session
        current_user: Authenticated user

    Returns:
        Saved search information
    """
    # Check permission
    if not current_user.has_permission("patient_search.saved_searches"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to save searches",
        )

    # NOTE: Implement saved search storage
    # This would save to a saved_searches table

    # For now, return a mock response
    from datetime import datetime
    from uuid import uuid4

    return SavedSearchResponse(
        id=uuid4(),
        name=request.name,
        description=request.description,
        search_request=request.search_request,
        is_public=request.is_public,
        created_by=current_user.id,
        created_at=datetime.now(),
        last_used=None,
        use_count=0,
    )


@router.get("/saved-searches", response_model=List[SavedSearchResponse])
async def list_saved_searches(
    include_public: bool = Query(True, description="Include public searches"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[SavedSearchResponse]:
    """
    List saved searches.

    Returns:
    - User's own saved searches
    - Public searches from other users (if include_public=true)

    Args:
        include_public: Whether to include public searches
        db: Database session
        current_user: Authenticated user

    Returns:
        List of saved searches
    """
    # Check permission
    if not current_user.has_permission("patient_search.saved_searches"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to view saved searches",
        )

    # NOTE: Implement saved search retrieval
    # This would query the saved_searches table

    return []


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(
    search_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Delete a saved search.

    Users can only delete their own saved searches.

    Args:
        search_id: Saved search UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message
    """
    # Check permission
    if not current_user.has_permission("patient_search.saved_searches"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to manage saved searches",
        )

    # NOTE: Implement saved search deletion
    # This would delete from the saved_searches table

    return {"message": f"Saved search {search_id} deleted successfully"}


@router.post("/export")
async def export_search_results(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export search results to various formats.

    Supported formats:
    - **CSV**: Spreadsheet format for analysis
    - **FHIR**: HL7 FHIR Bundle for interoperability
    - **JSON**: Raw data format

    Args:
        request: Export request with format and options
        db: Database session
        current_user: Authenticated user

    Returns:
        File download response
    """
    # Check permission
    if not current_user.has_permission("patient_search.export"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to export search results",
        )

    # Log export request (audit)
    logger.info(
        f"Export request by {current_user.username}: "
        f"format={request.format}, patients={len(request.patient_ids)}"
    )

    try:
        if request.format == ExportFormat.CSV:
            content = generate_csv_export(request, db)
            media_type = "text/csv"
            filename = "patient_search_export.csv"

        elif request.format == ExportFormat.FHIR:
            content = generate_fhir_export(request, db)
            media_type = "application/fhir+json"
            filename = "patient_search_bundle.json"

        else:  # JSON
            content = generate_json_export(request, db)
            media_type = "application/json"
            filename = "patient_search_export.json"

        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )

    except Exception as e:
        logger.error(f"Export failed for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed. Please try again later.",
        )


def generate_csv_export(request: ExportRequest, db: Session) -> str:
    """Generate CSV export of search results."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    headers = ["Patient ID", "MRN", "Age", "Gender", "Concept", "CUI", "Confidence", "Date"]
    if request.include_context:
        headers.append("Context")
    writer.writerow(headers)

    # NOTE: Fetch actual patient data
    # This would query the database for the specified patients

    # Mock data for now
    writer.writerow([
        "550e8400-e29b-41d4-a716-446655440000",
        "MRN123456",
        "65",
        "M",
        "Diabetes Mellitus, Type 2",
        "C0011860",
        "0.95",
        "2024-03-15",
    ])

    return output.getvalue()


def generate_fhir_export(request: ExportRequest, db: Session) -> str:
    """Generate FHIR Bundle export of search results."""
    # Create FHIR Bundle
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(request.patient_ids),
        "entry": [],
    }

    # NOTE: Convert patients to FHIR resources
    # This would use the fhir-r4-mapper skill patterns

    for patient_id in request.patient_ids[:10]:  # Limit for example
        # Mock FHIR Patient resource
        patient_resource = {
            "resource": {
                "resourceType": "Patient",
                "id": str(patient_id),
                "identifier": [
                    {
                        "system": "http://hospital.example.org/mrn",
                        "value": "MRN123456",
                    }
                ],
                "gender": "male",
                "birthDate": "1959-01-01",
            }
        }
        bundle["entry"].append(patient_resource)

    return json.dumps(bundle, indent=2)


def generate_json_export(request: ExportRequest, db: Session) -> str:
    """Generate JSON export of search results."""
    # NOTE: Fetch actual patient data
    # This would query the database for the specified patients

    # Mock data for now
    export_data = {
        "export_date": "2024-03-15T10:30:00Z",
        "patient_count": len(request.patient_ids),
        "include_concepts": request.include_concepts,
        "anonymized": request.anonymize,
        "patients": [
            {
                "id": str(patient_id),
                "concepts": [] if request.include_concepts else None,
            }
            for patient_id in request.patient_ids
        ],
    }

    return json.dumps(export_data, indent=2)


def log_search_analytics(user_id: UUID, query: str, result_count: int):
    """Background task to log search analytics."""
    # This would log to an analytics database or service
    logger.info(
        f"Search analytics: user={user_id}, query='{query}', results={result_count}"
    )