"""Alert Management API endpoints for Sprint 7 - Automated Alerting.

Provides REST API for managing alert rules, triggered alerts, and notifications.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.alerting.alert_manager import AlertManager
from app.schemas.alerting.alert_rule import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertRuleVersionResponse,
    RuleTestRequest,
    RuleTestResponse,
)
from app.schemas.alerting.triggered_alert import (
    TriggeredAlertResponse,
    AlertAcknowledgeRequest,
    AlertDismissRequest,
    AlertSnoozeRequest,
    BulkAcknowledgeRequest,
    BulkAcknowledgeResponse,
    AlertListResponse,
)
from app.schemas.alerting.notification import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationStatsResponse,
)
from app.schemas.alerting.statistics import AlertStatisticsResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def get_alert_manager(db: Session = Depends(get_db)) -> AlertManager:
    """Dependency to get AlertManager instance."""
    return AlertManager(db)


# ==================== Alert Rules ====================

@router.post(
    "/rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert rule",
    description="Create a new alert rule with conditions, severity, and notification settings."
)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> AlertRuleResponse:
    """Create a new alert rule."""
    rule = await manager.create_rule(
        name=rule_data.name,
        description=rule_data.description,
        conditions=rule_data.conditions.model_dump(),
        severity=rule_data.severity,
        notification_channels=rule_data.notification_channels,
        escalation_minutes=rule_data.escalation_minutes,
        enabled=rule_data.enabled,
        created_by=current_user.id
    )
    return AlertRuleResponse.model_validate(rule)


@router.get(
    "/rules",
    response_model=List[AlertRuleResponse],
    summary="List alert rules",
    description="Get a list of alert rules with optional filtering."
)
async def list_alert_rules(
    enabled_only: bool = Query(False, description="Only return enabled rules"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> List[AlertRuleResponse]:
    """List all alert rules."""
    rules = await manager.list_rules(
        enabled_only=enabled_only,
        severity=severity,
        limit=limit,
        offset=offset
    )
    return [AlertRuleResponse.model_validate(r) for r in rules]


@router.get(
    "/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Get alert rule by ID"
)
async def get_alert_rule(
    rule_id: UUID,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> AlertRuleResponse:
    """Get a specific alert rule."""
    rule = await manager.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    return AlertRuleResponse.model_validate(rule)


@router.put(
    "/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Update alert rule"
)
async def update_alert_rule(
    rule_id: UUID,
    rule_data: AlertRuleUpdate,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> AlertRuleResponse:
    """Update an existing alert rule."""
    update_dict = rule_data.model_dump(exclude_unset=True, exclude={"change_reason"})

    # Convert conditions if provided
    if "conditions" in update_dict and update_dict["conditions"]:
        update_dict["conditions"] = rule_data.conditions.model_dump()

    rule = await manager.update_rule(
        rule_id=rule_id,
        updated_by=current_user.id,
        change_reason=rule_data.change_reason,
        **update_dict
    )

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    return AlertRuleResponse.model_validate(rule)


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert rule"
)
async def delete_alert_rule(
    rule_id: UUID,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
):
    """Delete an alert rule."""
    if not await manager.delete_rule(rule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )


@router.get(
    "/rules/{rule_id}/versions",
    response_model=List[AlertRuleVersionResponse],
    summary="Get rule version history"
)
async def get_rule_versions(
    rule_id: UUID,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> List[AlertRuleVersionResponse]:
    """Get version history for an alert rule."""
    versions = await manager.get_rule_versions(rule_id)
    return [AlertRuleVersionResponse.model_validate(v) for v in versions]


@router.post(
    "/rules/{rule_id}/test",
    response_model=RuleTestResponse,
    summary="Test a rule against sample data"
)
async def test_alert_rule(
    rule_id: UUID,
    test_request: RuleTestRequest,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> RuleTestResponse:
    """Test an alert rule against sample data without triggering."""
    result = await manager.rules_engine.test_rule(rule_id, test_request.test_data)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return RuleTestResponse(**result)


# ==================== Triggered Alerts ====================

@router.get(
    "/",
    response_model=AlertListResponse,
    summary="List triggered alerts",
    description="Get a list of triggered alerts with optional filtering."
)
async def list_triggered_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    start_date: Optional[datetime] = Query(None, description="Filter by triggered date start"),
    end_date: Optional[datetime] = Query(None, description="Filter by triggered date end"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> AlertListResponse:
    """List triggered alerts with filtering."""
    alerts = await manager.list_alerts(
        status=status,
        severity=severity,
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit + 1,  # Get one extra to check has_more
        offset=offset
    )

    has_more = len(alerts) > limit
    if has_more:
        alerts = alerts[:limit]

    # Enrich with rule name
    alert_responses = []
    for alert in alerts:
        response = TriggeredAlertResponse.model_validate(alert)
        if alert.rule:
            response.rule_name = alert.rule.name
        alert_responses.append(response)

    return AlertListResponse(
        alerts=alert_responses,
        total=len(alerts),  # Would be total count from DB in production
        limit=limit,
        offset=offset,
        has_more=has_more
    )


@router.get(
    "/{alert_id}",
    response_model=TriggeredAlertResponse,
    summary="Get triggered alert by ID"
)
async def get_triggered_alert(
    alert_id: UUID,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> TriggeredAlertResponse:
    """Get a specific triggered alert."""
    alert = await manager.get_alert(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    response = TriggeredAlertResponse.model_validate(alert)
    if alert.rule:
        response.rule_name = alert.rule.name
    return response


@router.post(
    "/{alert_id}/acknowledge",
    response_model=TriggeredAlertResponse,
    summary="Acknowledge an alert"
)
async def acknowledge_alert(
    alert_id: UUID,
    ack_request: AlertAcknowledgeRequest,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> TriggeredAlertResponse:
    """Acknowledge a triggered alert."""
    alert = await manager.acknowledge_alert(
        alert_id=alert_id,
        user_id=current_user.id,
        notes=ack_request.notes
    )

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return TriggeredAlertResponse.model_validate(alert)


@router.post(
    "/{alert_id}/dismiss",
    response_model=TriggeredAlertResponse,
    summary="Dismiss an alert"
)
async def dismiss_alert(
    alert_id: UUID,
    dismiss_request: AlertDismissRequest,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> TriggeredAlertResponse:
    """Dismiss a triggered alert."""
    alert = await manager.dismiss_alert(
        alert_id=alert_id,
        user_id=current_user.id,
        notes=dismiss_request.notes
    )

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return TriggeredAlertResponse.model_validate(alert)


@router.post(
    "/{alert_id}/snooze",
    response_model=TriggeredAlertResponse,
    summary="Snooze an alert"
)
async def snooze_alert(
    alert_id: UUID,
    snooze_request: AlertSnoozeRequest,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> TriggeredAlertResponse:
    """Snooze a triggered alert for specified duration."""
    alert = await manager.snooze_alert(
        alert_id=alert_id,
        snooze_minutes=snooze_request.snooze_minutes
    )

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return TriggeredAlertResponse.model_validate(alert)


@router.post(
    "/bulk-acknowledge",
    response_model=BulkAcknowledgeResponse,
    summary="Bulk acknowledge alerts"
)
async def bulk_acknowledge_alerts(
    bulk_request: BulkAcknowledgeRequest,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> BulkAcknowledgeResponse:
    """Acknowledge multiple alerts at once."""
    acknowledged_count = await manager.bulk_acknowledge(
        alert_ids=bulk_request.alert_ids,
        user_id=current_user.id,
        notes=bulk_request.notes
    )

    # Calculate failed IDs
    failed_ids = []
    for aid in bulk_request.alert_ids:
        alert = await manager.get_alert(aid)
        if alert is None or alert.status != "acknowledged":
            failed_ids.append(aid)

    return BulkAcknowledgeResponse(
        acknowledged_count=acknowledged_count,
        failed_ids=failed_ids
    )


# ==================== Statistics ====================

@router.get(
    "/statistics",
    response_model=AlertStatisticsResponse,
    summary="Get alert statistics"
)
async def get_alert_statistics(
    start_date: Optional[datetime] = Query(None, description="Start of date range"),
    end_date: Optional[datetime] = Query(None, description="End of date range"),
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> AlertStatisticsResponse:
    """Get alert statistics for a time period."""
    stats = await manager.get_alert_statistics(start_date, end_date)
    return AlertStatisticsResponse(**stats)


@router.get(
    "/notifications/stats",
    response_model=NotificationStatsResponse,
    summary="Get notification delivery statistics"
)
async def get_notification_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> NotificationStatsResponse:
    """Get notification delivery statistics."""
    stats = await manager.notification_service.get_notification_stats(start_date, end_date)
    # stats = {} # Placeholder until NotificationService is refactored
    return NotificationStatsResponse(**stats)


# ==================== User Preferences ====================

@router.get(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Get current user's notification preferences"
)
async def get_notification_preferences(
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> NotificationPreferencesResponse:
    """Get notification preferences for the current user."""
    prefs = await manager.get_user_preferences(current_user.id)

    if not prefs:
        # Create default preferences
        prefs = await manager.update_user_preferences(current_user.id)

    return NotificationPreferencesResponse.model_validate(prefs)


@router.put(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Update notification preferences"
)
async def update_notification_preferences(
    prefs_data: NotificationPreferencesUpdate,
    manager: AlertManager = Depends(get_alert_manager),
    current_user: User = Depends(get_current_user)
) -> NotificationPreferencesResponse:
    """Update notification preferences for the current user."""
    from datetime import time

    update_dict = prefs_data.model_dump(exclude_unset=True)

    # Convert time strings to time objects
    if "quiet_hours_start" in update_dict and update_dict["quiet_hours_start"]:
        h, m = map(int, update_dict["quiet_hours_start"].split(":"))
        update_dict["quiet_hours_start"] = time(h, m)
    if "quiet_hours_end" in update_dict and update_dict["quiet_hours_end"]:
        h, m = map(int, update_dict["quiet_hours_end"].split(":"))
        update_dict["quiet_hours_end"] = time(h, m)

    prefs = await manager.update_user_preferences(current_user.id, **update_dict)
    return NotificationPreferencesResponse.model_validate(prefs)
