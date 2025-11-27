# Technical Plan: Event Bus Foundation (Sprint 5.5)

**Version**: 1.0.0
**Date**: 2025-11-18
**Sprint Duration**: 2 weeks (~60 hours)
**Dependencies**: Sprints 1-5

---

## Overview

### Goals

Sprint 5.5 establishes **event-driven architecture** foundation:
- **Event bus infrastructure** (Redis Streams or RabbitMQ)
- **Event publishing** from core modules (patient updates, document changes)
- **Event consumers** for decoupled processing (notifications, audit, analytics)
- **Event replay** for debugging and recovery
- **Dead letter queue** for failed event processing

### Success Criteria

- [ ] Event bus operational (Redis Streams or RabbitMQ)
- [ ] Core events published: patient.created, patient.updated, document.created, document.coded
- [ ] 3+ event consumers operational (audit logger, notification sender, analytics aggregator)
- [ ] Event replay capability for debugging
- [ ] Dead letter queue for failed events
- [ ] 80% test coverage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Publishers                         │
│  - PatientService (patient.created, patient.updated)        │
│  - DocumentService (document.created, document.indexed)     │
│  - CodingService (document.coded)                           │
│  - SearchService (search.performed)                         │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    Event Bus (Redis Streams)                │
│  - Streams: patient-events, document-events, coding-events  │
│  - Consumer groups for parallel processing                  │
│  - Dead letter queue (failed events)                        │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    Event Consumers                          │
│  - AuditLogConsumer (write to audit_logs)                   │
│  - NotificationConsumer (send email/SMS)                    │
│  - AnalyticsConsumer (aggregate to analytics DB)            │
│  - CacheInvalidationConsumer (invalidate Redis cache)       │
└─────────────────────────────────────────────────────────────┘
```

### Event Flow Example

**Patient Created Event**:
1. PatientService creates patient → emits `patient.created` event
2. Event published to `patient-events` stream in Redis
3. Multiple consumers subscribe:
   - AuditLogConsumer → logs patient creation to audit_logs
   - NotificationConsumer → sends email to admin
   - AnalyticsConsumer → updates patient count metric
4. All consumers process event in parallel
5. If consumer fails → event moved to dead letter queue for retry

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Event Bus | Redis Streams | 7.2 | Message broker |
| Alternative | RabbitMQ | 3.12 | If Redis Streams insufficient |
| Consumer Framework | rq | 1.15 | Worker queue (if Redis) |
| Alternative | Celery | 5.3 | Worker queue (if RabbitMQ) |
| Serialization | JSON | stdlib | Event payload format |

---

## Event Schema Design

### Standard Event Format

```json
{
  "event_id": "evt-uuid",
  "event_type": "patient.created",
  "event_version": "1.0",
  "timestamp": "2023-11-17T10:30:00Z",
  "source": "patient-service",
  "actor": {
    "user_id": "user-123",
    "user_email": "doctor@hospital.org"
  },
  "payload": {
    "patient_id": "patient-456",
    "mrn": "MRN-789",
    "name": "John Doe"
  },
  "metadata": {
    "correlation_id": "req-abc",
    "trace_id": "trace-xyz"
  }
}
```

### Event Types

| Event Type | Payload | Purpose |
|-----------|---------|---------|
| `patient.created` | `{patient_id, mrn}` | Patient created |
| `patient.updated` | `{patient_id, fields_changed}` | Patient updated |
| `document.created` | `{document_id, patient_id}` | Document created |
| `document.indexed` | `{document_id}` | Document indexed to ES |
| `document.coded` | `{document_id, codes}` | Document coded (ICD-10) |
| `search.performed` | `{query, user_id, results}` | Search executed |
| `alert.triggered` | `{alert_id, patient_id}` | Alert triggered |

---

## API Design

### Event Publishing API (Internal)

```python
from app.events import EventBus, Event

event_bus = EventBus()

# Publish event
await event_bus.publish(
    Event(
        event_type="patient.created",
        payload={"patient_id": "patient-456", "mrn": "MRN-789"},
        actor={"user_id": "user-123"}
    )
)
```

### Event Consumer API (Internal)

```python
from app.events import EventConsumer, Event

class AuditLogConsumer(EventConsumer):
    """Consumer that writes events to audit_logs table"""

    async def handle_event(self, event: Event):
        await self.db.execute(
            """
            INSERT INTO audit_logs (user_id, action, resource_id, timestamp)
            VALUES (:user_id, :action, :resource_id, :timestamp)
            """,
            {
                "user_id": event.actor["user_id"],
                "action": event.event_type,
                "resource_id": event.payload.get("patient_id"),
                "timestamp": event.timestamp
            }
        )
```

### Admin Endpoints

#### GET `/api/v1/events/stream`

Stream events in real-time (SSE - Server-Sent Events).

**Response**: (Server-Sent Events stream)
```
event: patient.created
data: {"patient_id": "patient-456"}

event: document.coded
data: {"document_id": "doc-123"}
```

#### GET `/api/v1/events/replay`

Replay events for debugging.

**Query**: `?event_type=patient.created&from=2023-11-01&to=2023-11-30`

**Response**:
```json
{
  "events": [
    {"event_id": "evt-1", "event_type": "patient.created", ...},
    {"event_id": "evt-2", "event_type": "patient.created", ...}
  ]
}
```

---

## Database Schema

### `event_log` (Event Persistence for Replay)

```sql
CREATE TABLE event_log (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    event_version VARCHAR(10) DEFAULT '1.0',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(100),
    actor JSONB,
    payload JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_event_log_type ON event_log(event_type);
CREATE INDEX idx_event_log_timestamp ON event_log(timestamp);
```

### `dead_letter_queue` (Failed Events)

```sql
CREATE TABLE dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES event_log(event_id),
    consumer_name VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_dlq_event ON dead_letter_queue(event_id);
```

---

## Component Design

### Backend: `EventBus` (`app/events/event_bus.py`)

```python
from typing import Optional, Dict, Any
import redis.asyncio as redis
import json
import uuid
from datetime import datetime

class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = "cogstack-nlp"
    actor: Dict[str, Any]
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}

class EventBus:
    """Event bus using Redis Streams"""

    def __init__(self, redis_client: redis.Redis, db: AsyncSession):
        self.redis = redis_client
        self.db = db

    async def publish(self, event: Event):
        """
        Publish event to Redis stream.

        Events are published to stream named after event category:
        - patient.created → patient-events stream
        - document.coded → document-events stream
        """
        # Determine stream name from event type
        stream_name = self._get_stream_name(event.event_type)

        # Serialize event
        event_data = event.dict()

        # Publish to Redis stream
        await self.redis.xadd(
            stream_name,
            {"data": json.dumps(event_data)}
        )

        # Persist to event_log for replay
        await self.db.execute(
            """
            INSERT INTO event_log (event_id, event_type, event_version, timestamp, source, actor, payload, metadata)
            VALUES (:event_id, :event_type, :event_version, :timestamp, :source, :actor, :payload, :metadata)
            """,
            event_data
        )
        await self.db.commit()

    def _get_stream_name(self, event_type: str) -> str:
        """Get stream name from event type (e.g., patient.created → patient-events)"""
        category = event_type.split('.')[0]
        return f"{category}-events"

class EventConsumer:
    """Base class for event consumers"""

    def __init__(self, redis_client: redis.Redis, db: AsyncSession):
        self.redis = redis_client
        self.db = db
        self.consumer_name = self.__class__.__name__
        self.consumer_group = f"{self.consumer_name}-group"

    async def start(self, stream_names: List[str]):
        """Start consuming events from streams"""
        # Create consumer group if not exists
        for stream_name in stream_names:
            try:
                await self.redis.xgroup_create(stream_name, self.consumer_group, id='0', mkstream=True)
            except redis.ResponseError:
                pass  # Group already exists

        # Consume events
        while True:
            # Read from streams (blocking, 1 second timeout)
            events = await self.redis.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {stream: '>' for stream in stream_names},
                count=10,
                block=1000
            )

            for stream, messages in events:
                for message_id, data in messages:
                    event_json = data[b'data'].decode('utf-8')
                    event = Event(**json.loads(event_json))

                    try:
                        # Handle event (implemented by subclass)
                        await self.handle_event(event)

                        # Acknowledge message
                        await self.redis.xack(stream, self.consumer_group, message_id)

                    except Exception as e:
                        # Move to dead letter queue
                        await self._move_to_dlq(event, str(e))

    async def handle_event(self, event: Event):
        """Handle event (implemented by subclass)"""
        raise NotImplementedError

    async def _move_to_dlq(self, event: Event, error_message: str):
        """Move failed event to dead letter queue"""
        await self.db.execute(
            """
            INSERT INTO dead_letter_queue (event_id, consumer_name, error_message)
            VALUES (:event_id, :consumer_name, :error_msg)
            """,
            {"event_id": event.event_id, "consumer_name": self.consumer_name, "error_msg": error_message}
        )
        await self.db.commit()
```

### Example Consumers

#### `AuditLogConsumer`

```python
class AuditLogConsumer(EventConsumer):
    """Write all events to audit_logs table"""

    async def handle_event(self, event: Event):
        await self.db.execute(
            """
            INSERT INTO audit_logs (user_id, action, resource_id, timestamp, details)
            VALUES (:user_id, :action, :resource_id, :timestamp, :details)
            """,
            {
                "user_id": event.actor.get("user_id"),
                "action": event.event_type,
                "resource_id": event.payload.get("patient_id") or event.payload.get("document_id"),
                "timestamp": event.timestamp,
                "details": json.dumps(event.payload)
            }
        )
        await self.db.commit()
```

#### `CacheInvalidationConsumer`

```python
class CacheInvalidationConsumer(EventConsumer):
    """Invalidate cache when data changes"""

    async def handle_event(self, event: Event):
        if event.event_type == "patient.updated":
            # Invalidate patient cache
            await self.redis.delete(f"patient:{event.payload['patient_id']}")
        elif event.event_type == "document.coded":
            # Invalidate document cache
            await self.redis.delete(f"document:{event.payload['document_id']}")
```

---

## Testing Strategy

### Unit Tests (60%)

```python
@pytest.mark.asyncio
async def test_publish_event(event_bus):
    """Test event publishing"""
    event = Event(
        event_type="patient.created",
        actor={"user_id": "user-123"},
        payload={"patient_id": "patient-456"}
    )
    await event_bus.publish(event)

    # Verify event in Redis stream
    events = await event_bus.redis.xread({"patient-events": '0'}, count=1)
    assert len(events) > 0

@pytest.mark.asyncio
async def test_consumer_handles_event(audit_log_consumer):
    """Test consumer event handling"""
    event = Event(
        event_type="patient.created",
        actor={"user_id": "user-123"},
        payload={"patient_id": "patient-456"}
    )
    await audit_log_consumer.handle_event(event)

    # Verify audit log created
    log = await audit_log_consumer.db.fetchone("SELECT * FROM audit_logs WHERE action = 'patient.created'")
    assert log is not None
```

### Integration Tests (30%)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_flow_end_to_end(event_bus, audit_log_consumer):
    """Test event flow from publisher to consumer"""
    # Publish event
    event = Event(event_type="patient.created", actor={"user_id": "user-123"}, payload={"patient_id": "patient-456"})
    await event_bus.publish(event)

    # Start consumer (background task)
    asyncio.create_task(audit_log_consumer.start(["patient-events"]))

    # Wait for consumer to process
    await asyncio.sleep(2)

    # Verify audit log created
    log = await audit_log_consumer.db.fetchone("SELECT * FROM audit_logs WHERE action = 'patient.created'")
    assert log is not None
```

---

## Performance Requirements

- **Event publishing**: <10ms
- **Event processing latency**: <1 second (from publish to consumer processing)
- **Throughput**: 1,000 events/second
- **Consumer processing**: <100ms per event

---

## Risks & Mitigations

### Risk 1: Redis Streams vs RabbitMQ Trade-offs

**Risk**: Redis Streams may not provide advanced features needed later (message priority, complex routing)

**Mitigation**:
- Start with Redis Streams (simpler, already using Redis)
- Abstract event bus interface for easy migration to RabbitMQ
- Monitor for Redis Streams limitations

---

## Implementation Phases

### Phase 5.5.1: Event Bus Infrastructure (0.5 week, 15h)
- Set up Redis Streams
- Build EventBus class (publish, consume)
- Unit tests

### Phase 5.5.2: Core Event Publishers (0.5 week, 15h)
- Add event publishing to PatientService, DocumentService, CodingService
- Publish patient.created, document.created, document.coded events
- Unit tests

### Phase 5.5.3: Event Consumers (0.5 week, 15h)
- Build AuditLogConsumer, CacheInvalidationConsumer, NotificationConsumer
- Dead letter queue implementation
- Integration tests

### Phase 5.5.4: Event Replay & Monitoring (0.5 week, 15h)
- Event replay API endpoint
- Event monitoring dashboard (event rate, consumer lag)
- E2E tests

---

## Deployment Checklist

- [ ] Redis Streams configured (persistence enabled)
- [ ] Event consumers running as background workers
- [ ] event_log table created (migration applied)
- [ ] dead_letter_queue table created
- [ ] Monitoring dashboard for event rate, consumer lag

---

**Document Version**: 1.0.0
**Status**: Ready for implementation
**Estimated Effort**: 60 hours over 2 weeks
