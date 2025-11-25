# Technical Plan: Clinical Decision Support Module with Meditech Integration (Sprint 6)

**Version**: 1.0.0
**Date**: 2025-11-23
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Based on**: Sprint 6 Specification v2.0.0
**Estimated Duration**: 12 weeks (~360 hours)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [API Design](#api-design)
6. [Implementation Phases](#implementation-phases)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Plan](#deployment-plan)
9. [Dependencies](#dependencies)
10. [Risks & Mitigations](#risks--mitigations)

---

## Overview

### Goals

Build a Clinical Decision Support (CDS) system that:
1. **Reads patient data** from Meditech Expanse via FHIR R4 API
2. **Evaluates clinical guidelines** (ADA, AHA, USPSTF, NICE) against patient data
3. **Checks drug interactions** using NHS dm+d medication database
4. **Writes draft orders** to Meditech (MedicationRequest, ServiceRequest, Task, CommunicationRequest)
5. **Enforces clinical governance** (RBAC, approval workflows, safety checks)

### Implementation Approach

**Two-Phase Approach**:
1. **Phase A (Weeks 1-8)**: Build CDS core with **mock FHIR integration** (testable locally)
2. **Phase B (Weeks 9-12)**: Replace mocks with **real Meditech integration** (requires Meditech sandbox access)

**Why**: Meditech sandbox access/verification is a prerequisite that may take time to obtain. This approach allows development to start immediately using mock data, then integrate with Meditech once access is available.

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Meditech Expanse                         │
│                   (meditech-uk.cloud FHIR API)                   │
└────────┬────────────────────────────────────────────┬───────────┘
         │ READ (Patient, Condition,                  │ WRITE
         │  Observation, MedicationRequest)           │ (MedicationRequest,
         │                                            │  ServiceRequest,
         │                                            │  Task, Comm)
         ▼                                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    FHIR Integration Layer                       │
│  ┌─────────────────┐       ┌──────────────────────────────┐   │
│  │ FHIRClient      │       │ NHS FHIR UK Core Validator    │   │
│  │ (OAuth 2.0)     │       │ (dm+d, ODS, NHS number)       │   │
│  └─────────────────┘       └──────────────────────────────┘   │
└────────┬───────────────────────────────────────────┬───────────┘
         │                                            │
         ▼                                            ▼
┌────────────────────────────────────────────────────────────────┐
│                        CDS Core Engine                          │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────┐   │
│  │ Rules Engine │  │ Drug Interaction │  │ Recommendation │   │
│  │ (Guidelines) │  │ Checker (dm+d)   │  │ Generator      │   │
│  └──────────────┘  └─────────────────┘  └────────────────┘   │
└────────┬──────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│                      Clinical Governance                        │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ RBAC       │  │ Safety       │  │ Approval Workflow    │  │
│  │ (Roles)    │  │ Checks       │  │ (Draft → Review)     │  │
│  └────────────┘  └──────────────┘  └──────────────────────┘  │
└────────┬──────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│                          Data Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ PostgreSQL  │  │ Redis Cache  │  │ Audit Logs         │   │
│  │ (Guidelines,│  │ (Patient     │  │ (CDS Actions)      │   │
│  │  dm+d,      │  │  Data, 5min) │  │                    │   │
│  │  Rules)     │  │              │  │                    │   │
│  └─────────────┘  └──────────────┘  └────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

1. **FHIR Integration Layer**:
   - `FHIRClient`: OAuth 2.0 authentication, FHIR R4 read/write operations
   - `NHSFHIRValidator`: Validates NHS FHIR UK Core profiles (dm+d codes, ODS codes, NHS numbers)

2. **CDS Core Engine**:
   - `RulesEngine`: Evaluates clinical guidelines against patient data (IF-THEN logic)
   - `DrugInteractionChecker`: Checks new medications vs current medications (NHS dm+d database)
   - `RecommendationGenerator`: Generates recommendations with explanations, evidence grading

3. **Clinical Governance**:
   - `RBAC`: Role-based access control (doctors, pharmacists, nurses)
   - `SafetyChecks`: Drug allergies, contraindications, duplicate orders
   - `ApprovalWorkflow`: Draft orders → clinician review → finalize

4. **Data Layer**:
   - `PostgreSQL`: Clinical guidelines, NHS dm+d, CDS rules, patient data cache
   - `Redis`: Short-term patient data cache (5-minute TTL, reduce Meditech API calls)
   - `Audit Logs`: All CDS reads/writes to Meditech (HIPAA compliance)

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **FHIR Library** | `fhir.resources` | 7.1.0 | FHIR R4 resource models (Python) |
| **HTTP Client** | `httpx` | 0.27.0 | Async HTTP for Meditech API calls |
| **OAuth 2.0** | `authlib` | 1.3.0 | OAuth 2.0 client for Meditech auth |
| **Rules Engine** | `business-rules` | 1.0.1 | IF-THEN clinical guidelines engine |
| **Validation** | `jsonschema` | 4.22.0 | NHS FHIR UK Core validation |
| **Caching** | `redis` | 5.0.3 | Patient data cache (5-min TTL) |
| **Database** | `asyncpg` | 0.29.0 | PostgreSQL async driver |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **UI Framework** | Vue 3 | 3.4.0 | Reactive UI components |
| **Component Library** | Vuetify 3 | 3.6.0 | Material Design components |
| **Charts** | Chart.js | 4.4.0 | Recommendation visualizations |

### External Services

| Service | Purpose | URL |
|---------|---------|-----|
| **Meditech Expanse** | Patient data (FHIR R4) | `https://meditech-uk.cloud/fhir/r4` |
| **NHS dm+d** | UK medication dictionary | TRUD download (monthly updates) |
| **ODS (Org Data Service)** | NHS organization codes | `https://directory.spineservices.nhs.uk/ORD/2-0-0` |

---

## Database Schema

### Table: `cds_guidelines`

Clinical guidelines database (ADA, AHA, USPSTF, NICE).

```sql
CREATE TABLE cds_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guideline_source VARCHAR(50) NOT NULL,  -- 'ADA', 'AHA', 'USPSTF', 'NICE'
    guideline_name VARCHAR(255) NOT NULL,   -- 'Diabetes Type 2 Management'
    condition_code VARCHAR(50) NOT NULL,    -- ICD-10 or SNOMED CT code
    recommendation TEXT NOT NULL,           -- 'Start metformin 500mg BD'
    evidence_level VARCHAR(10) NOT NULL,    -- 'A', 'B', 'C'
    rationale TEXT NOT NULL,                -- Why this recommendation
    last_updated TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_guideline UNIQUE (guideline_source, guideline_name, condition_code)
);

CREATE INDEX idx_cds_guidelines_condition ON cds_guidelines (condition_code);
```

**Example Data**:
```sql
INSERT INTO cds_guidelines (guideline_source, guideline_name, condition_code, recommendation, evidence_level, rationale, last_updated) VALUES
('ADA', 'Type 2 Diabetes - First Line Therapy', 'E11.9', 'Start metformin 500mg BD', 'A', 'Metformin is first-line per ADA 2024 guidelines (reduces HbA1c by 1-2%)', '2024-01-15'),
('AHA', 'Hypertension - Blood Pressure Target', 'I10', 'Target BP <140/90 mmHg for most adults, <130/80 for diabetes/CKD', 'A', 'AHA 2017 guidelines reduce CVD events by 25%', '2017-11-13');
```

---

### Table: `cds_rules`

CDS decision rules (IF-THEN logic).

```sql
CREATE TABLE cds_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,   -- Higher = more urgent
    conditions JSONB NOT NULL,             -- IF conditions (JSON)
    actions JSONB NOT NULL,                -- THEN actions (JSON)
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cds_rules_active ON cds_rules (active);
CREATE INDEX idx_cds_rules_priority ON cds_rules (priority DESC);
```

**Example Data**:
```sql
INSERT INTO cds_rules (rule_name, description, priority, conditions, actions) VALUES
(
    'Diabetes - New Diagnosis - Start Metformin',
    'Patient with new T2DM diagnosis → recommend metformin + baseline labs',
    10,  -- High priority
    '{
        "condition_code": "E11.9",
        "diagnosis_age_days": {"max": 30},
        "current_medications": {"not_contains": "metformin"}
    }',
    '{
        "recommendations": [
            {
                "type": "medication",
                "code": "39113611000001102",
                "display": "Metformin 500mg oral tablet",
                "dosage": "500mg twice daily with meals",
                "guideline": "ADA 2024 - Type 2 Diabetes First Line Therapy"
            },
            {
                "type": "lab_order",
                "code": "43396009",
                "display": "HbA1c measurement",
                "reason": "Baseline HbA1c for diabetes monitoring",
                "guideline": "ADA 2024 - Initial Evaluation"
            }
        ]
    }'
);
```

---

### Table: `nhs_dmd_medications`

NHS Dictionary of Medicines and Devices (dm+d).

**Note**: Download from TRUD (Technology Reference Data Update Distribution), load monthly updates.

```sql
CREATE TABLE nhs_dmd_medications (
    dm_d_code VARCHAR(50) PRIMARY KEY,      -- dm+d code (e.g., '39113611000001102')
    name VARCHAR(500) NOT NULL,             -- 'Metformin 500mg oral tablet'
    vtm_code VARCHAR(50),                   -- Virtual Therapeutic Moiety code
    vmp_code VARCHAR(50),                   -- Virtual Medicinal Product code
    amp_code VARCHAR(50),                   -- Actual Medicinal Product code
    form VARCHAR(100),                      -- 'Oral tablet', 'Injection'
    strength VARCHAR(100),                  -- '500mg'
    unit VARCHAR(50),                       -- 'mg', 'ml'
    active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dmd_name ON nhs_dmd_medications USING gin(to_tsvector('english', name));
CREATE INDEX idx_dmd_vtm ON nhs_dmd_medications (vtm_code);
```

---

### Table: `drug_interactions`

Drug interaction database (from OpenFDA or commercial API).

```sql
CREATE TABLE drug_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_a_code VARCHAR(50) NOT NULL,       -- dm+d code or RxNorm
    drug_b_code VARCHAR(50) NOT NULL,       -- dm+d code or RxNorm
    severity VARCHAR(20) NOT NULL,          -- 'contraindicated', 'major', 'moderate', 'minor'
    description TEXT NOT NULL,              -- 'Increased bleeding risk'
    mechanism TEXT,                         -- 'Both inhibit platelet aggregation'
    alternative_drug_codes TEXT[],          -- [dm+d codes for safer alternatives]
    source VARCHAR(100),                    -- 'OpenFDA', 'Micromedex'
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_interaction UNIQUE (drug_a_code, drug_b_code)
);

CREATE INDEX idx_drug_interactions_a ON drug_interactions (drug_a_code);
CREATE INDEX idx_drug_interactions_b ON drug_interactions (drug_b_code);
CREATE INDEX idx_drug_interactions_severity ON drug_interactions (severity);
```

**Example Data**:
```sql
INSERT INTO drug_interactions (drug_a_code, drug_b_code, severity, description, mechanism, alternative_drug_codes, source) VALUES
('319864002', '387458008', 'major', 'Increased bleeding risk', 'Both warfarin and aspirin inhibit platelet aggregation and coagulation', ARRAY['108537001'], 'OpenFDA');
-- warfarin (319864002) + aspirin (387458008) → suggest clopidogrel (108537001)
```

---

### Table: `cds_recommendations`

Generated CDS recommendations (audit trail).

```sql
CREATE TABLE cds_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(100) NOT NULL,       -- NHS number or MRN
    rule_id UUID REFERENCES cds_rules(id),
    recommendation_type VARCHAR(50) NOT NULL, -- 'medication', 'lab_order', 'referral', 'task'
    recommendation_text TEXT NOT NULL,
    evidence_level VARCHAR(10),             -- 'A', 'B', 'C'
    priority VARCHAR(20) NOT NULL,          -- 'critical', 'high', 'medium', 'low'
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'rejected', 'cancelled'
    rejected_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ,
    created_by_user_id UUID REFERENCES users(id),
    CONSTRAINT check_status CHECK (status IN ('pending', 'accepted', 'rejected', 'cancelled'))
);

CREATE INDEX idx_cds_recommendations_patient ON cds_recommendations (patient_id);
CREATE INDEX idx_cds_recommendations_status ON cds_recommendations (status);
CREATE INDEX idx_cds_recommendations_created ON cds_recommendations (created_at DESC);
```

---

### Table: `meditech_write_log`

Audit log of all writes to Meditech (HIPAA compliance).

```sql
CREATE TABLE meditech_write_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,     -- 'MedicationRequest', 'ServiceRequest', 'Task'
    resource_id VARCHAR(100),               -- Meditech FHIR resource ID (if successful)
    fhir_bundle JSONB NOT NULL,             -- Full FHIR resource sent to Meditech
    http_status INTEGER,                    -- 201 (success), 400 (validation error), etc.
    response_body JSONB,                    -- Meditech API response
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id)
);

CREATE INDEX idx_meditech_write_patient ON meditech_write_log (patient_id);
CREATE INDEX idx_meditech_write_created ON meditech_write_log (created_at DESC);
CREATE INDEX idx_meditech_write_status ON meditech_write_log (http_status);
```

---

## API Design

### CDS API Endpoints

#### 1. Get CDS Recommendations for Patient

**Endpoint**: `GET /api/v1/cds/recommendations/{patient_id}`

**Description**: Fetch patient data from Meditech, evaluate CDS rules, return recommendations.

**Parameters**:
- `patient_id` (path): NHS number or Meditech MRN

**Response** (200 OK):
```json
{
  "patient_id": "1234567890",
  "recommendations": [
    {
      "id": "rec-uuid-1",
      "type": "medication",
      "priority": "high",
      "title": "Start Metformin for Type 2 Diabetes",
      "description": "Patient diagnosed with Type 2 Diabetes (E11.9) 15 days ago. No metformin prescribed.",
      "guideline": "ADA 2024 - Type 2 Diabetes First Line Therapy",
      "evidence_level": "A",
      "medication": {
        "dm_d_code": "39113611000001102",
        "name": "Metformin 500mg oral tablet",
        "dosage": "500mg twice daily with meals",
        "instructions": "Start with 500mg BD, titrate to 1000mg BD over 2 weeks if tolerated"
      },
      "actions": [
        {
          "label": "Create Draft Order",
          "action": "create_medication_request"
        },
        {
          "label": "Dismiss",
          "action": "dismiss"
        }
      ]
    },
    {
      "id": "rec-uuid-2",
      "type": "lab_order",
      "priority": "medium",
      "title": "Order HbA1c Baseline",
      "description": "Baseline HbA1c needed for diabetes monitoring.",
      "guideline": "ADA 2024 - Initial Evaluation",
      "evidence_level": "A",
      "lab_order": {
        "snomed_code": "43396009",
        "name": "Hemoglobin A1c measurement",
        "reason": "Baseline HbA1c for diabetes monitoring"
      }
    }
  ],
  "generated_at": "2025-11-23T10:30:00Z"
}
```

---

#### 2. Create Draft Order in Meditech

**Endpoint**: `POST /api/v1/cds/create-order`

**Description**: Create draft MedicationRequest/ServiceRequest/Task in Meditech.

**Request Body**:
```json
{
  "recommendation_id": "rec-uuid-1",
  "patient_id": "1234567890",
  "order_type": "medication_request",
  "medication": {
    "dm_d_code": "39113611000001102",
    "dosage": "500mg twice daily with meals"
  }
}
```

**Response** (201 Created):
```json
{
  "meditech_resource_id": "MedicationRequest/mt-12345",
  "status": "draft",
  "message": "Draft MedicationRequest created in Meditech. Clinician can review in order entry screen.",
  "meditech_url": "https://meditech-uk.cloud/orders/mt-12345"
}
```

---

#### 3. Check Drug Interactions

**Endpoint**: `POST /api/v1/cds/check-interactions`

**Description**: Check new medication vs patient's current medications.

**Request Body**:
```json
{
  "patient_id": "1234567890",
  "new_medication_code": "387458008"  // Aspirin (SNOMED CT)
}
```

**Response** (200 OK):
```json
{
  "interactions": [
    {
      "severity": "major",
      "interacting_medication": {
        "code": "319864002",
        "name": "Warfarin"
      },
      "description": "Increased bleeding risk",
      "mechanism": "Both warfarin and aspirin inhibit platelet aggregation",
      "alternatives": [
        {
          "code": "108537001",
          "name": "Clopidogrel 75mg oral tablet",
          "reason": "Safer antiplatelet option with warfarin"
        }
      ]
    }
  ]
}
```

---

#### 4. Admin: Manage CDS Rules

**Endpoint**: `POST /api/v1/cds/admin/rules`

**Description**: Create/update CDS rule (admin only).

**Request Body**:
```json
{
  "rule_name": "Hypertension - Uncontrolled - Add Medication",
  "description": "Patient with hypertension, BP ≥140/90 on last 2 visits → recommend add medication",
  "priority": 8,
  "conditions": {
    "condition_code": "I10",
    "systolic_bp": {"min": 140},
    "bp_measurements_count": 2,
    "current_medications_count": {"max": 2}
  },
  "actions": {
    "recommendations": [
      {
        "type": "medication",
        "options": ["ACE inhibitor", "Calcium channel blocker", "Thiazide diuretic"],
        "guideline": "AHA 2017 - Hypertension Management"
      }
    ]
  }
}
```

**Response** (201 Created):
```json
{
  "rule_id": "rule-uuid-5",
  "message": "CDS rule created successfully"
}
```

---

## Implementation Phases

### Phase 6.1: CDS Core Infrastructure (Weeks 1-3, 90 hours)

**Goal**: Build CDS core engine (rules, guidelines, recommendations) with **mock patient data**.

#### Tasks

1. **Setup FHIR Models** (15 hours)
   - Install `fhir.resources` Python package
   - Create Pydantic models for:
     - NHS FHIR UK Core Patient (NHS number validation)
     - UKCore-Condition (ICD-10, SNOMED CT codes)
     - UKCore-Observation (vital signs, lab results)
     - UKCore-MedicationRequest (dm+d codes)
   - Write unit tests (validate NHS number checksum, dm+d code format)

2. **Clinical Guidelines Database** (25 hours)
   - Create `cds_guidelines` table migration
   - Load initial guidelines:
     - ADA 2024: Type 2 Diabetes (10 guidelines)
     - AHA 2017: Hypertension (8 guidelines)
     - USPSTF: Preventive screening (15 guidelines)
     - NICE: UK-specific guidelines (10 guidelines)
   - Create guidelines API: `GET /api/v1/cds/guidelines` (search by condition, guideline source)
   - Write tests (43 guidelines loadable, searchable)

3. **CDS Rules Engine** (20 hours)
   - Install `business-rules` package (IF-THEN logic)
   - Create `cds_rules` table migration
   - Implement `RulesEngine` class:
     - `evaluate_rules(patient_data: dict) -> List[Recommendation]`
     - IF-THEN condition matching (JSON-based conditions)
     - Priority-based rule sorting
   - Create 5 initial rules:
     - Diabetes new diagnosis → metformin + HbA1c
     - Hypertension uncontrolled → add medication
     - Diabetes + no eye exam in 12 months → refer ophthalmology
     - Age ≥50, no colonoscopy → screening recommendation
     - CKD + ACE inhibitor contraindication → ARB alternative
   - Write tests (15+ unit tests, rule matching logic)

4. **Recommendation Generator** (20 hours)
   - Create `RecommendationGenerator` class:
     - `generate(rule_match: RuleMatch, patient_data: dict) -> Recommendation`
     - Add evidence level (A/B/C) from guidelines
     - Add explanation text (why recommended, which guideline)
     - Priority calculation (critical/high/medium/low)
   - Create `cds_recommendations` table migration
   - Implement recommendation CRUD API:
     - `POST /api/v1/cds/recommendations` (generate)
     - `PATCH /api/v1/cds/recommendations/{id}` (accept/reject)
   - Write tests (20+ unit tests, recommendation generation)

5. **Mock Patient Data Service** (10 hours)
   - Create `MockFHIRService` class (returns fake patient data)
   - Mock patient profiles (5 patients):
     - Patient 1: New T2DM diagnosis (triggers metformin rule)
     - Patient 2: Uncontrolled hypertension (triggers medication rule)
     - Patient 3: Diabetes + no eye exam (triggers referral rule)
     - Patient 4: Age 55, no colonoscopy (triggers screening rule)
     - Patient 5: CKD + ACE inhibitor allergy (triggers ARB rule)
   - Write tests (mock service returns valid FHIR resources)

**Deliverable**: CDS engine evaluates rules against mock patient data, generates recommendations (testable via API).

**Testing**: 78+ unit tests, all passing.

---

### Phase 6.2: Meditech Read Integration (Weeks 4-5, 60 hours)

**Goal**: Replace `MockFHIRService` with real Meditech FHIR API integration.

#### Tasks

1. **OAuth 2.0 Authentication** (15 hours)
   - Install `authlib` package
   - Create `MeditechOAuthClient` class:
     - OAuth 2.0 client credentials flow
     - Token caching in Redis (avoid repeated auth)
     - Token refresh on expiry
   - Store credentials in environment variables:
     - `MEDITECH_CLIENT_ID`
     - `MEDITECH_CLIENT_SECRET`
     - `MEDITECH_TOKEN_URL=https://meditech-uk.cloud/oauth2/token`
   - Write tests (12 tests: token fetch, refresh, expiry handling)

2. **FHIR Read Operations** (20 hours)
   - Create `MeditechFHIRClient` class:
     - `get_patient(nhs_number: str) -> UKCorePatient`
     - `get_conditions(patient_id: str) -> List[UKCoreCondition]`
     - `get_observations(patient_id: str) -> List[UKCoreObservation]`
     - `get_medication_requests(patient_id: str) -> List[UKCoreMedicationRequest]`
   - HTTP client: `httpx.AsyncClient` (async API calls)
   - Error handling:
     - 401 Unauthorized → retry with token refresh
     - 404 Not Found → return empty list
     - 429 Rate Limit → exponential backoff (retry after 1s, 2s, 4s)
     - 500 Server Error → log error, return empty list
   - Write tests (25 tests: read operations, error handling, retries)

3. **NHS FHIR UK Core Validation** (15 hours)
   - Create `NHSFHIRValidator` class:
     - `validate_nhs_number(nhs_number: str) -> bool` (10-digit, checksum validation)
     - `validate_dm_d_code(code: str) -> bool` (18-digit SNOMED CT dm+d code)
     - `validate_ods_code(code: str) -> bool` (organization code format)
   - Checksum algorithm: NHS number Modulus 11 checksum
   - Write tests (18 tests: valid/invalid NHS numbers, dm+d codes, ODS codes)

4. **Patient Data Caching** (5 hours)
   - Create `PatientDataCache` class (Redis backend):
     - `get_patient_data(patient_id: str) -> Optional[dict]`
     - `set_patient_data(patient_id: str, data: dict, ttl=300)` (5-minute TTL)
   - Cache key format: `patient:fhir:{nhs_number}`
   - Cache hit reduces Meditech API calls (important for rate limiting)
   - Write tests (8 tests: cache get/set, expiry, cache misses)

5. **Integration Test with Meditech Sandbox** (5 hours)
   - **Prerequisite**: Meditech sandbox access (OAuth credentials, test patient data)
   - Test real FHIR read operations:
     - Fetch test patient from Meditech sandbox
     - Verify conditions, observations, medications returned
   - Log API response times (target: <500ms per FHIR read)
   - Write tests (5 integration tests, run against Meditech sandbox)

**Deliverable**: CDS can read patient data from Meditech sandbox, cache in Redis.

**Testing**: 68 tests total (55 unit + 13 integration).

---

### Phase 6.3: Drug Interaction Checking (Weeks 6, 30 hours)

**Goal**: Implement drug interaction checking using NHS dm+d medication database.

#### Tasks

1. **Download and Load NHS dm+d** (10 hours)
   - Download dm+d from TRUD: https://isd.digital.nhs.uk/trud3/user/guest/group/0/pack/6
   - Create `nhs_dmd_medications` table migration
   - Create ETL script: `scripts/load_dmd.py`
     - Parse dm+d XML files (VTM, VMP, AMP)
     - Load into PostgreSQL
     - ~200,000 medication records
   - Create search API: `GET /api/v1/cds/medications/search?q=metformin`
   - Write tests (10 tests: dm+d loading, search functionality)

2. **Drug Interaction Database Setup** (10 hours)
   - Option A: OpenFDA Drug Interactions API (free, public)
     - URL: https://api.fda.gov/drug/drugsfda.json
     - Pros: Free, comprehensive
     - Cons: Uses RxNorm codes (need mapping to dm+d)
   - Option B: Commercial API (Micromedex, First Databank)
     - Pros: Supports NHS dm+d codes, clinical-grade
     - Cons: Expensive (£10,000+/year)
   - **Recommendation**: Start with OpenFDA (free), create RxNorm ↔ dm+d mapping table
   - Create `drug_interactions` table migration
   - Load initial interactions from OpenFDA (top 50 common interactions)
   - Write tests (8 tests: interaction loading, querying)

3. **Interaction Detection Logic** (5 hours)
   - Create `DrugInteractionChecker` class:
     - `check_interactions(new_medication_code: str, current_medications: List[str]) -> List[Interaction]`
     - Query `drug_interactions` table (JOIN on drug_a_code, drug_b_code)
     - Severity filtering (return contraindicated + major + moderate, skip minor)
   - Create API: `POST /api/v1/cds/check-interactions`
   - Write tests (12 tests: interaction detection, severity filtering)

4. **Alternative Medication Suggestions** (5 hours)
   - Create `AlternativeFinder` class:
     - `find_alternatives(interacting_medication: str, therapeutic_class: str) -> List[str]`
     - Query dm+d for same therapeutic class (VTM level)
     - Exclude interacting medications
     - Sort by usage frequency (most prescribed first)
   - Example: Warfarin + Aspirin interaction → suggest Clopidogrel
   - Write tests (10 tests: alternative suggestions, therapeutic class matching)

**Deliverable**: CDS checks drug interactions, suggests safer alternatives.

**Testing**: 40 tests total.

---

### Phase 6.4: Meditech Write Integration (Weeks 7-9, 90 hours)

**Goal**: Implement FHIR write operations to create draft orders in Meditech.

#### Tasks

1. **POST MedicationRequest** (20 hours)
   - Create `MeditechOrderCreator` class:
     - `create_medication_request(patient_id: str, medication: dict) -> FHIRResponse`
     - POST `https://meditech-uk.cloud/fhir/r4/MedicationRequest`
     - NHS FHIR UK Core UKCore-MedicationRequest profile
   - Required fields:
     - `status: "draft"` (requires clinician approval)
     - `intent: "order"`
     - `medicationCodeableConcept: {coding: [{system: "https://dmd.nhs.uk", code: dm_d_code}]}`
     - `subject: {reference: "Patient/{nhs_number}"}`
     - `requester: {reference: "Device/cds-system"}` (CDS system as requester)
     - `dosageInstruction: [{text: "500mg twice daily with meals"}]`
   - Error handling:
     - 400 Bad Request → validation error (log specific field)
     - 403 Forbidden → insufficient permissions (log user role)
     - 422 Unprocessable Entity → business rule violation (e.g., duplicate order)
   - Write tests (18 tests: successful POST, validation errors, permission errors)

2. **POST ServiceRequest** (20 hours)
   - Create `create_service_request(patient_id: str, service: dict) -> FHIRResponse`
   - POST `https://meditech-uk.cloud/fhir/r4/ServiceRequest`
   - NHS FHIR UK Core UKCore-ServiceRequest profile
   - Required fields:
     - `status: "draft"`
     - `intent: "order"`
     - `code: {coding: [{system: "http://snomed.info/sct", code: snomed_code}]}`
     - `subject: {reference: "Patient/{nhs_number}"}`
     - `requester: {reference: "Device/cds-system"}`
   - Use cases:
     - Lab orders (HbA1c, lipid panel, urine ACR)
     - Imaging orders (chest X-ray, echocardiogram)
     - Referrals (cardiology, endocrinology, ophthalmology)
   - Write tests (18 tests: lab orders, imaging orders, referrals)

3. **POST Task** (15 hours)
   - Create `create_task(patient_id: str, task: dict) -> FHIRResponse`
   - POST `https://meditech-uk.cloud/fhir/r4/Task`
   - Required fields:
     - `status: "requested"`
     - `intent: "order"`
     - `code: {coding: [{code: "follow-up"}]}`
     - `for: {reference: "Patient/{nhs_number}"}`
     - `owner: {reference: "Practitioner/{practitioner_id}"}` (assigned clinician)
     - `description: "Schedule 3-month diabetes follow-up appointment"`
   - Use cases:
     - Schedule follow-up appointments
     - Review lab results
     - Patient education tasks
   - Write tests (12 tests: task creation, assignment, descriptions)

4. **POST CommunicationRequest** (15 hours)
   - Create `create_communication_request(patient_id: str, alert: dict) -> FHIRResponse`
   - POST `https://meditech-uk.cloud/fhir/r4/CommunicationRequest`
   - Required fields:
     - `status: "active"`
     - `priority: "routine" | "urgent" | "stat"`
     - `subject: {reference: "Patient/{nhs_number}"}`
     - `recipient: [{reference: "Practitioner/{practitioner_id}"}]`
     - `payload: [{contentString: "Patient overdue for HbA1c (last: 14 months ago)"}]`
   - Alert appears in Meditech InBasket (clinician's task inbox)
   - Write tests (10 tests: alert creation, priority levels, InBasket delivery)

5. **NHS FHIR UK Core Write Validation** (10 hours)
   - Create `validate_write_request(resource: dict, resource_type: str) -> ValidationResult`
   - Validations:
     - dm+d code exists in `nhs_dmd_medications` table
     - ODS code valid (query ODS API: `https://directory.spineservices.nhs.uk/ORD/2-0-0`)
     - NHS number checksum valid (Modulus 11)
     - SNOMED CT code valid (use UK edition terminology server)
   - Return validation errors with field-level details
   - Write tests (15 tests: valid/invalid dm+d, ODS, NHS numbers, SNOMED CT)

6. **Transaction Bundles** (5 hours)
   - Create `create_transaction_bundle(resources: List[dict]) -> FHIRResponse`
   - POST `https://meditech-uk.cloud/fhir/r4` (Bundle with type="transaction")
   - Example: Create metformin + HbA1c order + follow-up task (all or nothing)
   - FHIR Bundle structure:
     ```json
     {
       "resourceType": "Bundle",
       "type": "transaction",
       "entry": [
         {"request": {"method": "POST", "url": "MedicationRequest"}, "resource": {...}},
         {"request": {"method": "POST", "url": "ServiceRequest"}, "resource": {...}},
         {"request": {"method": "POST", "url": "Task"}, "resource": {...}}
       ]
     }
     ```
   - Meditech processes all resources atomically (all succeed or all fail)
   - Write tests (8 tests: successful bundles, partial failures, rollback)

7. **Write Error Handling** (5 hours)
   - Create `handle_write_error(response: httpx.Response) -> None`
   - Error scenarios:
     - Meditech rejection (400/422): Log error, notify clinician via in-app alert
     - Validation errors: Return specific field errors to frontend
     - Network errors (500/503): Retry with exponential backoff (3 retries max: 1s, 2s, 4s)
     - Rate limiting (429): Queue write request, process when rate limit resets
   - Create `meditech_write_log` table (audit trail)
   - Write tests (12 tests: error handling, retries, audit logging)

**Deliverable**: CDS can write draft orders (MedicationRequest, ServiceRequest, Task, CommunicationRequest) to Meditech.

**Testing**: 93 tests total.

---

### Phase 6.5: Clinical Governance & RBAC (Week 10, 30 hours)

**Goal**: Implement role-based access control, safety checks, approval workflows.

#### Tasks

1. **Role-Based Write Permissions** (10 hours)
   - Extend existing RBAC system (from Phase 2):
     - Add roles: `cds_doctor`, `cds_pharmacist`, `cds_nurse`
   - Permission matrix:
     | Role | MedicationRequest | ServiceRequest | Task | CommunicationRequest |
     |------|-------------------|----------------|------|----------------------|
     | Doctor | ✅ Create draft | ✅ Create draft | ✅ Create | ✅ Create |
     | Pharmacist | ✅ Create draft (medication review only) | ❌ | ✅ Create | ✅ Create |
     | Nurse | ❌ | ❌ | ✅ Create | ✅ Create |
   - Decorator: `@require_cds_role("doctor", "pharmacist")`
   - Write tests (15 tests: permission checks, role enforcement)

2. **Approval Workflows** (10 hours)
   - Draft order workflow:
     1. CDS creates MedicationRequest with `status="draft"`
     2. Draft appears in Meditech order entry screen
     3. Clinician reviews, modifies if needed, signs → `status="active"`
     4. Final order sent to pharmacy/lab
   - Admin setting: `CDS_AUTO_FINALIZE_ORDERS` (default: `false`, requires clinical governance approval)
   - Low-risk scenarios where auto-finalize may be allowed:
     - Preventive screening (mammography, colonoscopy)
     - Flu vaccination reminders
     - NOT allowed: Medication orders (too risky)
   - Write tests (12 tests: draft order creation, clinician approval, auto-finalize settings)

3. **Clinical Safety Checks** (5 hours)
   - Create `SafetyChecker` class:
     - `check_drug_allergies(patient_id: str, medication_code: str) -> List[Alert]`
       - Query Meditech AllergyIntolerance resources
       - Alert if new medication matches allergy
     - `check_contraindications(patient_id: str, medication_code: str) -> List[Alert]`
       - Check conditions (e.g., ACE inhibitor contraindicated in pregnancy)
     - `check_duplicate_orders(patient_id: str, medication_code: str) -> List[Alert]`
       - Check if same medication already ordered (prevent duplicates)
   - Safety checks run BEFORE creating draft order
   - If critical alert (e.g., allergy), block order creation, show error
   - Write tests (15 tests: allergy checking, contraindications, duplicate detection)

4. **Override Tracking** (5 hours)
   - When clinician rejects CDS recommendation:
     - Capture rejection reason (free text or dropdown)
     - Log in `cds_recommendations` table: `status="rejected"`, `rejected_reason="Patient declined metformin"`
     - Audit log entry (HIPAA compliance)
   - Create API: `PATCH /api/v1/cds/recommendations/{id}/reject`
   - Write tests (8 tests: rejection tracking, audit logging, reasons)

**Deliverable**: CDS respects RBAC, creates draft orders only, runs safety checks, tracks overrides.

**Testing**: 50 tests total.

---

### Phase 6.6: Meditech Workflow Integration (Week 11, 30 hours)

**Goal**: Integrate CDS alerts into Meditech clinician workflows (InBasket, order entry).

#### Tasks

1. **InBasket Integration** (10 hours)
   - **Meditech InBasket**: Clinician's task inbox in Meditech Expanse
   - CDS alerts delivered via CommunicationRequest (created in Phase 6.4)
   - Test InBasket delivery:
     - Create CommunicationRequest with `priority="urgent"`
     - Verify alert appears in Meditech sandbox InBasket
     - Clinician clicks alert → link to CDS recommendation UI
   - Write tests (5 tests: InBasket delivery, alert priority, link navigation)

2. **Order Entry Pre-Population** (10 hours)
   - **Goal**: CDS recommendations pre-fill Meditech order forms (not require manual re-entry)
   - Mechanism:
     - CDS creates draft MedicationRequest
     - Meditech reads draft MedicationRequest
     - Meditech pre-populates order entry form fields:
       - Medication name (from dm+d code)
       - Dosage (from dosageInstruction)
       - Frequency, route
     - Clinician reviews, modifies if needed, signs
   - Test order entry pre-population:
     - Create draft MedicationRequest for metformin
     - Open Meditech order entry screen
     - Verify fields pre-populated
   - Write tests (8 tests: pre-population, field values, clinician modifications)

3. **Task Creation** (5 hours)
   - CDS creates Task resources in Meditech (follow-up appointments, lab review)
   - Tasks appear in Meditech task list
   - Test task creation:
     - CDS creates Task: "Schedule 3-month diabetes follow-up"
     - Verify task appears in Meditech task list
     - Task assigned to clinician (owner field)
   - Write tests (5 tests: task creation, assignment, task list display)

4. **UI Testing with Meditech Sandbox** (5 hours)
   - Manual testing with Meditech Expanse sandbox:
     - Login as clinician
     - View InBasket alerts
     - Click alert → navigate to CDS recommendation
     - Review draft order in order entry screen
     - Sign order → verify status changes to "active"
   - Document workflow with screenshots
   - Write tests (5 integration tests: full workflow end-to-end)

**Deliverable**: CDS alerts appear in Meditech InBasket, draft orders pre-populate Meditech forms, tasks appear in task list.

**Testing**: 23 tests total.

---

### Phase 6.7: Testing & Validation (Week 12, 30 hours)

**Goal**: Comprehensive testing (unit, integration, UAT), performance validation.

#### Tasks

1. **Unit Tests** (10 hours)
   - Target: 90% code coverage for Sprint 6 code
   - Focus areas:
     - CDS rules engine (rule matching, priority sorting)
     - Drug interaction checker (interaction detection, alternatives)
     - FHIR validators (NHS number, dm+d codes, ODS codes)
     - Safety checkers (allergies, contraindications, duplicates)
   - Use `pytest` + `pytest-cov` (coverage reporting)
   - Write tests (100+ unit tests, 90% coverage target)

2. **Integration Tests** (10 hours)
   - Test Meditech FHIR API integration:
     - OAuth 2.0 authentication (token fetch, refresh)
     - FHIR read operations (Patient, Condition, Observation, MedicationRequest)
     - FHIR write operations (MedicationRequest, ServiceRequest, Task, CommunicationRequest)
     - Transaction bundles (atomic writes, rollback on error)
   - Test Redis caching (patient data cache, token cache)
   - Test database (guidelines, rules, dm+d, interactions)
   - Use Meditech sandbox (or mock FHIR server if sandbox unavailable)
   - Write tests (40+ integration tests)

3. **User Acceptance Testing (UAT)** (5 hours)
   - Recruit 2-3 pilot clinicians (doctors or pharmacists)
   - UAT scenarios:
     - Scenario 1: Patient with new T2DM diagnosis
       - CDS recommends metformin + HbA1c
       - Clinician reviews recommendation in InBasket
       - Clinician creates draft order from CDS
       - Clinician signs order in Meditech
     - Scenario 2: Drug interaction detected
       - Patient on warfarin
       - Clinician attempts to prescribe aspirin
       - CDS alerts: "Major interaction - increased bleeding risk"
       - CDS suggests alternative: Clopidogrel
       - Clinician accepts alternative
     - Scenario 3: Preventive screening reminder
       - Patient age 55, no colonoscopy
       - CDS recommends colonoscopy referral
       - Clinician creates ServiceRequest
   - Collect feedback (usability, accuracy, workflow integration)
   - UAT sign-off criteria:
     - All 3 scenarios completed successfully
     - Clinician satisfaction score ≥4/5
     - No critical usability issues

4. **Performance Testing** (5 hours)
   - Performance targets (from NFRs):
     - CDS recommendation generation: <2 seconds (99th percentile)
     - Meditech FHIR read: <500ms per resource
     - Meditech FHIR write: <1 second per resource
     - Concurrent users: 50 clinicians (no degradation)
   - Load testing tools: `locust` (Python load testing)
   - Test scenarios:
     - 50 concurrent users requesting CDS recommendations
     - 100 drug interaction checks per minute
     - 20 draft orders created per minute
   - Measure response times, throughput, error rates
   - Write tests (10 performance tests)

**Deliverable**: 90% code coverage, UAT sign-off, performance targets met.

**Testing**: 150+ tests total (100 unit + 40 integration + 10 performance).

---

## Testing Strategy

### Test Coverage Targets

| Component | Unit Tests | Integration Tests | E2E Tests | Coverage Target |
|-----------|------------|-------------------|-----------|-----------------|
| **CDS Rules Engine** | 50 tests | 10 tests | 5 tests | 95% |
| **Drug Interaction Checker** | 30 tests | 8 tests | 3 tests | 90% |
| **FHIR Client (Meditech)** | 40 tests | 25 tests | 10 tests | 85% |
| **Recommendation Generator** | 25 tests | 5 tests | 3 tests | 90% |
| **Safety Checker** | 20 tests | 5 tests | 3 tests | 95% |
| **RBAC** | 15 tests | 5 tests | 2 tests | 95% |
| **TOTAL** | 180 tests | 58 tests | 26 tests | **90%** |

### Testing Tools

- **Unit Tests**: `pytest` (Python), `vitest` (Vue 3)
- **Integration Tests**: `pytest` + `httpx` (mock Meditech API)
- **E2E Tests**: `playwright` (browser automation)
- **Performance Tests**: `locust` (load testing)
- **Coverage**: `pytest-cov` (code coverage reporting)

---

## Deployment Plan

### Environment Setup

1. **Development** (local):
   - PostgreSQL 15 (guidelines, dm+d, interactions)
   - Redis 7 (patient data cache, token cache)
   - Mock Meditech FHIR server (for development without sandbox access)

2. **Staging** (Meditech sandbox):
   - PostgreSQL 15 (production-like data)
   - Redis 7 (production-like cache)
   - Meditech Expanse sandbox (`https://meditech-uk.cloud/fhir/r4`)
   - OAuth 2.0 test credentials

3. **Production** (NHS trust):
   - PostgreSQL 15 (production data)
   - Redis 7 (production cache)
   - Meditech Expanse production (`https://meditech-nhs-trust.cloud/fhir/r4`)
   - OAuth 2.0 production credentials
   - Clinical governance approval required before go-live

### Deployment Steps

1. **Week 0**: Obtain Meditech sandbox access, OAuth credentials
2. **Weeks 1-3**: Develop CDS core with mock data (no Meditech required)
3. **Weeks 4-5**: Integrate with Meditech sandbox (read operations)
4. **Weeks 6-9**: Implement write operations (draft orders)
5. **Weeks 10-12**: Testing, UAT, clinical governance review
6. **Production Go-Live**: After UAT sign-off, deploy to production Meditech

---

## Dependencies

### External Dependencies

1. **Meditech Expanse Sandbox Access** (CRITICAL)
   - OAuth 2.0 credentials
   - Test patient data
   - FHIR read/write permissions
   - Timeline: Request in Week 0, expect 2-4 weeks for access

2. **NHS dm+d Database** (CRITICAL)
   - Download from TRUD: https://isd.digital.nhs.uk/trud3/user/guest/group/0/pack/6
   - Requires NHS Digital account (free)
   - Updates: Monthly (load latest dm+d on 1st of each month)

3. **Drug Interaction Database**
   - Option A: OpenFDA (free, public, uses RxNorm)
   - Option B: Commercial API (Micromedex, FDB) - £10,000+/year
   - Recommendation: Start with OpenFDA

4. **Clinical Governance Approval** (for production)
   - NHS trust clinical safety officer review
   - Approval for draft order creation
   - Approval for InBasket alert delivery
   - Timeline: 4-8 weeks (start in Week 4-6 of development)

### Internal Dependencies

1. **Sprint 5: Clinical Coding** (ICD-10, SNOMED CT)
   - CDS rules match on ICD-10 condition codes
   - Requires Sprint 5 complete (ICD-10 coding service)

2. **Base Application**: Authentication, RBAC, Audit Logging
   - CDS extends existing RBAC (add CDS-specific roles)
   - CDS uses existing audit logging (HIPAA compliance)

---

## Risks & Mitigations

### Risk 1: Meditech Sandbox Access Delayed

**Likelihood**: MEDIUM | **Impact**: HIGH

**Mitigation**:
- **Week 0**: Request Meditech sandbox access immediately
- **Parallel development**: Build CDS core with mock data (Weeks 1-3) while waiting for sandbox
- **Fallback**: Use public FHIR test servers (Synthea, HAPI FHIR) for development
- **Timeline buffer**: 12-week plan includes 2-week buffer for delays

---

### Risk 2: Meditech FHIR API Doesn't Support Write Operations

**Likelihood**: LOW | **Impact**: HIGH

**Mitigation**:
- **Week 0**: Verify Meditech CapabilityStatement: `GET https://meditech-uk.cloud/fhir/r4/metadata`
- Check for write permissions: `MedicationRequest`, `ServiceRequest`, `Task`, `CommunicationRequest`
- **Fallback**: If write not supported, implement read-only CDS (display recommendations in standalone UI, clinician manually creates orders in Meditech)

---

### Risk 3: NHS dm+d Medication Code Mapping Complexity

**Likelihood**: MEDIUM | **Impact**: MEDIUM

**Mitigation**:
- **Week 0**: Query Meditech MedicationRequest resources, inspect medication codes
- If Meditech uses RxNorm: Create mapping table (RxNorm ↔ dm+d)
- If Meditech uses SNOMED CT drugs: Use SNOMED CT dm+d extension
- **Contingency**: Use multi-code-system drug interaction database (supports RxNorm, dm+d, SNOMED CT)

---

### Risk 4: Clinical Governance Rejects Automated Ordering

**Likelihood**: MEDIUM | **Impact**: HIGH

**Mitigation**:
- **Early engagement**: Present CDS design to clinical safety officer (Week 4-6)
- **Draft orders only**: CDS creates draft orders (status="draft") requiring clinician approval (safest approach)
- **Safety checks**: Drug allergies, contraindications, duplicate orders (Phase 6.5)
- **Audit trail**: Comprehensive logging (HIPAA compliance)
- **Pilot program**: Start with 2-3 clinicians, low-risk recommendations
- **Fallback**: If automated ordering rejected, implement read-only CDS (recommendation display only)

---

## Appendix

### Glossary

- **CDS**: Clinical Decision Support
- **dm+d**: NHS Dictionary of Medicines and Devices (UK medication codes)
- **FHIR**: Fast Healthcare Interoperability Resources (HL7 standard)
- **ODS**: Organisation Data Service (NHS organization codes)
- **TRUD**: Technology Reference Data Update Distribution (NHS terminology downloads)
- **UAT**: User Acceptance Testing
- **VTM**: Virtual Therapeutic Moiety (dm+d medication level)
- **VMP**: Virtual Medicinal Product (dm+d medication level)
- **AMP**: Actual Medicinal Product (dm+d medication level)

---

## Next Steps

1. **Immediate (Week 0)**:
   - Request Meditech sandbox access (OAuth credentials, test patient data)
   - Create NHS Digital account, download NHS dm+d from TRUD
   - Review Sprint 6 specification with stakeholders (clinical safety officer, Meditech integration team)

2. **Week 1**: Start Phase 6.1 (CDS Core Infrastructure)
   - Setup FHIR models (`fhir.resources` package)
   - Create clinical guidelines database (ADA, AHA, USPSTF, NICE)
   - Implement CDS rules engine (IF-THEN logic)

3. **Week 4**: Engage clinical governance
   - Present CDS design to NHS trust clinical safety officer
   - Get approval for draft order creation approach
   - Clarify safety requirements (allergies, contraindications, audit logging)

4. **Week 12**: UAT and production readiness
   - Complete UAT with 2-3 pilot clinicians
   - Performance testing (50 concurrent users)
   - Final clinical governance approval
   - Production deployment planning

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-23
**Status**: ✅ Ready for Development
**Estimated Completion**: Week 12 (360 hours total)
