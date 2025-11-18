# Tasks: Clinical Decision Support + Meditech Integration (Sprint 6)

**Plan Reference**: `.specify/plans/sprint-6-clinical-decision-support-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-6-clinical-decision-support.md` (v1.0.0)
**Estimated Total Time**: 360 hours (12 weeks)
**Dependencies**:
- Sprints 1-5.5 completed
- Meditech Expanse sandbox access (FHIR R4)
- NHS dm+d database downloaded

**CRITICAL**: Week 0 verification of Meditech sandbox capabilities REQUIRED before sprint starts

---

## Phase 6.1: CDS Core Infrastructure (90 hours)

### Task 6.1.1: Verify Meditech Sandbox Capabilities (Week 0)
**Goal**: **MANDATORY PRE-SPRINT** - Verify Meditech FHIR API capabilities
**Phase**: 6.1 | **Dependencies**: None | **Time**: 8h
**Steps**: 1) Test OAuth 2.0 auth, 2) Test FHIR read (Patient, Condition, Observation, MedicationRequest), 3) Test FHIR write (draft orders), 4) Document supported resources, 5) Identify limitations
**Acceptance**: Sandbox capabilities documented, read/write verified
**Files**: `docs/meditech-sandbox-capabilities.md`

### Task 6.1.2: Setup FHIR Client Library
**Goal**: Configure fhir.resources Python library
**Phase**: 6.1 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Install fhir.resources, 2) Configure FHIR R4 client, 3) Test basic operations (create Patient resource)
**Acceptance**: FHIR client configured, basic operations work
**Files**: `backend/requirements.txt`, `backend/app/clients/fhir_client.py`

### Task 6.1.3: Create Clinical Guidelines Database
**Goal**: PostgreSQL table for clinical guidelines (ADA, AHA, USPSTF, NICE)
**Phase**: 6.1 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Create clinical_guidelines table, 2) Define schema (guideline_id, name, version, rules JSON), 3) Load initial guidelines (≥5 guidelines)
**Acceptance**: Guidelines table created, 5+ guidelines loaded
**Files**: `backend/alembic/versions/XXX_create_clinical_guidelines.py`, `scripts/load_clinical_guidelines.py`

### Task 6.1.4: Create Rule Engine
**Goal**: Engine to evaluate clinical rules (IF-THEN logic)
**Phase**: 6.1 | **Dependencies**: Task 6.1.3 | **Time**: 12h
**Steps**: 1) Write tests (TDD), 2) Create `RuleEngine` class, 3) Implement rule evaluation (IF conditions → THEN recommendations), 4) Support operators (>, <, ==, AND, OR), 5) Support time-based conditions
**Acceptance**: Rules evaluated correctly, supports complex logic
**Test Coverage**: 20 unit tests
**Files**: `backend/app/services/rule_engine.py`, `tests/unit/services/test_rule_engine.py`

### Task 6.1.5: Create CDS Service
**Goal**: Service to generate CDS recommendations
**Phase**: 6.1 | **Dependencies**: Task 6.1.4 | **Time**: 12h
**Steps**: 1) Write tests, 2) Create `CDSService`, 3) Fetch patient data (FHIR), 4) Evaluate rules, 5) Generate recommendations, 6) Grade evidence (A/B/C), 7) Return recommendations
**Acceptance**: Recommendations generated for ≥5 guidelines
**Test Coverage**: 18 unit tests
**Files**: `backend/app/services/cds_service.py`, `tests/unit/services/test_cds_service.py`

### Task 6.1.6: Create CDS API Endpoint
**Goal**: POST /api/v1/cds/recommendations
**Phase**: 6.1 | **Dependencies**: Task 6.1.5 | **Time**: 6h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call CDS service, 4) Return recommendations with evidence
**Acceptance**: Endpoint returns recommendations
**Test Coverage**: 10 integration tests
**Files**: `backend/app/api/v1/endpoints/cds.py`, `tests/integration/test_cds_api.py`

### Task 6.1.7: Create Audit Logging for CDS
**Goal**: Log all CDS recommendations and clinician actions
**Phase**: 6.1 | **Dependencies**: Task 6.1.6 | **Time**: 4h
**Steps**: 1) Log recommendation generation, 2) Log acceptance/rejection, 3) Log overrides
**Acceptance**: All CDS operations logged
**Files**: `backend/app/api/v1/endpoints/cds.py` (updated)

### Task 6.1.8: Unit Tests - CDS Service
**Goal**: Comprehensive unit tests
**Phase**: 6.1 | **Dependencies**: Task 6.1.5 | **Time**: 8h
**Steps**: 1) Write tests for all guidelines, 2) Test edge cases, 3) Test error handling
**Acceptance**: Code coverage ≥85%, all tests passing
**Test Coverage**: 30+ unit tests
**Files**: `tests/unit/services/test_cds_service.py` (expanded)

### Task 6.1.9: Create CDS UI Component
**Goal**: Frontend component to display CDS recommendations
**Phase**: 6.1 | **Dependencies**: Task 6.1.6 | **Time**: 10h
**Steps**: 1) Create `CDSRecommendationsPanel.vue`, 2) Fetch recommendations, 3) Display with evidence grades, 4) Accept/reject/override buttons
**Acceptance**: UI displays recommendations, allows clinician actions
**Files**: `webapp/src/components/cds/CDSRecommendationsPanel.vue`

### Task 6.1.10: Integration Tests - CDS Workflow
**Goal**: Integration tests for CDS workflow
**Phase**: 6.1 | **Dependencies**: Task 6.1.6 | **Time**: 6h
**Steps**: 1) Write tests (fetch patient data → generate recommendations → display), 2) Run tests
**Acceptance**: All integration tests passing
**Test Coverage**: 12 integration tests
**Files**: `tests/integration/test_cds_workflow.py`

### Task 6.1.11: Performance Testing - CDS
**Goal**: Verify CDS response <3 seconds
**Phase**: 6.1 | **Dependencies**: Task 6.1.5 | **Time**: 4h
**Steps**: 1) Performance tests with varying patient complexity, 2) Measure response time
**Acceptance**: CDS recommendations <3 seconds
**Files**: `tests/performance/test_cds_performance.py`

### Task 6.1.12: Documentation - CDS Guidelines
**Goal**: Document clinical guidelines implemented
**Phase**: 6.1 | **Dependencies**: Task 6.1.3 | **Time**: 10h
**Steps**: 1) Document each guideline, 2) Document evidence sources, 3) Document rule logic
**Acceptance**: All guidelines documented
**Files**: `docs/clinical-guidelines/`

---

## Phase 6.2: Meditech Read Integration (60 hours)

### Task 6.2.1: Implement OAuth 2.0 Authentication
**Goal**: OAuth 2.0 client for Meditech authentication
**Phase**: 6.2 | **Dependencies**: Task 6.1.1 | **Time**: 8h
**Steps**: 1) Install authlib, 2) Create OAuth client, 3) Implement token acquisition, 4) Implement token refresh, 5) Store tokens securely
**Acceptance**: OAuth authentication works, tokens refresh automatically
**Files**: `backend/app/clients/meditech_oauth_client.py`, `tests/unit/clients/test_meditech_oauth.py`

### Task 6.2.2: Create Meditech FHIR Client
**Goal**: Client to read FHIR resources from Meditech
**Phase**: 6.2 | **Dependencies**: Task 6.2.1 | **Time**: 8h
**Steps**: 1) Write tests (TDD), 2) Create `MeditechFHIRClient`, 3) Implement `get_patient(nhs_number)`, 4) Implement `get_conditions(patient_id)`, 5) Implement `get_observations(patient_id)`, 6) Implement `get_medications(patient_id)`
**Acceptance**: All read operations work against Meditech sandbox
**Test Coverage**: 15 unit tests
**Files**: `backend/app/clients/meditech_fhir_client.py`, `tests/unit/clients/test_meditech_fhir_client.py`

### Task 6.2.3: Map NHS FHIR UK Core Profiles
**Goal**: Handle NHS FHIR UK Core profile nuances
**Phase**: 6.2 | **Dependencies**: Task 6.2.2 | **Time**: 6h
**Steps**: 1) Review NHS FHIR UK Core profiles, 2) Map NHS number identifier, 3) Map UK-specific codings (SNOMED CT UK edition, dm+d)
**Acceptance**: UK FHIR profiles handled correctly
**Files**: `backend/app/clients/meditech_fhir_client.py` (updated)

### Task 6.2.4: Implement Patient Data Caching (Redis)
**Goal**: Cache patient data to reduce Meditech API calls
**Phase**: 6.2 | **Dependencies**: Task 6.2.2 | **Time**: 4h
**Steps**: 1) Cache patient data in Redis, 2) TTL: 5 minutes, 3) Cache key: `meditech:patient:{patient_id}`
**Acceptance**: Patient data cached, cache hit rate >50%
**Files**: `backend/app/clients/meditech_fhir_client.py` (updated)

### Task 6.2.5: Implement Error Handling and Circuit Breaker
**Goal**: Handle Meditech API failures gracefully
**Phase**: 6.2 | **Dependencies**: Task 6.2.2 | **Time**: 6h
**Steps**: 1) Implement retry logic (3 retries with backoff), 2) Implement circuit breaker (open after 5 failures in 1 minute), 3) Fallback to cached data
**Acceptance**: Circuit breaker prevents cascading failures
**Files**: `backend/app/clients/meditech_fhir_client.py` (updated)

### Task 6.2.6: Create Meditech Patient Data API Endpoint (Internal)
**Goal**: GET /api/internal/meditech/patients/{nhs_number}
**Phase**: 6.2 | **Dependencies**: Task 6.2.2 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call Meditech client, 4) Return FHIR resources
**Acceptance**: Endpoint returns patient data from Meditech
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/internal/endpoints/meditech.py`, `tests/integration/test_meditech_read_api.py`

### Task 6.2.7: Integration Tests - Meditech Read
**Goal**: Integration tests against Meditech sandbox
**Phase**: 6.2 | **Dependencies**: Task 6.2.2 | **Time**: 8h
**Steps**: 1) Write integration tests (read Patient, Condition, Observation, Medication), 2) Run against sandbox
**Acceptance**: All integration tests passing against Meditech sandbox
**Test Coverage**: 15 integration tests
**Files**: `tests/integration/test_meditech_read_integration.py`

### Task 6.2.8: Performance Testing - Meditech Read
**Goal**: Verify read performance acceptable
**Phase**: 6.2 | **Dependencies**: Task 6.2.4 | **Time**: 4h
**Steps**: 1) Performance tests (uncached vs cached), 2) Measure response time
**Acceptance**: Cached reads <500ms, uncached <3 seconds
**Files**: `tests/performance/test_meditech_read_performance.py`

### Task 6.2.9: Documentation - Meditech Read Integration
**Goal**: Document Meditech read integration
**Phase**: 6.2 | **Dependencies**: Task 6.2.2 | **Time**: 4h
**Steps**: 1) Document API endpoints, 2) Document data flows, 3) Document error handling
**Acceptance**: Documentation complete
**Files**: `docs/integrations/meditech-read-integration.md`

### Task 6.2.10: E2E Tests - CDS with Meditech Data
**Goal**: E2E tests using real Meditech data
**Phase**: 6.2 | **Dependencies**: Tasks 6.1.6, 6.2.2 | **Time**: 8h
**Steps**: 1) Write E2E tests (fetch Meditech data → generate CDS recommendations)
**Acceptance**: E2E tests passing
**Test Coverage**: 8 E2E tests
**Files**: `tests/e2e/test_cds_meditech.py`

---

## Phase 6.3: Drug Interaction Checking (30 hours)

### Task 6.3.1: Download NHS dm+d Database
**Goal**: Download dictionary of medicines and devices
**Phase**: 6.3 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Register for NHS TRUD access, 2) Download dm+d database, 3) Parse XML, 4) Extract drug codes and names
**Acceptance**: dm+d database downloaded and parsed
**Files**: `scripts/download_dmd.py`

### Task 6.3.2: Create Drug Interaction Database Schema
**Goal**: PostgreSQL table for drug interactions
**Phase**: 6.3 | **Dependencies**: Task 6.3.1 | **Time**: 4h
**Steps**: 1) Create drug_interactions table, 2) Define schema (drug1_code, drug2_code, severity, description), 3) Load interaction data
**Acceptance**: Interactions table created, data loaded
**Files**: `backend/alembic/versions/XXX_create_drug_interactions.py`, `scripts/load_drug_interactions.py`

### Task 6.3.3: Create Drug Interaction Service
**Goal**: Service to detect drug interactions
**Phase**: 6.3 | **Dependencies**: Task 6.3.2 | **Time**: 8h
**Steps**: 1) Write tests (TDD), 2) Create `DrugInteractionService`, 3) Implement `check_interactions(medication_list)`, 4) Query interactions table, 5) Classify severity (contraindicated, major, moderate, minor), 6) Suggest alternatives
**Acceptance**: Interactions detected with ≥99% accuracy for contraindicated/major
**Test Coverage**: 15 unit tests
**Files**: `backend/app/services/drug_interaction_service.py`, `tests/unit/services/test_drug_interaction_service.py`

### Task 6.3.4: Integrate Drug Checking into CDS
**Goal**: Include drug interaction checks in CDS recommendations
**Phase**: 6.3 | **Dependencies**: Tasks 6.1.5, 6.3.3 | **Time**: 4h
**Steps**: 1) Call drug interaction service in CDS service, 2) Add interaction warnings to recommendations
**Acceptance**: CDS includes drug interaction warnings
**Files**: `backend/app/services/cds_service.py` (updated)

### Task 6.3.5: Create Drug Interaction API Endpoint
**Goal**: POST /api/v1/drugs/check-interactions
**Phase**: 6.3 | **Dependencies**: Task 6.3.3 | **Time**: 3h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call drug interaction service, 4) Return interactions
**Acceptance**: Endpoint returns drug interactions
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/v1/endpoints/drugs.py`, `tests/integration/test_drug_interaction_api.py`

### Task 6.3.6: Integration Tests - Drug Interactions
**Goal**: Integration tests for drug interaction checking
**Phase**: 6.3 | **Dependencies**: Task 6.3.3 | **Time**: 3h
**Steps**: 1) Write tests (known interactions, no interactions, alternative suggestions)
**Acceptance**: All integration tests passing
**Test Coverage**: 10 integration tests
**Files**: `tests/integration/test_drug_interaction_integration.py`

### Task 6.3.7: Documentation - Drug Interaction Database
**Goal**: Document drug interaction data sources
**Phase**: 6.3 | **Dependencies**: Task 6.3.2 | **Time**: 4h
**Steps**: 1) Document NHS dm+d, 2) Document interaction data sources, 3) Document update procedure
**Acceptance**: Documentation complete
**Files**: `docs/drug-interactions.md`

---

## Phase 6.4: Meditech Write Integration (90 hours)

### Task 6.4.1: Implement FHIR Write Operations (Draft Orders Only)
**Goal**: Create draft MedicationRequest, ServiceRequest, Task, CommunicationRequest
**Phase**: 6.4 | **Dependencies**: Task 6.2.2 | **Time**: 12h
**Steps**: 1) Write tests (TDD), 2) Implement `create_medication_request(patient_id, medication, status='draft')`, 3) Implement `create_service_request()`, 4) Implement `create_task()`, 5) Implement `create_communication_request()`, 6) Validate NHS FHIR UK Core profiles
**Acceptance**: Draft orders created in Meditech sandbox
**Test Coverage**: 20 unit tests
**Files**: `backend/app/clients/meditech_fhir_client.py` (updated), `tests/unit/clients/test_meditech_write.py`

### Task 6.4.2: Implement Write Validation and Safety Checks
**Goal**: Safety checks before writing to Meditech
**Phase**: 6.4 | **Dependencies**: Task 6.4.1 | **Time**: 12h
**Steps**: 1) Check drug allergies (patient allergies vs medication), 2) Check contraindications (conditions vs medication), 3) Check duplicate orders (same medication active), 4) Block write if critical safety issue, 5) Warn if moderate issue
**Acceptance**: Safety checks prevent unsafe orders (100% for critical)
**Test Coverage**: 18 unit tests
**Files**: `backend/app/services/order_safety_service.py`, `tests/unit/services/test_order_safety.py`

### Task 6.4.3: Implement Transaction Bundles (Atomic Writes)
**Goal**: Use FHIR transaction bundles for atomic multi-resource writes
**Phase**: 6.4 | **Dependencies**: Task 6.4.1 | **Time**: 8h
**Steps**: 1) Create FHIR Bundle (type='transaction'), 2) Add multiple resources, 3) Submit bundle to Meditech, 4) Handle rollback on failure
**Acceptance**: Transaction bundles work, rollback on failure
**Test Coverage**: 10 unit tests
**Files**: `backend/app/clients/meditech_fhir_client.py` (updated)

### Task 6.4.4: Create Draft Order API Endpoint
**Goal**: POST /api/v1/meditech/orders/draft
**Phase**: 6.4 | **Dependencies**: Tasks 6.4.1, 6.4.2 | **Time**: 8h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Validate request, 4) Run safety checks, 5) Create draft order, 6) Return order ID
**Acceptance**: Endpoint creates draft orders, safety checks enforced
**Test Coverage**: 12 integration tests
**Files**: `backend/app/api/v1/endpoints/meditech_orders.py`, `tests/integration/test_meditech_orders_api.py`

### Task 6.4.5: Create Write Error Handling
**Goal**: Handle Meditech write errors gracefully
**Phase**: 6.4 | **Dependencies**: Task 6.4.1 | **Time**: 6h
**Steps**: 1) Parse Meditech OperationOutcome errors, 2) Map to user-friendly messages, 3) Log errors, 4) Retry transient errors
**Acceptance**: Errors handled gracefully, user-friendly messages
**Files**: `backend/app/clients/meditech_fhir_client.py` (updated)

### Task 6.4.6: Integration Tests - Meditech Write
**Goal**: Integration tests for Meditech write operations
**Phase**: 6.4 | **Dependencies**: Task 6.4.1 | **Time**: 12h
**Steps**: 1) Write integration tests (create draft MedicationRequest, ServiceRequest, etc.), 2) Run against sandbox, 3) Verify resources created
**Acceptance**: All integration tests passing against Meditech sandbox
**Test Coverage**: 18 integration tests
**Files**: `tests/integration/test_meditech_write_integration.py`

### Task 6.4.7: Performance Testing - Meditech Write
**Goal**: Verify write performance acceptable
**Phase**: 6.4 | **Dependencies**: Task 6.4.1 | **Time**: 4h
**Steps**: 1) Performance tests (single resource, bundle), 2) Measure response time
**Acceptance**: Single write <2 seconds, bundle <5 seconds
**Files**: `tests/performance/test_meditech_write_performance.py`

### Task 6.4.8: Create CDS-Driven Order Creation UI
**Goal**: UI to create orders from CDS recommendations
**Phase**: 6.4 | **Dependencies**: Tasks 6.1.9, 6.4.4 | **Time**: 12h
**Steps**: 1) Add "Create Order" button to CDS recommendations, 2) Pre-populate order form, 3) Display safety checks, 4) Submit draft order, 5) Show confirmation
**Acceptance**: Orders created from CDS recommendations
**Files**: `webapp/src/components/cds/CDSRecommendationsPanel.vue` (updated)

### Task 6.4.9: E2E Tests - CDS to Order Creation
**Goal**: E2E tests for CDS-driven order workflow
**Phase**: 6.4 | **Dependencies**: Task 6.4.8 | **Time**: 8h
**Steps**: 1) Write E2E tests (CDS recommendation → create order → verify in Meditech)
**Acceptance**: E2E tests passing
**Test Coverage**: 6 E2E tests
**Files**: `tests/e2e/test_cds_order_creation.py`

### Task 6.4.10: Documentation - Meditech Write Integration
**Goal**: Document Meditech write integration
**Phase**: 6.4 | **Dependencies**: Task 6.4.1 | **Time**: 8h
**Steps**: 1) Document write operations, 2) Document safety checks, 3) Document error handling, 4) Document draft order workflow
**Acceptance**: Documentation complete
**Files**: `docs/integrations/meditech-write-integration.md`

---

## Phase 6.5: Clinical Governance & RBAC (30 hours)

### Task 6.5.1: Define Roles for Order Creation
**Goal**: RBAC roles for order creation (prescriber, nurse, admin)
**Phase**: 6.5 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Define roles in database, 2) Assign permissions (prescriber can create MedicationRequest, nurse can create Task)
**Acceptance**: Roles defined, permissions enforced
**Files**: `backend/alembic/versions/XXX_add_prescriber_roles.py`

### Task 6.5.2: Implement Approval Workflows (Draft Orders)
**Goal**: Draft orders require clinician approval before activation
**Phase**: 6.5 | **Dependencies**: Task 6.4.1 | **Time**: 8h
**Steps**: 1) Create order_approvals table, 2) Draft orders created with status='draft', 3) Approval endpoint to activate order, 4) UI for approval workflow
**Acceptance**: Draft orders require approval
**Files**: `backend/alembic/versions/XXX_create_order_approvals.py`, `backend/app/api/v1/endpoints/meditech_orders.py` (updated)

### Task 6.5.3: Implement Override Tracking
**Goal**: Track when clinicians override CDS recommendations or safety warnings
**Phase**: 6.5 | **Dependencies**: Task 6.4.2 | **Time**: 6h
**Steps**: 1) Create cds_overrides table, 2) Log overrides with reason, 3) Display override history in audit reports
**Acceptance**: Overrides tracked with reasons
**Files**: `backend/alembic/versions/XXX_create_cds_overrides.py`

### Task 6.5.4: Create Clinical Safety Dashboard (Admin)
**Goal**: Dashboard to monitor CDS usage and overrides
**Phase**: 6.5 | **Dependencies**: Task 6.5.3 | **Time**: 8h
**Steps**: 1) Create `ClinicalSafetyDashboardView.vue`, 2) Display CDS recommendation acceptance rate, 3) Display override frequency, 4) Display safety warnings triggered
**Acceptance**: Dashboard shows clinical safety metrics
**Files**: `webapp/src/views/admin/ClinicalSafetyDashboardView.vue`

### Task 6.5.5: Integration Tests - RBAC and Approvals
**Goal**: Integration tests for RBAC and approval workflows
**Phase**: 6.5 | **Dependencies**: Tasks 6.5.1, 6.5.2 | **Time**: 4h
**Steps**: 1) Write tests (non-prescriber blocked, draft order approval flow)
**Acceptance**: All integration tests passing
**Test Coverage**: 10 integration tests
**Files**: `tests/integration/test_clinical_governance.py`

---

## Phase 6.6: Meditech Workflow Integration (30 hours)

### Task 6.6.1: Research Meditech InBasket Integration
**Goal**: Determine feasibility of InBasket alerts
**Phase**: 6.6 | **Dependencies**: Task 6.1.1 | **Time**: 8h
**Steps**: 1) Review Meditech InBasket API, 2) Test creating InBasket messages, 3) Document capabilities/limitations
**Acceptance**: InBasket capabilities documented
**Files**: `docs/meditech-inbasket-integration.md`

### Task 6.6.2: Implement InBasket Alert Creation (If Supported)
**Goal**: Send CDS alerts to Meditech InBasket
**Phase**: 6.6 | **Dependencies**: Task 6.6.1 | **Time**: 12h
**Steps**: 1) Create InBasket message for CDS alert, 2) Include recommendation, evidence, link to app, 3) Test in sandbox
**Acceptance**: Alerts appear in Meditech InBasket
**Files**: `backend/app/clients/meditech_inbasket_client.py` (if supported)

### Task 6.6.3: Implement Order Entry Pre-Population (If Supported)
**Goal**: Pre-populate Meditech order entry with CDS recommendations
**Phase**: 6.6 | **Dependencies**: Task 6.1.1 | **Time**: 10h
**Steps**: 1) Research Meditech order entry API, 2) Implement pre-population, 3) Test in sandbox
**Acceptance**: Order entry pre-populated (if supported)
**Files**: `backend/app/clients/meditech_order_entry_client.py` (if supported)

---

## Phase 6.7: Testing & Validation (30 hours)

### Task 6.7.1: UAT with Pilot Users
**Goal**: User acceptance testing with clinicians
**Phase**: 6.7 | **Dependencies**: All previous phases | **Time**: 12h
**Steps**: 1) Recruit 5 pilot users, 2) Conduct UAT sessions, 3) Collect feedback, 4) Prioritize issues
**Acceptance**: UAT completed, critical issues resolved
**Files**: `docs/uat-sprint6-report.md`

### Task 6.7.2: Security Review
**Goal**: Security audit for Meditech integration
**Phase**: 6.7 | **Dependencies**: All previous phases | **Time**: 8h
**Steps**: 1) Review OAuth implementation, 2) Review data flows, 3) Review audit logging, 4) Identify vulnerabilities
**Acceptance**: Security review passed, vulnerabilities remediated
**Files**: `docs/security-review-sprint6.md`

### Task 6.7.3: Performance Testing - End-to-End
**Goal**: Load testing complete CDS + Meditech workflow
**Phase**: 6.7 | **Dependencies**: All previous phases | **Time**: 6h
**Steps**: 1) Load test with 20 concurrent users, 2) Measure response times, 3) Verify targets met
**Acceptance**: 20 concurrent users supported, response times acceptable
**Files**: `tests/performance/test_sprint6_e2e_performance.py`

### Task 6.7.4: Deployment to Staging
**Goal**: Deploy Sprint 6 to staging environment
**Phase**: 6.7 | **Dependencies**: All previous phases | **Time**: 4h
**Steps**: 1) Deploy backend, 2) Deploy frontend, 3) Run smoke tests, 4) Verify Meditech connectivity
**Acceptance**: Deployment successful, smoke tests passing

---

## Deployment Checklist

- [ ] **Week 0 verification completed** (Meditech sandbox capabilities documented)
- [ ] Meditech sandbox access configured (OAuth credentials)
- [ ] Clinical guidelines loaded (≥5 guidelines)
- [ ] NHS dm+d database loaded
- [ ] Drug interactions database loaded
- [ ] RBAC roles configured (prescriber, nurse, admin)
- [ ] Audit logging enabled
- [ ] Security review passed

---

## Summary

**Total Tasks**: 60+ tasks across 7 phases
**Total Estimated Time**: 360 hours (12 weeks)

**Phase Breakdown**:
- Phase 6.1 (CDS Infrastructure): 90 hours, 12 tasks
- Phase 6.2 (Meditech Read): 60 hours, 10 tasks
- Phase 6.3 (Drug Interactions): 30 hours, 7 tasks
- Phase 6.4 (Meditech Write): 90 hours, 10 tasks
- Phase 6.5 (Governance & RBAC): 30 hours, 5 tasks
- Phase 6.6 (Workflow Integration): 30 hours, 3 tasks
- Phase 6.7 (Testing & Validation): 30 hours, 4 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%
- Drug interaction accuracy: ≥99% for contraindicated/major

**Performance Targets**:
- CDS recommendations: <3 seconds
- Meditech read (cached): <500ms
- Meditech write: <2 seconds (single), <5 seconds (bundle)
