# Specification: Clinical Decision Support Module with Meditech Expanse Integration (Sprint 6)

**Version**: 2.0.0
**Date**: 2025-11-17
**Status**: Draft - Critical Analysis Revised
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 12 weeks (~360 hours)

**Version History**:
- **1.0.0** (2025-11-17): Initial specification for generic CDS module
- **2.0.0** (2025-11-17): **MAJOR UPDATE** - Meditech Expanse bidirectional integration, NHS FHIR UK Core compliance, increased scope from 5 weeks to 12 weeks

---

## Executive Summary

**What Changed (v1.0 → v2.0)**:
- ✅ **EHR Platform**: Generic (Epic/Cerner) → **Meditech Expanse on meditech-uk.cloud**
- ✅ **Integration Type**: Read-only → **Bidirectional (read + write)**
- ✅ **FHIR Profile**: Base FHIR R4 → **NHS FHIR UK Core**
- ✅ **Medication Codes**: RxNorm → **NHS dm+d (Dictionary of Medicines and Devices)**
- ✅ **Duration**: 5 weeks → **12 weeks**
- ✅ **Effort**: 150 hours → **360 hours**
- ✅ **New Scope**: Clinical governance, approval workflows, bidirectional write operations

**Why This Matters**:
- Bidirectional integration enables CDS to **write orders directly to Meditech** (not just display recommendations)
- NHS UK compliance ensures **integration with UK NHS trust workflows**
- Clinical governance prevents **unsafe automated ordering**

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [Meditech Expanse Integration](#meditech-expanse-integration)
8. [NHS FHIR UK Core Compliance](#nhs-fhir-uk-core-compliance)
9. [Clinical Governance](#clinical-governance)
10. [Database Schema](#database-schema)
11. [API Design](#api-design)
12. [Testing Strategy](#testing-strategy)
13. [Implementation Phases](#implementation-phases)
14. [Performance Requirements](#performance-requirements)
15. [Security & Compliance](#security--compliance)
16. [Deployment Considerations](#deployment-considerations)
17. [Risks & Mitigations](#risks--mitigations)
18. [Open Questions](#open-questions)
19. [Acceptance Criteria](#acceptance-criteria)
20. [Alignment with Constitution](#alignment-with-constitution)

---

## Context

### Background

The **Clinical Decision Support (CDS) Module** provides evidence-based recommendations integrated into **Meditech Expanse** clinical workflows via **bidirectional FHIR R4 integration**.

**CogStack Product Alignment**: Clinical Decision Support (real-time clinical guidance)

**Sprints 1-5 delivered**: Patient Search, Timeline View, Full-Text Search, De-Identification, Clinical Coding

### The Problem

Clinicians using **Meditech Expanse** need **real-time clinical guidance** during patient care:

1. **Guideline adherence**: Hard to remember all clinical guidelines (diabetes, hypertension, anticoagulation, etc.)
2. **Drug interactions**: Risk of prescribing contraindicated medications
3. **Preventive care gaps**: Miss screening recommendations (mammography, colonoscopy)
4. **Treatment options**: Unsure of evidence-based treatment choices
5. **Manual workflow**: CDS recommendations should **pre-populate Meditech orders** (not require manual re-entry)

**Example Use Case**:

Clinician opens patient chart in Meditech Expanse:
- Patient has new diagnosis: Type 2 Diabetes (ICD-10: E11.9)
- CDS module analyzes patient data via FHIR API
- CDS **generates recommendations**:
  - Start metformin 500mg BD (first-line therapy per ADA guidelines)
  - Order HbA1c, lipid panel, urine ACR (baseline labs)
  - Refer to diabetes educator
- CDS **writes draft orders to Meditech**:
  - MedicationRequest (metformin - dm+d code: 39113611000001102)
  - ServiceRequest (HbA1c lab order - SNOMED: 43396009)
  - Task (schedule 3-month follow-up)
- Clinician **reviews and approves** draft orders in Meditech
- Orders finalized and sent to pharmacy/lab

**Result**: Evidence-based care with **minimal manual effort** (no copy-paste from CDS to Meditech)

### Why Bidirectional Integration Matters

**Read-Only CDS** (v1.0):
- ❌ Clinician sees recommendation in CDS UI
- ❌ Clinician manually types order into Meditech
- ❌ Transcription errors possible
- ❌ Extra steps reduce adoption

**Bidirectional CDS** (v2.0):
- ✅ CDS writes draft order directly to Meditech
- ✅ Clinician reviews/approves in Meditech (single workflow)
- ✅ No transcription errors
- ✅ Faster, safer, higher adoption

### Deployment Context

- **Platform**: Clinical Care Tools Base Application + Meditech Expanse Cloud
- **Meditech Environment**: meditech-uk.cloud (sandbox + test + production)
- **Users**: Clinicians (receive CDS alerts in Meditech), Admin (configure CDS rules)
- **Data Source**: Patient data from Meditech via FHIR R4 API
- **Integration**: Bidirectional FHIR R4 (read patient data, write orders/tasks)
- **Compliance**: NHS FHIR UK Core, HIPAA, GDPR, NHS Data Security and Protection Toolkit

---

## Goals

### Primary Goals (P0 - Must Have)

1. **Meditech Patient Data Read** (P0)
   - OAuth 2.0 authentication with meditech-uk.cloud
   - Read Patient, Condition, Observation, MedicationRequest resources via FHIR R4 API
   - NHS FHIR UK Core profile compliance (NHS number, ODS codes)
   - Patient data caching (reduce API calls, 5-minute TTL)

2. **Clinical Decision Support Engine** (P0)
   - Clinical guidelines database (ADA, AHA, USPSTF, NICE)
   - Rule engine (IF condition THEN recommendation)
   - Evidence grading (Level A, B, C)
   - Recommendation explanations (why suggested, which guideline)
   - Recommendation prioritization (critical, high, medium, low)

3. **Drug Interaction Checking** (P0)
   - NHS dm+d medication database integration
   - Interaction detection (check new medication vs current medications)
   - Severity classification (contraindicated, major, moderate, minor)
   - Alternative medication suggestions (safer options from dm+d)

4. **Meditech Write Operations** (P0) **[NEW in v2.0]**
   - Create MedicationRequest in Meditech (prescription orders)
   - Create ServiceRequest in Meditech (lab orders, imaging, referrals)
   - Create Task in Meditech (clinician follow-up tasks)
   - Create CommunicationRequest in Meditech (alerts to clinicians)
   - NHS FHIR UK Core write validation (dm+d codes, ODS codes)
   - Transaction bundles (atomic writes, rollback on error)

5. **Clinical Governance & Safety** (P0) **[NEW in v2.0]**
   - Role-based write permissions (RBAC: who can create orders?)
   - Approval workflows (draft orders require clinician review)
   - Rollback/cancellation (undo incorrect CDS writes)
   - Clinical safety checks (drug allergies, contraindications)
   - Override tracking (log when clinician rejects CDS suggestion)

6. **Meditech Workflow Integration** (P0) **[NEW in v2.0]**
   - InBasket integration (CDS alerts appear in Meditech clinician inbox)
   - Order entry pre-population (CDS suggestions pre-fill Meditech order forms)
   - Task creation (CDS creates follow-up tasks in Meditech task list)
   - Real-time updates (CDS recommendations update as patient data changes)

7. **Comprehensive Audit Logging** (P0)
   - Log all Meditech API calls (read and write)
   - Log CDS recommendations displayed
   - Log clinician actions (accepted, rejected, dismissed)
   - Log write operations to Meditech (WHO wrote WHAT to Meditech WHEN)
   - Audit trail immutability
   - Compliance reporting (HIPAA, GDPR, NHS DSPT)

### Secondary Goals (P1 - Should Have)

8. **Preventive Care Reminders** (P1)
   - Screening recommendations (mammography, colonoscopy, vaccines)
   - Age/gender/risk-based guidelines
   - Overdue reminders

9. **Custom CDS Rules** (P1)
   - Admin can create custom rules (condition-based)
   - Rule builder UI (no coding required)
   - Rule testing/validation

10. **CDS Hooks Integration** (P1) **[Conditional - if Meditech supports]**
    - Implement CDS Hooks 1.0 specification (if Meditech Expanse supports webhooks)
    - Hooks: `patient-view`, `order-select`, `order-sign`
    - Card responses (suggestions, links)

---

## Non-Goals

1. **Real-Time Meditech Webhooks** - MVP: Poll-based (CDS queries Meditech every 5 minutes), future: CDS Hooks if Meditech supports
2. **SMART on FHIR Apps** - Embed external SMART apps (future)
3. **Machine Learning Predictions** - Rule-based CDS only (no ML in this sprint)
4. **Multi-Language Support** - English guidelines only
5. **Final Orders** - CDS creates **draft orders only** (clinician approval required)
6. **Multi-EHR Support** - Meditech Expanse only (not Epic, Cerner)

---

## User Stories

### Clinician User Stories

#### US-CL1: Receive CDS Alerts in Meditech
**As a** clinician using Meditech Expanse
**I want to** receive CDS alerts in my Meditech inbox
**So that** I get evidence-based recommendations without leaving Meditech

**Acceptance Criteria**:
- [ ] Open patient chart in Meditech → CDS alert appears in InBasket
- [ ] Alert shows:
  - Recommendation (e.g., "Start metformin for T2DM")
  - Evidence (e.g., "ADA 2023 guidelines, Level A evidence")
  - Severity (info, warning, critical)
- [ ] Actions: "Accept & Create Draft Order", "Dismiss", "View Details"
- [ ] Audit log entry created (PHI access + CDS alert displayed)

---

#### US-CL2: Accept CDS Recommendation (Creates Draft Order in Meditech)
**As a** clinician
**I want to** accept a CDS recommendation and have it create a draft order in Meditech
**So that** I don't need to manually type the order

**Acceptance Criteria**:
- [ ] Click "Accept & Create Draft Order" in CDS alert
- [ ] CDS writes MedicationRequest to Meditech via FHIR API (dm+d code)
- [ ] Draft order appears in Meditech order entry screen (pre-populated)
- [ ] Clinician reviews draft order (can modify dose, frequency)
- [ ] Clinician signs order → final order sent to pharmacy
- [ ] Audit log: CDS write to Meditech + clinician acceptance

---

#### US-CL3: Check Drug Interactions Before Prescribing
**As a** clinician
**I want to** check for drug interactions when prescribing
**So that** I avoid contraindicated medications

**Acceptance Criteria**:
- [ ] Enter new medication in Meditech order entry
- [ ] CDS queries current medications from Meditech FHIR API
- [ ] CDS checks drug interactions (new medication vs current medications)
- [ ] If interaction found:
  - Alert severity: contraindicated (red), major (orange), moderate (yellow)
  - Description: "Warfarin + Aspirin increases bleeding risk"
  - Alternatives: "Consider clopidogrel instead"
- [ ] Clinician can override (with reason required for critical interactions)

---

#### US-CL4: Reject CDS Recommendation
**As a** clinician
**I want to** reject a CDS recommendation if not appropriate for my patient
**So that** I maintain clinical autonomy

**Acceptance Criteria**:
- [ ] Click "Dismiss" on CDS alert
- [ ] Optional: Provide reason ("Patient already on alternative medication")
- [ ] Audit log: Recommendation rejected + reason
- [ ] No draft order created in Meditech
- [ ] CDS does not re-trigger same alert for 7 days (configurable)

---

### Admin User Stories

#### US-A1: Configure CDS Rules
**As an** admin
**I want to** configure CDS rules
**So that** clinicians receive relevant alerts

**Acceptance Criteria**:
- [ ] Admin panel for CDS rules:
  - Enable/disable rules (e.g., disable "Metformin for T2DM" rule)
  - Set alert thresholds (e.g., HbA1c >7% triggers diabetes control alert)
  - Configure guideline versions (ADA 2023 vs 2024)
  - Set alert frequency (do not re-trigger within X days)
- [ ] Settings saved to database
- [ ] Changes take effect within 5 minutes (cache refresh)

---

#### US-A2: Review CDS Audit Logs
**As an** admin
**I want to** review CDS audit logs
**So that** I can monitor CDS usage and effectiveness

**Acceptance Criteria**:
- [ ] Audit log dashboard:
  - Total alerts displayed (last 7 days, 30 days, 90 days)
  - Acceptance rate (% of alerts accepted vs dismissed)
  - Top 10 most frequent alerts
  - Top 10 most rejected alerts (identify alert fatigue)
- [ ] Filter by date range, clinician, rule
- [ ] Export to CSV for analysis

---

## Requirements

### Functional Requirements

#### FR1: Meditech Patient Data Read (P0)

- **FR1.1**: OAuth 2.0 authentication with meditech-uk.cloud
  - Client credentials grant (client ID + secret)
  - Token refresh before expiry (1-hour tokens typical)
  - Error handling (invalid credentials, expired token)

- **FR1.2**: Read Patient resource via FHIR API
  - GET `https://meditech-uk.cloud/fhir/r4/Patient/{id}`
  - NHS FHIR UK Core UKCore-Patient profile
  - Extract: NHS number, name, DOB, gender, address (for ODS code)

- **FR1.3**: Read Condition resources (diagnoses)
  - GET `https://meditech-uk.cloud/fhir/r4/Condition?patient={id}`
  - Filter by clinical status: active, recurrence (exclude resolved)
  - Extract: SNOMED CT code, onset date, severity

- **FR1.4**: Read Observation resources (vitals, labs)
  - GET `https://meditech-uk.cloud/fhir/r4/Observation?patient={id}&category=vital-signs`
  - Extract: HbA1c, blood pressure, weight, BMI
  - Extract: observation date (for "last HbA1c 3 months ago" logic)

- **FR1.5**: Read MedicationRequest resources (current medications)
  - GET `https://meditech-uk.cloud/fhir/r4/MedicationRequest?patient={id}&status=active`
  - NHS FHIR UK Core UKCore-MedicationRequest profile
  - Extract: dm+d code, dose, frequency, start date

- **FR1.6**: Patient data caching
  - Cache FHIR responses in Redis (key: `meditech:patient:{id}`)
  - TTL: 5 minutes (reduce Meditech API calls)
  - Invalidate cache on write (if CDS writes to Meditech, refresh cache)

- **FR1.7**: Error handling
  - Network failures: retry with exponential backoff (3 retries max)
  - Auth errors: refresh token and retry
  - Rate limiting: respect Meditech rate limits (50 requests/minute typical)
  - Meditech unavailable: graceful degradation (use cached data, disable writes)

---

#### FR2: Clinical Decision Support Engine (P0)

- **FR2.1**: Clinical guidelines database
  - Store guidelines: ADA (diabetes), AHA (cardiovascular), USPSTF (screening), NICE (UK-specific)
  - Format: JSON or database table
  - Fields: condition (SNOMED CT), recommendation (text), evidence level (A/B/C), source URL

- **FR2.2**: Rule engine
  - IF-THEN logic: `IF patient has T2DM AND no HbA1c in 3 months THEN suggest HbA1c order`
  - Support multiple conditions: AND, OR, NOT
  - Support time-based logic: "no HbA1c in last 90 days"
  - Evaluate rules on patient data load (when clinician opens chart)

- **FR2.3**: Evidence grading
  - Level A: Strong evidence (RCTs, meta-analyses)
  - Level B: Moderate evidence (cohort studies)
  - Level C: Weak evidence (expert opinion)
  - Display evidence level in alert ("ADA 2023, Level A evidence")

- **FR2.4**: Recommendation explanations
  - Why suggested: "Patient has HbA1c >9%, ADA guidelines recommend insulin initiation"
  - Guideline reference: Link to ADA guidelines PDF/URL
  - Evidence summary: "RCTs show insulin reduces complications in T2DM with HbA1c >9%"

- **FR2.5**: Recommendation prioritization
  - Critical: Drug interaction contraindication, life-threatening condition
  - High: Guideline-recommended treatment missing (e.g., metformin for T2DM)
  - Medium: Preventive care overdue (e.g., HbA1c not done in 6 months)
  - Low: Lifestyle recommendations (diet, exercise)

---

#### FR3: Drug Interaction Checking (P0)

- **FR3.1**: NHS dm+d medication database
  - Download dm+d from NHS TRUD (Technology Reference data Update Distribution)
  - URL: https://isd.digital.nhs.uk/trud
  - Load dm+d codes into PostgreSQL: VMP (Virtual Medicinal Product), AMP (Actual Medicinal Product)
  - Example: Metformin 500mg tablets = dm+d code 39113611000001102

- **FR3.2**: Drug interaction database
  - Source: Open-source (OpenFDA) OR commercial (Lexicomp, Micromedex)
  - Store interactions: drug A (dm+d code) + drug B (dm+d code) → interaction type + severity
  - Example: Warfarin (dm+d 9191801000001103) + Aspirin (dm+d 319740003) → "Increased bleeding risk" (major)

- **FR3.3**: Interaction detection
  - When CDS recommends new medication:
    - Query current medications from Meditech FHIR API
    - Check new medication vs each current medication
    - Return interactions sorted by severity (contraindicated first)

- **FR3.4**: Severity classification
  - **Contraindicated**: Never use together (e.g., MAOI + SSRI)
  - **Major**: Serious interaction, requires dose adjustment or monitoring (e.g., warfarin + aspirin)
  - **Moderate**: Monitor patient, may need intervention (e.g., ACE inhibitor + potassium supplement)
  - **Minor**: Usually safe, inform patient (e.g., antacid + iron)

- **FR3.5**: Alternative medication suggestions
  - If contraindicated/major interaction: suggest alternative from dm+d
  - Example: "Warfarin + aspirin contraindicated → Consider clopidogrel (dm+d 108537001) instead"
  - Logic: Query dm+d for same therapeutic class, exclude interacting medications

---

#### FR4: Meditech Write Operations (P0) **[NEW in v2.0]**

- **FR4.1**: Create MedicationRequest (prescription orders)
  - POST `https://meditech-uk.cloud/fhir/r4/MedicationRequest`
  - NHS FHIR UK Core UKCore-MedicationRequest profile
  - Required fields:
    - status: "draft" (requires clinician approval)
    - intent: "order"
    - medicationCodeableConcept: dm+d code
    - subject: reference to Patient
    - requester: reference to CDS system (Practitioner or Device)
    - dosageInstruction: dose, frequency, route
  - Example: Metformin 500mg BD (dm+d: 39113611000001102)

- **FR4.2**: Create ServiceRequest (lab orders, imaging, referrals)
  - POST `https://meditech-uk.cloud/fhir/r4/ServiceRequest`
  - NHS FHIR UK Core UKCore-ServiceRequest profile
  - Required fields:
    - status: "draft"
    - intent: "order"
    - code: SNOMED CT code (e.g., HbA1c = 43396009)
    - subject: reference to Patient
    - requester: reference to CDS system
  - Example: HbA1c lab order (SNOMED: 43396009)

- **FR4.3**: Create Task (clinician follow-up tasks)
  - POST `https://meditech-uk.cloud/fhir/r4/Task`
  - Fields:
    - status: "requested"
    - intent: "order"
    - code: "follow-up" OR "review-results"
    - for: reference to Patient
    - owner: reference to Practitioner (assigned clinician)
    - description: "Schedule 3-month diabetes follow-up"
  - Example: Create task for clinician to schedule follow-up appointment

- **FR4.4**: Create CommunicationRequest (alerts to clinicians)
  - POST `https://meditech-uk.cloud/fhir/r4/CommunicationRequest`
  - Fields:
    - status: "active"
    - priority: "routine" OR "urgent" OR "stat"
    - subject: reference to Patient
    - recipient: reference to Practitioner
    - payload: Alert message ("Patient overdue for HbA1c")
  - Appears in Meditech InBasket

- **FR4.5**: NHS FHIR UK Core write validation
  - Validate dm+d codes (medication must exist in dm+d database)
  - Validate ODS codes (organization must exist in ODS database)
  - Validate NHS numbers (10-digit, checksum validation)
  - Validate SNOMED CT codes (use UK edition)

- **FR4.6**: Transaction bundles (atomic writes)
  - If creating multiple resources (MedicationRequest + ServiceRequest + Task):
    - Use FHIR Bundle with type "transaction"
    - All resources created OR none created (rollback on error)
    - Example: Create metformin prescription + HbA1c order + follow-up task (all or nothing)

- **FR4.7**: Write error handling
  - Meditech rejection: Log error, notify clinician ("CDS failed to create order, please create manually")
  - Validation errors: Show specific error ("Invalid dm+d code: 12345")
  - Network errors: Retry with exponential backoff (3 retries max)
  - Rate limiting: Queue writes (process when rate limit resets)

---

#### FR5: Clinical Governance & Safety (P0) **[NEW in v2.0]**

- **FR5.1**: Role-based write permissions (RBAC)
  - **Doctors**: Can create MedicationRequest, ServiceRequest, Task
  - **Pharmacists**: Can create MedicationRequest only (medication review recommendations)
  - **Nurses**: Can create Task, CommunicationRequest only (no prescribing)
  - **CDS System**: Can create "draft" orders only (never "active" final orders)
  - Enforce in backend: Check user role before FHIR write operation

- **FR5.2**: Approval workflows
  - **Draft orders** (default for CDS):
    - CDS creates MedicationRequest with status="draft"
    - Clinician sees draft order in Meditech order entry screen
    - Clinician reviews, modifies if needed, signs → status="active"
    - Final order sent to pharmacy/lab
  - **Final orders** (disabled by default, requires admin approval):
    - Admin can enable "auto-finalize orders" for low-risk scenarios (e.g., preventive screening)
    - Requires clinical safety review before enabling

- **FR5.3**: Rollback/cancellation
  - Clinician can delete draft order in Meditech (no CDS action needed)
  - CDS can cancel draft order via DELETE or UPDATE status="cancelled"
  - Audit log: Record cancellation (who, when, why)
  - Example: CDS created duplicate order → CDS cancels duplicate

- **FR5.4**: Clinical safety checks (before writing to Meditech)
  - **Drug allergies**: Query Meditech AllergyIntolerance resources, do not recommend allergenic medications
  - **Contraindications**: Check patient conditions (e.g., do not recommend metformin if eGFR <30)
  - **Duplicate orders**: Check existing MedicationRequests, do not create duplicate prescriptions
  - **Interaction checks**: Run FR3 drug interaction checking before creating MedicationRequest
  - Block write if safety check fails, log reason

- **FR5.5**: Override tracking
  - If clinician rejects CDS recommendation:
    - Prompt for reason (free text)
    - Log: user_id, recommendation, rejection_reason, timestamp
  - Use for CDS improvement: "90% of clinicians reject metformin recommendation for reason 'patient already on SGLT2 inhibitor' → update rule to check current medications first"

---

#### FR6: Meditech Workflow Integration (P0) **[NEW in v2.0]**

- **FR6.1**: InBasket integration
  - CDS alerts appear in Meditech clinician inbox (InBasket)
  - Mechanism: Create CommunicationRequest resource (FR4.4)
  - Alert format:
    - Subject: "CDS Alert: Start metformin for T2DM"
    - Body: Recommendation + evidence + actions
    - Priority: routine/urgent/stat (maps to CDS recommendation priority)
  - Clinician clicks alert → opens patient chart with CDS details

- **FR6.2**: Order entry pre-population
  - When clinician accepts CDS recommendation:
    - CDS creates draft MedicationRequest/ServiceRequest (FR4.1, FR4.2)
    - Meditech displays draft order in order entry screen
    - Order form pre-populated:
      - Medication: Metformin 500mg tablets (dm+d: 39113611000001102)
      - Dose: 500mg
      - Frequency: Twice daily
      - Route: Oral
      - Duration: 90 days
    - Clinician can modify before signing

- **FR6.3**: Task creation
  - CDS creates Task resource in Meditech (FR4.3)
  - Task appears in clinician task list
  - Example: "Schedule 3-month diabetes follow-up appointment for Patient NHS# 1234567890"
  - Task can be assigned to specific clinician (e.g., patient's GP)

- **FR6.4**: Real-time updates (future enhancement)
  - If patient data changes in Meditech → trigger CDS re-evaluation
  - Mechanism: CDS Hooks webhooks (if Meditech supports) OR polling (every 5 minutes)
  - Example: Clinician orders HbA1c → CDS detects order → removes "HbA1c overdue" alert

---

#### FR7: Comprehensive Audit Logging (P0)

- **FR7.1**: Log all Meditech API calls
  - Log read operations: GET Patient, Condition, Observation, MedicationRequest
  - Log write operations: POST MedicationRequest, ServiceRequest, Task, CommunicationRequest
  - Fields: timestamp, user_id (CDS system), endpoint, http_method, response_status, response_time_ms
  - Purpose: Debugging, performance monitoring, compliance

- **FR7.2**: Log CDS recommendations displayed
  - Log every recommendation shown to clinician
  - Fields: timestamp, patient_id, clinician_id, rule_id, recommendation_text, evidence_level, priority
  - Purpose: CDS effectiveness tracking, alert fatigue monitoring

- **FR7.3**: Log clinician actions
  - Log when clinician accepts/rejects/dismisses CDS alert
  - Fields: timestamp, patient_id, clinician_id, rule_id, action (accepted/rejected/dismissed), rejection_reason (if rejected)
  - Purpose: Acceptance rate calculation, rule improvement

- **FR7.4**: Log write operations to Meditech
  - Log every FHIR write to Meditech (separate from FR7.1 for emphasis)
  - Fields: timestamp, user_id (CDS system on behalf of clinician), resource_type (MedicationRequest/ServiceRequest/Task), resource_id, status (draft/active/cancelled)
  - Purpose: Clinical governance, audit trail for "who ordered what"

- **FR7.5**: Audit trail immutability
  - Use centralized `audit_logs` table (from MVP specification)
  - PostgreSQL rule: DENY UPDATE/DELETE on audit_logs (append-only)
  - Retention: 8 years (NHS compliance)

- **FR7.6**: Compliance reporting
  - Admin dashboard:
    - Total PHI accesses via Meditech API (last 30 days)
    - Total writes to Meditech (last 30 days)
    - CDS alert acceptance rate
    - Export audit logs for NHS DSPT compliance review

---

### Non-Functional Requirements

#### NFR1: Performance

- **NFR1.1**: CDS recommendation generation <2 seconds
  - From clinician opens patient chart → CDS alerts displayed in Meditech
  - Includes: Meditech API calls (read patient data), rule evaluation, alert creation

- **NFR1.2**: Meditech FHIR read API calls <1 second
  - Cached responses: <100ms (from Redis)
  - Uncached responses: <1 second (from Meditech)

- **NFR1.3**: Meditech FHIR write operations <2 seconds
  - POST MedicationRequest/ServiceRequest/Task → response from Meditech <2 seconds
  - Transaction bundles (3 resources): <3 seconds

- **NFR1.4**: Support 10 concurrent clinicians
  - 10 clinicians triggering CDS simultaneously
  - No performance degradation

---

#### NFR2: Security

- **NFR2.1**: OAuth 2.0 authentication with meditech-uk.cloud
  - Client credentials grant (backend service, no user login)
  - Token storage: Encrypted in PostgreSQL or environment variables
  - Token refresh: Automatic (before expiry)

- **NFR2.2**: TLS 1.3 for all Meditech API calls
  - Enforce HTTPS only (no HTTP fallback)
  - Certificate validation

- **NFR2.3**: IP whitelisting (if required by Meditech UK)
  - Configure Meditech to accept API calls only from Clinical Care Tools backend IP

- **NFR2.4**: Audit logging for all write operations
  - Every write to Meditech logged to immutable audit trail

---

#### NFR3: Reliability

- **NFR3.1**: Graceful degradation if Meditech API unavailable
  - Show cached recommendations (from last successful query)
  - Disable writes (do not create orders if Meditech down)
  - Display warning to clinician: "Meditech unavailable, CDS using cached data"

- **NFR3.2**: Retry logic with exponential backoff
  - Meditech API rate limits: Retry after delay (1s, 2s, 4s)
  - Network errors: Retry 3 times max

- **NFR3.3**: Circuit breaker
  - If Meditech API fails repeatedly (5 failures in 1 minute):
    - Open circuit (stop calling Meditech for 5 minutes)
    - Prevent cascading failures
    - Log: "Circuit breaker opened for Meditech API"

- **NFR3.4**: Write rollback on error
  - If transaction bundle fails (e.g., MedicationRequest created, ServiceRequest failed):
    - Rollback entire transaction (delete MedicationRequest)
    - Prevents partial writes

---

#### NFR4: Compliance

- **NFR4.1**: HIPAA audit trail
  - All PHI access via Meditech API logged
  - Audit log fields: user, patient, action, timestamp, IP

- **NFR4.2**: GDPR data processing agreement with Meditech UK
  - Document: Meditech UK is data processor
  - Purpose: CDS module accesses patient data for clinical decision support

- **NFR4.3**: NHS Data Security and Protection Toolkit (DSPT) compliance
  - Annual assertion required for NHS trusts
  - Requirements: Audit logging, encryption, access control
  - Provide audit log exports for DSPT review

- **NFR4.4**: Clinical safety review (DCB0129, DCB0160 if applicable)
  - **DCB0129**: Clinical Risk Management (if CDS module is considered "health software")
  - **DCB0160**: Clinical Safety Case Reports
  - Consult with NHS trust clinical safety officer

---

(Continued in next message due to length...)

## Implementation Phases

### Phase 6.1: CDS Core Infrastructure (3 weeks, 90 hours)

**Tasks**:
1. CDS Hooks 1.0 specification implementation (if Meditech supports) - 20h
2. FHIR R4 client library integration (`fhir.resources` Python package) - 15h
3. Clinical guidelines database setup (ADA, AHA, USPSTF, NICE) - 25h
4. Rule engine implementation (IF-THEN logic, time-based conditions) - 20h
5. Audit logging for CDS actions - 10h

**Deliverable**: CDS engine can evaluate rules and generate recommendations (standalone, not yet integrated with Meditech)

---

### Phase 6.2: Meditech Read Integration (2 weeks, 60 hours)

**Tasks**:
1. OAuth 2.0 authentication with meditech-uk.cloud - 15h
2. FHIR R4 read operations (GET Patient, Condition, Observation, MedicationRequest) - 20h
3. NHS FHIR UK Core profile mapping (NHS number, ODS codes) - 15h
4. Patient data caching in Redis (5-minute TTL) - 5h
5. Error handling (network failures, auth expiry, rate limiting) - 5h

**Deliverable**: CDS can read patient data from Meditech sandbox

---

### Phase 6.3: Drug Interaction Checking (1 week, 30 hours)

**Tasks**:
1. Download NHS dm+d from TRUD, load into PostgreSQL - 10h
2. Drug interaction database setup (OpenFDA or commercial API) - 10h
3. Interaction detection logic (new medication vs current medications) - 5h
4. Alternative medication suggestions from dm+d - 5h

**Deliverable**: CDS can check drug interactions using NHS dm+d codes

---

### Phase 6.4: Meditech Write Integration (3 weeks, 90 hours)

**Tasks**:
1. Implement FHIR write operations:
   - POST MedicationRequest (prescription orders) - 20h
   - POST ServiceRequest (lab orders, imaging, referrals) - 20h
   - POST Task (clinician follow-up tasks) - 15h
   - POST CommunicationRequest (alerts to clinicians) - 15h
2. NHS FHIR UK Core write validation (dm+d codes, ODS codes, NHS numbers) - 10h
3. Transaction bundles (atomic writes, rollback on error) - 5h
4. Write error handling (Meditech rejection, validation failures, network errors) - 5h

**Deliverable**: CDS can write draft orders to Meditech sandbox

---

### Phase 6.5: Clinical Governance & RBAC (1 week, 30 hours)

**Tasks**:
1. Role-based write permissions (doctors, pharmacists, nurses) - 10h
2. Approval workflows (draft orders, clinician review/approval) - 10h
3. Clinical safety checks (drug allergies, contraindications, duplicate orders) - 5h
4. Override tracking (log when clinician rejects CDS suggestion) - 5h

**Deliverable**: CDS respects RBAC, creates draft orders only, tracks overrides

---

### Phase 6.6: Meditech Workflow Integration (1 week, 30 hours)

**Tasks**:
1. InBasket integration (CDS alerts appear in Meditech clinician inbox) - 10h
2. Order entry pre-population (CDS suggestions pre-fill Meditech order forms) - 10h
3. Task creation (CDS creates follow-up tasks in Meditech task list) - 5h
4. UI testing with Meditech sandbox - 5h

**Deliverable**: CDS alerts appear in Meditech InBasket, orders pre-populate Meditech forms

---

### Phase 6.7: Testing & Validation (1 week, 30 hours)

**Tasks**:
1. Unit tests (CDS rule engine, drug interaction checking) - 10h
2. Integration tests (Meditech FHIR API read/write operations) - 10h
3. UAT with Meditech test environment (2-3 pilot clinicians) - 5h
4. Performance testing (response times, concurrent users) - 5h

**Deliverable**: 80% test coverage, all tests passing, UAT sign-off from clinicians

---

## Risks & Mitigations

### Risk 1: Meditech FHIR API Capabilities Unknown
**Risk**: Meditech Expanse may not support all FHIR write operations (MedicationRequest, ServiceRequest, Task) or NHS FHIR UK Core profiles

**Likelihood**: Medium | **Impact**: HIGH (blocks bidirectional integration)

**Mitigation**:
- **Week 0**: Verify Meditech sandbox capabilities (see Week 0 checklist)
- Test FHIR write permissions: Can OAuth app create MedicationRequest? ServiceRequest? Task?
- Review Meditech CapabilityStatement: GET https://meditech-uk.cloud/fhir/r4/metadata
- **Contingency**: If writes not supported, fallback to read-only CDS (display recommendations in standalone UI, not Meditech)

---

### Risk 2: NHS dm+d Medication Code Mapping Complexity
**Risk**: Meditech may use different medication code systems (RxNorm, SNOMED CT drugs) instead of NHS dm+d

**Likelihood**: Medium | **Impact**: MEDIUM (drug interaction checking inaccurate)

**Mitigation**:
- **Week 0**: Query Meditech MedicationRequest resources, inspect medication codes
- If Meditech uses RxNorm: Create mapping table (RxNorm ↔ dm+d)
- If Meditech uses SNOMED CT drugs: Use SNOMED CT drug hierarchy for interactions
- **Contingency**: Use multi-code-system drug interaction database (supports RxNorm, dm+d, SNOMED CT)

---

### Risk 3: CDS Hooks Not Supported by Meditech Expanse
**Risk**: Meditech Expanse may not support CDS Hooks 1.0 webhooks (real-time integration)

**Likelihood**: HIGH (many EHRs don't support CDS Hooks yet) | **Impact**: MEDIUM (requires polling instead)

**Mitigation**:
- **Week 0**: Verify CDS Hooks support with Meditech (ask Meditech support or test webhook registration)
- If not supported: Use polling approach (CDS queries Meditech every 5 minutes for new/updated patients)
- **Impact**: Slight delay (up to 5 minutes) before CDS recommendations appear (acceptable for most clinical workflows)

---

### Risk 4: Clinical Safety Concerns (Automated Ordering)
**Risk**: NHS trust clinical governance may reject automated ordering (draft or final orders) due to patient safety concerns

**Likelihood**: MEDIUM | **Impact**: HIGH (reduces CDS value if only displays recommendations, doesn't write orders)

**Mitigation**:
- **Early engagement**: Present CDS design to NHS trust clinical safety officer (Week 4-6)
- **Draft orders only**: CDS creates draft orders (status="draft") requiring clinician approval (default, safest)
- **Safety checks**: Implement drug allergy checks, contraindication checks, duplicate order checks (Phase 6.5)
- **Audit trail**: Comprehensive logging of all CDS writes to Meditech (Phase 6.7)
- **Pilot program**: Start with 2-3 clinicians, low-risk recommendations only (e.g., preventive screening, not medications)
- **Contingency**: If automated ordering rejected, fallback to "recommendation display only" (clinician manually creates orders)

---

### Risk 5: Meditech API Rate Limiting
**Risk**: Meditech API may have rate limits (e.g., 50 requests/minute) that block CDS at scale

**Likelihood**: MEDIUM | **Impact**: MEDIUM (CDS slow or unavailable during peak hours)

**Mitigation**:
- **Week 0**: Test Meditech API rate limits (send 100 requests/minute, observe errors)
- **Caching**: Cache patient data in Redis (5-minute TTL) to reduce API calls (Phase 6.2)
- **Rate limiting**: Implement exponential backoff, queue write operations (Phase 6.4)
- **Monitoring**: Track API call volume, alert if approaching rate limits
- **Contingency**: Request higher rate limit from Meditech UK (may require commercial agreement)

---

## Open Questions

### Meditech Environment (Week 0 - MUST ANSWER)

1. **Meditech Expanse version**: 6.x, 7.x, or 8.x? (affects FHIR R4 support)
2. **FHIR write permissions**: Can OAuth app create MedicationRequest, ServiceRequest, Task, CommunicationRequest?
3. **CDS Hooks support**: Does Meditech Expanse support CDS Hooks 1.0 webhooks?
4. **Medication codes**: Does Meditech use NHS dm+d, RxNorm, or SNOMED CT drugs?
5. **ODS organization code**: What is the NHS trust ODS code? (required for FHIR resources)
6. **OAuth credentials**: Client ID + secret for sandbox, test, production environments?
7. **Rate limits**: What are Meditech API rate limits (requests/minute)?

### Clinical Governance (Week 4-6 - Before Phase 6.5)

8. **Draft vs final orders**: Should CDS create draft orders (requiring clinician approval) or final orders (auto-finalized)?
9. **RBAC for writes**: Which roles can CDS write orders for? (doctors only, or doctors + pharmacists + nurses?)
10. **Clinical safety review**: Is DCB0129/DCB0160 compliance required for CDS module?
11. **Pilot program**: Which clinicians will pilot CDS? (2-3 volunteers, which specialties?)

### Drug Interaction Database (Week 2-4 - Before Phase 6.3)

12. **Commercial vs open-source**: Use commercial drug interaction database (Lexicomp, Micromedex) or open-source (OpenFDA)?
   - Commercial: More accurate, costs ~£5,000-10,000/year
   - Open-source: Free, less comprehensive

---

## Acceptance Criteria

### Sprint 6 Success Metrics

#### Functional Acceptance

- [ ] **Meditech Read Integration**: CDS can read Patient, Condition, Observation, MedicationRequest from Meditech sandbox
- [ ] **CDS Recommendations**: CDS generates evidence-based recommendations for ≥5 clinical guidelines (diabetes, hypertension, etc.)
- [ ] **Drug Interaction Checking**: CDS detects contraindicated and major drug interactions with ≥99% accuracy
- [ ] **Meditech Write Integration**: CDS can create draft MedicationRequest, ServiceRequest, Task, CommunicationRequest in Meditech sandbox
- [ ] **Clinical Governance**: CDS respects RBAC (only authorized roles can write orders)
- [ ] **Audit Logging**: All Meditech API calls (read and write) logged to immutable audit trail
- [ ] **Clinician UAT**: 2-3 pilot clinicians sign off on CDS workflow in Meditech test environment

#### Performance Acceptance

- [ ] CDS recommendation generation: <2 seconds (from patient chart open to alerts displayed)
- [ ] Meditech FHIR read API calls: <1 second (uncached), <100ms (cached)
- [ ] Meditech FHIR write operations: <2 seconds (single resource), <3 seconds (transaction bundle)
- [ ] Support 10 concurrent clinicians without performance degradation

#### Security & Compliance Acceptance

- [ ] OAuth 2.0 authentication with Meditech: Tokens refresh automatically before expiry
- [ ] TLS 1.3 for all Meditech API calls (HTTPS only)
- [ ] Audit logging: All PHI access via Meditech API logged with user, patient, action, timestamp, IP
- [ ] NHS FHIR UK Core compliance: All FHIR writes validate dm+d codes, ODS codes, NHS numbers

#### Test Coverage Acceptance

- [ ] Unit test coverage: ≥80% for CDS rule engine, drug interaction checking
- [ ] Integration test coverage: ≥70% for Meditech FHIR API integration
- [ ] UAT sign-off: 2-3 pilot clinicians approve CDS workflow in Meditech test environment

---

## Alignment with Constitution

### Patient Safety First (Principle 1)
- ✅ **Clinical safety checks**: Drug allergies, contraindications, duplicate orders (FR5.4)
- ✅ **Draft orders only**: CDS creates draft orders requiring clinician approval (FR5.2)
- ✅ **Override tracking**: Clinicians can reject recommendations, reasons logged (FR5.5)
- ✅ **Evidence-based guidelines**: ADA, AHA, USPSTF, NICE (FR2.1)

### Privacy by Design (Principle 2)
- ✅ **OAuth 2.0**: Secure authentication with Meditech (NFR2.1)
- ✅ **TLS 1.3**: All Meditech API calls encrypted in transit (NFR2.2)
- ✅ **Audit logging**: All PHI access via Meditech API logged (FR7.1, FR7.4)
- ✅ **Minimum necessary access**: CDS reads only patient data required for rule evaluation (FR1.2-FR1.5)

### Evidence-Based Development (Principle 3)
- ✅ **Clinical guidelines database**: ADA, AHA, USPSTF, NICE (FR2.1)
- ✅ **Evidence grading**: Level A/B/C displayed in recommendations (FR2.3)
- ✅ **Drug interaction database**: Evidence-based interactions (FR3.2)

### Transparency and Explainability (Principle 6)
- ✅ **Recommendation explanations**: Why suggested, which guideline, evidence summary (FR2.4)
- ✅ **Evidence grading**: Level A/B/C (strong/moderate/weak evidence) (FR2.3)
- ✅ **Audit logging**: Comprehensive audit trail for compliance reporting (FR7.5-FR7.6)

### Open Standards and Interoperability (Principle 5)
- ✅ **FHIR R4**: Industry standard for healthcare interoperability (FR1.2-FR1.5, FR4.1-FR4.4)
- ✅ **NHS FHIR UK Core**: UK-specific profiles for NHS integration (FR1.2, FR4.5)
- ✅ **CDS Hooks**: Open standard for CDS integration (FR1.1-FR1.4, if Meditech supports)

---

**Document Version**: 2.0.0
**Last Updated**: 2025-11-17
**Status**: ✅ Ready for Week 0 Meditech Verification
**Next Steps**: 
1. Complete Week 0 Meditech API Verification Checklist
2. Answer Open Questions (Meditech environment capabilities)
3. Create Technical Plan for Sprint 6 after specification approval
4. Estimated Start: Week 43 (after Sprints 2-5.5 complete)
5. Estimated Completion: Week 54 (12 weeks duration)

**Dependencies**: 
- MVP (Base Application complete)
- Sprint 5 (ICD-10 coding for guideline matching)
- **Week 0 Meditech verification** (MUST complete before Sprint 6 starts)

**Reviewers**: [NHS trust clinical safety officer, Meditech integration team, Clinical governance committee]
