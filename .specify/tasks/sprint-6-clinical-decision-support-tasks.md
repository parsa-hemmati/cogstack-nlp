# Task Breakdown: Clinical Decision Support Module (Sprint 6)

**Version**: 1.0.0
**Date**: 2025-11-23
**Status**: Ready for Implementation
**Based on**: Technical Plan v1.0.0
**Total Tasks**: 67 tasks
**Estimated Duration**: 12 weeks (360 hours)

---

## Table of Contents

1. [Phase 6.1: CDS Core Infrastructure](#phase-61-cds-core-infrastructure) (22 tasks, 90 hours)
2. [Phase 6.2: Meditech Read Integration](#phase-62-meditech-read-integration) (15 tasks, 60 hours)
3. [Phase 6.3: Drug Interaction Checking](#phase-63-drug-interaction-checking) (10 tasks, 30 hours)
4. [Phase 6.4: Meditech Write Integration](#phase-64-meditech-write-integration) (20 tasks, 90 hours)
5. [Phase 6.5: Clinical Governance & RBAC](#phase-65-clinical-governance--rbac) (10 tasks, 30 hours)
6. [Phase 6.6: Meditech Workflow Integration](#phase-66-meditech-workflow-integration) (8 tasks, 30 hours)
7. [Phase 6.7: Testing & Validation](#phase-67-testing--validation) (8 tasks, 30 hours)

---

## Phase 6.1: CDS Core Infrastructure (22 tasks, 90 hours)

**Goal**: Build CDS core engine with mock patient data

### Task 6.1.1: Setup FHIR Models and Validation (2 hours)

**Prerequisites**: None

**Steps**:
1. Install `fhir.resources==7.1.0` package (pip install)
2. Create `backend/app/schemas/cds/fhir_models.py`
3. Import NHS FHIR UK Core models:
   - UKCorePatient (with NHS number validation)
   - UKCoreCondition (ICD-10, SNOMED CT codes)
   - UKCoreObservation (vital signs, lab results)
   - UKCoreMedicationRequest (dm+d codes)
4. Create NHS number checksum validator (Modulus 11 algorithm)
5. Write unit tests (10 tests):
   - Valid NHS numbers (1234567881, 9876543210)
   - Invalid NHS numbers (wrong checksum)
   - dm+d code format validation (18-digit SNOMED CT codes)

**Acceptance Criteria**:
- [ ] fhir.resources installed successfully
- [ ] 4 FHIR models imported and wrapped
- [ ] NHS number validator with Modulus 11 checksum
- [ ] 10 unit tests passing (100% coverage for validators)

**Files Created**:
- `backend/app/schemas/cds/fhir_models.py`
- `backend/tests/unit/schemas/test_fhir_models.py`

**Skills**: None (basic Python/Pydantic)

---

### Task 6.1.2: Create Clinical Guidelines Database Schema (2 hours)

**Prerequisites**: Task 6.1.1

**Steps**:
1. Create migration `backend/alembic/versions/012_cds_guidelines.py`
2. Define `cds_guidelines` table:
   - id (UUID primary key)
   - guideline_source (VARCHAR 50: 'ADA', 'AHA', 'USPSTF', 'NICE')
   - guideline_name (VARCHAR 255)
   - condition_code (VARCHAR 50: ICD-10 or SNOMED CT)
   - recommendation (TEXT)
   - evidence_level (VARCHAR 10: 'A', 'B', 'C')
   - rationale (TEXT)
   - last_updated (TIMESTAMPTZ)
   - created_at (TIMESTAMPTZ default NOW())
   - UNIQUE constraint (guideline_source, guideline_name, condition_code)
   - Index on condition_code
3. Run migration: `alembic upgrade head`
4. Verify table created in PostgreSQL

**Acceptance Criteria**:
- [ ] Migration file created
- [ ] Table created successfully
- [ ] Unique constraint enforced
- [ ] Index on condition_code created

**Files Created**:
- `backend/alembic/versions/012_cds_guidelines.py`

**Skills**: None (SQL/Alembic)

---

### Task 6.1.3: Load Initial Clinical Guidelines Data (3 hours)

**Prerequisites**: Task 6.1.2

**Steps**:
1. Create data loading script `backend/scripts/load_guidelines.py`
2. Load ADA 2024 guidelines (10 guidelines):
   - Type 2 Diabetes first-line therapy (metformin)
   - HbA1c monitoring (every 3 months)
   - Blood pressure targets (<140/90 for most, <130/80 for diabetes/CKD)
   - Lipid management (statin therapy)
   - Diabetic retinopathy screening (annual)
   - Diabetic nephropathy screening (annual urine ACR)
   - Foot examination (annual)
   - Aspirin therapy (cardiovascular prevention)
   - ACE inhibitor/ARB (diabetes + CKD)
   - Diabetes education (at diagnosis)
3. Load AHA 2017 guidelines (8 guidelines):
   - Hypertension blood pressure targets
   - Antiplatelet therapy (post-MI, post-stroke)
   - Statin therapy (ASCVD risk ≥7.5%)
   - Heart failure management (ACE inhibitor + beta-blocker)
4. Load USPSTF guidelines (15 guidelines):
   - Colorectal cancer screening (age 50-75)
   - Breast cancer screening (mammography age 50-74)
   - Cervical cancer screening (age 21-65)
   - Lung cancer screening (age 50-80, smoking history)
   - Osteoporosis screening (women age 65+)
5. Load NICE guidelines (10 guidelines):
   - UK-specific diabetes management
   - UK-specific hypertension management
6. Write tests (8 tests):
   - Verify 43 guidelines loaded
   - Query by condition_code
   - Query by guideline_source

**Acceptance Criteria**:
- [ ] 43 guidelines loaded successfully
- [ ] All evidence levels (A/B/C) represented
- [ ] Search by condition works
- [ ] 8 tests passing

**Files Created**:
- `backend/scripts/load_guidelines.py`
- `backend/tests/unit/scripts/test_load_guidelines.py`

**Skills**: None (data loading)

---

### Task 6.1.4: Create Guidelines API Endpoint (2 hours)

**Prerequisites**: Task 6.1.3

**Steps**:
1. Create `backend/app/api/v1/endpoints/cds_guidelines.py`
2. Implement endpoints:
   - `GET /api/v1/cds/guidelines` - List all guidelines (paginated)
   - `GET /api/v1/cds/guidelines/search?condition={code}` - Search by condition
   - `GET /api/v1/cds/guidelines/{id}` - Get specific guideline
3. Add RBAC: `@require_role("clinician", "admin")`
4. Add audit logging for guideline access
5. Write tests (10 tests):
   - List guidelines (pagination)
   - Search by ICD-10 code (E11.9 → diabetes guidelines)
   - Search by SNOMED CT code
   - Search by source (ADA, AHA, USPSTF, NICE)
   - Get by ID

**Acceptance Criteria**:
- [ ] 3 endpoints implemented
- [ ] RBAC protection
- [ ] Audit logging
- [ ] 10 tests passing

**Files Created**:
- `backend/app/api/v1/endpoints/cds_guidelines.py`
- `backend/tests/integration/api/test_cds_guidelines_api.py`

**Skills**: None (FastAPI standard patterns)

---

### Task 6.1.5: Create CDS Rules Database Schema (2 hours)

**Prerequisites**: Task 6.1.2

**Steps**:
1. Create migration `backend/alembic/versions/013_cds_rules.py`
2. Define `cds_rules` table:
   - id (UUID primary key)
   - rule_name (VARCHAR 255 unique)
   - description (TEXT)
   - priority (INTEGER default 0, higher = more urgent)
   - conditions (JSONB: IF conditions)
   - actions (JSONB: THEN actions)
   - active (BOOLEAN default TRUE)
   - created_at (TIMESTAMPTZ default NOW())
   - updated_at (TIMESTAMPTZ default NOW())
   - Index on active
   - Index on priority DESC
3. Run migration: `alembic upgrade head`
4. Verify table created

**Acceptance Criteria**:
- [ ] Migration created
- [ ] Table with JSONB fields
- [ ] Indexes created
- [ ] Updated_at trigger

**Files Created**:
- `backend/alembic/versions/013_cds_rules.py`

**Skills**: None (SQL/JSONB)

---

### Task 6.1.6: Install Business Rules Engine (1 hour)

**Prerequisites**: None

**Steps**:
1. Install `business-rules==1.0.1` package
2. Create `backend/app/services/cds/rules_engine.py`
3. Initialize RulesEngine class with basic structure:
   - `__init__()` - setup
   - `evaluate_rules(patient_data: dict) -> List[RuleMatch]` - stub
4. Write placeholder unit tests (5 tests)

**Acceptance Criteria**:
- [ ] business-rules installed
- [ ] RulesEngine class created
- [ ] Basic structure in place
- [ ] 5 placeholder tests

**Files Created**:
- `backend/app/services/cds/rules_engine.py`
- `backend/tests/unit/services/test_rules_engine.py`

**Skills**: None (package installation)

---

### Task 6.1.7: Implement IF-THEN Rule Matching Logic (4 hours)

**Prerequisites**: Task 6.1.6

**Steps**:
1. Implement `evaluate_rules` method:
   - Load active rules from database (active=True)
   - Sort by priority DESC
   - For each rule:
     - Evaluate IF conditions against patient_data
     - If match: append to results
2. Implement condition evaluators:
   - `condition_code` match (patient has ICD-10 code)
   - `diagnosis_age_days` check (how recently diagnosed)
   - `current_medications` check (not_contains, contains)
   - `age` check (min, max)
   - `lab_value` check (HbA1c, BP, etc.)
3. Write tests (20 tests):
   - Simple condition match (condition_code=E11.9)
   - Complex AND conditions
   - NOT conditions (medication NOT present)
   - Age-based rules
   - Lab value-based rules
   - Priority sorting (higher priority first)

**Acceptance Criteria**:
- [ ] IF-THEN logic working
- [ ] 5 condition types supported
- [ ] Priority-based sorting
- [ ] 20 tests passing (edge cases covered)

**Files Modified**:
- `backend/app/services/cds/rules_engine.py`
- `backend/tests/unit/services/test_rules_engine.py`

**Skills**: None (business logic)

---

### Task 6.1.8: Load Initial CDS Rules (3 hours)

**Prerequisites**: Task 6.1.5, Task 6.1.7

**Steps**:
1. Create `backend/scripts/load_cds_rules.py`
2. Load 5 initial rules:
   - **Rule 1**: Diabetes new diagnosis → metformin + HbA1c
     - Conditions: {condition_code: "E11.9", diagnosis_age_days: {max: 30}, current_medications: {not_contains: "metformin"}}
     - Actions: {medications: ["metformin 500mg BD"], lab_orders: ["HbA1c"], rationale: "ADA 2024 first-line therapy"}
   - **Rule 2**: Hypertension uncontrolled → add medication
     - Conditions: {condition_code: "I10", systolic_bp: {min: 140}, bp_measurements_count: 2, current_medications_count: {max: 2}}
     - Actions: {recommendations: ["Consider adding ACE inhibitor or CCB"], rationale: "AHA 2017 guidelines"}
   - **Rule 3**: Diabetes + no eye exam in 12 months → refer ophthalmology
     - Conditions: {condition_code: "E11.9", last_eye_exam_days_ago: {min: 365}}
     - Actions: {referrals: ["Ophthalmology"], rationale: "Diabetic retinopathy screening"}
   - **Rule 4**: Age ≥50, no colonoscopy → screening recommendation
     - Conditions: {age: {min: 50, max: 75}, last_colonoscopy: null}
     - Actions: {screening: ["Colonoscopy"], rationale: "USPSTF colorectal cancer screening"}
   - **Rule 5**: CKD + ACE inhibitor contraindication → ARB alternative
     - Conditions: {condition_code: "N18", allergy: "ACE inhibitor"}
     - Actions: {medications: ["ARB (losartan 50mg)"], rationale: "Alternative for renal protection"}
3. Write tests (10 tests):
   - Verify 5 rules loaded
   - Rule matching works for each rule
   - Priority ordering

**Acceptance Criteria**:
- [ ] 5 rules loaded successfully
- [ ] All rules have valid JSON conditions
- [ ] Rules match against mock patient data
- [ ] 10 tests passing

**Files Created**:
- `backend/scripts/load_cds_rules.py`
- `backend/tests/unit/scripts/test_load_cds_rules.py`

**Skills**: None (data loading)

---

### Task 6.1.9: Create Recommendation Generator Class (3 hours)

**Prerequisites**: Task 6.1.7

**Steps**:
1. Create `backend/app/services/cds/recommendation_generator.py`
2. Implement `RecommendationGenerator` class:
   - `generate(rule_match: RuleMatch, patient_data: dict) -> Recommendation`
   - Extract evidence level from guideline (A/B/C)
   - Create explanation text (why recommended, which guideline)
   - Calculate priority (critical/high/medium/low):
     - Critical: contraindicated medication, severe interaction
     - High: new diagnosis needs treatment, overdue screening
     - Medium: routine monitoring
     - Low: lifestyle recommendations
3. Create Pydantic models:
   - `Recommendation` (id, type, priority, title, description, guideline, evidence_level, actions)
   - `MedicationRecommendation` (medication, dosage, instructions)
   - `LabOrderRecommendation` (lab_code, lab_name, reason)
4. Write tests (15 tests):
   - Generate medication recommendation
   - Generate lab order recommendation
   - Generate referral recommendation
   - Evidence level extraction
   - Priority calculation

**Acceptance Criteria**:
- [ ] RecommendationGenerator class complete
- [ ] 3 Pydantic models defined
- [ ] Evidence levels (A/B/C) populated
- [ ] Priority calculation logic
- [ ] 15 tests passing

**Files Created**:
- `backend/app/services/cds/recommendation_generator.py`
- `backend/app/schemas/cds/recommendation.py`
- `backend/tests/unit/services/test_recommendation_generator.py`

**Skills**: None (business logic)

---

### Task 6.1.10: Create CDS Recommendations Database Schema (2 hours)

**Prerequisites**: Task 6.1.9

**Steps**:
1. Create migration `backend/alembic/versions/014_cds_recommendations.py`
2. Define `cds_recommendations` table:
   - id (UUID primary key)
   - patient_id (VARCHAR 100, NHS number or MRN)
   - rule_id (UUID foreign key → cds_rules.id)
   - recommendation_type (VARCHAR 50: 'medication', 'lab_order', 'referral', 'task')
   - recommendation_text (TEXT)
   - evidence_level (VARCHAR 10: 'A', 'B', 'C')
   - priority (VARCHAR 20: 'critical', 'high', 'medium', 'low')
   - status (VARCHAR 50: 'pending', 'accepted', 'rejected', 'cancelled')
   - rejected_reason (TEXT nullable)
   - created_at (TIMESTAMPTZ default NOW())
   - accepted_at (TIMESTAMPTZ nullable)
   - rejected_at (TIMESTAMPTZ nullable)
   - created_by_user_id (UUID foreign key → users.id)
   - CHECK constraint on status
   - Index on patient_id
   - Index on status
   - Index on created_at DESC
3. Run migration: `alembic upgrade head`

**Acceptance Criteria**:
- [ ] Migration created
- [ ] Table with foreign keys
- [ ] Status check constraint
- [ ] Indexes created

**Files Created**:
- `backend/alembic/versions/014_cds_recommendations.py`

**Skills**: None (SQL/migrations)

---

### Task 6.1.11: Create Recommendation CRUD API (3 hours)

**Prerequisites**: Task 6.1.10

**Steps**:
1. Create `backend/app/api/v1/endpoints/cds_recommendations.py`
2. Implement endpoints:
   - `POST /api/v1/cds/recommendations/generate` - Generate recommendations for patient
   - `GET /api/v1/cds/recommendations` - List recommendations (filtered by status, patient)
   - `PATCH /api/v1/cds/recommendations/{id}/accept` - Accept recommendation
   - `PATCH /api/v1/cds/recommendations/{id}/reject` - Reject recommendation (with reason)
3. Add RBAC: `@require_role("clinician", "admin")`
4. Add audit logging for recommendation actions
5. Write tests (15 tests):
   - Generate recommendations (returns 3 for diabetes patient)
   - Accept recommendation
   - Reject recommendation (with reason)
   - List pending recommendations
   - Filter by patient_id

**Acceptance Criteria**:
- [ ] 4 endpoints implemented
- [ ] RBAC protection
- [ ] Audit logging for accept/reject
- [ ] 15 tests passing

**Files Created**:
- `backend/app/api/v1/endpoints/cds_recommendations.py`
- `backend/tests/integration/api/test_cds_recommendations_api.py`

**Skills**: healthcare-compliance-checker (audit logging for recommendations)

---

### Task 6.1.12: Create Mock FHIR Service for Development (2 hours)

**Prerequisites**: Task 6.1.1

**Steps**:
1. Create `backend/app/services/cds/mock_fhir_service.py`
2. Implement `MockFHIRService` class with 5 mock patient profiles:
   - **Patient 1**: New T2DM diagnosis (triggers metformin rule)
     - NHS number: 1234567881
     - Condition: E11.9 (Type 2 Diabetes), diagnosed 15 days ago
     - Current medications: None
     - Expected: metformin recommendation + HbA1c order
   - **Patient 2**: Uncontrolled hypertension (triggers medication rule)
     - NHS number: 2345678892
     - Condition: I10 (Hypertension)
     - BP readings: 148/92, 152/94 (last 2 visits)
     - Current medications: amlodipine 5mg
     - Expected: add ACE inhibitor recommendation
   - **Patient 3**: Diabetes + no eye exam (triggers referral rule)
     - NHS number: 3456789903
     - Condition: E11.9
     - Last eye exam: 450 days ago
     - Expected: ophthalmology referral
   - **Patient 4**: Age 55, no colonoscopy (triggers screening rule)
     - NHS number: 4567890014
     - Age: 55
     - Last colonoscopy: never
     - Expected: colonoscopy screening recommendation
   - **Patient 5**: CKD + ACE inhibitor allergy (triggers ARB rule)
     - NHS number: 5678901125
     - Condition: N18 (CKD stage 3)
     - Allergies: ["ACE inhibitor"]
     - Expected: ARB (losartan) recommendation
3. Implement methods:
   - `get_patient(nhs_number: str) -> UKCorePatient`
   - `get_conditions(patient_id: str) -> List[UKCoreCondition]`
   - `get_observations(patient_id: str) -> List[UKCoreObservation]`
   - `get_medication_requests(patient_id: str) -> List[UKCoreMedicationRequest]`
4. Write tests (10 tests):
   - Fetch each mock patient
   - Verify FHIR resource structure

**Acceptance Criteria**:
- [ ] 5 mock patient profiles
- [ ] Valid FHIR R4 resources returned
- [ ] Covers all 5 initial CDS rules
- [ ] 10 tests passing

**Files Created**:
- `backend/app/services/cds/mock_fhir_service.py`
- `backend/tests/unit/services/test_mock_fhir_service.py`

**Skills**: None (mock data)

---

### Task 6.1.13: Integrate Rules Engine with Mock FHIR (2 hours)

**Prerequisites**: Task 6.1.11, Task 6.1.12

**Steps**:
1. Create `backend/app/services/cds/cds_service.py`
2. Implement `CDSService` class:
   - `get_recommendations_for_patient(patient_id: str) -> List[Recommendation]`
   - Fetch patient data from MockFHIRService
   - Transform FHIR resources → patient_data dict
   - Call RulesEngine.evaluate_rules(patient_data)
   - For each rule match: call RecommendationGenerator.generate()
   - Save recommendations to database
   - Return list of recommendations
3. Write tests (12 tests):
   - Patient 1 → metformin + HbA1c recommendations
   - Patient 2 → ACE inhibitor recommendation
   - Patient 3 → ophthalmology referral
   - Patient 4 → colonoscopy screening
   - Patient 5 → ARB recommendation

**Acceptance Criteria**:
- [ ] CDSService integrates all components
- [ ] Mock FHIR data → recommendations
- [ ] Recommendations saved to database
- [ ] 12 tests passing (one per patient + edge cases)

**Files Created**:
- `backend/app/services/cds/cds_service.py`
- `backend/tests/unit/services/test_cds_service.py`

**Skills**: None (integration logic)

---

### Task 6.1.14: Implement GET Recommendations API with Mock Data (2 hours)

**Prerequisites**: Task 6.1.13

**Steps**:
1. Update `cds_recommendations.py` endpoint:
   - Wire `POST /api/v1/cds/recommendations/generate` to CDSService
   - Add patient_id validation (NHS number format)
2. Create integration test workflow:
   - Call generate endpoint for Patient 1
   - Verify 2 recommendations returned (metformin + HbA1c)
   - Verify recommendations have evidence_level='A' (from ADA guideline)
   - Verify priority='high' (new diagnosis)
3. Write tests (10 tests):
   - Generate for all 5 mock patients
   - Verify recommendation counts
   - Verify recommendation types
   - Verify priority and evidence levels

**Acceptance Criteria**:
- [ ] API endpoint generates recommendations
- [ ] Works with mock FHIR data
- [ ] Returns proper FHIR-like responses
- [ ] 10 tests passing

**Files Modified**:
- `backend/app/api/v1/endpoints/cds_recommendations.py`
- `backend/tests/integration/api/test_cds_recommendations_api.py`

**Skills**: None (API integration)

---

### Task 6.1.15: Create Audit Logging for CDS Actions (2 hours)

**Prerequisites**: Task 6.1.14

**Steps**:
1. Extend audit logging service for CDS:
   - Action: CDS_RECOMMENDATION_GENERATED
   - Action: CDS_RECOMMENDATION_ACCEPTED
   - Action: CDS_RECOMMENDATION_REJECTED
2. Add audit logs to all CDS endpoints:
   - Generate recommendations → log patient_id, rule_ids triggered
   - Accept recommendation → log recommendation_id, user_id
   - Reject recommendation → log recommendation_id, rejected_reason
3. Write tests (8 tests):
   - Verify audit log created on generate
   - Verify audit log created on accept
   - Verify audit log created on reject
   - Verify PHI (patient_id) logged correctly

**Acceptance Criteria**:
- [ ] 3 new audit action types
- [ ] Audit logs on all CDS endpoints
- [ ] PHI handling compliant
- [ ] 8 tests passing

**Files Modified**:
- `backend/app/services/audit_service.py`
- `backend/app/api/v1/endpoints/cds_recommendations.py`
- `backend/tests/integration/services/test_audit_service.py`

**Skills**: healthcare-compliance-checker (audit logging for PHI access)

---

### Task 6.1.16: Write Comprehensive Unit Tests for Phase 6.1 (3 hours)

**Prerequisites**: Tasks 6.1.1-6.1.15

**Steps**:
1. Review current test coverage: `pytest --cov=app.services.cds --cov=app.schemas.cds --cov-report=term`
2. Identify gaps (target: 95% coverage for Phase 6.1 code)
3. Write additional tests for:
   - Edge cases (empty rule results, no matching guidelines)
   - Error handling (invalid NHS numbers, malformed JSONB)
   - Concurrent rule evaluation
   - Priority tie-breaking
4. Add performance tests:
   - 100 rules evaluated in <500ms
   - 1000 guidelines searchable in <100ms
5. Total tests written this phase: 78+ tests

**Acceptance Criteria**:
- [ ] 95% code coverage for Phase 6.1
- [ ] All edge cases covered
- [ ] Performance tests passing
- [ ] 78+ tests total

**Files Modified**:
- Various test files

**Skills**: None (testing)

---

### Task 6.1.17-6.1.22: Frontend Components for CDS (Parallel - 6 tasks, 12 hours total)

**Note**: These can be done in parallel or skipped for backend-focused development

**Task 6.1.17**: Create CDS Recommendations Component (2 hours)
- Vue 3 component: `frontend/src/components/cds/CDSRecommendations.vue`
- Display list of recommendations with priority badges
- Actions: Accept, Reject (with reason dialog)
- Write 15 unit tests (Vitest)

**Task 6.1.18**: Create Recommendation Card Component (2 hours)
- Vue 3 component: `frontend/src/components/cds/RecommendationCard.vue`
- Show recommendation title, description, guideline, evidence level
- Expandable details section
- Write 12 unit tests

**Task 6.1.19**: Create useCDSRecommendations Composable (2 hours)
- Composable: `frontend/src/composables/useCDSRecommendations.ts`
- State management for recommendations
- API integration (fetch, accept, reject)
- Write 10 unit tests

**Task 6.1.20**: Create CDS Settings View (Admin) (2 hours)
- View: `frontend/src/views/admin/CDSSettings.vue`
- List CDS rules with active/inactive toggle
- Edit rule priority
- Write 8 unit tests

**Task 6.1.21**: Integration Tests for CDS Frontend (2 hours)
- E2E tests: `frontend/tests/e2e/cds.spec.ts`
- Full workflow: Generate → Accept → Verify
- Test all 5 mock patients
- 10 E2E tests

**Task 6.1.22**: Update Navigation and Routing (2 hours)
- Add CDS routes to router
- Add navigation menu items
- Update breadcrumbs
- Write 5 tests

---

## Phase 6.2: Meditech Read Integration (15 tasks, 60 hours)

**Goal**: Replace MockFHIRService with real Meditech integration

### Task 6.2.1: Setup OAuth 2.0 Client (3 hours)

**Prerequisites**: Meditech sandbox credentials obtained

**Steps**:
1. Install `authlib==1.3.0` package
2. Create `backend/app/clients/meditech_oauth_client.py`
3. Implement `MeditechOAuthClient` class:
   - `get_access_token() -> str`
   - OAuth 2.0 client credentials flow
   - POST to `MEDITECH_TOKEN_URL` (from env)
   - Cache token in Redis (TTL = token expiry - 60 seconds)
   - Refresh token automatically when expired
4. Add environment variables:
   - `MEDITECH_CLIENT_ID`
   - `MEDITECH_CLIENT_SECRET`
   - `MEDITECH_TOKEN_URL=https://meditech-uk.cloud/oauth2/token`
   - `MEDITECH_FHIR_BASE_URL=https://meditech-uk.cloud/fhir/r4`
5. Write tests (12 tests):
   - Token fetch success
   - Token cached in Redis
   - Token refresh on expiry
   - Invalid credentials handling

**Acceptance Criteria**:
- [ ] OAuth 2.0 client implemented
- [ ] Token caching in Redis
- [ ] Auto-refresh on expiry
- [ ] 12 tests passing

**Files Created**:
- `backend/app/clients/meditech_oauth_client.py`
- `backend/tests/unit/clients/test_meditech_oauth_client.py`

**Skills**: None (OAuth standard patterns)

---

### Task 6.2.2: Create FHIR Client for Read Operations (4 hours)

**Prerequisites**: Task 6.2.1

**Steps**:
1. Install `httpx==0.27.0` package (async HTTP client)
2. Create `backend/app/clients/meditech_fhir_client.py`
3. Implement `MeditechFHIRClient` class:
   - `__init__(oauth_client: MeditechOAuthClient)`
   - `get_patient(nhs_number: str) -> UKCorePatient`
   - `get_conditions(patient_id: str) -> List[UKCoreCondition]`
   - `get_observations(patient_id: str) -> List[UKCoreObservation]`
   - `get_medication_requests(patient_id: str) -> List[UKCoreMedicationRequest]`
4. Use `httpx.AsyncClient` for all requests
5. Add Authorization header: `Bearer {access_token}`
6. Error handling:
   - 401 Unauthorized → retry with token refresh
   - 404 Not Found → return empty list
   - 429 Rate Limit → exponential backoff (1s, 2s, 4s, max 3 retries)
   - 500 Server Error → log error, return empty list
7. Write tests (25 tests):
   - Successful GET Patient
   - Successful GET Conditions
   - 401 → token refresh → retry success
   - 404 → empty list
   - 429 → exponential backoff
   - 500 → error logged

**Acceptance Criteria**:
- [ ] 4 read methods implemented
- [ ] Async HTTP with httpx
- [ ] Error handling for 401, 404, 429, 500
- [ ] 25 tests passing

**Files Created**:
- `backend/app/clients/meditech_fhir_client.py`
- `backend/tests/unit/clients/test_meditech_fhir_client.py`

**Skills**: None (HTTP client)

---

### Task 6.2.3: Implement NHS FHIR UK Core Validation (3 hours)

**Prerequisites**: Task 6.1.1

**Steps**:
1. Create `backend/app/services/cds/nhs_fhir_validator.py`
2. Implement `NHSFHIRValidator` class:
   - `validate_nhs_number(nhs_number: str) -> bool`
     - 10 digits
     - Modulus 11 checksum algorithm
   - `validate_dm_d_code(code: str) -> bool`
     - 18-digit SNOMED CT dm+d code format
   - `validate_ods_code(code: str) -> bool`
     - Organization code format (3-5 alphanumeric)
3. NHS number checksum algorithm:
   - Multiply first 9 digits by weights (10, 9, 8, 7, 6, 5, 4, 3, 2)
   - Sum products
   - Modulus 11
   - 11 - result = check digit (10th digit)
4. Write tests (18 tests):
   - Valid NHS numbers (1234567881, 9876543210)
   - Invalid NHS numbers (wrong checksum, wrong length)
   - Valid dm+d codes (18 digits)
   - Invalid dm+d codes
   - Valid ODS codes
   - Invalid ODS codes

**Acceptance Criteria**:
- [ ] 3 validation methods
- [ ] NHS number Modulus 11 checksum
- [ ] 18 tests passing (valid + invalid for each)

**Files Created**:
- `backend/app/services/cds/nhs_fhir_validator.py`
- `backend/tests/unit/services/test_nhs_fhir_validator.py`

**Skills**: None (validation logic)

---

### Task 6.2.4: Implement Patient Data Caching (2 hours)

**Prerequisites**: Task 6.2.2

**Steps**:
1. Create `backend/app/services/cds/patient_data_cache.py`
2. Implement `PatientDataCache` class:
   - `get_patient_data(patient_id: str) -> Optional[dict]`
   - `set_patient_data(patient_id: str, data: dict, ttl: int = 300)` (5-minute TTL)
   - Cache key format: `patient:fhir:{nhs_number}`
   - Store FHIR resources as JSON in Redis
3. Integrate caching into MeditechFHIRClient:
   - Check cache before FHIR API call
   - If cache hit: return cached data
   - If cache miss: call FHIR API, cache result, return
4. Write tests (8 tests):
   - Cache miss → FHIR call → cache set
   - Cache hit → no FHIR call
   - Cache expiry after 5 minutes
   - Cache invalidation

**Acceptance Criteria**:
- [ ] Redis caching implemented
- [ ] 5-minute TTL
- [ ] Cache hit reduces FHIR calls
- [ ] 8 tests passing

**Files Created**:
- `backend/app/services/cds/patient_data_cache.py`
- `backend/tests/unit/services/test_patient_data_cache.py`

**Skills**: None (caching patterns)

---

### Task 6.2.5-6.2.15: Additional Meditech Integration Tasks (11 tasks)

**Task 6.2.5**: Integration Test with Meditech Sandbox (1 hour)
- Test real FHIR read operations against Meditech sandbox
- Verify Patient, Condition, Observation, MedicationRequest resources
- Measure API response times (target: <500ms per read)
- Write 5 integration tests

**Task 6.2.6**: Replace MockFHIRService with MeditechFHIRClient (1 hour)
- Update CDSService to use MeditechFHIRClient instead of Mock
- Add feature flag: `USE_MOCK_FHIR` (default: False)
- Keep MockFHIRService for local development/testing
- Write 3 tests

**Task 6.2.7**: Implement Rate Limiting Handling (2 hours)
- Track FHIR API calls per minute
- Implement exponential backoff on 429 responses
- Log rate limit warnings
- Write 8 tests

**Task 6.2.8**: Add Meditech Error Monitoring (2 hours)
- Log all FHIR API errors to application logs
- Track success/failure rates
- Alert on high error rates
- Write 6 tests

**Task 6.2.9**: Implement FHIR Resource Mapping (3 hours)
- Transform FHIR resources → patient_data dict for rules engine
- Handle missing fields gracefully
- Write 12 tests

**Task 6.2.10**: Add FHIR Search Parameters (2 hours)
- Support filtering by date range
- Support filtering by code (ICD-10, SNOMED CT)
- Write 8 tests

**Task 6.2.11**: Implement Batch FHIR Requests (3 hours)
- Fetch multiple resources in single API call (FHIR Bundle)
- Reduce API calls from 4 to 1 per patient
- Write 10 tests

**Task 6.2.12**: Add FHIR Pagination Support (2 hours)
- Handle paginated responses (100 resources per page)
- Follow `next` links automatically
- Write 6 tests

**Task 6.2.13**: Create FHIR Audit Logging (2 hours)
- Log all FHIR reads to audit_logs table
- Include: patient_id, resource_type, user_id, timestamp
- Write 8 tests

**Task 6.2.14**: Performance Testing for FHIR Integration (2 hours)
- Test 50 concurrent FHIR reads
- Verify <500ms response time (P95)
- Verify cache hit rate >50%
- Write 5 performance tests

**Task 6.2.15**: Update Documentation for Meditech Integration (2 hours)
- Document OAuth 2.0 setup
- Document FHIR read operations
- Add troubleshooting guide
- Update CONTEXT.md with ADR

---

## Phase 6.3: Drug Interaction Checking (10 tasks, 30 hours)

**Goal**: Implement drug interaction detection using NHS dm+d

### Task 6.3.1: Download and Parse NHS dm+d Data (4 hours)

**Prerequisites**: NHS Digital TRUD account created

**Steps**:
1. Download dm+d from TRUD: https://isd.digital.nhs.uk/trud3/user/guest/group/0/pack/6
2. Create `backend/scripts/download_dmd.py`:
   - Authenticate with TRUD API
   - Download latest dm+d XML files
   - Extract to `backend/data/dmd/`
3. Create `backend/scripts/parse_dmd.py`:
   - Parse VTM (Virtual Therapeutic Moiety) XML
   - Parse VMP (Virtual Medicinal Product) XML
   - Parse AMP (Actual Medicinal Product) XML
   - Extract: dm_d_code, name, form, strength, unit
4. Write tests (5 tests):
   - Parse VTM XML (1000 records)
   - Parse VMP XML (50000 records)
   - Parse AMP XML (150000 records)

**Acceptance Criteria**:
- [ ] dm+d downloaded successfully
- [ ] XML parsing works
- [ ] ~200,000 medications extracted
- [ ] 5 tests passing

**Files Created**:
- `backend/scripts/download_dmd.py`
- `backend/scripts/parse_dmd.py`
- `backend/tests/unit/scripts/test_parse_dmd.py`

**Skills**: None (data ETL)

---

### Task 6.3.2: Create NHS dm+d Database Schema and Load Data (3 hours)

**Prerequisites**: Task 6.3.1

**Steps**:
1. Create migration `backend/alembic/versions/015_nhs_dmd_medications.py`
2. Define `nhs_dmd_medications` table (see technical plan schema)
3. Create `backend/scripts/load_dmd.py`:
   - Read parsed dm+d data
   - Bulk insert into PostgreSQL (batches of 1000)
   - Create full-text search index: `CREATE INDEX idx_dmd_name_gin ON nhs_dmd_medications USING gin(to_tsvector('english', name))`
4. Run load script: `python backend/scripts/load_dmd.py`
5. Verify: `SELECT COUNT(*) FROM nhs_dmd_medications` (expect ~200,000)
6. Write tests (5 tests):
   - Bulk insert 1000 records
   - Full-text search works
   - Query by dm_d_code

**Acceptance Criteria**:
- [ ] Table created
- [ ] ~200,000 medications loaded
- [ ] Full-text search index created
- [ ] 5 tests passing

**Files Created**:
- `backend/alembic/versions/015_nhs_dmd_medications.py`
- `backend/scripts/load_dmd.py`
- `backend/tests/integration/scripts/test_load_dmd.py`

**Skills**: None (data loading)

---

### Task 6.3.3: Create Medication Search API (2 hours)

**Prerequisites**: Task 6.3.2

**Steps**:
1. Create `backend/app/api/v1/endpoints/cds_medications.py`
2. Implement endpoint:
   - `GET /api/v1/cds/medications/search?q={query}`
   - Full-text search using `to_tsquery`
   - Return top 20 results
3. Write tests (8 tests):
   - Search "metformin" → find metformin 500mg, 850mg, 1000mg
   - Search "aspirin" → find aspirin products
   - Search partial word "metfor" → find metformin

**Acceptance Criteria**:
- [ ] Search endpoint working
- [ ] Full-text search accurate
- [ ] 8 tests passing

**Files Created**:
- `backend/app/api/v1/endpoints/cds_medications.py`
- `backend/tests/integration/api/test_cds_medications_api.py`

**Skills**: None (search API)

---

### Task 6.3.4: Setup Drug Interaction Database (OpenFDA) (3 hours)

**Prerequisites**: None

**Steps**:
1. Create `backend/scripts/fetch_openfda_interactions.py`:
   - Query OpenFDA API: `https://api.fda.gov/drug/drugsfda.json`
   - Extract top 50 common drug interactions
   - Map RxNorm codes to drug names
2. Create `RxNorm ↔ dm+d` mapping table:
   - Create migration `016_rxnorm_dmd_mapping.py`
   - Table: rxnorm_code, dm_d_code, mapping_source
   - Load initial mappings for top 100 medications
3. Create migration `017_drug_interactions.py` (see technical plan schema)
4. Load interactions: `python backend/scripts/load_drug_interactions.py`
5. Write tests (8 tests):
   - OpenFDA fetch works
   - RxNorm mapping works
   - Interaction loading works

**Acceptance Criteria**:
- [ ] OpenFDA integration working
- [ ] RxNorm ↔ dm+d mapping table
- [ ] 50 interactions loaded
- [ ] 8 tests passing

**Files Created**:
- `backend/scripts/fetch_openfda_interactions.py`
- `backend/scripts/load_drug_interactions.py`
- `backend/alembic/versions/016_rxnorm_dmd_mapping.py`
- `backend/alembic/versions/017_drug_interactions.py`

**Skills**: None (data integration)

---

### Task 6.3.5: Implement DrugInteractionChecker Class (3 hours)

**Prerequisites**: Task 6.3.4

**Steps**:
1. Create `backend/app/services/cds/drug_interaction_checker.py`
2. Implement `DrugInteractionChecker` class:
   - `check_interactions(new_medication_code: str, current_medications: List[str]) -> List[Interaction]`
   - Query drug_interactions table:
     - WHERE (drug_a_code = new_med AND drug_b_code IN current_meds) OR vice versa
   - Filter severity: return contraindicated + major + moderate (skip minor)
   - Sort by severity: contraindicated first, then major, then moderate
3. Write tests (12 tests):
   - Warfarin + Aspirin → major interaction
   - ACE inhibitor + Potassium supplement → moderate interaction
   - Metformin + Insulin → no interaction
   - Multiple current medications → find all interactions

**Acceptance Criteria**:
- [ ] Interaction detection working
- [ ] Severity filtering (contraindicated/major/moderate)
- [ ] 12 tests passing

**Files Created**:
- `backend/app/services/cds/drug_interaction_checker.py`
- `backend/tests/unit/services/test_drug_interaction_checker.py`

**Skills**: None (business logic)

---

### Task 6.3.6-6.3.10: Additional Drug Interaction Tasks (5 tasks)

**Task 6.3.6**: Implement AlternativeFinder Class (3 hours)
- Find alternative medications in same therapeutic class
- Exclude interacting medications
- Sort by usage frequency
- Write 10 tests

**Task 6.3.7**: Create Drug Interaction Check API (2 hours)
- `POST /api/v1/cds/check-interactions`
- Integrate DrugInteractionChecker
- Return interactions + alternatives
- Write 10 tests

**Task 6.3.8**: Add Interaction Checking to CDS Rules (2 hours)
- Before recommending medication, check interactions
- If contraindicated/major: don't recommend, suggest alternative
- Write 8 tests

**Task 6.3.9**: Create Interaction Warnings UI Component (2 hours)
- Vue component: InteractionWarning.vue
- Red banner for contraindicated
- Orange banner for major
- Yellow banner for moderate
- Write 10 tests

**Task 6.3.10**: Integration Tests for Drug Interactions (3 hours)
- Full workflow: New medication → check interactions → display warning → suggest alternative
- Test all severity levels
- Write 12 integration tests

---

## Phase 6.4: Meditech Write Integration (20 tasks, 90 hours)

[Continuing with similar detailed task breakdowns for write operations...]

**Note**: Due to length constraints, I'm providing the structure. The remaining phases would follow the same pattern with 1-2 hour tasks, clear prerequisites, steps, acceptance criteria, and skills.

---

## Phase 6.5: Clinical Governance & RBAC (10 tasks, 30 hours)

**Tasks include**:
- 6.5.1: Extend RBAC for CDS roles
- 6.5.2: Implement approval workflows
- 6.5.3: Drug allergy checking
- 6.5.4: Contraindication checking
- 6.5.5: Duplicate order detection
- 6.5.6: Override tracking
- 6.5.7-6.5.10: Additional safety and governance tasks

---

## Phase 6.6: Meditech Workflow Integration (8 tasks, 30 hours)

**Tasks include**:
- 6.6.1: InBasket alert integration
- 6.6.2: Order entry pre-population
- 6.6.3: Task creation in Meditech
- 6.6.4-6.6.8: Additional workflow integration tasks

---

## Phase 6.7: Testing & Validation (8 tasks, 30 hours)

**Tasks include**:
- 6.7.1: Achieve 90% unit test coverage
- 6.7.2: Integration tests for all FHIR operations
- 6.7.3: UAT with pilot clinicians
- 6.7.4: Performance testing (50 concurrent users)
- 6.7.5-6.7.8: Additional testing and validation tasks

---

## Summary

**Total Tasks**: 67 tasks
**Total Estimated Time**: 360 hours (12 weeks)
**Test Coverage Target**: 90% overall, 100% for PHI-related code

**Dependencies**:
- Meditech sandbox access (required by Week 0)
- NHS dm+d download (required by Phase 6.3)
- Clinical governance approval (required before production)

**Skills Required Throughout**:
- healthcare-compliance-checker (for all PHI-related tasks)
- medcat-meta-annotations (for NLP-related tasks if integrated)
- fhir-r4-mapper (for FHIR resource handling)

**Next Steps**:
1. Review and approve task breakdown
2. Begin Phase 6.1 Task 6.1.1 (Setup FHIR Models)
3. Update CONTEXT.md as tasks complete
4. Create `.claude/ccpm/epics/sprint-6-cds/` directory with individual task files

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-23
**Status**: ✅ Ready for Implementation
