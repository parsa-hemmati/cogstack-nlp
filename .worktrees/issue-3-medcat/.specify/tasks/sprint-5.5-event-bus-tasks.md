# Tasks: Event Bus Foundation (Sprint 5.5)

**Plan Reference**: `.specify/plans/sprint-5.5-event-bus-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-5.5-event-bus.md` (v1.0.0)
**Estimated Total Time**: 60 hours (2 weeks)
**Dependencies**:
- Sprints 1-5 completed
- Redis 7.2 running (Redis Streams)

---

## Phase 5.5.1: Event Bus Infrastructure (15 hours)

### Task 5.5.1.1: Create Event Schema and Models
**Goal**: Define Event Pydantic model and standard schema
**Phase**: 5.5.1 | **Dependencies**: None | **Time**: 2h
**Steps**: 1) Write tests, 2) Create `Event` Pydantic model (event_id, event_type, timestamp, source, actor, payload, metadata), 3) Create event type enums
**Acceptance**: Event model validates correctly, includes all fields
**Test Coverage**: 8 unit tests
**Files**: `backend/app/models/events.py`, `tests/unit/models/test_events.py`

### Task 5.5.1.2: Create event_log Table
**Goal**: PostgreSQL table for event persistence (replay capability)
**Phase**: 5.5.1 | **Dependencies**: None | **Time**: 2h
**Steps**: 1) Create migration, 2) Define schema (event_id, event_type, payload, timestamp, etc.), 3) Add indexes
**Acceptance**: Table created, indexes on event_type and timestamp
**Files**: `backend/alembic/versions/XXX_create_event_log.py`

### Task 5.5.1.3: Create dead_letter_queue Table
**Goal**: Table for failed events
**Phase**: 5.5.1 | **Dependencies**: None | **Time**: 2h
**Steps**: 1) Create migration, 2) Define schema (event_id, consumer_name, error_message, retry_count)
**Acceptance**: Table created
**Files**: `backend/alembic/versions/XXX_create_dead_letter_queue.py`

### Task 5.5.1.4: Implement EventBus Class (Redis Streams)
**Goal**: Core event bus class for publish/consume
**Phase**: 5.5.1 | **Dependencies**: Task 5.5.1.1 | **Time**: 6h
**Steps**: 1) Write tests (TDD), 2) Create `EventBus` class, 3) Implement `publish(event)` method (Redis XADD), 4) Store event in event_log table, 5) Determine stream name from event type (patient.created → patient-events)
**Acceptance**: Events published to Redis Streams and persisted to DB
**Test Coverage**: 12 unit tests
**Files**: `backend/app/events/event_bus.py`, `tests/unit/events/test_event_bus.py`

### Task 5.5.1.5: Implement EventConsumer Base Class
**Goal**: Base class for event consumers
**Phase**: 5.5.1 | **Dependencies**: Task 5.5.1.4 | **Time**: 3h
**Steps**: 1) Write tests, 2) Create `EventConsumer` base class, 3) Implement `start(stream_names)` method (xreadgroup), 4) Implement `handle_event(event)` abstract method, 5) Handle failures → move to DLQ
**Acceptance**: Consumer reads from Redis Streams, handles events, DLQ for failures
**Test Coverage**: 10 unit tests
**Files**: `backend/app/events/event_consumer.py`, `tests/unit/events/test_event_consumer.py`

---

## Phase 5.5.2: Core Event Publishers (15 hours)

### Task 5.5.2.1: Add Event Publishing to PatientService
**Goal**: Publish patient.created, patient.updated events
**Phase**: 5.5.2 | **Dependencies**: Task 5.5.1.4 | **Time**: 3h
**Steps**: 1) Update `PatientService.create_patient()` to publish patient.created event, 2) Update `update_patient()` to publish patient.updated, 3) Include actor (user_id), payload (patient_id, fields_changed)
**Acceptance**: Events published on patient create/update
**Files**: `backend/app/services/patient_service.py` (updated)

### Task 5.5.2.2: Add Event Publishing to DocumentService
**Goal**: Publish document.created, document.indexed events
**Phase**: 5.5.2 | **Dependencies**: Task 5.5.1.4 | **Time**: 3h
**Steps**: 1) Publish document.created on document upload, 2) Publish document.indexed after Elasticsearch indexing
**Acceptance**: Events published on document operations
**Files**: `backend/app/services/document_service.py` (updated)

### Task 5.5.2.3: Add Event Publishing to CodingService
**Goal**: Publish document.coded events
**Phase**: 5.5.2 | **Dependencies**: Task 5.5.1.4 | **Time**: 3h
**Steps**: 1) Publish document.coded when codes assigned, 2) Include codes in payload
**Acceptance**: Events published on code assignment
**Files**: `backend/app/services/clinical_coding_service.py` (updated)

### Task 5.5.2.4: Add Event Publishing to SearchService
**Goal**: Publish search.performed events
**Phase**: 5.5.2 | **Dependencies**: Task 5.5.1.4 | **Time**: 2h
**Steps**: 1) Publish search.performed after search execution, 2) Include query, total_results
**Acceptance**: Events published on search
**Files**: `backend/app/services/search_service.py` (updated)

### Task 5.5.2.5: Integration Tests - Event Publishing
**Goal**: Integration tests for event publishing
**Phase**: 5.5.2 | **Dependencies**: Tasks 5.5.2.1-5.5.2.4 | **Time**: 4h
**Steps**: 1) Write tests (create patient → event in Redis, upload document → event in Redis), 2) Run tests
**Acceptance**: All integration tests passing
**Test Coverage**: 12 integration tests
**Files**: `tests/integration/test_event_publishing.py`

---

## Phase 5.5.3: Event Consumers (15 hours)

### Task 5.5.3.1: Implement AuditLogConsumer
**Goal**: Write all events to audit_logs table
**Phase**: 5.5.3 | **Dependencies**: Task 5.5.1.5 | **Time**: 4h
**Steps**: 1) Write tests, 2) Create `AuditLogConsumer` extending `EventConsumer`, 3) Implement `handle_event()` to insert audit log, 4) Start consumer as background worker
**Acceptance**: All events logged to audit_logs
**Test Coverage**: 8 unit tests
**Files**: `backend/app/events/consumers/audit_log_consumer.py`, `tests/unit/events/test_audit_log_consumer.py`

### Task 5.5.3.2: Implement CacheInvalidationConsumer
**Goal**: Invalidate Redis cache when data changes
**Phase**: 5.5.3 | **Dependencies**: Task 5.5.1.5 | **Time**: 4h
**Steps**: 1) Write tests, 2) Create `CacheInvalidationConsumer`, 3) On patient.updated → delete patient cache, 4) On document.coded → delete document cache
**Acceptance**: Cache invalidated on relevant events
**Test Coverage**: 6 unit tests
**Files**: `backend/app/events/consumers/cache_invalidation_consumer.py`, `tests/unit/events/test_cache_invalidation_consumer.py`

### Task 5.5.3.3: Implement NotificationConsumer (Optional for MVP)
**Goal**: Send notifications (email/SMS) for critical events
**Phase**: 5.5.3 | **Dependencies**: Task 5.5.1.5 | **Time**: 4h
**Steps**: 1) Create `NotificationConsumer`, 2) On alert.triggered → send email/SMS, 3) Use SMTP for email
**Acceptance**: Notifications sent for critical events
**Files**: `backend/app/events/consumers/notification_consumer.py`

### Task 5.5.3.4: Create Consumer Manager Script
**Goal**: Script to start all consumers as background workers
**Phase**: 5.5.3 | **Dependencies**: Tasks 5.5.3.1-5.5.3.3 | **Time**: 2h
**Steps**: 1) Create `scripts/start_consumers.py`, 2) Start each consumer in separate thread/process, 3) Graceful shutdown on SIGTERM
**Acceptance**: All consumers start and run in background
**Files**: `scripts/start_consumers.py`

### Task 5.5.3.5: Integration Tests - Consumers
**Goal**: Integration tests for event consumption
**Phase**: 5.5.3 | **Dependencies**: Tasks 5.5.3.1-5.5.3.4 | **Time**: 1h
**Steps**: 1) Write tests (publish event → verify consumed, audit log created, cache invalidated)
**Acceptance**: All integration tests passing
**Test Coverage**: 10 integration tests
**Files**: `tests/integration/test_event_consumption.py`

---

## Phase 5.5.4: Event Replay & Monitoring (15 hours)

### Task 5.5.4.1: Create Event Replay Service
**Goal**: Service to replay events from event_log
**Phase**: 5.5.4 | **Dependencies**: Task 5.5.1.2 | **Time**: 4h
**Steps**: 1) Write tests, 2) Create `EventReplayService`, 3) Implement `replay_events(event_type, date_from, date_to)`, 4) Query event_log, 5) Re-publish events to Redis Streams
**Acceptance**: Events replayed successfully
**Test Coverage**: 8 unit tests
**Files**: `backend/app/services/event_replay_service.py`, `tests/unit/services/test_event_replay_service.py`

### Task 5.5.4.2: Create Event Replay API Endpoint (Admin Only)
**Goal**: GET /api/v1/events/replay
**Phase**: 5.5.4 | **Dependencies**: Task 5.5.4.1 | **Time**: 3h
**Steps**: 1) Write tests, 2) Create endpoint, 3) Call replay service, 4) Return replayed events
**Acceptance**: Endpoint replays events, admin-only access
**Test Coverage**: 6 integration tests
**Files**: `backend/app/api/v1/endpoints/events.py`, `tests/integration/test_event_replay_api.py`

### Task 5.5.4.3: Create Event Stream SSE Endpoint (Admin Only)
**Goal**: GET /api/v1/events/stream - real-time event streaming
**Phase**: 5.5.4 | **Dependencies**: Task 5.5.1.4 | **Time**: 4h
**Steps**: 1) Create SSE endpoint, 2) Subscribe to all Redis Streams, 3) Stream events to clients
**Acceptance**: Real-time event stream works
**Files**: `backend/app/api/v1/endpoints/events.py` (updated)

### Task 5.5.4.4: Create Event Monitoring Dashboard UI (Admin)
**Goal**: Admin dashboard to monitor events
**Phase**: 5.5.4 | **Dependencies**: Task 5.5.4.3 | **Time**: 4h
**Steps**: 1) Create `EventMonitoringView.vue`, 2) Display live event stream, 3) Display event rate metrics, 4) Display consumer lag
**Acceptance**: Dashboard shows live events and metrics
**Files**: `webapp/src/views/admin/EventMonitoringView.vue`

---

## Deployment Checklist

- [ ] Redis Streams configured (persistence enabled)
- [ ] event_log, dead_letter_queue tables created
- [ ] Event consumers running as background workers (`scripts/start_consumers.py`)
- [ ] Consumer monitoring enabled

---

## Summary

**Total Tasks**: 20 tasks across 4 phases
**Total Estimated Time**: 60 hours (2 weeks)

**Phase Breakdown**:
- Phase 5.5.1 (Infrastructure): 15 hours, 5 tasks
- Phase 5.5.2 (Publishers): 15 hours, 5 tasks
- Phase 5.5.3 (Consumers): 15 hours, 5 tasks
- Phase 5.5.4 (Replay & Monitoring): 15 hours, 4 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%

**Performance Targets**:
- Event publishing: <10ms
- Event processing latency: <1 second
- Throughput: 1,000 events/second
