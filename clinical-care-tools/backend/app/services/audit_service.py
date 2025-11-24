"""
Audit logging service.

Provides functions to log all user actions for HIPAA compliance.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: str,
    username: str,
    action: str,
    resource_type: str,
    resource_id: str,
    ip_address: str,
    user_agent: str,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Log a user action to the audit trail.

    Args:
        db: Database session
        user_id: ID of user performing action (WHO)
        username: Username of user (WHO)
        action: Action being performed (WHAT) - e.g., "VIEW_PATIENT", "UPDATE_DOCUMENT"
        resource_type: Type of resource (WHAT) - e.g., "patient", "document", "user"
        resource_id: ID of specific resource (WHAT)
        ip_address: IP address of request (WHERE)
        user_agent: User-Agent header (WHERE)
        details: Optional additional context as JSONB

    Returns:
        Created AuditLog entry

    Example:
        await log_action(
            db,
            user_id="user-123",
            username="john_doe",
            action="VIEW_PATIENT",
            resource_type="patient",
            resource_id="patient-456",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            details={"reason": "routine checkup", "duration_seconds": 45}
        )

    Common Actions:
        Authentication: LOGIN, LOGOUT, REFRESH_TOKEN
        Patient Data: VIEW_PATIENT, UPDATE_PATIENT, DELETE_PATIENT, EXPORT_PATIENT
        Documents: VIEW_DOCUMENT, CREATE_DOCUMENT, UPDATE_DOCUMENT, DELETE_DOCUMENT
        Users: VIEW_USER, CREATE_USER, UPDATE_USER, DELETE_USER
        Break Glass: BREAK_GLASS_ACCESS
        Admin: CONFIG_CHANGE, SYSTEM_SETTING_UPDATE
    """
    log_entry = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )

    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    return log_entry


async def get_audit_logs_for_user(
    db: AsyncSession,
    user_id: str,
    limit: int = 100
) -> List[AuditLog]:
    """
    Get audit logs for a specific user.

    Args:
        db: Database session
        user_id: User ID to query
        limit: Maximum number of logs to return (default 100)

    Returns:
        List of AuditLog entries, ordered by timestamp descending (newest first)

    Example:
        logs = await get_audit_logs_for_user(db, "user-123", limit=50)
        for log in logs:
            print(f"{log.timestamp}: {log.action} on {log.resource_type}")
    """
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_audit_logs_for_resource(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
    limit: int = 100
) -> List[AuditLog]:
    """
    Get audit logs for a specific resource.

    Args:
        db: Database session
        resource_type: Type of resource (e.g., "patient", "document")
        resource_id: Specific resource ID
        limit: Maximum number of logs to return (default 100)

    Returns:
        List of AuditLog entries, ordered by timestamp descending (newest first)

    Example:
        logs = await get_audit_logs_for_resource(
            db, "patient", "patient-456", limit=20
        )
        for log in logs:
            print(f"{log.username} performed {log.action} at {log.timestamp}")
    """
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        )
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_audit_logs_by_action(
    db: AsyncSession,
    action: str,
    limit: int = 100
) -> List[AuditLog]:
    """
    Get audit logs for a specific action type.

    Args:
        db: Database session
        action: Action to query (e.g., "VIEW_PATIENT", "DELETE_USER")
        limit: Maximum number of logs to return (default 100)

    Returns:
        List of AuditLog entries, ordered by timestamp descending (newest first)

    Example:
        # Find all break-glass access events
        logs = await get_audit_logs_by_action(db, "BREAK_GLASS_ACCESS")
        for log in logs:
            print(f"Break glass by {log.username} at {log.timestamp}")
    """
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.action == action)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_audit_logs_by_timerange(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    limit: int = 1000
) -> List[AuditLog]:
    """
    Get audit logs within a time range.

    Args:
        db: Database session
        start_time: Start of time range (inclusive)
        end_time: End of time range (inclusive)
        limit: Maximum number of logs to return (default 1000)

    Returns:
        List of AuditLog entries, ordered by timestamp descending (newest first)

    Example:
        from datetime import datetime, timedelta
        start = datetime.utcnow() - timedelta(hours=24)
        end = datetime.utcnow()
        logs = await get_audit_logs_by_timerange(db, start, end)
    """
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time
        )
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def search_audit_logs(
    db: AsyncSession,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
) -> List[AuditLog]:
    """
    Search audit logs with multiple optional filters.

    Args:
        db: Database session
        user_id: Optional user ID filter
        action: Optional action filter
        resource_type: Optional resource type filter
        resource_id: Optional resource ID filter
        start_time: Optional start time filter
        end_time: Optional end time filter
        limit: Maximum number of logs to return (default 100)

    Returns:
        List of AuditLog entries matching filters, ordered by timestamp descending

    Example:
        # Find all patient views by specific user in last 24 hours
        logs = await search_audit_logs(
            db,
            user_id="user-123",
            action="VIEW_PATIENT",
            start_time=datetime.utcnow() - timedelta(hours=24)
        )
    """
    query = select(AuditLog)

    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    if start_time:
        query = query.where(AuditLog.timestamp >= start_time)
    if end_time:
        query = query.where(AuditLog.timestamp <= end_time)

    # Order and limit
    query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
