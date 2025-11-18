# Tasks: Automated Alerting Module (Sprint 7)

**Plan Reference**: `.specify/plans/sprint-7-automated-alerting-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-7-automated-alerting.md` (v1.0.0)
**Estimated Total Time**: 150 hours (5 weeks)
**Dependencies**:
- Sprints 1-6 completed
- Event Bus (Sprint 5.5) operational
- SMTP server configured (email)
- Twilio account (SMS, optional)

---

## Phase 7.1: Alert Detection Engine (30 hours)

### Task 7.1.1: Create alert_rules Table
**Goal**: Database table for alert rule definitions
**Phase**: 7.1 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Create migration, 2) Define schema (rule_id, name, conditions JSON, notification_channels, severity), 3) Seed default rules
**Acceptance**: Table created, 5+ default rules loaded
**Files**: `backend/alembic/versions/XXX_create_alert_rules.py`, `scripts/load_default_alert_rules.py`

### Task 7.1.2: Create AlertingService - Pattern Matching
**Goal**: Service to evaluate alert rules
**Phase**: 7.1 | **Dependencies**: Task 7.1.1 | **Time**: 12h
**Steps**: 1) Write tests (TDD), 2) Create `AlertingService`, 3) Implement pattern matching (drug combinations, comorbidities, abnormal labs), 4) Evaluate rules against patient data, 5) Trigger alerts when conditions met
**Acceptance**: Rules evaluated correctly, alerts triggered
**Test Coverage**: 20 unit tests
**Files**: `backend/app/services/alerting_service.py`, `tests/unit/services/test_alerting_service.py`

### Task 7.1.3: Create Continuous Scanning Task (Celery)
**Goal**: Celery beat task to scan for alerts every 5 minutes
**Phase**: 7.1 | **Dependencies**: Task 7.1.2 | **Time**: 6h
**Steps**: 1) Create `scan_for_alerts_task()` Celery beat task, 2) Run every 5 minutes, 3) Fetch active patients, 4) Evaluate alert rules, 5) Trigger alerts
**Acceptance**: Task runs every 5 minutes, alerts triggered
**Files**: `backend/app/tasks/alert_scanning.py`

### Task 7.1.4: Create triggered_alerts Table
**Goal**: Store triggered alerts
**Phase**: 7.1 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Create migration, 2) Define schema (alert_id, rule_id, patient_id, triggered_at, acknowledged_by, status)
**Acceptance**: Table created
**Files**: `backend/alembic/versions/XXX_create_triggered_alerts.py`

### Task 7.1.5: Integration Tests - Alert Detection
**Goal**: Integration tests for alert detection
**Phase**: 7.1 | **Dependencies**: Task 7.1.2 | **Time**: 6h
**Steps**: 1) Write tests (patient meets criteria → alert triggered)
**Acceptance**: All integration tests passing
**Test Coverage**: 12 integration tests
**Files**: `tests/integration/test_alert_detection.py`

---

## Phase 7.2: Notification Infrastructure (30 hours)

### Task 7.2.1: Create NotificationService - Email (SMTP)
**Goal**: Send email notifications
**Phase**: 7.2 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Write tests, 2) Create `NotificationService`, 3) Implement `send_email(to, subject, body)` using smtplib, 4) Configure SMTP settings from environment
**Acceptance**: Emails sent successfully
**Test Coverage**: 8 unit tests
**Files**: `backend/app/services/notification_service.py`, `tests/unit/services/test_notification_service.py`

### Task 7.2.2: Create NotificationService - SMS (Twilio)
**Goal**: Send SMS notifications (optional)
**Phase**: 7.2 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Install twilio SDK, 2) Implement `send_sms(to, message)`, 3) Configure Twilio credentials
**Acceptance**: SMS sent successfully (if Twilio configured)
**Files**: `backend/app/services/notification_service.py` (updated)

### Task 7.2.3: Create NotificationService - In-App (WebSocket)
**Goal**: Send in-app notifications via WebSocket
**Phase**: 7.2 | **Dependencies**: None | **Time**: 8h
**Steps**: 1) Install websockets library, 2) Create WebSocket server, 3) Implement `send_in_app_notification()`, 4) Frontend WebSocket client
**Acceptance**: In-app notifications received in real-time
**Files**: `backend/app/services/websocket_notification_service.py`, `webapp/src/services/websocket_client.ts`

### Task 7.2.4: Implement Escalation Workflows
**Goal**: Escalate alerts if not acknowledged within time limit
**Phase**: 7.2 | **Dependencies**: Tasks 7.2.1-7.2.3 | **Time**: 6h
**Steps**: 1) Create escalation rules (if not acknowledged in 15 minutes → escalate to supervisor), 2) Celery task to check unacknowledged alerts, 3) Escalate notifications
**Acceptance**: Alerts escalated if not acknowledged
**Files**: `backend/app/tasks/alert_escalation.py`

### Task 7.2.5: Integration Tests - Notifications
**Goal**: Integration tests for notification sending
**Phase**: 7.2 | **Dependencies**: Tasks 7.2.1-7.2.3 | **Time**: 4h
**Steps**: 1) Write tests (email sent, SMS sent, WebSocket notification received)
**Acceptance**: All integration tests passing
**Test Coverage**: 10 integration tests
**Files**: `tests/integration/test_notifications.py`

---

## Phase 7.3: Alert Management UI (30 hours)

### Task 7.3.1: Create AlertInboxView Component
**Goal**: Alert inbox UI for clinicians
**Phase**: 7.3 | **Dependencies**: Phase 7.1 completed | **Time**: 12h
**Steps**: 1) Create `AlertInboxView.vue`, 2) Fetch triggered alerts, 3) Display alerts in list (patient, rule, severity, triggered time), 4) Acknowledge/dismiss/snooze buttons
**Acceptance**: Inbox displays alerts, allows actions
**Files**: `webapp/src/views/AlertInboxView.vue`, `webapp/src/stores/alerts.ts`

### Task 7.3.2: Implement Acknowledge/Dismiss/Snooze Actions
**Goal**: Alert action buttons
**Phase**: 7.3 | **Dependencies**: Task 7.3.1 | **Time**: 6h
**Steps**: 1) Acknowledge: mark alert as acknowledged, 2) Dismiss: mark as dismissed, 3) Snooze: re-alert in X hours
**Acceptance**: All actions work, alert status updated
**Files**: `webapp/src/views/AlertInboxView.vue` (updated)

### Task 7.3.3: Create Alert History View
**Goal**: View past alerts for patient
**Phase**: 7.3 | **Dependencies**: Task 7.3.1 | **Time**: 6h
**Steps**: 1) Create `AlertHistoryView.vue`, 2) Fetch alerts for patient, 3) Display with filters (date range, status)
**Acceptance**: Alert history displayed
**Files**: `webapp/src/views/AlertHistoryView.vue`

### Task 7.3.4: Create Real-Time Alert Notifications (WebSocket)
**Goal**: Display real-time alerts in UI
**Phase**: 7.3 | **Dependencies**: Task 7.2.3 | **Time**: 6h
**Steps**: 1) Connect to WebSocket, 2) Listen for alert events, 3) Display toast notification, 4) Play sound, 5) Update badge count
**Acceptance**: Real-time alerts displayed
**Files**: `webapp/src/views/AlertInboxView.vue` (updated)

---

## Phase 7.4: Alert Rules Engine (30 hours)

### Task 7.4.1: Create Alert Rule Builder UI (Admin)
**Goal**: UI to create/edit alert rules
**Phase**: 7.4 | **Dependencies**: Phase 7.1 completed | **Time**: 12h
**Steps**: 1) Create `AlertRuleBuilderView.vue`, 2) Visual rule builder (conditions, notification channels, severity), 3) Save rule to database
**Acceptance**: Rules created via UI
**Files**: `webapp/src/views/admin/AlertRuleBuilderView.vue`

### Task 7.4.2: Implement Rule Testing/Validation
**Goal**: Test rules before activating
**Phase**: 7.4 | **Dependencies**: Task 7.4.1 | **Time**: 8h
**Steps**: 1) Test rule against sample patient data, 2) Display results, 3) Validate rule logic
**Acceptance**: Rules tested before activation
**Files**: `webapp/src/views/admin/AlertRuleBuilderView.vue` (updated)

### Task 7.4.3: Implement Rule Versioning
**Goal**: Track rule changes over time
**Phase**: 7.4 | **Dependencies**: Task 7.4.1 | **Time**: 6h
**Steps**: 1) Create alert_rule_versions table, 2) Store version on rule update, 3) Display version history
**Acceptance**: Rule versions tracked
**Files**: `backend/alembic/versions/XXX_create_alert_rule_versions.py`

### Task 7.4.4: Integration Tests - Rule Builder
**Goal**: Integration tests for rule management
**Phase**: 7.4 | **Dependencies**: Task 7.4.1 | **Time**: 4h
**Steps**: 1) Write tests (create rule, edit rule, test rule, activate rule)
**Acceptance**: All integration tests passing
**Test Coverage**: 10 integration tests
**Files**: `tests/integration/test_alert_rule_management.py`

---

## Phase 7.5: Testing & Deployment (30 hours)

### Task 7.5.1: Unit Tests - Alerting Service
**Goal**: Comprehensive unit tests
**Phase**: 7.5 | **Dependencies**: Phase 7.1 completed | **Time**: 6h
**Steps**: 1) Write tests for all alert patterns, 2) Test edge cases
**Acceptance**: Code coverage ≥85%, all tests passing
**Test Coverage**: 30+ unit tests
**Files**: `tests/unit/services/test_alerting_service.py` (expanded)

### Task 7.5.2: Integration Tests - End-to-End Alerting
**Goal**: E2E integration tests
**Phase**: 7.5 | **Dependencies**: All phases completed | **Time**: 8h
**Steps**: 1) Write E2E tests (patient meets criteria → alert triggered → notification sent → alert acknowledged)
**Acceptance**: All E2E tests passing
**Test Coverage**: 10 E2E tests
**Files**: `tests/integration/test_alerting_e2e.py`

### Task 7.5.3: Performance Testing - Alert Scanning
**Goal**: Verify scanning performance
**Phase**: 7.5 | **Dependencies**: Phase 7.1 completed | **Time**: 4h
**Steps**: 1) Performance tests with 1000 patients, 2) Measure scan time
**Acceptance**: Scan completes in <5 minutes for 1000 patients
**Files**: `tests/performance/test_alert_scanning_performance.py`

### Task 7.5.4: E2E Tests with Playwright
**Goal**: E2E UI tests
**Phase**: 7.5 | **Dependencies**: Phase 7.3 completed | **Time**: 6h
**Steps**: 1) Write Playwright tests (navigate to inbox, acknowledge alert)
**Acceptance**: All E2E tests passing
**Test Coverage**: 6 E2E tests
**Files**: `webapp/tests/e2e/alerts.spec.ts`

### Task 7.5.5: Deploy to Staging
**Goal**: Deploy Sprint 7 to staging
**Phase**: 7.5 | **Dependencies**: All phases completed | **Time**: 4h
**Steps**: 1) Deploy backend, 2) Deploy frontend, 3) Configure SMTP, 4) Run smoke tests
**Acceptance**: Deployment successful, alerts working in staging

### Task 7.5.6: User Training
**Goal**: Train clinicians on alert system
**Phase**: 7.5 | **Dependencies**: Task 7.5.5 | **Time**: 2h
**Steps**: 1) Create training materials, 2) Conduct training session
**Acceptance**: Users trained, feedback collected

---

## Deployment Checklist

- [ ] SMTP server configured (email notifications)
- [ ] Twilio configured (SMS notifications, optional)
- [ ] WebSocket server running (in-app notifications)
- [ ] Celery beat scheduler running (alert scanning every 5 minutes)
- [ ] alert_rules, triggered_alerts tables created
- [ ] Default alert rules loaded

---

## Summary

**Total Tasks**: 25 tasks across 5 phases
**Total Estimated Time**: 150 hours (5 weeks)

**Phase Breakdown**:
- Phase 7.1 (Alert Detection): 30 hours, 5 tasks
- Phase 7.2 (Notifications): 30 hours, 5 tasks
- Phase 7.3 (Alert Management UI): 30 hours, 4 tasks
- Phase 7.4 (Rule Builder): 30 hours, 4 tasks
- Phase 7.5 (Testing & Deployment): 30 hours, 6 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%
- E2E tests: Critical workflows

**Performance Targets**:
- Alert scanning: <5 minutes for 1000 patients
- Notification delivery: <10 seconds
- Real-time alerts: <1 second latency
