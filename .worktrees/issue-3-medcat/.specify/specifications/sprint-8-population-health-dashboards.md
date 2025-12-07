# Specification: Population Health Dashboards (Sprint 8)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 5 weeks (~150 hours)

---

## Context

**CogStack Product Alignment**: Population Health/Caseload Dashboards (analytics and visualization tools)

**Problem**: Healthcare organizations need **population-level insights**:
- Disease prevalence (how many patients with diabetes?)
- Quality metrics (HbA1c control rates, blood pressure control)
- Service planning (patient volumes, resource allocation)
- Clinical audit (compliance with guidelines, outcome trends)
- Registry support (diabetes registry, cancer registry)

**Example**: Endocrinology department wants to see:
- Total diabetes patients: 5,432
- HbA1c <7% (controlled): 62%
- HbA1c ≥7% (uncontrolled): 38%
- Trend: Control rate improving (+5% vs last year)

---

## Goals

### Primary Goals (P0)

1. **Cohort Analytics Dashboard**
   - Disease prevalence (patients by condition)
   - Demographics breakdown (age, gender, ethnicity)
   - Comorbidity analysis (diabetes + CKD, CHF + COPD)
   - Time trends (new diagnoses per month)

2. **Quality Metrics Dashboard**
   - Clinical quality measures (HbA1c control, BP control, LDL control)
   - Screening rates (mammography, colonoscopy, diabetic retinopathy screening)
   - Compliance metrics (medication adherence, appointment attendance)
   - Benchmarking (facility vs national averages)

3. **Service Planning Dashboard**
   - Patient volumes (visits per day/month/year)
   - Resource utilization (clinic capacity, wait times)
   - Referral patterns (primary care → specialist)
   - Forecast demand (predict future patient volumes)

4. **Clinical Audit Dashboard**
   - Guideline adherence (% patients on evidence-based therapy)
   - Outcome trends (mortality, readmission, complications)
   - Adverse events (medication errors, hospital-acquired infections)
   - Performance indicators (door-to-needle time, length of stay)

5. **Data Export**
   - Export dashboard data (CSV, Excel, PDF)
   - Scheduled reports (email weekly/monthly reports)
   - API access (integrate with BI tools: Tableau, Power BI)

### Secondary Goals (P1)

6. **Custom Dashboard Builder**
   - Drag-and-drop widget builder
   - Save custom dashboards
   - Share dashboards with team

7. **Registry Support**
   - Diabetes registry (track all diabetes patients)
   - Cancer registry
   - Chronic disease registries (CKD, COPD, CHF)

---

## User Stories

### Population Health Manager User Stories

#### US-PM1: View Disease Prevalence
**As a** population health manager
**I want to** see disease prevalence across patient population
**So that** I can plan services

**Acceptance Criteria**:
- [ ] Dashboard shows:
  - Total patients by condition (diabetes: 5,432, hypertension: 8,921, etc.)
  - Demographics breakdown (age groups, gender, ethnicity)
  - Time trends (new diagnoses per month)
  - Geographic distribution (if available)
- [ ] Filter by date range, department, clinic
- [ ] Drill-down to patient list (click diabetes → see all diabetes patients)

#### US-PM2: Track Quality Metrics
**As a** population health manager
**I want to** track clinical quality metrics
**So that** I can improve patient outcomes

**Acceptance Criteria**:
- [ ] Dashboard shows:
  - HbA1c control rate (% <7%)
  - Blood pressure control rate (% <140/90)
  - LDL control rate (% <100)
  - Screening completion rates (mammography, colonoscopy)
- [ ] Trend charts (quality improving/declining over time)
- [ ] Benchmark comparison (facility vs national average)
- [ ] Export to CSV/Excel for reporting

### Clinician User Stories

#### US-CL1: View Caseload Summary
**As a** clinician
**I want to** see my caseload summary
**So that** I know my patient panel characteristics

**Acceptance Criteria**:
- [ ] Dashboard shows:
  - Total patients assigned to me
  - Top diagnoses in my panel
  - Patients due for preventive care (overdue screenings)
  - Patients with uncontrolled conditions (HbA1c ≥9%, BP ≥160/100)
- [ ] Click patient → open patient chart

### Admin User Stories

#### US-A1: Configure Dashboards
**As an** admin
**I want to** configure which dashboards are visible
**So that** users see relevant metrics

**Acceptance Criteria**:
- [ ] Admin panel for dashboard configuration
- [ ] Enable/disable dashboards per role
- [ ] Set default dashboard for each role

---

## Requirements

### Functional Requirements

#### FR1: Cohort Analytics
- **FR1.1**: Disease prevalence (patient count by ICD-10 code, SNOMED concept)
- **FR1.2**: Demographics breakdown (age groups, gender, ethnicity)
- **FR1.3**: Comorbidity analysis (patients with multiple conditions)
- **FR1.4**: Time trends (new diagnoses per month, rolling 12-month average)
- **FR1.5**: Geographic distribution (if patient addresses available)

#### FR2: Quality Metrics
- **FR2.1**: HbA1c control rate (diabetes patients with HbA1c <7%)
- **FR2.2**: Blood pressure control rate (hypertension patients with BP <140/90)
- **FR2.3**: LDL control rate (hyperlipidemia patients with LDL <100)
- **FR2.4**: Screening rates (mammography, colonoscopy, diabetic retinopathy)
- **FR2.5**: Benchmark comparison (facility vs national HEDIS benchmarks)

#### FR3: Service Planning
- **FR3.1**: Patient volumes (visits per day/week/month)
- **FR3.2**: Clinic capacity (available slots, booked slots, utilization %)
- **FR3.3**: Wait times (days from referral to appointment)
- **FR3.4**: Referral patterns (primary care → specialist referrals)
- **FR3.5**: Demand forecast (predict future volumes using historical trends)

#### FR4: Clinical Audit
- **FR4.1**: Guideline adherence (% diabetes patients on metformin)
- **FR4.2**: Outcome trends (mortality rate, readmission rate within 30 days)
- **FR4.3**: Adverse events (medication errors, falls, hospital-acquired infections)
- **FR4.4**: Performance indicators (ER door-to-doctor time, ICU length of stay)

#### FR5: Data Export
- **FR5.1**: Export to CSV, Excel, PDF
- **FR5.2**: Scheduled reports (email dashboard snapshot weekly/monthly)
- **FR5.3**: API access (REST API for BI tools integration)
- **FR5.4**: Audit log for exports

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Dashboard loading: <3 seconds for <100,000 patients
- **NFR1.2**: Chart rendering: <1 second
- **NFR1.3**: Drill-down queries: <2 seconds

#### NFR2: Scalability
- **NFR2.1**: Support 100,000+ patient records
- **NFR2.2**: Support 10,000+ data points per chart
- **NFR2.3**: Concurrent dashboard users: 50

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  DashboardView.vue                                    │  │
│  │  - Dashboard selector                                 │  │
│  │  - Chart widgets (line, bar, pie, table)             │  │
│  │  - Filters (date range, department, clinic)          │  │
│  │  - Export buttons                                     │  │
│  └───────────────────────────────────────────────────────┘  │
│  - Chart library: Chart.js or ECharts                       │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Population Health Service                            │  │
│  │  - GET /api/v1/dashboards/cohort-analytics            │  │
│  │  - GET /api/v1/dashboards/quality-metrics             │  │
│  │  - GET /api/v1/dashboards/service-planning            │  │
│  │  - GET /api/v1/dashboards/clinical-audit              │  │
│  └───────────────────────────────────────────────────────┘  │
│  - PostgreSQL aggregations                                  │
│  - Elasticsearch aggregations (for large datasets)          │
└─────────────────────────────────────────────────────────────┘
```

### Backend Services

**PopulationHealthService** (`app/services/population_health_service.py`)
```python
class PopulationHealthService:
    """Population health analytics"""

    async def get_disease_prevalence(
        self,
        filters: DashboardFilters
    ) -> Dict[str, int]:
        """Get patient count by condition"""
        # Query PostgreSQL:
        # SELECT icd10_code, COUNT(DISTINCT patient_id)
        # FROM coding_assignments
        # WHERE coded_at BETWEEN :start_date AND :end_date
        # GROUP BY icd10_code

    async def get_quality_metrics(
        self,
        metric: str,  # "hba1c_control", "bp_control", "ldl_control"
        filters: DashboardFilters
    ) -> QualityMetricResult:
        """Calculate quality metric"""
        # Example: HbA1c control
        # 1. Get all diabetes patients
        # 2. Get most recent HbA1c for each
        # 3. Calculate % with HbA1c <7%
        # 4. Return result with trend (vs previous period)

    async def export_dashboard_data(
        self,
        dashboard: str,
        format: str  # "csv", "excel", "pdf"
    ) -> bytes:
        """Export dashboard data"""
```

### Database Models

```python
class DashboardFilters(BaseModel):
    date_range: DateRange
    departments: Optional[List[str]]
    clinics: Optional[List[str]]

class QualityMetricResult(BaseModel):
    metric_name: str
    numerator: int  # Patients meeting target
    denominator: int  # Total eligible patients
    rate: float  # numerator / denominator
    trend: str  # "improving", "declining", "stable"
    benchmark: Optional[float]  # National average
```

### API Endpoints

#### GET `/api/v1/dashboards/cohort-analytics`

**Response**:
```json
{
  "disease_prevalence": {
    "E11.9": {"name": "Type 2 Diabetes", "count": 5432},
    "I10": {"name": "Hypertension", "count": 8921}
  },
  "demographics": {
    "age_groups": {
      "18-39": 1234,
      "40-64": 3456,
      "65+": 2345
    },
    "gender": {
      "male": 3500,
      "female": 3932
    }
  },
  "time_trends": {
    "2023-01": 120,
    "2023-02": 135,
    "2023-03": 142
  }
}
```

#### GET `/api/v1/dashboards/quality-metrics`

**Response**:
```json
{
  "hba1c_control": {
    "numerator": 3368,
    "denominator": 5432,
    "rate": 0.62,
    "trend": "improving",
    "benchmark": 0.58
  }
}
```

---

## Database Schema

### New Tables

#### `dashboard_configs` (Custom Dashboards)
```sql
CREATE TABLE dashboard_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(200),
    widgets JSONB,  -- Dashboard configuration
    is_shared BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_disease_prevalence():
    result = await pop_health_service.get_disease_prevalence(
        filters=DashboardFilters(date_range=DateRange(...))
    )
    assert "E11.9" in result
    assert result["E11.9"]["count"] > 0
```

---

## Deployment Considerations

### Environment Variables
```bash
DASHBOARDS_ENABLED=true
DASHBOARD_CACHE_TTL_MINUTES=10
```

---

## Open Questions

1. **Chart Library**: Use Chart.js, ECharts, or D3.js?
2. **Benchmark Data**: Source for national HEDIS benchmarks?
3. **Scheduled Reports**: Use Celery cron for scheduled email reports?

---

**Status**: Ready for review and approval
**Dependencies**: Base Application, ICD-10 codes, quality metrics definitions
**Estimated Effort**: 150 hours over 5 weeks
