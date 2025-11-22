"""
Audit Log API Endpoints
HIPAA-compliant audit trail export and search
"""
import csv
import io
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.services.audit_service import audit_service


router = APIRouter()


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: str = Field(..., description="Audit log ID")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    details: Optional[dict] = Field(None, description="Additional details")
    timestamp: datetime = Field(..., description="Timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    success: str = Field(..., description="Success status")
    error_message: Optional[str] = Field(None, description="Error message")

    class Config:
        from_attributes = True


class AuditLogSearchResponse(BaseModel):
    """Audit log search results."""

    logs: List[AuditLogResponse] = Field(..., description="Audit log entries")
    total: int = Field(..., description="Total matching entries")
    limit: int = Field(..., description="Page limit")
    offset: int = Field(..., description="Page offset")


@router.get("/search", response_model=AuditLogSearchResponse)
@require_role("admin")
async def search_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    success: Optional[str] = Query(None, description="Filter by success status"),
    limit: int = Query(100, ge=1, le=1000, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> AuditLogSearchResponse:
    """
    Search audit logs with filters.

    **Admin only**

    Filters:
    - user_id: Filter by user
    - action: Filter by action (e.g., "DEIDENTIFY_NOTE")
    - resource_type: Filter by resource type (e.g., "deidentification_job")
    - resource_id: Filter by specific resource
    - start_date/end_date: Date range (ISO format)
    - success: Filter by success status

    Returns paginated results.
    """
    # Build filters
    filters = {
        "limit": limit,
        "offset": offset,
    }

    if user_id:
        filters["user_id"] = user_id
    if action:
        filters["action"] = action
    if resource_type:
        filters["resource_type"] = resource_type
    if resource_id:
        filters["resource_id"] = resource_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if success:
        filters["success"] = success

    # Search logs
    logs = await audit_service.search_audit_logs(db, filters)

    # Convert to response models
    log_responses = [
        AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id),
            username=log.username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            timestamp=log.timestamp,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            success=log.success,
            error_message=log.error_message,
        )
        for log in logs
    ]

    return AuditLogSearchResponse(
        logs=log_responses,
        total=len(log_responses),  # Would need count query for accurate total
        limit=limit,
        offset=offset,
    )


@router.get("/export")
@require_role("admin")
async def export_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    format: str = Query("csv", regex="^(csv|json)$", description="Export format (csv or json)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
) -> StreamingResponse:
    """
    Export audit logs for compliance review.

    **Admin only**

    Required:
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)

    Optional:
    - format: csv or json (default: csv)
    - user_id: Filter by user
    - action: Filter by action

    Returns:
    - CSV: Comma-separated values file
    - JSON: JSON array of audit log entries

    Security:
    - Admin-only access
    - No PHI in audit logs
    - Audit export is logged
    """
    # Validate date range
    try:
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
        )

    # Build filters
    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "limit": 10000,  # Max export limit
    }

    if user_id:
        filters["user_id"] = user_id
    if action:
        filters["action"] = action

    # Fetch logs
    logs = await audit_service.search_audit_logs(db, filters)

    # Log export action
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="EXPORT_AUDIT_LOGS",
        resource_type="audit_log",
        details={
            "start_date": start_date,
            "end_date": end_date,
            "format": format,
            "count": len(logs),
        },
    )

    # Export as CSV
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "timestamp",
                "user_id",
                "username",
                "action",
                "resource_type",
                "resource_id",
                "success",
                "ip_address",
                "details",
                "error_message",
            ]
        )
        writer.writeheader()

        for log in logs:
            writer.writerow({
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "user_id": str(log.user_id),
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id or "",
                "success": log.success,
                "ip_address": log.ip_address or "",
                "details": json.dumps(log.details) if log.details else "",
                "error_message": log.error_message or "",
            })

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{start_date}_{end_date}.csv"
            }
        )

    # Export as JSON
    else:
        log_data = [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "user_id": str(log.user_id),
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "success": log.success,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "details": log.details,
                "error_message": log.error_message,
            }
            for log in logs
        ]

        json_output = json.dumps(log_data, indent=2)

        return StreamingResponse(
            iter([json_output]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{start_date}_{end_date}.json"
            }
        )
