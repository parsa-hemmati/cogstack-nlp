"""CDS Guidelines API Endpoints.

Provides endpoints for managing clinical decision support guidelines from
authoritative sources (ADA, AHA, USPSTF, NICE).
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.services.cds.guidelines_service import GuidelinesService
from app.schemas.cds import (
    CDSGuidelineCreate,
    CDSGuidelineUpdate,
    CDSGuidelineResponse,
    CDSGuidelineListResponse,
    CDSGuidelineSearchRequest,
)
from app.services.audit_logger import audit_logger


router = APIRouter(prefix="/cds/guidelines", tags=["cds-guidelines"])


@router.get("", response_model=CDSGuidelineListResponse)
async def list_guidelines(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
):
    """List all CDS guidelines with pagination.

    Returns guidelines ordered by evidence level (A > B > C) and last_updated (desc).

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        db: Database session
        current_user: Authenticated user with clinician/researcher/admin role

    Returns:
        Paginated list of CDS guidelines
    """
    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_GUIDELINES_LIST",
        resource_type="cds_guidelines",
        details={"page": page, "page_size": page_size}
    )

    # Get guidelines
    guidelines, total = await GuidelinesService.list_guidelines(
        db=db,
        page=page,
        page_size=page_size
    )

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return CDSGuidelineListResponse(
        items=[CDSGuidelineResponse.model_validate(g) for g in guidelines],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/search", response_model=CDSGuidelineListResponse)
async def search_guidelines(
    condition_code: Optional[str] = Query(None, description="Filter by condition code (ICD-10 or SNOMED CT)"),
    guideline_source: Optional[str] = Query(None, description="Filter by source (ADA, AHA, USPSTF, NICE)"),
    evidence_level: Optional[str] = Query(None, description="Filter by evidence level (A, B, C)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
):
    """Search CDS guidelines with filters.

    Filter by condition code, guideline source, and/or evidence level.
    Results are ordered by evidence level (A > B > C) and last_updated (desc).

    Args:
        condition_code: ICD-10 or SNOMED CT condition code
        guideline_source: Guideline source (ADA, AHA, USPSTF, NICE)
        evidence_level: Evidence level (A, B, C)
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of matching guidelines
    """
    # Build search request
    search_params = CDSGuidelineSearchRequest(
        condition_code=condition_code,
        guideline_source=guideline_source,
        evidence_level=evidence_level,
        page=page,
        page_size=page_size
    )

    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_GUIDELINES_SEARCH",
        resource_type="cds_guidelines",
        details=search_params.model_dump(exclude_none=True)
    )

    # Search guidelines
    guidelines, total = await GuidelinesService.search_guidelines(
        db=db,
        search_params=search_params
    )

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return CDSGuidelineListResponse(
        items=[CDSGuidelineResponse.model_validate(g) for g in guidelines],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{guideline_id}", response_model=CDSGuidelineResponse)
async def get_guideline(
    guideline_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("clinician", "researcher", "admin")),
):
    """Get a specific CDS guideline by ID.

    Args:
        guideline_id: Guideline UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        CDS guideline details

    Raises:
        HTTPException: 404 if guideline not found
    """
    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_GUIDELINE_VIEW",
        resource_type="cds_guidelines",
        resource_id=str(guideline_id)
    )

    # Get guideline
    guideline = await GuidelinesService.get_guideline_by_id(db=db, guideline_id=guideline_id)

    if not guideline:
        raise HTTPException(status_code=404, detail="Guideline not found")

    return CDSGuidelineResponse.model_validate(guideline)


@router.post("", response_model=CDSGuidelineResponse, status_code=201)
async def create_guideline(
    guideline_data: CDSGuidelineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),  # Only admins can create guidelines
):
    """Create a new CDS guideline.

    Requires admin role. Used for loading guidelines from authoritative sources.

    Args:
        guideline_data: Guideline creation data
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Created guideline

    Raises:
        HTTPException: 400 if guideline already exists (duplicate source/name/condition)
    """
    try:
        guideline = await GuidelinesService.create_guideline(
            db=db,
            guideline_data=guideline_data
        )

        # Audit log
        await audit_logger.log(
            db=db,
            user_id=current_user.id,
            action="CDS_GUIDELINE_CREATE",
            resource_type="cds_guidelines",
            resource_id=str(guideline.id),
            details={"guideline_source": guideline.guideline_source, "guideline_name": guideline.guideline_name}
        )

        return CDSGuidelineResponse.model_validate(guideline)

    except Exception as e:
        # Likely unique constraint violation
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Guideline already exists for this source/name/condition combination"
            )
        raise


@router.put("/{guideline_id}", response_model=CDSGuidelineResponse)
async def update_guideline(
    guideline_id: UUID,
    guideline_data: CDSGuidelineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update a CDS guideline.

    Requires admin role.

    Args:
        guideline_id: Guideline UUID
        guideline_data: Update data
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Updated guideline

    Raises:
        HTTPException: 404 if guideline not found
    """
    guideline = await GuidelinesService.update_guideline(
        db=db,
        guideline_id=guideline_id,
        guideline_data=guideline_data
    )

    if not guideline:
        raise HTTPException(status_code=404, detail="Guideline not found")

    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_GUIDELINE_UPDATE",
        resource_type="cds_guidelines",
        resource_id=str(guideline_id),
        details=guideline_data.model_dump(exclude_unset=True)
    )

    return CDSGuidelineResponse.model_validate(guideline)


@router.delete("/{guideline_id}", status_code=204)
async def delete_guideline(
    guideline_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Delete a CDS guideline.

    Requires admin role.

    Args:
        guideline_id: Guideline UUID
        db: Database session
        current_user: Authenticated admin user

    Raises:
        HTTPException: 404 if guideline not found
    """
    deleted = await GuidelinesService.delete_guideline(db=db, guideline_id=guideline_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Guideline not found")

    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_GUIDELINE_DELETE",
        resource_type="cds_guidelines",
        resource_id=str(guideline_id)
    )

    return None
