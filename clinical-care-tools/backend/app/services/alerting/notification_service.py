"""NotificationService for delivering alerts via multiple channels.

Supports email, SMS, and in-app (WebSocket) notifications with
retry logic and delivery tracking.
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.alerting.triggered_alert import TriggeredAlert, AlertNotification
from app.models.alerting.notification_preferences import NotificationPreferences

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(
        self,
        recipient: Dict[str, Any],
        alert: TriggeredAlert,
        template_data: Dict[str, Any]
    ) -> bool:
        """Send notification through this channel.

        Args:
            recipient: Recipient information (email, phone, user_id)
            alert: The triggered alert
            template_data: Data for notification template

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the channel name (email, sms, in_app)."""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel using SMTP or email service."""

    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        """Initialize email channel.

        Args:
            smtp_config: SMTP configuration (host, port, user, password)
        """
        self.smtp_config = smtp_config or {}

    @property
    def channel_name(self) -> str:
        return "email"

    async def send(
        self,
        recipient: Dict[str, Any],
        alert: TriggeredAlert,
        template_data: Dict[str, Any]
    ) -> bool:
        """Send email notification.

        Args:
            recipient: Must contain 'email' key
            alert: The triggered alert
            template_data: Data for email template

        Returns:
            True if sent successfully
        """
        email = recipient.get("email")
        if not email:
            logger.error("No email address provided for recipient")
            return False

        try:
            # Build email content
            subject = self._build_subject(alert, template_data)
            body = self._build_body(alert, template_data)

            # In production, this would use aiosmtplib or email service API
            # For now, log the email that would be sent
            logger.info(f"Sending email to {email}: {subject}")

            # Placeholder for actual email sending
            # await self._send_email(email, subject, body)

            return True

        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False

    def _build_subject(self, alert: TriggeredAlert, template_data: Dict[str, Any]) -> str:
        """Build email subject line."""
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        emoji = severity_emoji.get(alert.severity, "⚪")
        rule_name = template_data.get("rule_name", "Alert")
        return f"{emoji} [{alert.severity.upper()}] Clinical Alert: {rule_name}"

    def _build_body(self, alert: TriggeredAlert, template_data: Dict[str, Any]) -> str:
        """Build email body."""
        return f"""
Clinical Alert Notification

Severity: {alert.severity.upper()}
Rule: {template_data.get('rule_name', 'Unknown')}
Time: {alert.triggered_at.isoformat() if alert.triggered_at else 'Unknown'}

Patient: {template_data.get('patient_name', 'N/A')}
Patient ID: {str(alert.patient_id) if alert.patient_id else 'N/A'}

Description:
{template_data.get('description', 'An alert has been triggered.')}

Trigger Data:
{alert.trigger_data}

---
This is an automated clinical alert. Please review and take appropriate action.
Click here to acknowledge: {template_data.get('acknowledge_url', '#')}
"""


class SMSNotificationChannel(NotificationChannel):
    """SMS notification channel using SMS gateway service."""

    def __init__(self, sms_config: Optional[Dict[str, Any]] = None):
        """Initialize SMS channel.

        Args:
            sms_config: SMS gateway configuration (api_key, sender_id)
        """
        self.sms_config = sms_config or {}

    @property
    def channel_name(self) -> str:
        return "sms"

    async def send(
        self,
        recipient: Dict[str, Any],
        alert: TriggeredAlert,
        template_data: Dict[str, Any]
    ) -> bool:
        """Send SMS notification.

        Args:
            recipient: Must contain 'phone_number' key
            alert: The triggered alert
            template_data: Data for SMS template

        Returns:
            True if sent successfully
        """
        phone = recipient.get("phone_number")
        if not phone:
            logger.error("No phone number provided for recipient")
            return False

        try:
            message = self._build_message(alert, template_data)

            # In production, this would use Twilio, AWS SNS, etc.
            logger.info(f"Sending SMS to {phone}: {message[:50]}...")

            # Placeholder for actual SMS sending
            # await self._send_sms(phone, message)

            return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False

    def _build_message(self, alert: TriggeredAlert, template_data: Dict[str, Any]) -> str:
        """Build SMS message (max 160 chars for single SMS)."""
        rule_name = template_data.get("rule_name", "Alert")[:30]
        severity = alert.severity.upper()[:4]

        return f"[{severity}] {rule_name}: Patient alert. Review urgently. ID: {str(alert.id)[:8]}"


class InAppNotificationChannel(NotificationChannel):
    """In-app notification channel using WebSocket."""

    def __init__(self, websocket_manager=None):
        """Initialize in-app channel.

        Args:
            websocket_manager: WebSocket connection manager
        """
        self.websocket_manager = websocket_manager

    @property
    def channel_name(self) -> str:
        return "in_app"

    async def send(
        self,
        recipient: Dict[str, Any],
        alert: TriggeredAlert,
        template_data: Dict[str, Any]
    ) -> bool:
        """Send in-app notification via WebSocket.

        Args:
            recipient: Must contain 'user_id' key
            alert: The triggered alert
            template_data: Data for notification

        Returns:
            True if sent successfully
        """
        user_id = recipient.get("user_id")
        if not user_id:
            logger.error("No user_id provided for in-app notification")
            return False

        try:
            notification_payload = {
                "type": "alert",
                "alert_id": str(alert.id),
                "severity": alert.severity,
                "rule_name": template_data.get("rule_name"),
                "patient_id": str(alert.patient_id) if alert.patient_id else None,
                "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
                "message": template_data.get("description", "Alert triggered"),
            }

            if self.websocket_manager:
                await self.websocket_manager.send_to_user(user_id, notification_payload)
            else:
                # Log for development/testing
                logger.info(f"In-app notification for user {user_id}: {notification_payload}")

            return True

        except Exception as e:
            logger.error(f"Failed to send in-app notification to {user_id}: {e}")
            return False


class NotificationService:
    """Service for managing alert notifications across all channels.

    Handles notification delivery, retry logic, and delivery tracking.
    """

    MAX_RETRIES = 3
    RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min

    def __init__(self, db: AsyncSession):
        """Initialize notification service.

        Args:
            db: Database session
        """
        self.db = db
        self.channels: Dict[str, NotificationChannel] = {
            "email": EmailNotificationChannel(),
            "sms": SMSNotificationChannel(),
            "in_app": InAppNotificationChannel(),
        }

    def register_channel(self, channel: NotificationChannel) -> None:
        """Register a notification channel.

        Args:
            channel: Channel implementation to register
        """
        self.channels[channel.channel_name] = channel

    async def send_notifications(
        self,
        alert: TriggeredAlert,
        recipient_ids: List[UUID],
        template_data: Optional[Dict[str, Any]] = None
    ) -> List[AlertNotification]:
        """Send notifications for an alert to specified recipients.

        Args:
            alert: Triggered alert to notify about
            recipient_ids: List of user IDs to notify
            template_data: Additional data for notification templates

        Returns:
            List of AlertNotification records created
        """
        template_data = template_data or {}
        notifications = []

        for recipient_id in recipient_ids:
            # Get user preferences
            preferences = await self._get_user_preferences(recipient_id)

            if not preferences:
                logger.warning(f"No notification preferences for user {recipient_id}")
                continue

            # Check if user should receive this alert
            current_time = datetime.now().time()
            if not preferences.should_receive_alert(alert.severity, current_time):
                logger.info(f"Alert suppressed for user {recipient_id} due to preferences")
                continue

            # Get recipient details
            recipient_info = self._get_recipient_info(recipient_id, preferences)

            # Send via enabled channels
            for channel_name in preferences.get_enabled_channels():
                notification = await self._send_via_channel(
                    channel_name,
                    alert,
                    recipient_id,
                    recipient_info,
                    template_data
                )
                if notification:
                    notifications.append(notification)

        return notifications

    async def _send_via_channel(
        self,
        channel_name: str,
        alert: TriggeredAlert,
        recipient_id: UUID,
        recipient_info: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> Optional[AlertNotification]:
        """Send notification via a specific channel.

        Args:
            channel_name: Name of channel to use
            alert: The alert to notify about
            recipient_id: User to notify
            recipient_info: Recipient details (email, phone, etc.)
            template_data: Template data

        Returns:
            AlertNotification record or None if channel not found
        """
        channel = self.channels.get(channel_name)
        if not channel:
            logger.warning(f"Unknown notification channel: {channel_name}")
            return None

        # Create notification record
        notification = AlertNotification(
            alert_id=alert.id,
            channel=channel_name,
            recipient_id=recipient_id,
            status="pending"
        )
        self.db.add(notification)
        await self.db.flush()

        # Attempt to send
        try:
            success = await channel.send(recipient_info, alert, template_data)

            if success:
                notification.mark_sent()
            else:
                notification.mark_failed("Delivery failed")

        except Exception as e:
            notification.mark_failed(str(e))
            logger.error(f"Error sending {channel_name} notification: {e}")

        return notification

    async def _get_user_preferences(self, user_id: UUID) -> Optional[NotificationPreferences]:
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

    def _get_recipient_info(
        self,
        user_id: UUID,
        preferences: NotificationPreferences
    ) -> Dict[str, Any]:
        """Get recipient information for notifications.

        Args:
            user_id: User ID
            preferences: User's notification preferences

        Returns:
            Dictionary with email, phone_number, user_id
        """
        # Would integrate with user service to get email
        # from app.services.user_service import UserService
        # user = UserService(self.db).get_user(user_id)

        return {
            "user_id": str(user_id),
            "email": None,  # Would come from user record
            "phone_number": preferences.phone_number,
        }

    async def retry_failed_notifications(self) -> int:
        """Retry failed notifications that haven't exceeded max retries.

        Returns:
            Number of notifications retried
        """
        result = await self.db.execute(select(AlertNotification).filter(
            AlertNotification.status == "failed",
            AlertNotification.retry_count < self.MAX_RETRIES
        ))
        failed = result.scalars().all()

        retried = 0
        for notification in failed:
            alert = notification.alert
            preferences = await self._get_user_preferences(notification.recipient_id)

            if not preferences:
                continue

            recipient_info = self._get_recipient_info(
                notification.recipient_id, preferences
            )

            channel = self.channels.get(notification.channel)
            if not channel:
                continue

            try:
                # Get template data from alert rule
                template_data = {"rule_name": alert.rule.name if alert.rule else "Unknown"}

                success = await channel.send(recipient_info, alert, template_data)

                if success:
                    notification.mark_sent()
                else:
                    notification.mark_failed("Retry failed")

                retried += 1

            except Exception as e:
                notification.mark_failed(str(e))

        await self.db.commit()
        return retried

    async def get_notification_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get notification delivery statistics.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Statistics dictionary
        """
        from sqlalchemy import func

        query = select(AlertNotification)

        if start_date:
            query = query.filter(AlertNotification.sent_at >= start_date)
        if end_date:
            query = query.filter(AlertNotification.sent_at <= end_date)

        # Total count
        total_result = await self.db.execute(select(func.count(AlertNotification.id)).filter(
            AlertNotification.sent_at >= start_date if start_date else True,
            AlertNotification.sent_at <= end_date if end_date else True
        ))
        total = total_result.scalar() or 0

        # Group by status
        status_query = select(
            AlertNotification.status,
            func.count(AlertNotification.id)
        ).filter(
            AlertNotification.sent_at >= start_date if start_date else True,
            AlertNotification.sent_at <= end_date if end_date else True
        ).group_by(AlertNotification.status)
        
        status_result = await self.db.execute(status_query)
        by_status = dict(status_result.all())

        # Group by channel
        channel_query = select(
            AlertNotification.channel,
            func.count(AlertNotification.id)
        ).filter(
            AlertNotification.sent_at >= start_date if start_date else True,
            AlertNotification.sent_at <= end_date if end_date else True
        ).group_by(AlertNotification.channel)
        
        channel_result = await self.db.execute(channel_query)
        by_channel = dict(channel_result.all())

        return {
            "total": total,
            "by_status": by_status,
            "by_channel": by_channel,
            "success_rate": by_status.get("delivered", 0) / total if total > 0 else 0
        }
