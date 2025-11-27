# Specification: Event Bus Foundation (Sprint 5.5)

**Version**: 1.0.0
**Date**: 2025-11-25
**Status**: Implemented
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 2 weeks (~60 hours)
**Dependencies**: Sprints 1-5

**Version History**:
- **1.0.0** (2025-11-25): Initial specification extracted from technical plan

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [API Design](#api-design)
8. [Database Schema](#database-schema)
9. [Integration Points](#integration-points)
10. [Performance Requirements](#performance-requirements)
11. [Constraints](#constraints)
12. [Acceptance Criteria](#acceptance-criteria)
13. [Alignment with Constitution](#alignment-with-constitution)
14. [Testing Strategy](#testing-strategy)
15. [Open Questions](#open-questions)

---

## Context

### Background

Sprint 5.5 establishes **event-driven architecture** as the foundation for decoupled, scalable system components. This is a cross-cutting infrastructure sprint that enables real-time communication between services without tight coupling.

**CogStack Product Alignment**: Enterprise Architecture (Infrastructure Layer)

### The Problem

Current system has several limitations:
- **Tight coupling** between services (patient service must call audit service directly)
- **Synchronous operations** blocking user requests (waiting for logging, notifications)
- **No replay capability** for debugging production issues
- **No dead letter handling** for failed operations
- **No real-time updates** to connected clients

### Solution

Implement an event bus using Redis Streams that:
1. Decouples publishers from consumers
2. Enables asynchronous processing
3. Provides event replay for debugging
4. Handles failed events with dead letter queues
5. Supports real-time streaming to clients (SSE)

### Business Value

- **Reliability**: Failed operations don't block user actions
- **Debuggability**: Replay events to reproduce issues
- **Scalability**: Add consumers without modifying publishers
- **Real-time**: Enable live updates for dashboards and alerts
- **Audit Trail**: Complete event history for compliance

---

## Goals

### Primary Goals

1. **Event Bus Infrastructure** (P0)
   - Redis Streams-based message broker
   - Event publishing from core services
   - Consumer groups for parallel processing
   - At-least-once delivery guarantee

2. **Core Event Publishers** (P0)
   - PatientService → `patient.created`, `patient.updated`
   - DocumentService → `document.created`, `document.indexed`
   - CodingService → `document.coded`
   - SearchService → `search.performed`

3. **Event Consumers** (P0)
   - AuditLogConsumer → writes to audit_logs table
   - CacheInvalidationConsumer → invalidates Redis cache
   - NotificationConsumer → sends email/SMS alerts

4. **Event Replay** (P1)
   - Replay events for debugging
   - Filter by event type, date range
   - Admin-only access

5. **Dead Letter Queue** (P1)
   - Failed events captured
   - Retry capability
   - Manual intervention workflow

### Secondary Goals

- Real-time event streaming (SSE endpoint)
- Event monitoring dashboard
- Performance metrics (event rate, consumer lag)

---

## Non-Goals

- **Complex routing** (use simple stream-based routing)
- **Message priority** (all events treated equally)
- **Cross-service transactions** (eventual consistency only)
- **RabbitMQ migration** (start with Redis Streams)

---

## User Stories

### US-5.5.1: Decoupled Audit Logging (P0)

**As a** system administrator
**I want** audit logs to be written asynchronously
**So that** user operations aren't blocked by logging failures

**Acceptance Criteria**:
- When a patient is created, audit log is written within 1 second
- If audit service is temporarily unavailable, event is queued
- User operation succeeds regardless of audit logging status

### US-5.5.2: Cache Invalidation (P0)

**As a** developer
**I want** caches to be automatically invalidated when data changes
**So that** users always see fresh data

**Acceptance Criteria**:
- When patient is updated, patient cache entry is deleted
- When document is coded, document cache entry is deleted
- Invalidation happens within 500ms of data change

### US-5.5.3: Event Replay (P1)

**As a** developer
**I want** to replay events from a specific time range
**So that** I can debug production issues

**Acceptance Criteria**:
- Can filter events by type and date range
- Can replay events to specific consumer
- Events are replayed in original order

### US-5.5.4: Dead Letter Handling (P1)

**As an** administrator
**I want** failed events to be captured and retryable
**So that** no data is lost due to transient failures

**Acceptance Criteria**:
- Failed events are moved to dead letter queue
- Can view failed events with error messages
- Can retry failed events manually

### US-5.5.5: Real-Time Dashboard Updates (P2)

**As a** clinician
**I want** dashboards to update in real-time
**So that** I see the latest patient activity

**Acceptance Criteria**:
- SSE endpoint streams relevant events
- Dashboard receives updates within 2 seconds
- Connection recovers from network interruptions

---

## Requirements

### Functional Requirements

#### FR-1: Event Schema

All events follow a standard format:

```json
{
  "event_id": "evt-uuid",
  "event_type": "patient.created",
  "event_version": "1.0",
  "timestamp": "2025-11-25T10:30:00Z",
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

#### FR-2: Event Types

| Event Type | Payload | Purpose |
|-----------|---------|---------|
| `patient.created` | `{patient_id, mrn}` | Patient created |
| `patient.updated` | `{patient_id, fields_changed}` | Patient updated |
| `document.created` | `{document_id, patient_id}` | Document created |
| `document.indexed` | `{document_id}` | Document indexed to ES |
| `document.coded` | `{document_id, codes}` | Document coded (ICD-10) |
| `search.performed` | `{query, user_id, results}` | Search executed |
| `alert.triggered` | `{alert_id, patient_id}` | Alert triggered |

#### FR-3: Event Persistence

- All events persisted to `event_log` table for replay
- Event retention: 90 days (configurable)
- Dead letter queue for failed events

### Non-Functional Requirements

#### NFR-1: Performance

- **Event publishing**: <10ms
- **Event processing latency**: <1 second
- **Throughput**: 1,000 events/second
- **Consumer processing**: <100ms per event

#### NFR-2: Reliability

- At-least-once delivery guarantee
- Event ordering preserved within stream
- Consumer group ensures no message loss
- Dead letter queue captures all failures

#### NFR-3: Scalability

- Multiple consumers per stream
- Horizontal scaling via consumer groups
- No single point of failure

---

## Architecture

### High-Level Architecture

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

### Component Design

#### EventBus (`app/events/event_bus.py`)

```python
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

    async def publish(self, event: Event):
        """Publish event to Redis stream and persist to event_log."""

    def _get_stream_name(self, event_type: str) -> str:
        """Get stream name from event type (e.g., patient.created → patient-events)"""
```

#### EventConsumer (`app/events/consumer.py`)

```python
class EventConsumer:
    """Base class for event consumers"""

    async def start(self, stream_names: List[str]):
        """Start consuming events from streams"""

    async def handle_event(self, event: Event):
        """Handle event (implemented by subclass)"""

    async def _move_to_dlq(self, event: Event, error_message: str):
        """Move failed event to dead letter queue"""
```

---

## API Design

### Internal APIs (Service-to-Service)

#### Event Publishing

```python
from app.events import EventBus, Event

event_bus = EventBus()

await event_bus.publish(
    Event(
        event_type="patient.created",
        payload={"patient_id": "patient-456", "mrn": "MRN-789"},
        actor={"user_id": "user-123"}
    )
)
```

### Admin Endpoints

#### GET /api/v1/events/stream

Stream events in real-time (Server-Sent Events).

**Response**: (Server-Sent Events stream)
```
event: patient.created
data: {"patient_id": "patient-456"}

event: document.coded
data: {"document_id": "doc-123"}
```

#### GET /api/v1/events/replay

Replay events for debugging.

**Query**: `?event_type=patient.created&from=2025-11-01&to=2025-11-30`

**Response**:
```json
{
  "events": [
    {"event_id": "evt-1", "event_type": "patient.created", ...},
    {"event_id": "evt-2", "event_type": "patient.created", ...}
  ]
}
```

#### GET /api/v1/events/dlq

View dead letter queue.

**Response**:
```json
{
  "failed_events": [
    {
      "id": "dlq-1",
      "event_id": "evt-3",
      "consumer_name": "AuditLogConsumer",
      "error_message": "Database connection failed",
      "retry_count": 2,
      "last_retry_at": "2025-11-25T11:00:00Z"
    }
  ]
}
```

#### POST /api/v1/events/dlq/{id}/retry

Retry a failed event.

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

## Integration Points

### Redis Streams

- **Required**: Yes
- **Version**: Redis 7.2+
- **Streams**: `patient-events`, `document-events`, `coding-events`, `search-events`
- **Consumer Groups**: One per consumer type

### PostgreSQL

- **Required**: Yes
- **Purpose**: Event persistence, dead letter queue
- **Tables**: `event_log`, `dead_letter_queue`

### Existing Services

- PatientService: Publish patient events
- DocumentService: Publish document events
- CodingService: Publish coding events
- SearchService: Publish search events

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Event Publishing | <10ms |
| Processing Latency | <1 second |
| Throughput | 1,000 events/sec |
| Consumer Processing | <100ms per event |

---

## Constraints

### Technical Constraints

- Redis 7.2+ required for Streams features
- Single Redis instance (no cluster for MVP)
- At-least-once delivery (not exactly-once)

### Operational Constraints

- Consumers must be idempotent (handle duplicate events)
- Event replay limited to 90-day retention
- Dead letter queue manual intervention required

---

## Acceptance Criteria

### Event Bus Infrastructure

- [ ] Redis Streams operational
- [ ] Event publishing works (<10ms)
- [ ] Consumer groups created
- [ ] At-least-once delivery verified

### Core Event Publishers

- [ ] `patient.created` event published on patient creation
- [ ] `patient.updated` event published on patient update
- [ ] `document.created` event published on document upload
- [ ] `document.coded` event published on ICD-10 coding

### Event Consumers

- [ ] AuditLogConsumer writes to audit_logs
- [ ] CacheInvalidationConsumer clears cache
- [ ] Consumers process events within 1 second

### Event Replay

- [ ] Can replay events by type and date range
- [ ] Events replayed in original order
- [ ] Admin-only access enforced

### Dead Letter Queue

- [ ] Failed events captured in DLQ
- [ ] Can view failed events with error details
- [ ] Can retry failed events

### Testing

- [ ] 80% test coverage
- [ ] Unit tests for EventBus and consumers
- [ ] Integration tests for end-to-end flow

---

## Alignment with Constitution

| Principle | How This Sprint Addresses It |
|-----------|------------------------------|
| Patient Safety First | Reliable event delivery for safety alerts |
| Privacy by Design | PHI not logged in event payloads |
| Transparency | Event replay for debugging |
| Performance | Async processing doesn't block users |
| Continuous Improvement | Metrics for event processing |

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
    log = await audit_log_consumer.db.fetchone(
        "SELECT * FROM audit_logs WHERE action = 'patient.created'"
    )
    assert log is not None
```

### Integration Tests (30%)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_flow_end_to_end(event_bus, audit_log_consumer):
    """Test event flow from publisher to consumer"""
    event = Event(
        event_type="patient.created",
        actor={"user_id": "user-123"},
        payload={"patient_id": "patient-456"}
    )
    await event_bus.publish(event)

    # Start consumer (background task)
    asyncio.create_task(audit_log_consumer.start(["patient-events"]))

    # Wait for consumer to process
    await asyncio.sleep(2)

    # Verify audit log created
    log = await audit_log_consumer.db.fetchone(
        "SELECT * FROM audit_logs WHERE action = 'patient.created'"
    )
    assert log is not None
```

### E2E Tests (10%)

- Full event flow from service to consumer
- Dead letter queue handling
- Event replay functionality

---

## Open Questions

1. **Event retention period**: 90 days sufficient for compliance?
   - Proposed: Make configurable, default 90 days

2. **Consumer failure alerting**: How to notify admins of DLQ growth?
   - Proposed: Email alert when DLQ > 100 events

3. **Event versioning**: How to handle schema changes?
   - Proposed: Include `event_version`, consumers handle multiple versions

---

## References

- Technical Plan: `.specify/plans/sprint-5.5-event-bus-plan.md`
- Tasks: `.specify/tasks/sprint-5.5-event-bus-tasks.md`
- Redis Streams Documentation: https://redis.io/docs/data-types/streams/
