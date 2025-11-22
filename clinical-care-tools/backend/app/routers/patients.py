"""
Patient Router

API endpoints for patient management, search, and timeline generation.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.patient import (
    PatientResponse, PatientListResponse, PatientSearchRequest,
    PatientTimelineResponse, TimelineEvent, PatientStatistics,
    PatientAggregationRequest, PatientMergeRequest, PatientAggregatedData
)
from app.schemas.document import DocumentResponse
from app.services.patient_service import PatientService
from app.services.audit_service import AuditService
from app.services.phi_extraction_service import PHIExtractionService
from app.services.phi_classifier import PHIClassifier

router = APIRouter(
    prefix="/api/v1/patients",
    tags=["patients"]
)


async def get_patient_service(db: AsyncSession = Depends(get_async_db)) -> PatientService:
    """Get patient service instance."""
    audit_service = AuditService(db)
    phi_classifier = PHIClassifier()
    phi_extraction_service = PHIExtractionService(db, phi_classifier, audit_service)
    return PatientService(db, audit_service, phi_extraction_service)


@router.get("/", response_model=PatientListResponse)
async def search_patients(
    query: Optional[str] = Query(None, description="General search query"),
    nhs_number: Optional[str] = Query(None, description="NHS number search"),
    mrn: Optional[str] = Query(None, description="MRN search"),
    last_name: Optional[str] = Query(None, description="Last name search"),
    postcode: Optional[str] = Query(None, description="Postcode search"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service)
) -> PatientListResponse:
    """
    Search for patients with various criteria.

    Supports searching by:
    - NHS number (exact match)
    - MRN (exact match)
    - Last name (partial match)
    - Postcode (exact match)
    - General query (searches across multiple fields)

    Args:
        query: General search query
        nhs_number: NHS number to search
        mrn: Medical record number to search
        last_name: Last name to search
        postcode: Postcode to search
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        service: Patient service

    Returns:
        Paginated list of patients
    """
    patients, total = await service.search_patients(
        query=query,
        nhs_number=nhs_number,
        mrn=mrn,
        last_name=last_name,
        postcode=postcode,
        page=page,
        page_size=page_size
    )

    return PatientListResponse(
        patients=[PatientResponse.model_validate(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service)
) -> PatientResponse:
    """
    Get patient details by ID.

    This operation is audit logged as it accesses PHI.

    Args:
        patient_id: Patient ID
        current_user: Authenticated user
        service: Patient service

    Returns:
        Patient details

    Raises:
        HTTPException: 404 if patient not found
    """
    patient = await service.get_patient(
        patient_id=patient_id,
        user_id=current_user.id
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}/timeline", response_model=PatientTimelineResponse)
async def get_patient_timeline(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service)
) -> PatientTimelineResponse:
    """
    Get patient clinical timeline.

    Generates a timeline of clinical events from all documents
    associated with the patient, including:
    - Document uploads
    - Diagnoses and conditions
    - Medications
    - Procedures
    - Lab results

    Args:
        patient_id: Patient ID
        current_user: Authenticated user
        service: Patient service

    Returns:
        Patient timeline with events

    Raises:
        HTTPException: 404 if patient not found
    """
    patient = await service.get_patient(
        patient_id=patient_id,
        user_id=current_user.id
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    events = await service.get_patient_timeline(
        patient_id=patient_id,
        user_id=current_user.id
    )

    timeline_events = [TimelineEvent(**event) for event in events]

    return PatientTimelineResponse(
        patient_id=patient_id,
        events=timeline_events,
        total_events=len(timeline_events)
    )


@router.get("/{patient_id}/documents", response_model=list[DocumentResponse])
async def get_patient_documents(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service)
) -> list[DocumentResponse]:
    """
    Get all documents associated with a patient.

    Args:
        patient_id: Patient ID
        current_user: Authenticated user
        service: Patient service

    Returns:
        List of documents for the patient

    Raises:
        HTTPException: 404 if patient not found
    """
    patient = await service.get_patient(
        patient_id=patient_id,
        user_id=current_user.id
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    documents = await service.get_patient_documents(patient_id)

    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{patient_id}/statistics", response_model=PatientStatistics)
async def get_patient_statistics(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service)
) -> PatientStatistics:
    """
    Get statistics for a patient.

    Provides aggregated statistics including:
    - Document count
    - Entity counts (PHI and clinical)
    - Unique conditions
    - Confidence score

    Args:
        patient_id: Patient ID
        current_user: Authenticated user
        service: Patient service

    Returns:
        Patient statistics

    Raises:
        HTTPException: 404 if patient not found
    """
    stats = await service.calculate_patient_statistics(patient_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    return PatientStatistics(**stats)


@router.post("/aggregate", response_model=PatientResponse)
async def aggregate_patient_from_document(
    request: PatientAggregationRequest,
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service)
) -> PatientResponse:
    """
    Create or update patient record from document.

    Extracts patient identifiers from document and matches
    to existing patient or creates new record.

    Args:
        request: Aggregation request with document ID
        current_user: Authenticated user
        service: Patient service

    Returns:
        Created or updated patient record

    Raises:
        HTTPException: 404 if document not found, 400 if no identifiers found
    """
    patient = await service.aggregate_patient_from_document(
        document_id=request.document_id,
        user_id=current_user.id
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No patient identifiers found in document"
        )

    return PatientResponse.model_validate(patient)


@router.post("/merge", status_code=status.HTTP_204_NO_CONTENT)
async def merge_duplicate_patients(
    request: PatientMergeRequest,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_role(["admin", "data_steward"])),
    service: PatientService = Depends(get_patient_service)
) -> None:
    """
    Merge duplicate patient records.

    Combines data from duplicate patient into primary patient
    and deletes the duplicate. Requires admin or data_steward role.

    Args:
        request: Merge request with patient IDs
        current_user: Authenticated user
        service: Patient service

    Raises:
        HTTPException: 404 if patients not found, 500 if merge fails
    """
    success = await service.merge_patients(
        primary_patient_id=request.primary_patient_id,
        duplicate_patient_id=request.duplicate_patient_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to merge patients"
        )


@router.get("/{patient_id}/aggregated", response_model=PatientAggregatedData)
async def get_patient_aggregated_data(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service),
    phi_extraction_service: PHIExtractionService = Depends(
        lambda db: PHIExtractionService(db, PHIClassifier(), AuditService(db))
    )
) -> PatientAggregatedData:
    """
    Get aggregated data for a patient across all documents.

    Provides comprehensive view including:
    - All identifiers
    - Demographics
    - Contact information
    - Clinical concepts with frequency
    - Important dates

    Args:
        patient_id: Patient ID
        current_user: Authenticated user
        service: Patient service
        phi_extraction_service: PHI extraction service

    Returns:
        Aggregated patient data

    Raises:
        HTTPException: 404 if patient not found
    """
    patient = await service.get_patient(
        patient_id=patient_id,
        user_id=current_user.id
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    aggregated = await phi_extraction_service.aggregate_patient_data(patient_id)

    if not aggregated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No aggregated data available"
        )

    return PatientAggregatedData(**aggregated)