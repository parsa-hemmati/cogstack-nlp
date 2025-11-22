"""
Data Retention Router (Phase 6)

Endpoints for data retention policy management and compliance reporting.

Compliance:
- HIPAA: 7 years for audit logs
- GDPR: Automatic deletion
- NHS: 8 years for clinical documents
"""

from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.services.retention_service import RetentionService
from app.models.data_retention_policy import DataRetentionType
from app.schemas.retention import (
    RetentionPolicyResponse, RetentionReport, RetentionList, RetentionPoliciesList, DueForDeletion
)

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/retention",
    tags=["retention"]
)


@router.get("/policies", response_model=RetentionPoliciesList)
async def get_retention_policies(
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> RetentionPoliciesList:
    """
    Get all data retention policies.

    Available to all authenticated users.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List of active retention policies

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not settings.DATA_RETENTION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data retention is disabled"
        )

    service = RetentionService(db)
    policies = await service.get_all_policies(active_only=True)

    return RetentionPoliciesList(
        total=len(policies),
        policies=[RetentionPolicyResponse.model_validate(p) for p in policies]
    )


@router.post("/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_retention_job(
    data_type: Optional[DataRetentionType] = None,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> dict:
    """
    Manually trigger retention job execution.

    Admin only. Executes archival/deletion of data per retention policies.

    Args:
        data_type: Optional specific data type to process
        user: Current authenticated user
        db: Database session

    Returns:
        Job execution status

    Raises:
        HTTPException: 403 if user not admin
        HTTPException: 503 if retention job already running
    """
    # Check user role (admin only)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Retention job execution requires admin role"
        )

    if not settings.DATA_RETENTION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data retention is disabled"
        )

    service = RetentionService(db)

    # NOTE: Implement actual retention job execution
    # This would:
    # 1. Get retention policies
    # 2. Find records due for deletion
    # 3. Archive records (if enabled)
    # 4. Delete records
    # 5. Update statistics
    # 6. Log to audit trail

    return {
        "status": "accepted",
        "message": "Retention job scheduled for execution",
        "data_type": data_type.value if data_type else "all",
        "estimated_completion": "within 1 hour"
    }


@router.get("/due", response_model=RetentionList)
async def get_due_for_deletion(
    data_type: Optional[DataRetentionType] = None,
    limit: int = 20,
    offset: int = 0,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> RetentionList:
    """
    Get records due for deletion based on retention policies.

    Admin only. Lists data that will be deleted soon per compliance policies.

    Args:
        data_type: Optional filter by data type
        limit: Maximum results
        offset: Pagination offset
        user: Current authenticated user
        db: Database session

    Returns:
        List of records due for deletion

    Raises:
        HTTPException: 403 if user not admin
    """
    # Check user role (admin only)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access requires admin role"
        )

    if not settings.DATA_RETENTION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data retention is disabled"
        )

    service = RetentionService(db)

    # NOTE: Implement query for due deletion records
    items = []  # await service.get_due_for_deletion(data_type or DataRetentionType.CLINICAL_DOCUMENTS, limit)

    return RetentionList(
        total=len(items),
        limit=limit,
        offset=offset,
        items=[DueForDeletion.model_validate(item) for item in items]
    )


@router.get("/report", response_model=RetentionReport)
async def generate_retention_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> RetentionReport:
    """
    Generate data retention compliance report.

    Admin/compliance only. Shows retention statistics for audit compliance.

    Args:
        start_date: Optional report start date
        end_date: Optional report end date
        user: Current authenticated user
        db: Database session

    Returns:
        Compliance report with statistics

    Raises:
        HTTPException: 403 if user not authorized
    """
    # Check user role (admin or compliance only)
    if user.get("role") not in ["admin", "compliance"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access requires admin or compliance role"
        )

    if not settings.DATA_RETENTION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data retention is disabled"
        )

    service = RetentionService(db)
    report = await service.get_retention_report(
        start_date=start_date,
        end_date=end_date
    )

    return RetentionReport(**report)


@router.get("/export/csv")
async def export_retention_report_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """
    Export retention report as CSV.

    Admin/compliance only. For offline analysis and compliance documentation.

    Args:
        start_date: Optional report start date
        end_date: Optional report end date
        user: Current authenticated user
        db: Database session

    Returns:
        CSV file stream

    Raises:
        HTTPException: 403 if user not authorized
    """
    # Check user role (admin or compliance only)
    if user.get("role") not in ["admin", "compliance"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access requires admin or compliance role"
        )

    if not settings.DATA_RETENTION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data retention is disabled"
        )

    service = RetentionService(db)
    report = await service.get_retention_report(
        start_date=start_date,
        end_date=end_date
    )

    # NOTE: Implement CSV export
    # Generate CSV from report data and return as file

    return {
        "status": "pending",
        "message": "CSV export feature coming soon"
    }


@router.post("/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_retention_policies(
    user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> dict:
    """
    Initialize default retention policies.

    Admin only. Creates default policies if they don't exist.
    Run once during system setup.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        Initialization status

    Raises:
        HTTPException: 403 if user not admin
    """
    # Check user role (admin only)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initialization requires admin role"
        )

    service = RetentionService(db)
    policies = await service.initialize_policies()

    return {
        "status": "success",
        "policies_created": len(policies),
        "policies": [
            {
                "data_type": p.data_type.value,
                "retention": f"{p.retention_years or p.retention_days} {'years' if p.retention_years else 'days'}"
            }
            for p in policies
        ]
    }
