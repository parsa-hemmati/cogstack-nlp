# Specification: Advanced Analytics Module (Sprint 9)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 5 weeks (~150 hours)

---

## Context

**CogStack Product Alignment**: Advanced Analytics (registry support, cohort deep phenotyping, custom report builder)

**Problem**: Researchers and quality teams need **advanced analytics capabilities**:
- Registry support (diabetes registry, cancer registry, chronic disease registries)
- Cohort deep phenotyping (comprehensive characterization of patient cohorts)
- Custom report builder (ad-hoc queries without SQL knowledge)
- Data export for external analysis (R, Python, SAS)
- Predictive analytics (optional: risk stratification, outcome prediction)

**Example**: Cancer registry needs to track:
- All cancer patients (ICD-10 C00-D49)
- Diagnosis date, stage, histology
- Treatment modalities (surgery, chemo, radiation)
- Outcomes (remission, recurrence, death)
- Survival analysis

---

## Goals

### Primary Goals (P0)

1. **Registry Support**
   - Diabetes registry (track all diabetes patients, complications, outcomes)
   - Cancer registry (track diagnosis, staging, treatment, outcomes)
   - Chronic disease registries (CKD, COPD, CHF, hypertension)
   - Registry data export (CSV, Excel, FHIR)
   - Registry quality metrics (completeness, accuracy)

2. **Cohort Deep Phenotyping**
   - Comprehensive patient characterization
   - Demographics, diagnoses, medications, labs, procedures
   - Comorbidity patterns (Charlson Comorbidity Index)
   - Treatment patterns (medication sequences, procedure timelines)
   - Outcome tracking (mortality, readmission, complications)

3. **Custom Report Builder**
   - Visual query builder (drag-and-drop, no SQL required)
   - Filter by demographics, diagnoses, medications, labs, dates
   - Aggregations (count, average, sum, percentiles)
   - Visualizations (tables, charts, graphs)
   - Save and share reports

4. **Data Export**
   - Export cohort data (CSV, Excel, JSON, FHIR)
   - Export for statistical analysis (R, Python, SAS)
   - De-identification option (automatic PHI removal)
   - Audit logging for exports

5. **Audit Logging**
   - Log all registry access
   - Log data exports
   - Log custom report queries

### Secondary Goals (P1)

6. **Predictive Analytics** (Optional)
   - Risk stratification (predict readmission, mortality)
   - Outcome prediction (predict HbA1c at 6 months)
   - Survival analysis (Kaplan-Meier curves, Cox regression)
   - Model training UI (upload datasets, train models)

---

## User Stories

### Researcher User Stories

#### US-R1: Create Patient Registry
**As a** researcher
**I want to** create a patient registry
**So that** I can track patient cohorts longitudinally

**Acceptance Criteria**:
- [ ] Create registry:
  - Name (e.g., "Diabetes Registry")
  - Inclusion criteria (ICD-10 codes, SNOMED concepts)
  - Data fields to track (HbA1c, BP, medications, complications)
- [ ] Registry auto-populates (patients meeting criteria added automatically)
- [ ] Registry dashboard shows:
  - Total patients
  - New patients this month
  - Key metrics (average HbA1c, % on metformin)
- [ ] Export registry data (CSV, Excel)

#### US-R2: Deep Phenotype Cohort
**As a** researcher
**I want to** deeply phenotype a patient cohort
**So that** I can characterize cohort comprehensively

**Acceptance Criteria**:
- [ ] Select cohort (from patient search or registry)
- [ ] Generate phenotype report showing:
  - Demographics (age, gender, ethnicity distribution)
  - Diagnoses (top 20 ICD-10 codes)
  - Medications (top 20 drugs)
  - Labs (average HbA1c, BP, LDL with ranges)
  - Procedures (common procedures)
  - Outcomes (mortality rate, readmission rate)
- [ ] Export phenotype report (PDF, CSV)

#### US-R3: Build Custom Report
**As a** researcher
**I want to** build custom reports without SQL
**So that** I can answer ad-hoc research questions

**Acceptance Criteria**:
- [ ] Visual query builder:
  - Drag filters (demographics, diagnoses, medications, labs, dates)
  - Select aggregations (count, average, sum, percentiles)
  - Choose visualizations (table, bar chart, line chart, pie chart)
- [ ] Execute query → results displayed
- [ ] Save report (name, description)
- [ ] Share report with team
- [ ] Schedule report (email weekly/monthly)

### Registry Manager User Stories

#### US-RM1: Monitor Registry Quality
**As a** registry manager
**I want to** monitor registry data quality
**So that** I ensure completeness and accuracy

**Acceptance Criteria**:
- [ ] Registry quality dashboard showing:
  - Completeness (% patients with all required data fields)
  - Accuracy (% patients with valid data ranges)
  - Timeliness (% patients with data updated in last 3 months)
  - Duplicates (# duplicate patient records)
- [ ] Data quality alerts (missing data, invalid data)

---

## Requirements

### Functional Requirements

#### FR1: Registry Support
- **FR1.1**: Create registry with inclusion criteria
- **FR1.2**: Auto-populate registry (patients meeting criteria added automatically)
- **FR1.3**: Registry dashboard (total patients, new patients, key metrics)
- **FR1.4**: Export registry data (CSV, Excel, JSON, FHIR)
- **FR1.5**: Registry quality metrics (completeness, accuracy, timeliness)

#### FR2: Cohort Deep Phenotyping
- **FR2.1**: Generate phenotype report for cohort:
  - Demographics distribution
  - Top diagnoses (ICD-10 codes)
  - Top medications (RxNorm)
  - Labs (average, ranges, percentiles)
  - Procedures (CPT codes)
  - Outcomes (mortality, readmission, complications)
- **FR2.2**: Comorbidity scoring (Charlson Comorbidity Index, Elixhauser)
- **FR2.3**: Treatment pattern analysis (medication sequences, procedure timelines)
- **FR2.4**: Export phenotype report (PDF, CSV)

#### FR3: Custom Report Builder
- **FR3.1**: Visual query builder (drag-and-drop filters, aggregations, visualizations)
- **FR3.2**: Filters:
  - Demographics (age range, gender, ethnicity)
  - Diagnoses (ICD-10 codes, SNOMED concepts)
  - Medications (RxNorm codes, drug names)
  - Labs (value ranges, dates)
  - Dates (absolute, relative)
- **FR3.3**: Aggregations (count, average, sum, min, max, percentiles)
- **FR3.4**: Visualizations (table, bar chart, line chart, pie chart, scatter plot)
- **FR3.5**: Save and share reports
- **FR3.6**: Schedule reports (email weekly/monthly)

#### FR4: Data Export
- **FR4.1**: Export cohort data (CSV, Excel, JSON, FHIR)
- **FR4.2**: Export for statistical analysis:
  - R format (RDS file)
  - Python format (pickle file)
  - SAS format (SAS7BDAT)
- **FR4.3**: De-identification option (automatic PHI removal before export)
- **FR4.4**: Audit log for all exports

#### FR5: Predictive Analytics (Optional)
- **FR5.1**: Risk stratification models (readmission risk, mortality risk)
- **FR5.2**: Outcome prediction (predict HbA1c at 6 months)
- **FR5.3**: Survival analysis (Kaplan-Meier curves, Cox proportional hazards)
- **FR5.4**: Model training UI (upload datasets, select features, train models)
- **FR5.5**: Model evaluation metrics (AUC-ROC, accuracy, precision, recall)

#### FR6: Audit Logging
- **FR6.1**: Log registry access (user, registry, timestamp)
- **FR6.2**: Log data exports (user, cohort, format, timestamp)
- **FR6.3**: Log custom report queries (user, query, timestamp)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Registry dashboard: <3 seconds
- **NFR1.2**: Deep phenotyping: <10 seconds for <1,000 patients
- **NFR1.3**: Custom report execution: <5 seconds for simple queries, <30 seconds for complex

#### NFR2: Scalability
- **NFR2.1**: Support registries with 100,000+ patients
- **NFR2.2**: Support deep phenotyping for 10,000+ patient cohorts
- **NFR2.3**: Support concurrent report executions: 20 users

#### NFR3: Security
- **NFR3.1**: Authentication required for all analytics
- **NFR3.2**: Only Researchers can access registries and analytics
- **NFR3.3**: Audit logging for all data access and exports
- **NFR3.4**: De-identification enforced for external data exports

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  RegistryView.vue                                     │  │
│  │  - Registry list                                      │  │
│  │  - Registry dashboard                                 │  │
│  │  - Deep phenotyping                                   │  │
│  │  - Custom report builder                              │  │
│  │  - Export tools                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Advanced Analytics Service                           │  │
│  │  - GET /api/v1/registries                             │  │
│  │  - POST /api/v1/registries                            │  │
│  │  - GET /api/v1/cohorts/{id}/phenotype                 │  │
│  │  - POST /api/v1/reports/custom                        │  │
│  │  - POST /api/v1/exports                               │  │
│  └───────────────────────────────────────────────────────┘  │
│  - PostgreSQL for structured data                           │
│  - Elasticsearch for full-text and aggregations             │
│  - Pandas/NumPy for analytics                               │
│  - Scikit-learn for predictive models (optional)            │
└─────────────────────────────────────────────────────────────┘
```

### Backend Services

**AdvancedAnalyticsService** (`app/services/advanced_analytics_service.py`)
```python
class AdvancedAnalyticsService:
    """Advanced analytics service"""

    async def create_registry(
        self,
        name: str,
        inclusion_criteria: Dict,
        data_fields: List[str]
    ) -> Registry:
        """Create patient registry"""
        # 1. Save registry definition
        # 2. Populate with patients meeting criteria
        # 3. Return Registry model

    async def deep_phenotype_cohort(
        self,
        cohort_ids: List[str]
    ) -> PhenotypeReport:
        """Generate deep phenotype report"""
        # 1. Query all data for cohort (demographics, diagnoses, meds, labs, procedures)
        # 2. Calculate statistics (distributions, averages, percentiles)
        # 3. Calculate comorbidity scores
        # 4. Return PhenotypeReport

    async def execute_custom_report(
        self,
        query: CustomReportQuery
    ) -> CustomReportResult:
        """Execute custom report query"""
        # 1. Parse query filters, aggregations, visualizations
        # 2. Build SQL/Elasticsearch query
        # 3. Execute query
        # 4. Format results
        # 5. Return CustomReportResult

    async def export_cohort_data(
        self,
        cohort_ids: List[str],
        format: str,  # "csv", "excel", "json", "fhir", "rds", "pickle", "sas"
        de_identify: bool = False
    ) -> bytes:
        """Export cohort data"""
        # 1. Query cohort data
        # 2. De-identify if requested
        # 3. Format as requested
        # 4. Audit log export
        # 5. Return file bytes
```

### Database Models

```python
class Registry(BaseModel):
    id: str
    name: str
    inclusion_criteria: Dict  # Conditions to include patients
    data_fields: List[str]  # Fields to track
    patient_count: int
    created_by: str
    created_at: datetime

class PhenotypeReport(BaseModel):
    cohort_size: int
    demographics: Demographics
    top_diagnoses: List[DiagnosisFrequency]
    top_medications: List[MedicationFrequency]
    lab_statistics: Dict[str, LabStatistics]
    procedures: List[ProcedureFrequency]
    outcomes: Outcomes
    comorbidity_scores: ComorbidityScores

class CustomReportQuery(BaseModel):
    filters: List[Filter]
    aggregations: List[Aggregation]
    visualizations: List[Visualization]

class CustomReportResult(BaseModel):
    query: CustomReportQuery
    results: List[Dict]
    row_count: int
    execution_time_ms: int
```

### API Endpoints

#### POST `/api/v1/registries`
Create registry.

**Request**:
```json
{
  "name": "Diabetes Registry",
  "inclusion_criteria": {
    "icd10_codes": ["E11"]
  },
  "data_fields": ["hba1c", "bp", "ldl", "medications", "complications"]
}
```

**Response**:
```json
{
  "id": "registry-123",
  "name": "Diabetes Registry",
  "patient_count": 5432,
  "created_at": "2023-11-17T10:00:00Z"
}
```

#### GET `/api/v1/cohorts/{cohort_id}/phenotype`
Get deep phenotype report.

**Response**:
```json
{
  "cohort_size": 5432,
  "demographics": {
    "age_mean": 58.5,
    "age_std": 12.3,
    "gender": {"male": 2800, "female": 2632}
  },
  "top_diagnoses": [
    {"code": "E11.9", "name": "Type 2 Diabetes", "count": 5432},
    {"code": "I10", "name": "Hypertension", "count": 3245}
  ],
  "top_medications": [
    {"code": "6809", "name": "Metformin", "count": 4123}
  ],
  "lab_statistics": {
    "hba1c": {"mean": 7.2, "std": 1.5, "p25": 6.5, "p50": 7.0, "p75": 7.8}
  },
  "outcomes": {
    "mortality_1yr": 0.05,
    "readmission_30d": 0.12
  },
  "comorbidity_scores": {
    "charlson": {"mean": 3.5, "std": 2.1}
  }
}
```

---

## Database Schema

### New Tables

#### `registries` (Patient Registries)
```sql
CREATE TABLE registries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200),
    inclusion_criteria JSONB,
    data_fields TEXT[],
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `registry_patients` (Registry Membership)
```sql
CREATE TABLE registry_patients (
    registry_id UUID REFERENCES registries(id),
    patient_id UUID REFERENCES patients(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (registry_id, patient_id)
);
```

#### `custom_reports` (Saved Custom Reports)
```sql
CREATE TABLE custom_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(200),
    query JSONB,
    is_shared BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_create_registry():
    registry = await analytics_service.create_registry(
        name="Diabetes Registry",
        inclusion_criteria={"icd10_codes": ["E11"]},
        data_fields=["hba1c", "bp"]
    )
    assert registry.name == "Diabetes Registry"
    assert registry.patient_count > 0

@pytest.mark.asyncio
async def test_deep_phenotype():
    phenotype = await analytics_service.deep_phenotype_cohort(
        cohort_ids=["patient-1", "patient-2"]
    )
    assert phenotype.cohort_size == 2
    assert "demographics" in phenotype
```

---

## Deployment Considerations

### Environment Variables
```bash
ANALYTICS_ENABLED=true
REGISTRIES_ENABLED=true
PREDICTIVE_ANALYTICS_ENABLED=false  # Optional
```

### Python Dependencies
```bash
pip install pandas numpy scikit-learn lifelines statsmodels
```

---

## Open Questions

1. **Predictive Analytics**: Include ML models in this sprint or defer to future?
2. **Statistical Analysis**: Include R/Python notebook integration?
3. **Registry Governance**: Approval workflow for registry creation?
4. **Data Retention**: How long to keep exported files?

---

**Status**: Ready for review and approval
**Dependencies**: Base Application, Registries infrastructure
**Estimated Effort**: 150 hours over 5 weeks
