"""Event Publisher Service (Sprint 5.5)

Publishes events to Redis Streams for asynchronous processing.
"""

import logging
import json
from typing import Optional
from uuid import uuid4
from datetime import datetime

from app.schemas.events import Event, EventType

logger = logging.getLogger(__name__)


class EventPublisher:
    """Service for publishing events to Redis Streams"""

    def __init__(self, redis_client=None):
        """Initialize event publisher

        Args:
            redis_client: Redis client (optional, created if None)
        """
        self.redis = redis_client
        self.stream_name = "clinical-events"

    async def publish(
        self,
        event_type: EventType,
        payload: dict,
        source: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish event to Redis Stream

        Args:
            event_type: Type of event
            payload: Event-specific data
            source: Event source (service/module name)
            user_id: User who triggered event (optional)
            correlation_id: Correlation ID for tracing (optional)

        Returns:
            Event ID

        Raises:
            Exception: If publishing fails
        """
        # Create event
        event = Event(
            event_id=uuid4(),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            source=source,
            user_id=user_id,
            correlation_id=correlation_id,
            payload=payload
        )

        # Publish to Redis Stream (if available)
        if self.redis:
            try:
                event_json = event.model_dump_json()
                self.redis.xadd(
                    self.stream_name,
                    {"event": event_json}
                )
                logger.info(f"Published event {event.event_id}: {event_type.value}")
            except Exception as e:
                logger.error(f"Failed to publish event to Redis: {e}")
                # Don't fail the operation if event publishing fails
        else:
            # No Redis available - just log
            logger.info(f"Event published (no Redis): {event.event_id} - {event_type.value}")

        return str(event.event_id)


# Global event publisher instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher


async def publish_event(
    event_type: EventType,
    payload: dict,
    source: str,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> str:
    """Convenience function to publish event

    Args:
        event_type: Type of event
        payload: Event-specific data
        source: Event source
        user_id: User who triggered event
        correlation_id: Correlation ID

    Returns:
        Event ID
    """
    publisher = get_event_publisher()
    return await publisher.publish(
        event_type=event_type,
        payload=payload,
        source=source,
        user_id=user_id,
        correlation_id=correlation_id
    )
