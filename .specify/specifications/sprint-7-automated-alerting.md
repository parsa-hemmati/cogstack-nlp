# Specification: Automated Alerting Module (Sprint 7)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 5 weeks (~150 hours)

---

## Context

**CogStack Product Alignment**: Automated Alerting (real-time clinical event detection)

**Problem**: Clinicians need automatic notifications for critical events:
- Drug combinations (polypharmacy risks)
- Comorbidity patterns (diabetes + CKD → high risk)
- Demographic risk factors (age >65 + fall risk)
- Critical lab values (K+ >6.0 → hyperkalemia)
- Deteriorating patients (sepsis criteria met)

**Example**: Patient prescribed warfarin + aspirin → automatic alert to clinician (major bleeding risk)

---

## Goals

### Primary Goals (P0)

1. **Real-Time Event Detection Engine**
   - Continuous scanning of patient data
   - Pattern matching (drug combos, comorbidities, demographics)
   - Configurable detection rules

2. **Automated Notification Infrastructure**
   - Email, SMS, in-app notifications
   - Escalation workflows (if not acknowledged in X minutes → escalate to supervisor)
   - Notification preferences (per user, per alert type)

3. **Alert Management UI**
   - Alert inbox (pending, acknowledged, resolved)
   - Snooze alerts (remind later)
   - Dismiss alerts (with reason)
   - Alert history

4. **Alert Rules Engine**
   - Admin configures alert rules (condition → action)
   - Rule builder UI (drag-and-drop)
   - Rule testing/validation
   - Rule versioning (track changes)

5. **Comprehensive Audit Logging**
   - Log all alerts triggered
   - Log clinician actions (acknowledged, dismissed, snoozed)
   - Log notification delivery (sent, failed)

### Secondary Goals (P1)

6. **Alert Effectiveness Metrics**
   - Track alert response times
   - Track false positive rate
   - Track patient outcomes after alert
   - Alert fatigue monitoring

---

## User Stories

### Clinician User Stories

#### US-CL1: Receive Critical Alert
**As a** clinician
**I want to** receive notifications for critical patient events
**So that** I can take immediate action

**Acceptance Criteria**:
- [ ] Alert triggered → notification sent (email, SMS, in-app)
- [ ] Alert shows:
  - Patient name and MRN
  - Event description (e.g., "Warfarin + Aspirin interaction")
  - Severity (critical, high, medium)
  - Recommended action
- [ ] Actions: Acknowledge, Dismiss, Snooze
- [ ] Audit log entry created

#### US-CL2: Manage Alerts
**As a** clinician
**I want to** view and manage my alerts
**So that** I can prioritize urgent tasks

**Acceptance Criteria**:
- [ ] Alert inbox showing:
  - Pending alerts (not yet acknowledged)
  - Acknowledged alerts
  - Resolved alerts
- [ ] Filter by severity, patient, date
- [ ] Bulk actions (acknowledge all, dismiss all)

### Admin User Stories

#### US-A1: Configure Alert Rules
**As an** admin
**I want to** configure alert rules
**So that** clinicians receive relevant alerts

**Acceptance Criteria**:
- [ ] Rule builder UI:
  - Trigger criteria (condition, drug combo, lab value)
  - Alert severity
  - Notification method (email, SMS, in-app)
  - Escalation workflow
- [ ] Test rule (preview alerts for sample patients)
- [ ] Save rule → activate immediately

---

## Requirements

### Functional Requirements

#### FR1: Real-Time Event Detection
- **FR1.1**: Continuous scanning (every 5 minutes for new patient data)
- **FR1.2**: Pattern matching:
  - Drug combinations (polypharmacy, interactions)
  - Comorbidity patterns (diabetes + CKD, CHF + COPD)
  - Demographic risk factors (age, gender, BMI)
  - Lab values (critical highs/lows)
  - Vital signs (fever, hypotension, tachycardia)
- **FR1.3**: Rule evaluation (match patient data against alert rules)
- **FR1.4**: Alert generation (create alert if rule triggered)

#### FR2: Notification Infrastructure
- **FR2.1**: Email notifications (SMTP)
- **FR2.2**: SMS notifications (Twilio API)
- **FR2.3**: In-app notifications (toast messages)
- **FR2.4**: Notification preferences (user configures which alerts to receive)
- **FR2.5**: Escalation workflows:
  - If not acknowledged in 15 minutes → escalate to supervisor
  - If not acknowledged in 30 minutes → escalate to department head

#### FR3: Alert Management
- **FR3.1**: Alert inbox (pending, acknowledged, resolved)
- **FR3.2**: Acknowledge alert (mark as seen)
- **FR3.3**: Dismiss alert (mark as not relevant, with reason)
- **FR3.4**: Snooze alert (remind in X minutes)
- **FR3.5**: Resolve alert (action taken, record outcome)
- **FR3.6**: Alert history (view past alerts)

#### FR4: Alert Rules Engine
- **FR4.1**: Rule builder UI (drag-and-drop conditions)
- **FR4.2**: Trigger criteria:
  - Drug combinations
  - Comorbidities (ICD-10 codes)
  - Lab values (thresholds)
  - Demographics (age, gender)
- **FR4.3**: Alert configuration:
  - Severity (critical, high, medium, low)
  - Notification method (email, SMS, in-app)
  - Recipients (clinician, supervisor, team)
- **FR4.4**: Rule testing (preview alerts for sample patients)
- **FR4.5**: Rule versioning (track changes)

#### FR5: Audit Logging
- **FR5.1**: Log alert triggers (rule, patient, timestamp)
- **FR5.2**: Log clinician actions (acknowledged, dismissed, snoozed, resolved)
- **FR5.3**: Log notification delivery (sent, failed, bounced)
- **FR5.4**: Log patient outcomes (was alert actionable?)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Alert detection: <5 seconds after patient data updated
- **NFR1.2**: Notification delivery: <10 seconds after alert triggered
- **NFR1.3**: Alert inbox loading: <1 second

#### NFR2: Reliability
- **NFR2.1**: Alert delivery: 99.9% success rate
- **NFR2.2**: No duplicate alerts (deduplicate within 1 hour)
- **NFR2.3**: Graceful degradation (if SMS fails, send email)

#### NFR3: Security
- **NFR3.1**: Notification content minimal PHI (patient ID only, not full name)
- **NFR3.2**: Audit logging for all alerts
- **NFR3.3**: Encrypted notification channels (TLS for email, HTTPS for SMS API)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Detection Engine                   │
│  - Polls patient data every 5 minutes                       │
│  - Evaluates alert rules                                    │
│  - Triggers alerts                                          │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    Notification Service                     │
│  - Email (SMTP)                                             │
│  - SMS (Twilio API)                                         │
│  - In-app (WebSocket push)                                  │
│  - Escalation workflows                                     │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    Alert Management UI                      │
│  - Alert inbox                                              │
│  - Acknowledge/Dismiss/Snooze                               │
│  - Alert history                                            │
└─────────────────────────────────────────────────────────────┘
```

### Backend Services

**AlertingService** (`app/services/alerting_service.py`)
```python
class AlertingService:
    """Automated alerting service"""

    async def detect_events(self):
        """Continuously scan for alert conditions"""
        # 1. Query recent patient data
        # 2. Evaluate alert rules
        # 3. Trigger alerts if conditions met

    async def send_notification(
        self,
        alert: Alert,
        method: str  # "email", "sms", "in_app"
    ):
        """Send alert notification"""
        # 1. Format notification message
        # 2. Send via appropriate channel
        # 3. Log delivery status

    async def escalate_alert(self, alert_id: str):
        """Escalate unacknowledged alert"""
        # 1. Identify escalation recipient (supervisor)
        # 2. Send escalation notification
        # 3. Log escalation
```

### Database Models

```python
class Alert(BaseModel):
    id: str
    patient_id: str
    rule_id: str
    severity: str  # "critical", "high", "medium", "low"
    message: str
    status: str  # "pending", "acknowledged", "dismissed", "resolved"
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]

class AlertRule(BaseModel):
    id: str
    name: str
    trigger_criteria: Dict  # Conditions to trigger alert
    severity: str
    notification_methods: List[str]  # ["email", "sms", "in_app"]
    escalation_minutes: int  # Minutes before escalation
    is_active: bool
```

### API Endpoints

#### GET `/api/v1/alerts`
Get alerts for current user.

**Response**:
```json
{
  "pending": [
    {
      "id": "alert-123",
      "patient_id": "patient-456",
      "severity": "critical",
      "message": "Warfarin + Aspirin interaction detected",
      "triggered_at": "2023-11-17T10:30:00Z"
    }
  ],
  "acknowledged": [],
  "resolved": []
}
```

#### POST `/api/v1/alerts/{alert_id}/acknowledge`
Acknowledge alert.

**Response**:
```json
{
  "alert_id": "alert-123",
  "status": "acknowledged",
  "acknowledged_at": "2023-11-17T10:35:00Z"
}
```

---

## Database Schema

### New Tables

#### `alert_rules` (Alert Rules Configuration)
```sql
CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200),
    trigger_criteria JSONB NOT NULL,
    severity VARCHAR(20),
    notification_methods TEXT[],
    escalation_minutes INTEGER DEFAULT 15,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `alerts` (Alert Instances)
```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    rule_id UUID REFERENCES alert_rules(id),
    severity VARCHAR(20),
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);
```

#### `alert_notifications` (Notification Delivery Log)
```sql
CREATE TABLE alert_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES alerts(id),
    recipient_id UUID REFERENCES users(id),
    method VARCHAR(20),  -- "email", "sms", "in_app"
    status VARCHAR(20),  -- "sent", "failed", "bounced"
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message TEXT
);
```

---

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_detect_drug_interaction_alert():
    # Patient on warfarin, prescribed aspirin
    alert = await alerting_service.detect_events(patient_id="patient-123")
    assert alert.severity == "critical"
    assert "Warfarin" in alert.message
    assert "Aspirin" in alert.message
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_send_sms_notification():
    alert = Alert(severity="critical", message="Test alert")
    await alerting_service.send_notification(alert, method="sms")
    # Verify SMS sent (mock Twilio API)
```

---

## Deployment Considerations

### Environment Variables
```bash
ALERTING_ENABLED=true
ALERT_DETECTION_INTERVAL_MINUTES=5
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
```

---

## Open Questions

1. **SMS Provider**: Use Twilio, AWS SNS, or other?
2. **Escalation Hierarchy**: Define escalation recipients (supervisor, department head)?
3. **Alert Fatigue**: How to minimize false positive alerts?
4. **Critical Alert Threshold**: What severity triggers immediate notification?

---

**Status**: Ready for review and approval
**Dependencies**: Base Application, Patient data integration
**Estimated Effort**: 150 hours over 5 weeks
