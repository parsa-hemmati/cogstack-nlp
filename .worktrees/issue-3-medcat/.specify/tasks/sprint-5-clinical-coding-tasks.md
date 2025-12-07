# Tasks: Clinical Coding Module (Sprint 5)

**Plan Reference**: `.specify/plans/sprint-5-clinical-coding-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-5-clinical-coding.md` (v1.0.0)
**Estimated Total Time**: 120 hours (4 weeks)
**Dependencies**:
- Sprints 1-4 completed
- CogStack-ModelServe with medcat_icd10 model
- ICD-10-CM 2024 library downloaded

---

## Phase 5.1: CogStack-ModelServe ICD-10 Integration (30 hours)

### Task 5.1.1: Download and Configure ICD-10 Model
**Goal**: Setup medcat_icd10 model in CogStack-ModelServe
**Phase**: Phase 5.1 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Download medcat_icd10 model, 2) Configure ModelServe with model, 3) Verify model loads, 4) Test extraction
**Acceptance**: Model loads, extracts ICD-10 codes with confidence scores
**Files**: `docker-compose.yml`, `.env`

### Task 5.1.2: Create ICD-10 Extraction Service
**Goal**: Service to extract ICD-10 codes from documents
**Phase**: Phase 5.1 | **Dependencies**: Task 5.1.1 | **Time**: 6h
**Steps**: 1) Write tests (TDD), 2) Create `ClinicalCodingService`, 3) Implement `get_code_suggestions(document_id)`, 4) Parse ICD-10 codes from ModelServe response
**Acceptance**: Service returns ICD-10 codes with confidence, evidence text, positions
**Test Coverage**: 12 unit tests
**Files**: `backend/app/services/clinical_coding_service.py`, `tests/unit/services/test_clinical_coding_service.py`

### Task 5.1.3: Test ICD-10 Extraction Accuracy
**Goal**: Validate ICD-10 model accuracy (≥90% precision, ≥85% recall)
**Phase**: Phase 5.1 | **Dependencies**: Task 5.1.2 | **Time**: 4h
**Steps**: 1) Create test dataset (50 coded notes), 2) Run extraction, 3) Calculate precision/recall, 4) Verify targets
**Acceptance**: Precision ≥90%, Recall ≥85%
**Files**: `tests/accuracy/test_icd10_extraction_accuracy.py`

### Task 5.1.4: Improve False Positives/Negatives
**Goal**: Reduce false positives/negatives through post-processing
**Phase**: Phase 5.1 | **Dependencies**: Task 5.1.3 | **Time**: 4h
**Steps**: 1) Analyze errors, 2) Implement confidence threshold filtering, 3) Add context validation, 4) Re-test
**Acceptance**: False positive rate reduced ≥30%, precision improved
**Files**: `backend/app/services/clinical_coding_service.py` (updated)

### Task 5.1.5: Create Code Suggestions API Endpoint
**Goal**: GET /api/v1/coding/documents/{id}/suggestions
**Phase**: Phase 5.1 | **Dependencies**: Task 5.1.2 | **Time**: 3h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call coding service, 4) Return suggestions
**Acceptance**: Endpoint returns AI-suggested codes with evidence
**Test Coverage**: 6 integration tests
**Files**: `backend/app/api/v1/endpoints/coding.py`, `tests/integration/test_coding_api.py`

### Task 5.1.6: Performance Testing - ICD-10 Extraction
**Goal**: Verify extraction <2 seconds per document
**Phase**: Phase 5.1 | **Dependencies**: Task 5.1.2 | **Time**: 3h
**Steps**: 1) Performance tests with varying document sizes, 2) Measure extraction time, 3) Optimize if needed
**Acceptance**: Extraction <2 seconds per document
**Files**: `tests/performance/test_icd10_extraction_performance.py`

### Task 5.1.7: Unit Tests - Coding Service
**Goal**: Comprehensive unit test coverage
**Phase**: Phase 5.1 | **Dependencies**: Task 5.1.2 | **Time**: 3h
**Steps**: 1) Write additional tests (edge cases, error handling), 2) Verify coverage ≥85%
**Acceptance**: Code coverage ≥85%, all tests passing
**Test Coverage**: 20+ unit tests
**Files**: `tests/unit/services/test_clinical_coding_service.py` (expanded)

### Task 5.1.8: Integration Tests - ModelServe ICD-10
**Goal**: Integration tests for ModelServe ICD-10 calls
**Phase**: Phase 5.1 | **Dependencies**: Task 5.1.2 | **Time**: 3h
**Steps**: 1) Write integration tests (ModelServe communication, error handling), 2) Run tests
**Acceptance**: All integration tests passing
**Test Coverage**: 8 integration tests
**Files**: `tests/integration/test_modelserve_icd10.py`

---

## Phase 5.2: Clinical Coder UI (30 hours)

### Task 5.2.1: Load ICD-10-CM 2024 Library to Database
**Goal**: Populate icd10_library table with CMS codes
**Phase**: Phase 5.2 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Download ICD-10-CM 2024 from CMS, 2) Parse codes, 3) Create migration script, 4) Load to database, 5) Create GIN index for full-text search
**Acceptance**: ~72,000 ICD-10 codes loaded, full-text search index created
**Files**: `scripts/load_icd10_library.py`, `backend/alembic/versions/XXX_create_icd10_library.py`

### Task 5.2.2: Create ICD-10 Search API Endpoint
**Goal**: GET /api/v1/coding/icd10/search for autocomplete
**Phase**: Phase 5.2 | **Dependencies**: Task 5.2.1 | **Time**: 3h
**Steps**: 1) Write tests, 2) Create endpoint, 3) Full-text search on description, 4) Return top 10 results
**Acceptance**: Autocomplete returns relevant codes, <100ms response time
**Test Coverage**: 5 integration tests
**Files**: `backend/app/api/v1/endpoints/coding.py` (updated), `tests/integration/test_icd10_search_api.py`

### Task 5.2.3: Create Coding Queue API Endpoint
**Goal**: GET /api/v1/coding/queue - uncoded, in-progress, coded documents
**Phase**: Phase 5.2 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Write tests, 2) Create endpoint, 3) Query documents by coding status, 4) Return queues
**Acceptance**: Endpoint returns documents grouped by status
**Test Coverage**: 6 integration tests
**Files**: `backend/app/api/v1/endpoints/coding.py` (updated), `tests/integration/test_coding_queue_api.py`

### Task 5.2.4: Create ClinicalCodingView Component
**Goal**: Main coding interface (queue, suggestions, assignment)
**Phase**: Phase 5.2 | **Dependencies**: Tasks 5.2.2, 5.2.3 | **Time**: 8h
**Steps**: 1) Create Vue component, 2) Document queue list, 3) AI suggestions display, 4) Approve/reject buttons, 5) Manual code search, 6) Assigned codes chips, 7) Save/Next buttons
**Acceptance**: UI displays queue, suggestions, allows approve/reject, manual add, save
**Files**: `webapp/src/views/ClinicalCodingView.vue`, `webapp/src/stores/coding.ts`

### Task 5.2.5: Implement Approve/Reject Workflow
**Goal**: Approve or reject AI suggestions
**Phase**: Phase 5.2 | **Dependencies**: Task 5.2.4 | **Time**: 3h
**Steps**: 1) Add approve/reject buttons, 2) Move to assigned codes on approve, 3) Remove from suggestions on reject, 4) Track metrics
**Acceptance**: Approve/reject works, metrics tracked (accepted vs rejected)
**Files**: `webapp/src/views/ClinicalCodingView.vue` (updated)

### Task 5.2.6: Implement Manual Code Search and Add
**Goal**: Search and manually add ICD-10 codes
**Phase**: Phase 5.2 | **Dependencies**: Task 5.2.2 | **Time**: 4h
**Steps**: 1) Add autocomplete input, 2) Call search API, 3) Display results, 4) Add to assigned codes on select
**Acceptance**: Manual code search works, codes added to assigned list
**Files**: `webapp/src/views/ClinicalCodingView.vue` (updated)

### Task 5.2.7: Unit Tests - Coding UI
**Goal**: Unit tests for ClinicalCodingView component
**Phase**: Phase 5.2 | **Dependencies**: Task 5.2.4 | **Time**: 3h
**Steps**: 1) Write component tests (rendering, interactions), 2) Run tests
**Acceptance**: All tests passing, ≥80% coverage
**Test Coverage**: 12 unit tests
**Files**: `webapp/tests/unit/views/ClinicalCodingView.test.ts`

### Task 5.2.8: Integration Tests - Coding Workflow
**Goal**: Integration tests for coding workflow
**Phase**: Phase 5.2 | **Dependencies**: Task 5.2.6 | **Time**: 2h
**Steps**: 1) Write integration tests (load document, approve suggestions, manual add, save)
**Acceptance**: All integration tests passing
**Test Coverage**: 8 integration tests
**Files**: `tests/integration/test_coding_workflow.py`

---

## Phase 5.3: Code Validation (30 hours)

### Task 5.3.1: Create Code Validator Service
**Goal**: Validate ICD-10 codes (format, existence, deprecation)
**Phase**: Phase 5.3 | **Dependencies**: Task 5.2.1 | **Time**: 6h
**Steps**: 1) Write tests (TDD), 2) Create `ICD10CodeValidator`, 3) Validate format (regex), 4) Check existence in library, 5) Check deprecation, 6) Return validation errors
**Acceptance**: Validator catches invalid formats, non-existent codes, deprecated codes
**Test Coverage**: 15 unit tests
**Files**: `backend/app/services/icd10_code_validator.py`, `tests/unit/services/test_icd10_validator.py`

### Task 5.3.2: Implement Excludes1/Excludes2 Validation (Advanced)
**Goal**: Validate excludes rules (optional for MVP)
**Phase**: Phase 5.3 | **Dependencies**: Task 5.3.1 | **Time**: 8h
**Steps**: 1) Load excludes rules from ICD-10-CM data, 2) Check assigned codes against excludes rules, 3) Return warnings
**Acceptance**: Excludes violations detected
**Files**: `backend/app/services/icd10_code_validator.py` (updated)

### Task 5.3.3: Integrate Validation into Assign Codes Endpoint
**Goal**: Validate codes before assigning
**Phase**: Phase 5.3 | **Dependencies**: Task 5.3.1 | **Time**: 3h
**Steps**: 1) Call validator in assign endpoint, 2) Return validation errors if invalid, 3) Block assignment if critical errors
**Acceptance**: Invalid codes rejected, validation errors returned
**Files**: `backend/app/api/v1/endpoints/coding.py` (updated)

### Task 5.3.4: Display Validation Errors in UI
**Goal**: Show validation errors to coder
**Phase**: Phase 5.3 | **Dependencies**: Task 5.3.3 | **Time**: 3h
**Steps**: 1) Catch validation errors from API, 2) Display error messages, 3) Highlight invalid codes
**Acceptance**: Validation errors shown in UI
**Files**: `webapp/src/views/ClinicalCodingView.vue` (updated)

### Task 5.3.5: Unit Tests - Validator
**Goal**: Comprehensive validator tests
**Phase**: Phase 5.3 | **Dependencies**: Task 5.3.1 | **Time**: 3h
**Steps**: 1) Write tests for all validation rules, 2) Test edge cases
**Acceptance**: Code coverage ≥90%, all tests passing
**Test Coverage**: 20+ unit tests
**Files**: `tests/unit/services/test_icd10_validator.py` (expanded)

### Task 5.3.6: Integration Tests - Validation
**Goal**: Integration tests for validation workflow
**Phase**: Phase 5.3 | **Dependencies**: Task 5.3.3 | **Time**: 2h
**Steps**: 1) Write integration tests (assign valid codes, assign invalid codes)
**Acceptance**: All integration tests passing
**Test Coverage**: 6 integration tests
**Files**: `tests/integration/test_coding_validation.py`

### Task 5.3.7: Performance Testing - Validation
**Goal**: Verify validation <100ms
**Phase**: Phase 5.3 | **Dependencies**: Task 5.3.1 | **Time**: 2h
**Steps**: 1) Performance tests with varying code counts, 2) Measure validation time
**Acceptance**: Validation <100ms for 20 codes
**Files**: `tests/performance/test_validation_performance.py`

### Task 5.3.8: Documentation - Validation Rules
**Goal**: Document validation rules for coders
**Phase**: Phase 5.3 | **Dependencies**: Task 5.3.1 | **Time**: 3h
**Steps**: 1) Create user guide for validation errors, 2) Add tooltips in UI
**Acceptance**: Documentation clear, tooltips helpful
**Files**: `docs/user-guides/clinical-coding-validation.md`

---

## Phase 5.4: Coding Quality Metrics (30 hours)

### Task 5.4.1: Create coding_assignments and coding_metrics Tables
**Goal**: Tables to track coding assignments and metrics
**Phase**: Phase 5.4 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Create migrations for both tables, 2) Apply migrations
**Acceptance**: Tables created with correct schemas
**Files**: `backend/alembic/versions/XXX_create_coding_tables.py`

### Task 5.4.2: Implement Assign Codes API Endpoint
**Goal**: POST /api/v1/coding/documents/{id}/codes - assign codes to document
**Phase**: Phase 5.4 | **Dependencies**: Task 5.4.1 | **Time**: 4h
**Steps**: 1) Write tests, 2) Create endpoint, 3) Validate codes, 4) Store in coding_assignments, 5) Create audit log, 6) Update metrics
**Acceptance**: Codes assigned successfully, stored in database, audit log created
**Test Coverage**: 10 integration tests
**Files**: `backend/app/api/v1/endpoints/coding.py` (updated), `tests/integration/test_assign_codes_api.py`

### Task 5.4.3: Create Coding Metrics Service
**Goal**: Service to calculate coding quality metrics
**Phase**: Phase 5.4 | **Dependencies**: Task 5.4.1 | **Time**: 6h
**Steps**: 1) Write tests, 2) Create `CodingMetricsService`, 3) Calculate AI precision/recall, 4) Calculate coder productivity, 5) Aggregate metrics by user/date
**Acceptance**: Metrics calculated correctly (AI acceptance rate, coder throughput)
**Test Coverage**: 12 unit tests
**Files**: `backend/app/services/coding_metrics_service.py`, `tests/unit/services/test_coding_metrics_service.py`

### Task 5.4.4: Update Metrics on Code Assignment
**Goal**: Track metrics when codes assigned
**Phase**: Phase 5.4 | **Dependencies**: Tasks 5.4.2, 5.4.3 | **Time**: 3h
**Steps**: 1) Call metrics service in assign endpoint, 2) Track: documents coded, AI accepted, AI rejected, manual added
**Acceptance**: Metrics updated on each assignment
**Files**: `backend/app/api/v1/endpoints/coding.py` (updated)

### Task 5.4.5: Create Metrics API Endpoint
**Goal**: GET /api/v1/coding/metrics - coding quality dashboard data
**Phase**: Phase 5.4 | **Dependencies**: Task 5.4.3 | **Time**: 3h
**Steps**: 1) Write tests, 2) Create endpoint, 3) Call metrics service, 4) Return aggregated metrics
**Acceptance**: Endpoint returns metrics (AI precision, coder productivity, etc.)
**Test Coverage**: 6 integration tests
**Files**: `backend/app/api/v1/endpoints/coding.py` (updated), `tests/integration/test_coding_metrics_api.py`

### Task 5.4.6: Create Metrics Dashboard UI
**Goal**: Dashboard to visualize coding metrics
**Phase**: Phase 5.4 | **Dependencies**: Task 5.4.5 | **Time**: 6h
**Steps**: 1) Create `CodingMetricsView.vue`, 2) Fetch metrics, 3) Display charts (AI acceptance rate, coder productivity), 4) Display tables (top coders)
**Acceptance**: Dashboard shows metrics with charts
**Files**: `webapp/src/views/admin/CodingMetricsView.vue`

### Task 5.4.7: Integration Tests - Metrics
**Goal**: Integration tests for metrics tracking
**Phase**: Phase 5.4 | **Dependencies**: Task 5.4.4 | **Time**: 2h
**Steps**: 1) Write integration tests (assign codes → metrics updated)
**Acceptance**: All integration tests passing
**Test Coverage**: 8 integration tests
**Files**: `tests/integration/test_coding_metrics_integration.py`

### Task 5.4.8: E2E Tests - Coding Workflow
**Goal**: E2E tests with Playwright
**Phase**: Phase 5.4 | **Dependencies**: Phase 5.2 completed | **Time**: 3h
**Steps**: 1) Write E2E tests (navigate to coding, load document, approve suggestions, save)
**Acceptance**: All E2E tests passing
**Test Coverage**: 6 E2E tests
**Files**: `webapp/tests/e2e/coding.spec.ts`

---

## Deployment Checklist

- [ ] CogStack-ModelServe with medcat_icd10 model running
- [ ] ICD-10-CM 2024 library loaded (72K codes)
- [ ] coding_assignments, coding_metrics tables created
- [ ] Audit logging enabled
- [ ] Clinical coder role configured (RBAC)
- [ ] User training completed

---

## Summary

**Total Tasks**: 30 tasks across 4 phases
**Total Estimated Time**: 120 hours (4 weeks)

**Phase Breakdown**:
- Phase 5.1 (ModelServe ICD-10): 30 hours, 8 tasks
- Phase 5.2 (Coder UI): 30 hours, 8 tasks
- Phase 5.3 (Validation): 30 hours, 8 tasks
- Phase 5.4 (Metrics): 30 hours, 6 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%
- ICD-10 accuracy: Precision ≥90%, Recall ≥85%

**Performance Targets**:
- ICD-10 extraction: <2 seconds
- Code validation: <100ms
- Coder UI: <300ms response
