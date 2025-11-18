# Tasks: Advanced Analytics Module (Sprint 9)

**Plan Reference**: `.specify/plans/sprint-9-advanced-analytics-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-9-advanced-analytics.md` (v1.0.0)
**Estimated Total Time**: 150 hours (5 weeks)
**Dependencies**:
- Sprints 1-8 completed
- pandas, numpy installed
- scipy, statsmodels (optional)

---

## Phase 9.1: Registry Support (30 hours)

### Task 9.1.1: Create registries Table
**Goal**: Database table for clinical registries
**Phase**: 9.1 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Create migration, 2) Define schema (registry_id, name, description, inclusion_criteria JSON, auto_populate boolean), 3) Seed example registries (diabetes, cancer)
**Acceptance**: Table created, 2+ registries seeded
**Files**: `backend/alembic/versions/XXX_create_registries.py`, `scripts/seed_registries.py`

### Task 9.1.2: Create registry_members Table
**Goal**: Table to track registry membership
**Phase**: 9.1 | **Dependencies**: Task 9.1.1 | **Time**: 2h
**Steps**: 1) Create migration, 2) Define schema (registry_id, patient_id, enrolled_at, status)
**Acceptance**: Table created
**Files**: `backend/alembic/versions/XXX_create_registry_members.py`

### Task 9.1.3: Create RegistryService - Auto-Population
**Goal**: Service to auto-populate registries based on criteria
**Phase**: 9.1 | **Dependencies**: Task 9.1.2 | **Time**: 10h
**Steps**: 1) Write tests (TDD), 2) Create `RegistryService`, 3) Implement `auto_populate_registry(registry_id)`, 4) Evaluate inclusion criteria against patients, 5) Enroll matching patients
**Acceptance**: Registries auto-populated correctly
**Test Coverage**: 15 unit tests
**Files**: `backend/app/services/registry_service.py`, `tests/unit/services/test_registry_service.py`

### Task 9.1.4: Create Registry API Endpoints
**Goal**: CRUD endpoints for registries
**Phase**: 9.1 | **Dependencies**: Task 9.1.3 | **Time**: 6h
**Steps**: 1) Write integration tests, 2) Create POST /api/v1/registries (create), 3) GET /api/v1/registries (list), 4) GET /api/v1/registries/{id} (get), 5) POST /api/v1/registries/{id}/populate (trigger population)
**Acceptance**: All endpoints work
**Test Coverage**: 10 integration tests
**Files**: `backend/app/api/v1/endpoints/registries.py`, `tests/integration/test_registries_api.py`

### Task 9.1.5: Create RegistryManagementView Component
**Goal**: Frontend UI for registry management
**Phase**: 9.1 | **Dependencies**: Task 9.1.4 | **Time**: 6h
**Steps**: 1) Create `RegistryManagementView.vue`, 2) List registries, 3) Create new registry, 4) View registry members, 5) Trigger population
**Acceptance**: UI manages registries
**Files**: `webapp/src/views/admin/RegistryManagementView.vue`

### Task 9.1.6: Integration Tests - Registry Workflow
**Goal**: Integration tests for registry workflow
**Phase**: 9.1 | **Dependencies**: Task 9.1.4 | **Time**: 3h
**Steps**: 1) Write tests (create registry → auto-populate → export members)
**Acceptance**: All integration tests passing
**Test Coverage**: 8 integration tests
**Files**: `tests/integration/test_registry_workflow.py`

---

## Phase 9.2: Cohort Deep Phenotyping (30 hours)

### Task 9.2.1: Create Deep Phenotyping Service
**Goal**: Service to generate comprehensive patient characterization
**Phase**: 9.2 | **Dependencies**: None | **Time**: 12h
**Steps**: 1) Write tests (TDD), 2) Create `DeepPhenotypingService`, 3) Implement `generate_phenotype_report(patient_ids)`, 4) Aggregate: demographics, diagnoses, medications, labs, procedures, outcomes, 5) Calculate summary statistics
**Acceptance**: Phenotype reports generated
**Test Coverage**: 18 unit tests
**Files**: `backend/app/services/deep_phenotyping_service.py`, `tests/unit/services/test_deep_phenotyping_service.py`

### Task 9.2.2: Create Comorbidity Scoring (Charlson, Elixhauser)
**Goal**: Calculate comorbidity scores
**Phase**: 9.2 | **Dependencies**: Task 9.2.1 | **Time**: 6h
**Steps**: 1) Implement Charlson Comorbidity Index, 2) Implement Elixhauser Comorbidity Index, 3) Calculate scores for cohort
**Acceptance**: Scores calculated correctly
**Files**: `backend/app/services/deep_phenotyping_service.py` (updated)

### Task 9.2.3: Create Treatment Pattern Analysis
**Goal**: Analyze treatment patterns in cohort
**Phase**: 9.2 | **Dependencies**: Task 9.2.1 | **Time**: 6h
**Steps**: 1) Implement `analyze_treatment_patterns()`, 2) Identify common medication sequences, 3) Identify common procedure sequences
**Acceptance**: Treatment patterns identified
**Files**: `backend/app/services/deep_phenotyping_service.py` (updated)

### Task 9.2.4: Create Deep Phenotyping API Endpoint
**Goal**: POST /api/v1/analytics/deep-phenotyping
**Phase**: 9.2 | **Dependencies**: Task 9.2.1 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call phenotyping service, 4) Return report
**Acceptance**: Endpoint returns phenotype report
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/v1/endpoints/analytics.py`, `tests/integration/test_deep_phenotyping_api.py`

### Task 9.2.5: Integration Tests - Deep Phenotyping
**Goal**: Integration tests for deep phenotyping
**Phase**: 9.2 | **Dependencies**: Task 9.2.4 | **Time**: 2h
**Steps**: 1) Write tests (generate report for cohort, verify statistics)
**Acceptance**: All integration tests passing
**Test Coverage**: 6 integration tests
**Files**: `tests/integration/test_deep_phenotyping_integration.py`

---

## Phase 9.3: Custom Report Builder (30 hours)

### Task 9.3.1: Design Visual Query Builder Schema
**Goal**: Define schema for visual query builder
**Phase**: 9.3 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Design query builder schema (filters, aggregations, visualizations), 2) Create query_templates table
**Acceptance**: Schema defined
**Files**: `backend/alembic/versions/XXX_create_query_templates.py`

### Task 9.3.2: Create Query Execution Engine
**Goal**: Engine to execute custom queries
**Phase**: 9.3 | **Dependencies**: Task 9.3.1 | **Time**: 12h
**Steps**: 1) Write tests (TDD), 2) Create `CustomReportService`, 3) Implement `execute_query(query_definition)`, 4) Build SQL from query definition, 5) Execute and return results
**Acceptance**: Queries executed correctly
**Test Coverage**: 20 unit tests
**Files**: `backend/app/services/custom_report_service.py`, `tests/unit/services/test_custom_report_service.py`

### Task 9.3.3: Create Custom Report API Endpoint
**Goal**: POST /api/v1/analytics/custom-reports
**Phase**: 9.3 | **Dependencies**: Task 9.3.2 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call custom report service, 4) Return results
**Acceptance**: Endpoint executes custom queries
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/v1/endpoints/analytics.py` (updated), `tests/integration/test_custom_reports_api.py`

### Task 9.3.4: Create ReportBuilderView Component
**Goal**: Visual query builder UI
**Phase**: 9.3 | **Dependencies**: Task 9.3.3 | **Time**: 10h
**Steps**: 1) Create `ReportBuilderView.vue`, 2) Drag-and-drop filter interface, 3) Select aggregations, 4) Select visualizations, 5) Execute query, 6) Display results
**Acceptance**: Query builder works, queries execute
**Files**: `webapp/src/views/admin/ReportBuilderView.vue`

---

## Phase 9.4: Data Export (30 hours)

### Task 9.4.1: Create Multi-Format Export Service
**Goal**: Export analytics data to CSV/Excel/JSON/FHIR
**Phase**: 9.4 | **Dependencies**: None | **Time**: 10h
**Steps**: 1) Write tests, 2) Create `AnalyticsExportService`, 3) Implement `export_to_csv()`, 4) Implement `export_to_excel()`, 5) Implement `export_to_json()`, 6) Implement `export_to_fhir()` (FHIR Bundle)
**Acceptance**: All export formats work
**Test Coverage**: 15 unit tests
**Files**: `backend/app/services/analytics_export_service.py`, `tests/unit/services/test_analytics_export_service.py`

### Task 9.4.2: Integrate De-identification into Export
**Goal**: De-identify exports using Sprint 4 service
**Phase**: 9.4 | **Dependencies**: Task 9.4.1, Sprint 4 | **Time**: 6h
**Steps**: 1) Add `de_identify=True` parameter to export, 2) Call Sprint 4 de-identification service, 3) Export de-identified data
**Acceptance**: De-identified exports work
**Files**: `backend/app/services/analytics_export_service.py` (updated)

### Task 9.4.3: Create Analytics Export API Endpoint
**Goal**: POST /api/v1/analytics/export
**Phase**: 9.4 | **Dependencies**: Task 9.4.2 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call export service, 4) Return download URL
**Acceptance**: Endpoint exports data
**Test Coverage**: 10 integration tests
**Files**: `backend/app/api/v1/endpoints/analytics.py` (updated), `tests/integration/test_analytics_export_api.py`

### Task 9.4.4: Add Export Buttons to Analytics UIs
**Goal**: Export buttons in all analytics views
**Phase**: 9.4 | **Dependencies**: Task 9.4.3 | **Time**: 6h
**Steps**: 1) Add export buttons to registry view, 2) Add to phenotyping view, 3) Add to custom reports view
**Acceptance**: Export works from all views
**Files**: All analytics Vue files (updated)

### Task 9.4.5: Integration Tests - Export with De-identification
**Goal**: Integration tests for de-identified exports
**Phase**: 9.4 | **Dependencies**: Task 9.4.2 | **Time**: 4h
**Steps**: 1) Write tests (export with de_identify=True, verify PHI removed)
**Acceptance**: All integration tests passing
**Test Coverage**: 8 integration tests
**Files**: `tests/integration/test_analytics_export_deidentified.py`

---

## Phase 9.5: Testing & Deployment (30 hours)

### Task 9.5.1: Unit Tests - All Analytics Services
**Goal**: Comprehensive unit tests
**Phase**: 9.5 | **Dependencies**: All previous phases | **Time**: 8h
**Steps**: 1) Write tests for all services, 2) Test edge cases
**Acceptance**: Code coverage ≥85%, all tests passing
**Test Coverage**: 50+ unit tests
**Files**: All analytics test files (expanded)

### Task 9.5.2: Integration Tests - Analytics Workflows
**Goal**: E2E integration tests
**Phase**: 9.5 | **Dependencies**: All previous phases | **Time**: 8h
**Steps**: 1) Write E2E tests (create registry → populate → phenotype → export)
**Acceptance**: All E2E tests passing
**Test Coverage**: 12 E2E tests
**Files**: `tests/integration/test_analytics_e2e.py`

### Task 9.5.3: Performance Testing - Large Cohorts
**Goal**: Verify performance with large cohorts (10K+ patients)
**Phase**: 9.5 | **Dependencies**: All previous phases | **Time**: 6h
**Steps**: 1) Seed 10K patients, 2) Test registry population, 3) Test phenotyping, 4) Test export
**Acceptance**: Operations complete in acceptable time (population <5 minutes, phenotyping <3 minutes)
**Files**: `tests/performance/test_analytics_performance.py`

### Task 9.5.4: E2E Tests with Playwright
**Goal**: E2E UI tests
**Phase**: 9.5 | **Dependencies**: All previous phases | **Time**: 4h
**Steps**: 1) Write Playwright tests (registry management, custom report builder)
**Acceptance**: All E2E tests passing
**Test Coverage**: 6 E2E tests
**Files**: `webapp/tests/e2e/analytics.spec.ts`

### Task 9.5.5: Deploy to Staging
**Goal**: Deploy Sprint 9 to staging
**Phase**: 9.5 | **Dependencies**: All previous phases | **Time**: 4h
**Steps**: 1) Deploy backend, 2) Deploy frontend, 3) Run smoke tests
**Acceptance**: Deployment successful

---

## Deployment Checklist

- [ ] pandas, numpy installed
- [ ] registries, registry_members tables created
- [ ] query_templates table created
- [ ] Benchmark data loaded (for comorbidity scoring)
- [ ] Sprint 4 de-identification service integrated

---

## Summary

**Total Tasks**: 25 tasks across 5 phases
**Total Estimated Time**: 150 hours (5 weeks)

**Phase Breakdown**:
- Phase 9.1 (Registry Support): 30 hours, 6 tasks
- Phase 9.2 (Deep Phenotyping): 30 hours, 5 tasks
- Phase 9.3 (Custom Report Builder): 30 hours, 4 tasks
- Phase 9.4 (Data Export): 30 hours, 5 tasks
- Phase 9.5 (Testing & Deployment): 30 hours, 5 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%

**Performance Targets**:
- Registry population: <5 minutes (10K patients)
- Deep phenotyping: <3 minutes (1K patients)
- Export: <10 seconds
