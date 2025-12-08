"""AlertManager - Facade for the alerting system.

Provides a unified interface for creating rules, evaluating conditions,
and managing alerts across the system.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func

from app.models.alerting.alert_rule import AlertRule, AlertRuleVersion
from app.models.alerting.triggered_alert import TriggeredAlert, AlertNotification
from app.models.alerting.notification_preferences import NotificationPreferences
from .rules_engine import AlertRulesEngine
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class AlertManager:
    """Facade for managing the alerting system.

    Provides high-level operations for:
    - Creating and managing alert rules
    - Evaluating data against rules
    - Managing triggered alerts (acknowledge, dismiss, snooze)
    - Retrieving alert history and statistics
    """

    def __init__(self, db: AsyncSession):
        """Initialize alert manager.

        Args:
            db: Database session
        """
        self.db = db
        self.rules_engine = AlertRulesEngine(db)
        self.notification_service = NotificationService(db)

    # ==================== Rule Management ====================

    async def create_rule(
        self,
        name: str,
        conditions: Dict[str, Any],
        severity: str,
        created_by: UUID,
        description: Optional[str] = None,
        notification_channels: Optional[List[str]] = None,
        escalation_minutes: Optional[int] = None,
        enabled: bool = True
    ) -> AlertRule:
        """Create a new alert rule.

        Args:
            name: Rule name
            conditions: JSON conditions structure
            severity: critical, high, medium, low
            created_by: User creating the rule
            description: Optional description
            notification_channels: Channels to notify (email, sms, in_app)
            escalation_minutes: Minutes before escalation
            enabled: Whether rule is active

        Returns:
            Created AlertRule
        """
        rule = AlertRule(
            name=name,
            description=description,
            conditions=conditions,
            severity=severity,
            notification_channels=notification_channels or ["in_app"],
            escalation_minutes=escalation_minutes,
            enabled=enabled,
            created_by=created_by
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(f"Created alert rule: {name} (id={rule.id})")
        return rule

    async def update_rule(
        self,
        rule_id: UUID,
        updated_by: UUID,
        change_reason: Optional[str] = None,
        **updates
    ) -> Optional[AlertRule]:
        """Update an existing alert rule.

        Creates a version record for audit trail.

        Args:
            rule_id: Rule to update
            updated_by: User making the update
            change_reason: Reason for the change
            **updates: Fields to update

        Returns:
            Updated rule or None if not found
        """
        rule = await self.get_rule(rule_id)
        if not rule:
            return None

        # Create version record before updating
        # Note: In async, simple counts are harder without a query, let's just get count
        result = await self.db.execute(
            select(func.count(AlertRuleVersion.id)).filter(AlertRuleVersion.rule_id == rule_id)
        )
        version_number = (result.scalar() or 0) + 1

        version = AlertRuleVersion(
            rule_id=rule.id,
            version=version_number,
            conditions=rule.conditions,  # Store old conditions
            changed_by=updated_by,
            change_reason=change_reason
        )
        self.db.add(version)

        # Apply updates
        allowed_fields = [
            "name", "description", "conditions", "severity",
            "notification_channels", "escalation_minutes", "enabled"
        ]
        for field, value in updates.items():
            if field in allowed_fields and hasattr(rule, field):
                setattr(rule, field, value)

        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(f"Updated alert rule: {rule.name} (version={version_number})")
        return rule

    async def delete_rule(self, rule_id: UUID) -> bool:
        """Delete an alert rule.

        Args:
            rule_id: Rule to delete

        Returns:
            True if deleted, False if not found
        """
        rule = await self.get_rule(rule_id)
        if not rule:
            return False

        await self.db.delete(rule)
        await self.db.commit()

        logger.info(f"Deleted alert rule: {rule.name}")
        return True

    async def get_rule(self, rule_id: UUID) -> Optional[AlertRule]:
        """Get a rule by ID.

        Args:
            rule_id: Rule ID

        Returns:
            AlertRule or None
        """
        result = await self.db.execute(select(AlertRule).filter(AlertRule.id == rule_id))
        return result.scalar_one_or_none()

    async def list_rules(
        self,
        enabled_only: bool = False,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlertRule]:
        """List alert rules with optional filtering.

        Args:
            enabled_only: Only return enabled rules
            severity: Filter by severity
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AlertRule objects
        """
        query = select(AlertRule)

        if enabled_only:
            query = query.filter(AlertRule.enabled == True)
        if severity:
            query = query.filter(AlertRule.severity == severity)

        # Order by newest first
        query = query.order_by(AlertRule.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_rule_versions(self, rule_id: UUID) -> List[AlertRuleVersion]:
        """Get version history for a rule.

        Args:
            rule_id: Rule ID

        Returns:
            List of AlertRuleVersion records
        """
        result = await self.db.execute(
            select(AlertRuleVersion)
            .filter(AlertRuleVersion.rule_id == rule_id)
            .order_by(desc(AlertRuleVersion.version))
        )
        return result.scalars().all()

    # ==================== Alert Evaluation ====================

    async def evaluate_and_notify(
        self,
        data: Dict[str, Any],
        patient_id: Optional[UUID] = None,
        notify_users: Optional[List[UUID]] = None
    ) -> List[TriggeredAlert]:
        """Evaluate data against rules and send notifications.

        Args:
            data: Data to evaluate
            patient_id: Optional patient ID
            notify_users: Specific users to notify (or use rule defaults)

        Returns:
            List of triggered alerts
        """
        # Evaluate rules
        triggered_alerts = await self.rules_engine.evaluate_rules(data, patient_id)

        if not triggered_alerts:
            return []

        # Send notifications for each triggered alert
        for alert in triggered_alerts:
            rule = await self.get_rule(alert.rule_id)
            if not rule:
                continue

            # Determine recipients
            if notify_users:
                recipient_ids = notify_users
            else:
                # Would get assigned users for the patient or default recipients
                recipient_ids = self._get_default_recipients(alert)

            # Build template data
            template_data = {
                "rule_name": rule.name,
                "description": rule.description,
            }

            # Send notifications
            await self.notification_service.send_notifications(
                alert, recipient_ids, template_data
            )

        await self.db.commit()
        return triggered_alerts

    def _get_default_recipients(self, alert: TriggeredAlert) -> List[UUID]:
        """Get default notification recipients for an alert.

        In a real system, this would get:
        - Care team members for the patient
        - Users assigned to the alert rule
        - On-call staff for critical alerts

        Args:
            alert: The triggered alert

        Returns:
            List of user IDs to notify
        """
        # Placeholder - would integrate with team/assignment service
        return []

    # ==================== Alert Management ====================

    async def get_alert(self, alert_id: UUID) -> Optional[TriggeredAlert]:
        """Get an alert by ID.

        Args:
            alert_id: Alert ID

        Returns:
            TriggeredAlert or None
        """
        result = await self.db.execute(select(TriggeredAlert).filter(TriggeredAlert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        patient_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TriggeredAlert]:
        """List triggered alerts with filtering.

        Args:
            status: Filter by status (new, acknowledged, dismissed, snoozed)
            severity: Filter by severity
            patient_id: Filter by patient
            start_date: Filter by triggered date start
            end_date: Filter by triggered date end
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of TriggeredAlert objects
        """
        query = select(TriggeredAlert)

        if status:
            query = query.filter(TriggeredAlert.status == status)
        if severity:
            query = query.filter(TriggeredAlert.severity == severity)
        if patient_id:
            query = query.filter(TriggeredAlert.patient_id == patient_id)
        if start_date:
            query = query.filter(TriggeredAlert.triggered_at >= start_date)
        if end_date:
            query = query.filter(TriggeredAlert.triggered_at <= end_date)

        query = query.order_by(desc(TriggeredAlert.triggered_at)).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> Optional[TriggeredAlert]:
        """Acknowledge an alert.

        Args:
            alert_id: Alert to acknowledge
            user_id: User acknowledging
            notes: Optional notes

        Returns:
            Updated alert or None
        """
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        alert.acknowledge(user_id, notes)
        await self.db.commit()
        await self.db.refresh(alert)

        logger.info(f"Alert acknowledged: {alert_id} by {user_id}")
        return alert

    async def dismiss_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> Optional[TriggeredAlert]:
        """Dismiss an alert.

        Args:
            alert_id: Alert to dismiss
            user_id: User dismissing
            notes: Optional notes (e.g., reason for dismissal)

        Returns:
            Updated alert or None
        """
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        alert.dismiss(user_id, notes)
        await self.db.commit()
        await self.db.refresh(alert)

        logger.info(f"Alert dismissed: {alert_id} by {user_id}")
        return alert

    async def snooze_alert(
        self,
        alert_id: UUID,
        snooze_minutes: int
    ) -> Optional[TriggeredAlert]:
        """Snooze an alert for specified duration.

        Args:
            alert_id: Alert to snooze
            snooze_minutes: Minutes to snooze

        Returns:
            Updated alert or None
        """
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        snooze_until = datetime.utcnow() + timedelta(minutes=snooze_minutes)
        alert.snooze(snooze_until)
        await self.db.commit()
        await self.db.refresh(alert)

        logger.info(f"Alert snoozed: {alert_id} until {snooze_until}")
        return alert

    async def bulk_acknowledge(
        self,
        alert_ids: List[UUID],
        user_id: UUID,
        notes: Optional[str] = None
    ) -> int:
        """Acknowledge multiple alerts at once.

        Args:
            alert_ids: List of alert IDs
            user_id: User acknowledging
            notes: Optional notes

        Returns:
            Number of alerts acknowledged
        """
        count = 0
        for alert_id in alert_ids:
            if await self.acknowledge_alert(alert_id, user_id, notes):
                count += 1
        return count

    # ==================== Statistics ====================

    async def get_alert_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get alert statistics for a time period.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Statistics dictionary
        """
        from sqlalchemy import func

        query = select(TriggeredAlert)

        if start_date:
            query = query.filter(TriggeredAlert.triggered_at >= start_date)
        if end_date:
            query = query.filter(TriggeredAlert.triggered_at <= end_date)

        # Count total
        total_result = await self.db.execute(select(func.count(TriggeredAlert.id)).filter(
            TriggeredAlert.triggered_at >= start_date if start_date else True,
            TriggeredAlert.triggered_at <= end_date if end_date else True
        ))
        total = total_result.scalar() or 0

        # Group by status
        status_query = select(
            TriggeredAlert.status,
            func.count(TriggeredAlert.id)
        ).filter(
            TriggeredAlert.triggered_at >= start_date if start_date else True,
            TriggeredAlert.triggered_at <= end_date if end_date else True
        ).group_by(TriggeredAlert.status)
        
        status_result = await self.db.execute(status_query)
        by_status = dict(status_result.all())

        # Group by severity
        severity_query = select(
            TriggeredAlert.severity,
            func.count(TriggeredAlert.id)
        ).filter(
             TriggeredAlert.triggered_at >= start_date if start_date else True,
             TriggeredAlert.triggered_at <= end_date if end_date else True
        ).group_by(TriggeredAlert.severity)

        severity_result = await self.db.execute(severity_query)
        by_severity = dict(severity_result.all())

        # Calculate average response time
        ack_query = select(TriggeredAlert).filter(
            TriggeredAlert.acknowledged_at.isnot(None),
            TriggeredAlert.triggered_at >= start_date if start_date else True,
            TriggeredAlert.triggered_at <= end_date if end_date else True
        )
        ack_result = await self.db.execute(ack_query)
        acknowledged = ack_result.scalars().all()

        if acknowledged:
            response_times = [
                (a.acknowledged_at - a.triggered_at).total_seconds()
                for a in acknowledged
                if a.acknowledged_at and a.triggered_at
            ]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        else:
            avg_response_time = 0

        # Critical unacknowledged
        crit_query = select(func.count(TriggeredAlert.id)).filter(
            TriggeredAlert.severity == "critical",
            TriggeredAlert.status == "new",
            TriggeredAlert.triggered_at >= start_date if start_date else True,
            TriggeredAlert.triggered_at <= end_date if end_date else True
        )
        crit_result = await self.db.execute(crit_query)
        critical_unacknowledged = crit_result.scalar() or 0

        return {
            "total_alerts": total,
            "by_status": by_status,
            "by_severity": by_severity,
            "avg_response_time_seconds": avg_response_time,
            "unacknowledged_count": by_status.get("new", 0),
            "critical_unacknowledged": critical_unacknowledged
        }

    # ==================== Notification Preferences ====================

    async def get_user_preferences(self, user_id: UUID) -> Optional[NotificationPreferences]:
        """Get notification preferences for a user.

        Args:
            user_id: User ID

        Returns:
            NotificationPreferences or None
        """
        result = await self.db.execute(select(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ))
        return result.scalar_one_or_none()

    async def update_user_preferences(
        self,
        user_id: UUID,
        **preferences
    ) -> NotificationPreferences:
        """Update notification preferences for a user.

        Creates preferences if they don't exist.

        Args:
            user_id: User ID
            **preferences: Preference fields to update

        Returns:
            Updated NotificationPreferences
        """
        prefs = await self.get_user_preferences(user_id)

        if not prefs:
            prefs = NotificationPreferences(user_id=user_id)
            self.db.add(prefs)

        allowed_fields = [
            "email_enabled", "sms_enabled", "in_app_enabled",
            "quiet_hours_start", "quiet_hours_end", "min_severity", "phone_number"
        ]

        for field, value in preferences.items():
            if field in allowed_fields:
                setattr(prefs, field, value)

        await self.db.commit()
        await self.db.refresh(prefs)

        return prefs
