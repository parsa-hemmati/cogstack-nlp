# Tasks: Population Health Dashboards (Sprint 8)

**Plan Reference**: `.specify/plans/sprint-8-population-health-dashboards-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-8-population-health-dashboards.md` (v1.0.0)
**Estimated Total Time**: 150 hours (5 weeks)
**Dependencies**:
- Sprints 1-7 completed
- Chart.js or ECharts installed
- PostgreSQL aggregations optimized
- Elasticsearch for large dataset queries

---

## Phase 8.1: Cohort Analytics Dashboard (30 hours)

### Task 8.1.1: Create PopulationHealthService - Disease Prevalence
**Goal**: Service to calculate disease prevalence
**Phase**: 8.1 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Write tests (TDD), 2) Create `PopulationHealthService`, 3) Implement `get_disease_prevalence(date_from, date_to)`, 4) Query coded conditions, 5) Calculate prevalence by disease
**Acceptance**: Prevalence calculated correctly
**Test Coverage**: 10 unit tests
**Files**: `backend/app/services/population_health_service.py`, `tests/unit/services/test_population_health_service.py`

### Task 8.1.2: Create Demographics Breakdown Query
**Goal**: Calculate demographics (age, gender, ethnicity)
**Phase**: 8.1 | **Dependencies**: Task 8.1.1 | **Time**: 4h
**Steps**: 1) Implement `get_demographics_breakdown()`, 2) Query patient demographics, 3) Aggregate by age groups, gender, ethnicity
**Acceptance**: Demographics aggregated correctly
**Files**: `backend/app/services/population_health_service.py` (updated)

### Task 8.1.3: Create Comorbidity Analysis Query
**Goal**: Calculate common comorbidities
**Phase**: 8.1 | **Dependencies**: Task 8.1.1 | **Time**: 6h
**Steps**: 1) Implement `get_comorbidity_analysis(primary_condition)`, 2) Find patients with primary condition, 3) Aggregate secondary conditions
**Acceptance**: Comorbidities identified correctly
**Files**: `backend/app/services/population_health_service.py` (updated)

### Task 8.1.4: Create Time Trends Query
**Goal**: Calculate disease trends over time
**Phase**: 8.1 | **Dependencies**: Task 8.1.1 | **Time**: 4h
**Steps**: 1) Implement `get_time_trends(disease, date_from, date_to)`, 2) Aggregate by month, 3) Calculate growth rate
**Acceptance**: Trends calculated correctly
**Files**: `backend/app/services/population_health_service.py` (updated)

### Task 8.1.5: Create Cohort Analytics API Endpoint
**Goal**: GET /api/v1/population-health/cohort-analytics
**Phase**: 8.1 | **Dependencies**: Tasks 8.1.1-8.1.4 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call population health service, 4) Return analytics
**Acceptance**: Endpoint returns cohort analytics
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/v1/endpoints/population_health.py`, `tests/integration/test_cohort_analytics_api.py`

### Task 8.1.6: Create CohortAnalyticsView Component
**Goal**: Frontend dashboard for cohort analytics
**Phase**: 8.1 | **Dependencies**: Task 8.1.5 | **Time**: 6h
**Steps**: 1) Create `CohortAnalyticsView.vue`, 2) Install Chart.js or ECharts, 3) Display disease prevalence (bar chart), 4) Display demographics (pie charts), 5) Display comorbidities (network graph), 6) Display time trends (line chart)
**Acceptance**: Dashboard displays all visualizations
**Files**: `webapp/src/views/admin/CohortAnalyticsView.vue`

---

## Phase 8.2: Quality Metrics Dashboard (30 hours)

### Task 8.2.1: Create Quality Metrics Service - HbA1c/BP Control
**Goal**: Calculate control rates for diabetes/hypertension
**Phase**: 8.2 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Write tests, 2) Create `QualityMetricsService`, 3) Implement `get_hba1c_control_rate()` (target <7%), 4) Implement `get_bp_control_rate()` (target <140/90)
**Acceptance**: Control rates calculated correctly
**Test Coverage**: 10 unit tests
**Files**: `backend/app/services/quality_metrics_service.py`, `tests/unit/services/test_quality_metrics_service.py`

### Task 8.2.2: Create Screening Rates Query
**Goal**: Calculate screening rates (mammography, colonoscopy, etc.)
**Phase**: 8.2 | **Dependencies**: Task 8.2.1 | **Time**: 6h
**Steps**: 1) Implement `get_screening_rates()`, 2) Query procedures, 3) Calculate % screened per eligible population
**Acceptance**: Screening rates calculated correctly
**Files**: `backend/app/services/quality_metrics_service.py` (updated)

### Task 8.2.3: Create Benchmark Comparison
**Goal**: Compare metrics to national benchmarks
**Phase**: 8.2 | **Dependencies**: Task 8.2.1 | **Time**: 4h
**Steps**: 1) Load benchmark data (national averages), 2) Implement `compare_to_benchmarks()`, 3) Calculate difference
**Acceptance**: Benchmark comparison works
**Files**: `backend/app/services/quality_metrics_service.py` (updated)

### Task 8.2.4: Create Quality Metrics API Endpoint
**Goal**: GET /api/v1/population-health/quality-metrics
**Phase**: 8.2 | **Dependencies**: Tasks 8.2.1-8.2.3 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call quality metrics service, 4) Return metrics
**Acceptance**: Endpoint returns quality metrics
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/v1/endpoints/population_health.py` (updated), `tests/integration/test_quality_metrics_api.py`

### Task 8.2.5: Create QualityMetricsView Component
**Goal**: Frontend dashboard for quality metrics
**Phase**: 8.2 | **Dependencies**: Task 8.2.4 | **Time**: 10h
**Steps**: 1) Create `QualityMetricsView.vue`, 2) Display control rates (gauges), 3) Display screening rates (bar charts), 4) Display benchmark comparison (comparison chart)
**Acceptance**: Dashboard displays all metrics
**Files**: `webapp/src/views/admin/QualityMetricsView.vue`

---

## Phase 8.3: Service Planning Dashboard (30 hours)

### Task 8.3.1: Create Service Planning Service - Patient Volumes
**Goal**: Calculate patient volumes by clinic/specialty
**Phase**: 8.3 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Write tests, 2) Create `ServicePlanningService`, 3) Implement `get_patient_volumes(date_from, date_to)`, 4) Aggregate by clinic, specialty
**Acceptance**: Volumes calculated correctly
**Test Coverage**: 10 unit tests
**Files**: `backend/app/services/service_planning_service.py`, `tests/unit/services/test_service_planning_service.py`

### Task 8.3.2: Create Clinic Capacity Analysis
**Goal**: Calculate clinic capacity utilization
**Phase**: 8.3 | **Dependencies**: Task 8.3.1 | **Time**: 6h
**Steps**: 1) Implement `get_clinic_capacity()`, 2) Calculate appointments vs capacity, 3) Calculate utilization %
**Acceptance**: Capacity calculated correctly
**Files**: `backend/app/services/service_planning_service.py` (updated)

### Task 8.3.3: Create Referral Patterns Analysis
**Goal**: Analyze referral patterns between departments
**Phase**: 8.3 | **Dependencies**: Task 8.3.1 | **Time**: 6h
**Steps**: 1) Implement `get_referral_patterns()`, 2) Query referrals, 3) Aggregate by source/destination
**Acceptance**: Referral patterns analyzed correctly
**Files**: `backend/app/services/service_planning_service.py` (updated)

### Task 8.3.4: Create Service Planning API Endpoint
**Goal**: GET /api/v1/population-health/service-planning
**Phase**: 8.3 | **Dependencies**: Tasks 8.3.1-8.3.3 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call service planning service, 4) Return metrics
**Acceptance**: Endpoint returns service planning metrics
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/v1/endpoints/population_health.py` (updated), `tests/integration/test_service_planning_api.py`

### Task 8.3.5: Create ServicePlanningView Component
**Goal**: Frontend dashboard for service planning
**Phase**: 8.3 | **Dependencies**: Task 8.3.4 | **Time**: 8h
**Steps**: 1) Create `ServicePlanningView.vue`, 2) Display patient volumes (bar charts), 3) Display capacity utilization (gauges), 4) Display referral patterns (Sankey diagram)
**Acceptance**: Dashboard displays all metrics
**Files**: `webapp/src/views/admin/ServicePlanningView.vue`

---

## Phase 8.4: Clinical Audit Dashboard (30 hours)

### Task 8.4.1: Create Clinical Audit Service - Guideline Adherence
**Goal**: Calculate guideline adherence rates
**Phase**: 8.4 | **Dependencies**: None | **Time**: 8h
**Steps**: 1) Write tests, 2) Create `ClinicalAuditService`, 3) Implement `get_guideline_adherence(guideline_id)`, 4) Compare actual care vs guideline recommendations
**Acceptance**: Adherence rates calculated correctly
**Test Coverage**: 12 unit tests
**Files**: `backend/app/services/clinical_audit_service.py`, `tests/unit/services/test_clinical_audit_service.py`

### Task 8.4.2: Create Outcome Trends Analysis
**Goal**: Analyze clinical outcomes over time
**Phase**: 8.4 | **Dependencies**: Task 8.4.1 | **Time**: 6h
**Steps**: 1) Implement `get_outcome_trends()`, 2) Query outcomes (readmissions, complications), 3) Calculate trends
**Acceptance**: Outcome trends calculated correctly
**Files**: `backend/app/services/clinical_audit_service.py` (updated)

### Task 8.4.3: Create Clinical Audit API Endpoint
**Goal**: GET /api/v1/population-health/clinical-audit
**Phase**: 8.4 | **Dependencies**: Tasks 8.4.1-8.4.2 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call clinical audit service, 4) Return metrics
**Acceptance**: Endpoint returns audit metrics
**Test Coverage**: 8 integration tests
**Files**: `backend/app/api/v1/endpoints/population_health.py` (updated), `tests/integration/test_clinical_audit_api.py`

### Task 8.4.4: Create ClinicalAuditView Component
**Goal**: Frontend dashboard for clinical audit
**Phase**: 8.4 | **Dependencies**: Task 8.4.3 | **Time**: 12h
**Steps**: 1) Create `ClinicalAuditView.vue`, 2) Display guideline adherence (bar charts), 3) Display outcome trends (line charts)
**Acceptance**: Dashboard displays all metrics
**Files**: `webapp/src/views/admin/ClinicalAuditView.vue`

---

## Phase 8.5: Data Export & Reports (30 hours)

### Task 8.5.1: Create Data Export Service (CSV/Excel/PDF)
**Goal**: Export dashboard data to files
**Phase**: 8.5 | **Dependencies**: All previous phases | **Time**: 10h
**Steps**: 1) Write tests, 2) Create `DataExportService`, 3) Implement `export_to_csv()`, 4) Implement `export_to_excel()` (openpyxl), 5) Implement `export_to_pdf()` (reportlab)
**Acceptance**: All export formats work
**Test Coverage**: 12 unit tests
**Files**: `backend/app/services/data_export_service.py`, `tests/unit/services/test_data_export_service.py`

### Task 8.5.2: Create Export API Endpoint
**Goal**: POST /api/v1/population-health/export
**Phase**: 8.5 | **Dependencies**: Task 8.5.1 | **Time**: 4h
**Steps**: 1) Write integration tests, 2) Create endpoint, 3) Call export service, 4) Return download URL
**Acceptance**: Endpoint returns export file
**Test Coverage**: 6 integration tests
**Files**: `backend/app/api/v1/endpoints/population_health.py` (updated), `tests/integration/test_export_api.py`

### Task 8.5.3: Create Scheduled Reports (Celery)
**Goal**: Email weekly/monthly reports
**Phase**: 8.5 | **Dependencies**: Tasks 8.5.1, 8.5.2 | **Time**: 8h
**Steps**: 1) Create `scheduled_report_task()` Celery task, 2) Generate report, 3) Email to recipients, 4) Schedule weekly/monthly
**Acceptance**: Scheduled reports sent
**Files**: `backend/app/tasks/scheduled_reports.py`

### Task 8.5.4: Create Export UI Buttons
**Goal**: Export buttons in all dashboards
**Phase**: 8.5 | **Dependencies**: Task 8.5.2 | **Time**: 6h
**Steps**: 1) Add export buttons to each dashboard, 2) Call export API, 3) Download file
**Acceptance**: Export works from all dashboards
**Files**: All dashboard Vue files (updated)

### Task 8.5.5: Performance Testing - Dashboard Loading
**Goal**: Verify dashboards load <3 seconds for 100K patients
**Phase**: 8.5 | **Dependencies**: All previous phases | **Time**: 2h
**Steps**: 1) Seed database with 100K patients, 2) Measure dashboard loading times
**Acceptance**: Loading <3 seconds for 100K patients
**Files**: `tests/performance/test_dashboard_performance.py`

---

## Deployment Checklist

- [ ] Chart.js or ECharts installed
- [ ] PostgreSQL aggregations optimized (indexes on dates, conditions)
- [ ] Elasticsearch aggregations configured
- [ ] Benchmark data loaded
- [ ] Celery beat scheduler configured (scheduled reports)

---

## Summary

**Total Tasks**: 25 tasks across 5 phases
**Total Estimated Time**: 150 hours (5 weeks)

**Phase Breakdown**:
- Phase 8.1 (Cohort Analytics): 30 hours, 6 tasks
- Phase 8.2 (Quality Metrics): 30 hours, 5 tasks
- Phase 8.3 (Service Planning): 30 hours, 5 tasks
- Phase 8.4 (Clinical Audit): 30 hours, 4 tasks
- Phase 8.5 (Data Export & Reports): 30 hours, 5 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%

**Performance Targets**:
- Dashboard loading: <3 seconds (100K patients)
- Export generation: <10 seconds
