"""Clinical Coding API Endpoints (Sprint 5)"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated
from uuid import UUID

from app.schemas.clinical_coding import (
    CodingSuggestionsResponse,
    AssignCodesRequest,
    AssignCodesResponse,
    ICD10SearchRequest,
    ICD10SearchResponse,
    CodingQueueResponse,
    ICD10Code,
    CodingQueueDocument
)
from app.services.coding import ICD10ExtractionService
from app.core.deps import get_current_user
from app.core.audit import audit_log
from app.models.user import User

router = APIRouter(prefix="/coding", tags=["Clinical Coding"])


def get_icd10_service() -> ICD10ExtractionService:
    """Dependency: Get ICD-10 extraction service"""
    return ICD10ExtractionService(use_mock=True)


@router.get(
    "/queue",
    response_model=CodingQueueResponse,
    summary="Get coding queue",
    description="Get documents in coding queue (uncoded, in-progress, coded)"
)
async def get_coding_queue(
    current_user: Annotated[User, Depends(get_current_user)],
    status: str = Query("all", description="Filter by status: uncoded, in_progress, coded, all")
) -> CodingQueueResponse:
    """Get coding queue

    Args:
        current_user: Authenticated user
        status: Filter by status

    Returns:
        Coding queue with documents
    """
    # TODO: Replace with actual database query
    # Mock implementation
    return CodingQueueResponse(
        uncoded=[],
        in_progress=[],
        coded=[],
        total=0
    )


@router.get(
    "/documents/{document_id}/suggestions",
    response_model=CodingSuggestionsResponse,
    summary="Get AI coding suggestions",
    description="""
    Get AI-suggested ICD-10 codes for document.

    Uses CogStack-ModelServe medcat_icd10 model (mock implementation in development).
    """
)
async def get_coding_suggestions(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ICD10ExtractionService, Depends(get_icd10_service)]
) -> CodingSuggestionsResponse:
    """Get AI coding suggestions

    Args:
        document_id: Document ID
        current_user: Authenticated user
        service: ICD-10 extraction service

    Returns:
        AI-suggested codes with evidence

    Raises:
        HTTPException: 404 if document not found
    """
    try:
        # TODO: Fetch document text from database
        # Mock implementation
        doc_text = "Patient has Type 2 Diabetes Mellitus and Essential Hypertension. Also diagnosed with Chronic Obstructive Pulmonary Disease (COPD)."

        # Extract codes
        suggestions = await service.extract_codes(doc_text)

        # Audit log
        audit_log(
            user_id=current_user.id,
            action="CODING_SUGGESTIONS_VIEWED",
            resource_type="document",
            resource_id=document_id,
            details={"suggestions_count": len(suggestions)}
        )

        return CodingSuggestionsResponse(
            document_id=document_id,
            suggestions=suggestions,
            total_suggestions=len(suggestions)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get coding suggestions: {str(e)}"
        )


@router.post(
    "/documents/{document_id}/codes",
    response_model=AssignCodesResponse,
    summary="Assign codes to document",
    description="""
    Assign ICD-10 codes to document.

    Validates codes and creates audit log.
    """,
    status_code=status.HTTP_201_CREATED
)
async def assign_codes(
    document_id: UUID,
    request: AssignCodesRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> AssignCodesResponse:
    """Assign codes to document

    Args:
        document_id: Document ID
        request: Codes to assign
        current_user: Authenticated user

    Returns:
        Assignment result

    Raises:
        HTTPException: 404 if document not found, 400 if validation fails
    """
    try:
        # TODO: Validate codes exist in ICD-10 library
        # TODO: Check for duplicate assignments
        # TODO: Store in database

        # Audit log
        audit_log_id = UUID(audit_log(
            user_id=current_user.id,
            action="CODES_ASSIGNED",
            resource_type="document",
            resource_id=document_id,
            details={
                "codes": [c.code for c in request.codes],
                "sources": [c.source.value for c in request.codes]
            }
        ))

        return AssignCodesResponse(
            document_id=document_id,
            codes_assigned=len(request.codes),
            validation_errors=[],
            audit_log_id=audit_log_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign codes: {str(e)}"
        )


@router.get(
    "/icd10/search",
    response_model=ICD10SearchResponse,
    summary="Search ICD-10 library",
    description="Search ICD-10-CM codes (autocomplete for manual entry)"
)
async def search_icd10(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    current_user: Annotated[User, Depends(get_current_user)] = Depends(get_current_user)
) -> ICD10SearchResponse:
    """Search ICD-10 library

    Args:
        q: Search query
        limit: Max results
        current_user: Authenticated user

    Returns:
        Matching codes
    """
    # TODO: Replace with actual database search
    # Mock implementation
    mock_results = [
        ICD10Code(
            code="E11.9",
            description="Type 2 diabetes mellitus without complications",
            category="E08-E13: Diabetes mellitus"
        ),
        ICD10Code(
            code="E10.9",
            description="Type 1 diabetes mellitus without complications",
            category="E08-E13: Diabetes mellitus"
        )
    ]

    return ICD10SearchResponse(
        results=mock_results if "diabetes" in q.lower() else [],
        total=len(mock_results) if "diabetes" in q.lower() else 0
    )
