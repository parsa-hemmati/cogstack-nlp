"""
Patient Management API Endpoints

Provides individual patient retrieval and management operations.
Complements patient_search.py which handles cohort search by concepts.

PRD Requirement: Sprint 1 - GET /api/v1/patients/{mrn}

Cherry-picked from: origin/development:clinical-care-tools/backend/app/api/v1/patients.py
Adapted to match existing model structure (nhs_number as identifier)
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import (
    PatientDetailResponse,
    PatientListResponse,
    PatientResponse,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get(
    "/{mrn}",
    response_model=PatientDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient by MRN/NHS number",
    description="""
    Retrieve a specific patient by their MRN (NHS number).

    **Authorization**: Requires one of: clinician, researcher, admin

    **HIPAA Compliance**: All patient access is logged to audit trail.

    **Response**: Full patient details including document count and timeline.
    """
)
async def get_patient_by_mrn(
    mrn: str,
    request: Request,
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
    db: AsyncSession = Depends(get_db),
) -> PatientDetailResponse:
    """
    Get patient by MRN (Medical Record Number / NHS Number).

    This endpoint retrieves a single patient record by their NHS number,
    including aggregated information from all linked documents.

    Args:
        mrn: NHS number (10 digits) or internal UUID
        request: FastAPI request (for IP logging)
        current_user: Authenticated user with required role
        db: Database session

    Returns:
        PatientDetailResponse with full patient details

    Raises:
        HTTPException 400: Invalid MRN format
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 403: Forbidden (insufficient role permissions)
        HTTPException 404: Patient not found

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/patients/1234567890" \\
          -H "Authorization: Bearer $TOKEN"
        ```

    Response:
        ```json
        {
          "id": "uuid-here",
          "nhs_number": "1234567890",
          "full_name": "John Smith",
          "date_of_birth": "1950-03-15",
          "age": 74,
          "address": "123 Main Street, London",
          "first_seen_at": "2020-01-15T10:30:00Z",
          "last_seen_at": "2024-11-20T14:45:00Z",
          "document_count": 25,
          "created_at": "2020-01-15T10:30:00Z",
          "updated_at": "2024-11-20T14:45:00Z",
          "nhs_number_masked": "XXX-XXX-7890"
        }
        ```
    """
    audit_service = AuditService()

    try:
        # Try to find by NHS number first
        stmt = select(Patient).where(Patient.nhs_number == mrn)
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()

        # If not found by NHS number, try UUID
        if not patient:
            try:
                patient_uuid = UUID(mrn)
                stmt = select(Patient).where(Patient.id == patient_uuid)
                result = await db.execute(stmt)
                patient = result.scalar_one_or_none()
            except ValueError:
                # Not a valid UUID, keep patient as None
                pass

        if not patient:
            logger.warning(
                f"Patient not found: mrn={mrn}, user={current_user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with MRN/ID '{mrn}' not found"
            )

        # Log audit trail (HIPAA compliance - PHI access)
        try:
            await audit_service.log_action(
                db=db,
                user=current_user,
                action="VIEW_PATIENT",
                resource_type="patient",
                resource_id=str(patient.id),
                details={
                    "nhs_number_last4": patient.nhs_number[-4:] if patient.nhs_number else None,
                    "ip_address": request.client.host if request.client else None,
                },
            )
        except Exception as audit_error:
            # Log failure but don't abort the request
            logger.error(
                f"Audit logging failed for patient view: {audit_error}",
                exc_info=True,
                extra={
                    "user_id": current_user.id,
                    "patient_id": str(patient.id),
                }
            )

        logger.info(
            f"Patient retrieved: user={current_user.username}, "
            f"patient_id={patient.id}, nhs_last4={patient.nhs_number[-4:]}"
        )

        # Build response with computed fields
        response_data = {
            "id": patient.id,
            "nhs_number": patient.nhs_number,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "address": patient.address,
            "first_seen_at": patient.first_seen_at,
            "last_seen_at": patient.last_seen_at,
            "document_count": patient.document_count,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
            "age": patient.get_age(),
            "nhs_number_masked": f"XXX-XXX-{patient.nhs_number[-4:]}" if patient.nhs_number else None,
        }

        return PatientDetailResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve patient: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient. Please try again."
        )


@router.get(
    "",
    response_model=PatientListResponse,
    status_code=status.HTTP_200_OK,
    summary="List patients (paginated)",
    description="""
    List all patients with pagination.

    **Authorization**: Requires admin role (PHI listing is sensitive)

    **Note**: For patient search by clinical concepts, use POST /api/v1/patients/search
    """
)
async def list_patients(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> PatientListResponse:
    """
    List all patients (admin only, paginated).

    This endpoint lists patients for administrative purposes.
    For clinical search by concepts, use POST /api/v1/patients/search instead.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        current_user: Authenticated admin user
        db: Database session

    Returns:
        Paginated list of patients

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 403: Forbidden (non-admin user)
    """
    try:
        # Get total count
        count_stmt = select(func.count(Patient.id))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            select(Patient)
            .order_by(Patient.last_seen_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        patients = result.scalars().all()

        # Build response
        patient_responses = []
        for patient in patients:
            patient_responses.append(
                PatientResponse(
                    id=patient.id,
                    nhs_number=patient.nhs_number,
                    full_name=patient.full_name,
                    date_of_birth=patient.date_of_birth,
                    address=patient.address,
                    first_seen_at=patient.first_seen_at,
                    last_seen_at=patient.last_seen_at,
                    document_count=patient.document_count,
                    created_at=patient.created_at,
                    updated_at=patient.updated_at,
                    age=patient.get_age(),
                )
            )

        logger.info(
            f"Patient list retrieved: user={current_user.username}, "
            f"page={page}, total={total}"
        )

        return PatientListResponse(
            patients=patient_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list patients: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list patients. Please try again."
        )
