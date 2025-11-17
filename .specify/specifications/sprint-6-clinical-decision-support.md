# Specification: Clinical Decision Support Module (Sprint 6)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 5 weeks (~150 hours)

**Version History**:
- **1.0.0** (2025-11-17): Initial specification for Clinical Decision Support Module

---

## Context

### Background

The **Clinical Decision Support (CDS) Module** provides evidence-based recommendations integrated into clinical workflows.

**CogStack Product Alignment**: Clinical Decision Support (real-time clinical guidance)

**Sprints 1-5 delivered**: Patient Search, Timeline View, Full-Text Search, De-Identification, Clinical Coding

### The Problem

Clinicians need **real-time clinical guidance** during patient care:
1. **Guideline adherence**: Hard to remember all clinical guidelines (diabetes, hypertension, anticoagulation, etc.)
2. **Drug interactions**: Risk of prescribing contraindicated medications
3. **Preventive care gaps**: Miss screening recommendations (mammography, colonoscopy)
4. **Treatment options**: Unsure of evidence-based treatment choices

**Example**: Clinician sees patient with new diagnosis of Type 2 Diabetes. CDS system suggests:
- Start metformin 500mg BD (first-line therapy per ADA guidelines)
- Order HbA1c, lipid panel, urine ACR (baseline labs)
- Refer to diabetes educator
- Schedule 3-month follow-up

### Why CDS Matters

**Clinical Value**:
- **Improved outcomes**: Evidence-based care → better patient outcomes
- **Reduced errors**: Catch drug interactions, contraindications
- **Guideline compliance**: Automated adherence to clinical guidelines
- **Efficiency**: Suggestions save clinician time (no manual guideline lookup)

### Deployment Context

- **Platform**: Extends Clinical Care Tools Base Application
- **Users**: Clinicians (receive CDS alerts), Admin (configure CDS rules)
- **Data Source**: Patient data, clinical concepts, ICD-10 codes
- **Integration**: CDS Hooks specification, FHIR R4, external EHR systems (Epic, Cerner)

---

## Goals

### Primary Goals

1. **CDS Hooks Integration** (P0)
   - Implement CDS Hooks 1.0 specification
   - Hooks: `patient-view`, `order-select`, `order-sign`
   - Card responses (suggestions, links, SMART apps)
   - EHR integration (Epic, Cerner)

2. **FHIR R4 Interoperability** (P0)
   - FHIR R4 Patient, Condition, Observation, MedicationRequest resources
   - FHIR API endpoints (read, search)
   - FHIR bundle support

3. **Evidence-Based Recommendations** (P0)
   - Clinical guidelines database (ADA, AHA, USPSTF, NICE)
   - Rule engine for recommendations
   - Evidence grading (Level A, B, C)
   - Recommendation explanations (why suggested)

4. **Drug Interaction Checking** (P0)
   - Medication database (RxNorm)
   - Interaction severity (contraindicated, major, moderate, minor)
   - Alternative suggestions (safer options)

5. **Comprehensive Audit Logging** (P0)
   - Log CDS alerts displayed
   - Log clinician actions (accepted, rejected, dismissed)
   - Log alert effectiveness (outcomes)

### Secondary Goals

6. **Preventive Care Reminders** (P1)
   - Screening recommendations (mammography, colonoscopy, vaccines)
   - Age/gender/risk-based guidelines
   - Overdue reminders

7. **Custom CDS Rules** (P1)
   - Admin can create custom rules (condition-based)
   - Rule builder UI (no coding required)
   - Rule testing/validation

---

## Non-Goals

1. **Real-Time EHR Integration** - MVP: Poll-based (future: WebHooks)
2. **SMART on FHIR Apps** - Embed external SMART apps (future)
3. **Machine Learning Predictions** - Rule-based CDS only (no ML in this sprint)
4. **Multi-Language Support** - English guidelines only

---

## User Stories

### Clinician User Stories

#### US-CL1: Receive CDS Alerts
**As a** clinician
**I want to** receive CDS alerts when viewing patient
**So that** I get evidence-based recommendations

**Acceptance Criteria**:
- [ ] Open patient chart → CDS alerts displayed
- [ ] Alert shows:
  - Recommendation (e.g., "Start metformin")
  - Evidence (e.g., "ADA 2023 guidelines")
  - Severity (info, warning, critical)
- [ ] Actions: Accept, Reject, Dismiss
- [ ] Audit log entry created

---

#### US-CL2: Check Drug Interactions
**As a** clinician
**I want to** check for drug interactions before prescribing
**So that** I avoid contraindicated medications

**Acceptance Criteria**:
- [ ] Enter medication → check interactions with current meds
- [ ] Show interaction severity (contraindicated, major, moderate)
- [ ] Suggest alternatives (safer options)

---

### Admin User Stories

#### US-A1: Configure CDS Rules
**As an** admin
**I want to** configure CDS rules
**So that** clinicians receive relevant alerts

**Acceptance Criteria**:
- [ ] Admin panel for CDS rules:
  - Enable/disable rules
  - Set alert thresholds
  - Configure guideline versions (e.g., ADA 2023 vs 2024)
- [ ] Settings saved to database

---

## Requirements

### Functional Requirements

#### FR1: CDS Hooks Integration
- **FR1.1**: Implement CDS Hooks 1.0 specification
- **FR1.2**: Support hooks: `patient-view`, `order-select`, `order-sign`
- **FR1.3**: Return card responses (info, warning, critical)
- **FR1.4**: Support suggestions, links, SMART app cards

#### FR2: FHIR R4 Interoperability
- **FR2.1**: FHIR R4 Patient resource (read, search)
- **FR2.2**: FHIR R4 Condition, Observation, MedicationRequest
- **FR2.3**: FHIR bundles
- **FR2.4**: FHIR search parameters (patient, date, code)

#### FR3: Evidence-Based Recommendations
- **FR3.1**: Clinical guidelines database (ADA, AHA, USPSTF, NICE)
- **FR3.2**: Rule engine (condition → recommendation)
- **FR3.3**: Evidence grading (Level A, B, C)
- **FR3.4**: Recommendation explanations

#### FR4: Drug Interaction Checking
- **FR4.1**: Medication database (RxNorm codes)
- **FR4.2**: Interaction database (contraindications, warnings)
- **FR4.3**: Severity classification (contraindicated, major, moderate, minor)
- **FR4.4**: Alternative drug suggestions

#### FR5: Audit Logging
- **FR5.1**: Log CDS alerts displayed (rule, patient, timestamp)
- **FR5.2**: Log clinician actions (accepted, rejected, dismissed)
- **FR5.3**: Log alert effectiveness (was recommendation followed?)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: CDS Hooks response time: <2 seconds
- **NFR1.2**: FHIR API response time: <500ms
- **NFR1.3**: Drug interaction check: <1 second

#### NFR2: Accuracy
- **NFR2.1**: Clinical guideline accuracy: 100% (match official guidelines)
- **NFR2.2**: Drug interaction accuracy: ≥99%

#### NFR3: Security
- **NFR3.1**: CDS Hooks authentication (OAuth 2.0)
- **NFR3.2**: FHIR API authentication (OAuth 2.0)
- **NFR3.3**: Audit logging for all CDS alerts

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EHR System (Epic, Cerner)                │
│  - Triggers CDS Hooks (patient-view, order-select)          │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑ (HTTPS)
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CDS Hooks Service                                    │  │
│  │  - POST /cds-services/patient-view                    │  │
│  │  - POST /cds-services/order-select                    │  │
│  │  - POST /cds-services/order-sign                      │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  FHIR R4 API                                          │  │
│  │  - GET /fhir/Patient/{id}                             │  │
│  │  - GET /fhir/Condition?patient={id}                   │  │
│  │  - GET /fhir/Observation?patient={id}                 │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CDS Rule Engine                                      │  │
│  │  - Evaluate clinical guidelines                       │  │
│  │  - Generate recommendations                           │  │
│  │  - Check drug interactions                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL (Clinical Guidelines DB)            │
│  - Guidelines (ADA, AHA, USPSTF, NICE)                      │
│  - Drug interactions (RxNorm)                               │
│  - CDS rules                                                │
└─────────────────────────────────────────────────────────────┘
```

### API Endpoints

#### CDS Hooks

**POST `/cds-services/patient-view`**

**Request**:
```json
{
  "hook": "patient-view",
  "hookInstance": "abc-123",
  "context": {
    "patientId": "patient-123",
    "userId": "clinician-456"
  },
  "prefetch": {
    "patient": {
      "resourceType": "Patient",
      "id": "patient-123",
      "birthDate": "1975-05-15"
    }
  }
}
```

**Response**:
```json
{
  "cards": [
    {
      "summary": "Start metformin for Type 2 Diabetes",
      "indicator": "warning",
      "detail": "Patient diagnosed with T2DM. ADA guidelines recommend metformin as first-line therapy.",
      "source": {
        "label": "ADA 2023 Guidelines",
        "url": "https://diabetesjournals.org/care/issue/46/Supplement_1"
      },
      "suggestions": [
        {
          "label": "Order metformin 500mg BD",
          "actions": [
            {
              "type": "create",
              "description": "Create metformin prescription",
              "resource": {
                "resourceType": "MedicationRequest",
                "medicationCodeableConcept": {
                  "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "6809",
                    "display": "Metformin"
                  }]
                },
                "dosageInstruction": [{
                  "text": "500mg twice daily"
                }]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

#### FHIR R4

**GET `/fhir/Patient/{id}`**

**Response**:
```json
{
  "resourceType": "Patient",
  "id": "patient-123",
  "name": [{
    "given": ["John"],
    "family": "Smith"
  }],
  "birthDate": "1975-05-15",
  "gender": "male"
}
```

---

## Database Schema

### New Tables

#### `clinical_guidelines` (Guidelines Database)
```sql
CREATE TABLE clinical_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guideline_id VARCHAR(100) NOT NULL,  -- "ADA_2023_T2DM_METFORMIN"
    organization VARCHAR(100),  -- "ADA", "AHA", "USPSTF"
    version VARCHAR(50),  -- "2023"
    condition VARCHAR(200),  -- "Type 2 Diabetes Mellitus"
    recommendation TEXT NOT NULL,
    evidence_level VARCHAR(10),  -- "A", "B", "C"
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `cds_rules` (CDS Rules)
```sql
CREATE TABLE cds_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200),
    description TEXT,
    condition_criteria JSONB,  -- Criteria to trigger rule
    recommendation_template TEXT,
    guideline_id UUID REFERENCES clinical_guidelines(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `drug_interactions` (Drug Interaction Database)
```sql
CREATE TABLE drug_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_a_rxnorm VARCHAR(50),  -- RxNorm code
    drug_b_rxnorm VARCHAR(50),
    interaction_type VARCHAR(50),  -- "contraindication", "major", "moderate", "minor"
    description TEXT,
    recommendation TEXT,  -- Alternative drugs
    source VARCHAR(100)
);
```

#### `cds_alerts_log` (CDS Alert Audit Log)
```sql
CREATE TABLE cds_alerts_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID,
    clinician_id UUID,
    rule_id VARCHAR(100),
    alert_severity VARCHAR(20),  -- "info", "warning", "critical"
    recommendation TEXT,
    clinician_action VARCHAR(50),  -- "accepted", "rejected", "dismissed"
    displayed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action_taken_at TIMESTAMP WITH TIME ZONE
);
```

---

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_cds_hooks_patient_view(cds_service):
    request = CDSHooksRequest(
        hook="patient-view",
        context={"patientId": "patient-123"}
    )
    response = await cds_service.process_hook(request)
    assert len(response.cards) > 0
    assert response.cards[0].indicator in ["info", "warning", "critical"]
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_cds_hooks_endpoint(async_client):
    response = await async_client.post(
        "/cds-services/patient-view",
        json={
            "hook": "patient-view",
            "context": {"patientId": "patient-123"}
        }
    )
    assert response.status_code == 200
    assert "cards" in response.json()
```

---

## Deployment Considerations

### Environment Variables
```bash
CDS_ENABLED=true
FHIR_BASE_URL=http://localhost:8080/fhir
CDS_HOOKS_BASE_URL=http://localhost:8080/cds-services
GUIDELINES_DB_PATH=/app/data/clinical_guidelines.json
```

---

## Open Questions

1. **Guideline Sources**: Which clinical guidelines to include? (ADA, AHA, USPSTF, NICE?)
2. **EHR Integration**: Start with Epic or Cerner?
3. **Drug Interaction Database**: Use commercial API (Lexicomp, Micromedex) or open-source?
4. **Alert Fatigue**: How to minimize false positive alerts?

---

**Status**: Ready for review and approval
**Next Steps**: Create Technical Plan for Sprint 6 (CDS) after specification approval
**Dependencies**: Base Application, FHIR R4 support
**Estimated Effort**: 150 hours over 5 weeks
