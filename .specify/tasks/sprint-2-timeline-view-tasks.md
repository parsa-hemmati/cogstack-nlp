# Tasks: Timeline View Module (Sprint 2)

**Plan Reference**: `.specify/plans/sprint-2-timeline-view-plan.md` v1.0.0
**Specification**: `.specify/specifications/sprint-2-timeline-view.md` v1.0.0
**Estimated Total Time**: 48 hours (6 days × 8 hours)
**Dependencies**: Clinical Care Tools Base Application (Phase 0-7) ✅ COMPLETE

---

## Task Dependencies Graph

```
Phase 1: Database Foundation
  Task 1.1 (Migrations) → Task 1.2 (Models)

Phase 2: Backend Services
  Task 1.2 → Task 2.1 (Elasticsearch repo)
  Task 1.2 → Task 2.2 (Timeline service)
  Task 2.1 + Task 2.2 → Task 2.3 (API endpoints)

Phase 3: Export Functionality
  Task 2.2 → Task 3.1 (PDF export)
  Task 2.2 → Task 3.2 (FHIR export)
  Task 2.2 → Task 3.3 (JSON export)

Phase 4: Frontend Components
  Task 2.3 → Task 4.1 (Timeline store)
  Task 4.1 → Task 4.2 (TimelineChart D3.js)
  Task 4.1 → Task 4.3 (Filters component)
  Task 4.1 → Task 4.4 (Timeline view)

Phase 5: Integration & Testing
  All previous → Task 5.1 (Integration tests)
  Task 5.1 → Task 5.2 (E2E tests)
  Task 5.2 → Task 5.3 (Performance tests)

Phase 6: Deployment
  Task 5.3 → Task 6.1 (Elasticsearch setup)
  Task 6.1 → Task 6.2 (Docker Compose updates)
```

---

## Phase 1: Database Foundation (3 hours)

### Task 1.1: Create Timeline Database Tables

**Goal**: Create `timeline_filters` and `timeline_exports` tables with PostgreSQL migrations

**Prerequisites**:
- PostgreSQL 15 running (Phase 0 ✅)
- Alembic configured (Phase 1 ✅)
- Base tables exist (users, patients, documents, audit_logs)

**Steps**:
1. **Write migration** (TDD approach)
   - Create Alembic migration: `alembic revision --autogenerate -m "add_timeline_tables"`
   - Add `timeline_filters` table DDL (user_id FK, name, filters JSONB, is_default)
   - Add `timeline_exports` table DDL (patient_id FK, user_id FK, format, status, file_path, expires_at)
   - Add indexes (user_id, patient_id, status, created_at, expires_at)
   - Add constraints (format IN ('pdf','fhir','json'), status IN ('processing','completed','failed'))
   - Add trigger for auto-expiry (7 days from creation)
2. **Test migration**
   - Run `alembic upgrade head`
   - Verify tables created: `psql -c "\d timeline_filters"`
   - Verify indexes: `psql -c "\di timeline_*"`
   - Verify trigger: Insert test export, check expires_at set correctly
   - Run `alembic downgrade -1`
   - Verify tables dropped
3. **Document schema**
   - Update technical plan with actual DDL

**Acceptance Criteria**:
- [ ] Migration file created in `alembic/versions/008_add_timeline_tables.py`
- [ ] `timeline_filters` table created with all fields (id, user_id, name, description, filters, is_default, created_at, updated_at)
- [ ] `timeline_exports` table created with all fields (id, patient_id, user_id, format, status, filters, options, file_path, file_size, content_hash, download_count, expires_at, created_at, completed_at, error_message, audit_log_id)
- [ ] Foreign key constraints to users, patients, audit_logs tables
- [ ] Unique constraint on (user_id, name) for timeline_filters
- [ ] Unique index on (user_id) WHERE is_default=TRUE for timeline_filters
- [ ] Check constraints for format and status enums
- [ ] Trigger `set_timeline_export_expiry` created and working
- [ ] Migration runs successfully: `alembic upgrade head`
- [ ] Migration rolls back successfully: `alembic downgrade -1`
- [ ] No errors in PostgreSQL logs

**Files Created/Modified**:
- `clinical-care-tools/backend/alembic/versions/008_add_timeline_tables.py` - Database migration

**Estimated Time**: 1.5 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Run migration
alembic upgrade head

# Verify tables
psql -U clinicaltools -d clinical_care_tools <<EOF
\d timeline_filters
\d timeline_exports
\di timeline_*

# Test trigger
INSERT INTO timeline_exports (patient_id, user_id, format, status, filters)
VALUES (
  (SELECT id FROM patients LIMIT 1),
  (SELECT id FROM users LIMIT 1),
  'pdf',
  'processing',
  '{}'::jsonb
);

SELECT id, expires_at, created_at, (expires_at - created_at) AS interval_check
FROM timeline_exports
ORDER BY created_at DESC LIMIT 1;
-- Expected: interval_check = '7 days'

# Rollback
EOF

alembic downgrade -1

# Verify dropped
psql -U clinicaltools -d clinical_care_tools -c "\dt timeline_*"
# Expected: No tables found
```

---

### Task 1.2: Create Timeline Pydantic Models

**Goal**: Create Pydantic schemas for timeline API request/response validation

**Prerequisites**:
- Task 1.1 completed (database tables exist)

**Steps**:
1. **Write model tests first** (TDD)
   - Create `clinical-care-tools/backend/tests/unit/modules/timeline/test_models.py`
   - Test: TimelineRequest validates date ranges
   - Test: TimelineRequest validates meta-annotation enums
   - Test: PatientTimeline serializes correctly
   - Test: TimelineExport validates format enum ('pdf', 'fhir', 'json')
   - Test: TimelineConcept groups mentions correctly
2. **Implement Pydantic models**
   - Create `clinical-care-tools/backend/app/modules/timeline/models.py`
   - Add `TimelineRequest` (filters: concept_cuis, date_range, meta_annotations, document_types)
   - Add `PatientTimeline` (patient_id, documents, concepts, date_range, filters_applied, statistics)
   - Add `TimelineDocument` (id, title, type, date, author, concept_count)
   - Add `TimelineConcept` (concept_cui, name, type, first_mention_date, mention_count, mentions)
   - Add `ConceptMention` (document_id, date, sentence, start/end_char, meta_annotations, confidence)
   - Add `ExportRequest` (format, filters, options)
   - Add `TimelineExport` (id, status, format, download_url, expires_at, audit_log_id)
   - Add `TimelineFilter` (id, user_id, name, description, filters, is_default)
   - Add validators for date ranges, enums, meta-annotations
3. **Run tests**
   - `pytest tests/unit/modules/timeline/test_models.py -v`

**Acceptance Criteria**:
- [ ] TimelineRequest schema with validators (date_start ≤ date_end, valid meta-annotation values)
- [ ] PatientTimeline schema with nested documents and concepts
- [ ] TimelineConcept schema with mentions list
- [ ] ConceptMention schema with meta_annotations dict
- [ ] ExportRequest schema with format enum validation
- [ ] TimelineExport schema with status enum validation
- [ ] TimelineFilter schema matching database table
- [ ] Email validation using Pydantic validator
- [ ] Unit tests written and passing (8+ tests)
- [ ] Test coverage ≥ 90% for models.py
- [ ] No validation bypasses (all fields validated)

**Files Created/Modified**:
- `clinical-care-tools/backend/app/modules/timeline/__init__.py` - Module initialization
- `clinical-care-tools/backend/app/modules/timeline/models.py` - Pydantic schemas
- `clinical-care-tools/backend/tests/unit/modules/timeline/__init__.py` - Test module init
- `clinical-care-tools/backend/tests/unit/modules/timeline/test_models.py` - Unit tests

**Estimated Time**: 1.5 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Run unit tests
pytest tests/unit/modules/timeline/test_models.py -v --cov=app/modules/timeline/models

# Expected output:
# test_timeline_request_validates_dates PASSED
# test_timeline_request_validates_meta_annotations PASSED
# test_patient_timeline_serialization PASSED
# test_timeline_export_format_enum PASSED
# test_timeline_concept_groups_mentions PASSED
# ...
# Coverage: 92% (target ≥90%)
```

---

## Phase 2: Backend Services (12 hours)

### Task 2.1: Create Elasticsearch Timeline Repository

**Goal**: Implement Elasticsearch queries for temporal concept aggregation and filtering

**Prerequisites**:
- Task 1.2 completed (Pydantic models exist)
- Elasticsearch 8.x available (Phase 0 assumption - will document workaround if not)

**Steps**:
1. **Write repository tests first** (TDD)
   - Create `clinical-care-tools/backend/tests/unit/modules/timeline/test_repository.py`
   - Test: query_patient_concepts filters by patient_id
   - Test: query_patient_concepts filters by date range
   - Test: query_patient_concepts filters by concept CUIs
   - Test: query_patient_concepts filters by meta-annotations (Negation, Experiencer, Temporality)
   - Test: aggregate_concept_frequency returns monthly counts
   - Mock Elasticsearch client responses
2. **Implement repository**
   - Create `clinical-care-tools/backend/app/modules/timeline/repository.py`
   - Add `ElasticsearchTimelineRepository` class
   - Implement `query_patient_concepts(patient_id, concept_cuis, date_range, meta_annotations)`
   - Implement `aggregate_concept_frequency(patient_id, granularity='month')`
   - Use elasticsearch-dsl library for query building
   - Build bool queries with must clauses for filters
   - Implement date histogram aggregation for frequency
3. **Run tests**
   - `pytest tests/unit/modules/timeline/test_repository.py -v`

**Acceptance Criteria**:
- [ ] ElasticsearchTimelineRepository class created
- [ ] query_patient_concepts method with all filters (patient_id, CUIs, dates, meta-annotations)
- [ ] Bool query construction with must clauses
- [ ] Date range query using 'range' filter
- [ ] Term queries for concept_cui filter
- [ ] Terms query for meta-annotation filtering
- [ ] aggregate_concept_frequency method with date histogram
- [ ] Granularity support: day, week, month, year
- [ ] Results grouped by concept CUI
- [ ] Unit tests written and passing (8+ tests with mocked ES client)
- [ ] Test coverage ≥ 85% for repository.py

**Files Created/Modified**:
- `clinical-care-tools/backend/app/modules/timeline/repository.py` - Elasticsearch repository
- `clinical-care-tools/backend/tests/unit/modules/timeline/test_repository.py` - Unit tests
- `clinical-care-tools/backend/requirements.txt` - Add elasticsearch==8.11.1, elasticsearch-dsl==8.11.0

**Estimated Time**: 3 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Install Elasticsearch dependencies
pip install elasticsearch==8.11.1 elasticsearch-dsl==8.11.0

# Run unit tests (mocked ES)
pytest tests/unit/modules/timeline/test_repository.py -v --cov=app/modules/timeline/repository

# Expected:
# test_query_patient_concepts_filters_by_patient PASSED
# test_query_patient_concepts_date_range PASSED
# test_query_patient_concepts_concept_cuis PASSED
# test_query_patient_concepts_meta_annotations PASSED
# test_aggregate_concept_frequency_monthly PASSED
# Coverage: 87% (target ≥85%)
```

**Environment Note**: If Elasticsearch 8.x not available in web environment, create mock implementation and document requirement for local/production setup.

---

### Task 2.2: Implement Timeline Service

**Goal**: Create TimelineService with business logic for timeline aggregation, filtering, and audit logging

**Prerequisites**:
- Task 1.2 completed (Pydantic models exist)
- Task 2.1 completed (Elasticsearch repository exists)
- Phase 1 AuditService exists ✅
- Phase 3 PHIExtractionService exists ✅

**Steps**:
1. **Write service tests first** (TDD)
   - Create `clinical-care-tools/backend/tests/unit/modules/timeline/test_service.py`
   - Test: get_patient_timeline logs PHI access
   - Test: get_patient_timeline verifies patient access
   - Test: get_patient_timeline fetches documents from database
   - Test: get_patient_timeline queries concepts from Elasticsearch
   - Test: get_patient_timeline filters by meta-annotations
   - Test: get_patient_timeline aggregates concept frequency
   - Test: export_timeline creates export record
   - Test: export_timeline logs audit entry
   - Mock database, Elasticsearch, audit service
2. **Implement service**
   - Create `clinical-care-tools/backend/app/modules/timeline/service.py`
   - Add `TimelineService` class with constructor injection (db, es_repo, audit_service, phi_service)
   - Implement `get_patient_timeline(patient_id, request, user, ip_address, user_agent)`
   - Implement `export_timeline(patient_id, export_request, user, ip_address, user_agent)`
   - Add `_verify_patient_access(user, patient)` helper
   - Add `_fetch_documents(patient_id, start_date, end_date, document_types)` helper
   - Follow Phase 1 audit logging patterns (call audit_service.log_phi_access)
   - Follow Phase 5 RBAC patterns (verify project assignment)
3. **Run tests**
   - `pytest tests/unit/modules/timeline/test_service.py -v`

**Acceptance Criteria**:
- [ ] TimelineService class created with dependency injection
- [ ] get_patient_timeline method with audit logging at start
- [ ] Patient existence verification (404 if not found)
- [ ] Patient access verification (403 if no permission via project)
- [ ] Document fetching from PostgreSQL with date filters
- [ ] Concept querying from Elasticsearch with all filters
- [ ] Concept frequency aggregation
- [ ] PatientTimeline response construction with statistics
- [ ] export_timeline method creates timeline_exports record
- [ ] Export audit logging with export_id
- [ ] Unit tests written and passing (12+ tests)
- [ ] Test coverage ≥ 85% for service.py
- [ ] All PHI access paths audited

**Files Created/Modified**:
- `clinical-care-tools/backend/app/modules/timeline/service.py` - Timeline business logic
- `clinical-care-tools/backend/tests/unit/modules/timeline/test_service.py` - Unit tests

**Estimated Time**: 4 hours

**Testing**:
```bash
cd clinical-care-tools/backend

pytest tests/unit/modules/timeline/test_service.py -v --cov=app/modules/timeline/service

# Expected:
# test_get_patient_timeline_logs_phi_access PASSED
# test_get_patient_timeline_verifies_patient_exists PASSED
# test_get_patient_timeline_verifies_access PASSED
# test_get_patient_timeline_fetches_documents PASSED
# test_get_patient_timeline_queries_concepts PASSED
# test_get_patient_timeline_filters_meta_annotations PASSED
# test_export_timeline_creates_record PASSED
# test_export_timeline_logs_audit PASSED
# Coverage: 88% (target ≥85%)
```

---

### Task 2.3: Create Timeline API Endpoints

**Goal**: Implement FastAPI REST endpoints for timeline access and export

**Prerequisites**:
- Task 2.2 completed (TimelineService exists)
- Phase 1 authentication/RBAC exists ✅

**Steps**:
1. **Write endpoint tests first** (TDD)
   - Create `clinical-care-tools/backend/tests/integration/modules/timeline/test_api.py`
   - Test: GET /api/v1/timeline/{patient_id} returns 200 with valid JWT
   - Test: GET /api/v1/timeline/{patient_id} returns 401 without JWT
   - Test: GET /api/v1/timeline/{patient_id} returns 403 if user lacks access
   - Test: GET /api/v1/timeline/{patient_id} returns 404 if patient not found
   - Test: GET /api/v1/timeline/{patient_id} applies filters correctly
   - Test: POST /api/v1/timeline/{patient_id}/export creates export record
   - Test: GET /api/v1/timeline/exports/{export_id} returns export status
   - Test: GET /api/v1/timeline/exports/{export_id}/download returns file
   - Use TestClient with auth headers
2. **Implement endpoints**
   - Create `clinical-care-tools/backend/app/modules/timeline/router.py`
   - Add `router = APIRouter(prefix="/api/v1/timeline", tags=["timeline"])`
   - Implement `GET /api/v1/timeline/{patient_id}` with TimelineService.get_patient_timeline
   - Implement `GET /api/v1/timeline/{patient_id}/concepts/{concept_cui}` for concept details
   - Implement `POST /api/v1/timeline/{patient_id}/export` with TimelineService.export_timeline
   - Implement `GET /api/v1/timeline/exports/{export_id}` for export status
   - Implement `GET /api/v1/timeline/exports/{export_id}/download` for file download
   - Implement `GET /api/v1/timeline/filters` for user's saved filters
   - Implement `POST /api/v1/timeline/filters` to save filter preset
   - Add require_role("clinician", "researcher", "admin") dependency on all endpoints
   - Add Request dependency for IP address extraction
3. **Register router in main app**
   - Update `clinical-care-tools/backend/app/main.py` to include timeline router
4. **Test endpoints**
   - `pytest tests/integration/modules/timeline/test_api.py -v`
   - Manual test with curl

**Acceptance Criteria**:
- [ ] GET /api/v1/timeline/{patient_id} endpoint with query params (filters)
- [ ] GET /api/v1/timeline/{patient_id}/concepts/{concept_cui} endpoint
- [ ] POST /api/v1/timeline/{patient_id}/export endpoint
- [ ] GET /api/v1/timeline/exports/{export_id} endpoint
- [ ] GET /api/v1/timeline/exports/{export_id}/download endpoint (file response)
- [ ] GET /api/v1/timeline/filters endpoint
- [ ] POST /api/v1/timeline/filters endpoint
- [ ] All endpoints require JWT authentication
- [ ] All endpoints require clinician/researcher/admin role
- [ ] Request/response validation using Pydantic models
- [ ] Error handling (400, 401, 403, 404, 500)
- [ ] IP address extraction from request.client.host
- [ ] User-agent extraction from request.headers
- [ ] Router registered in main.py
- [ ] Integration tests written and passing (12+ tests)
- [ ] Manual curl tests successful

**Files Created/Modified**:
- `clinical-care-tools/backend/app/modules/timeline/router.py` - API endpoints
- `clinical-care-tools/backend/app/main.py` - Register timeline router
- `clinical-care-tools/backend/tests/integration/modules/timeline/__init__.py` - Test module init
- `clinical-care-tools/backend/tests/integration/modules/timeline/test_api.py` - Integration tests

**Estimated Time**: 5 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Integration tests
pytest tests/integration/modules/timeline/test_api.py -v

# Manual test (requires backend running)
# Login first
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' | jq -r '.access_token')

# Get timeline
curl http://localhost:8000/api/v1/timeline/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with PatientTimeline JSON

# Export timeline
curl -X POST http://localhost:8000/api/v1/timeline/550e8400-e29b-41d4-a716-446655440000/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format":"pdf","filters":{}}'

# Expected: 202 Accepted with export_id
```

---

## Phase 3: Export Functionality (9 hours)

### Task 3.1: Implement PDF Export

**Goal**: Create PDF generation for timeline visualization using WeasyPrint

**Prerequisites**:
- Task 2.2 completed (TimelineService exists)
- WeasyPrint dependency available

**Steps**:
1. **Write export tests first** (TDD)
   - Create `clinical-care-tools/backend/tests/unit/modules/timeline/test_export.py`
   - Test: export_timeline_pdf generates PDF bytes
   - Test: export_timeline_pdf includes patient demographics
   - Test: export_timeline_pdf includes timeline visualization (SVG)
   - Test: export_timeline_pdf includes watermark
   - Test: export_timeline_pdf logs audit entry
   - Mock TimelineService, HTML template rendering
2. **Implement PDF export**
   - Create `clinical-care-tools/backend/app/modules/timeline/export.py`
   - Add `TimelineExportService` class
   - Implement `export_timeline_pdf(timeline, watermark_text, orientation, page_size)`
   - Create HTML template at `clinical-care-tools/backend/app/templates/timeline_pdf.html`
   - Use Jinja2 to render timeline data to HTML
   - Convert HTML to PDF using WeasyPrint
   - Add watermark via CSS (position: fixed; opacity: 0.3)
   - Return PDF bytes
3. **Run tests**
   - `pytest tests/unit/modules/timeline/test_export.py::test_pdf -v`

**Acceptance Criteria**:
- [ ] TimelineExportService class created
- [ ] export_timeline_pdf method generates PDF from timeline data
- [ ] HTML template with patient demographics section
- [ ] HTML template with timeline visualization section (tables or SVG placeholder)
- [ ] CSS watermark overlay (text rotated 45deg, opacity 0.3)
- [ ] Orientation support (portrait, landscape)
- [ ] Page size support (A4, Letter)
- [ ] PDF bytes returned (valid PDF format)
- [ ] Unit tests written and passing (6+ tests)
- [ ] Test coverage ≥ 80% for export.py
- [ ] Generated PDF opens in PDF reader without errors

**Files Created/Modified**:
- `clinical-care-tools/backend/app/modules/timeline/export.py` - Export service
- `clinical-care-tools/backend/app/templates/timeline_pdf.html` - Jinja2 template
- `clinical-care-tools/backend/tests/unit/modules/timeline/test_export.py` - Unit tests
- `clinical-care-tools/backend/requirements.txt` - Add WeasyPrint==62.0, Pillow==10.1.0

**Estimated Time**: 4 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Install WeasyPrint
pip install WeasyPrint==62.0 Pillow==10.1.0

# Run unit tests
pytest tests/unit/modules/timeline/test_export.py::test_pdf -v --cov=app/modules/timeline/export

# Manual test
python -c "
from app.modules.timeline.export import TimelineExportService
from app.modules.timeline.models import PatientTimeline
# Create mock timeline
export_service = TimelineExportService()
pdf_bytes = export_service.export_timeline_pdf(timeline, watermark='CONFIDENTIAL')
with open('/tmp/test_timeline.pdf', 'wb') as f:
    f.write(pdf_bytes)
print('PDF generated at /tmp/test_timeline.pdf')
"

# Open PDF to verify
# (In web environment, this would need to be downloaded)
```

**Environment Note**: WeasyPrint may require system libraries (cairo, pango). If unavailable in web environment, create stub implementation with documentation for local setup.

---

### Task 3.2: Implement FHIR R4 Export

**Goal**: Map timeline data to FHIR R4 Composition resource with embedded Observations and Conditions

**Prerequisites**:
- Task 2.2 completed (TimelineService exists)
- Task 3.1 completed (Export service structure exists)

**Steps**:
1. **Write FHIR export tests first** (TDD)
   - Add to `clinical-care-tools/backend/tests/unit/modules/timeline/test_export.py`
   - Test: export_timeline_fhir creates Composition resource
   - Test: FHIR Composition includes patient reference
   - Test: FHIR Composition includes document sections
   - Test: Concepts mapped to FHIR Observations
   - Test: Conditions mapped to FHIR Condition resources
   - Test: Provenance tracked for each resource
   - Validate against FHIR R4 schema
2. **Implement FHIR export**
   - Add `export_timeline_fhir(timeline, include_provenance)` to TimelineExportService
   - Use fhir.resources library for FHIR R4 models
   - Create Composition resource (type: "clinical-note", status: "final")
   - Map timeline.concepts to Observation resources (code from SNOMED-CT)
   - Map conditions to Condition resources
   - Add Provenance resources linking to source documents
   - Return FHIR Bundle as JSON
3. **Run tests**
   - `pytest tests/unit/modules/timeline/test_export.py::test_fhir -v`

**Acceptance Criteria**:
- [ ] export_timeline_fhir method in TimelineExportService
- [ ] FHIR Composition resource created with correct structure
- [ ] Patient reference (Reference(Patient/{patient_id}))
- [ ] Section for timeline concepts
- [ ] Observation resources with SNOMED-CT codes
- [ ] Condition resources for diagnoses
- [ ] Provenance resources with document references
- [ ] Valid FHIR R4 JSON (passes schema validation)
- [ ] Unit tests written and passing (6+ tests)
- [ ] Test coverage ≥ 80%
- [ ] FHIR JSON validates against official R4 schema

**Files Created/Modified**:
- `clinical-care-tools/backend/app/modules/timeline/export.py` - Add FHIR export method
- `clinical-care-tools/backend/tests/unit/modules/timeline/test_export.py` - Add FHIR tests
- `clinical-care-tools/backend/requirements.txt` - Add fhir.resources==7.1.0

**Estimated Time**: 3 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Install FHIR library
pip install fhir.resources==7.1.0

# Run FHIR tests
pytest tests/unit/modules/timeline/test_export.py::test_fhir -v --cov=app/modules/timeline/export

# Validate FHIR JSON (if validator available)
python -c "
from app.modules.timeline.export import TimelineExportService
from fhir.resources.composition import Composition
# Generate FHIR
fhir_json = export_service.export_timeline_fhir(timeline)
# Validate
composition = Composition.parse_obj(fhir_json)
print('FHIR validation passed!')
"
```

---

### Task 3.3: Implement JSON Export

**Goal**: Export timeline to machine-readable JSON format for research datasets

**Prerequisites**:
- Task 2.2 completed (TimelineService exists)
- Task 3.1 completed (Export service structure exists)

**Steps**:
1. **Write JSON export tests first** (TDD)
   - Add to `clinical-care-tools/backend/tests/unit/modules/timeline/test_export.py`
   - Test: export_timeline_json returns valid JSON
   - Test: JSON includes all timeline data (documents, concepts, mentions)
   - Test: JSON includes export metadata (exported_by, exported_at)
   - Test: JSON schema matches documented structure
2. **Implement JSON export**
   - Add `export_timeline_json(timeline)` to TimelineExportService
   - Convert PatientTimeline Pydantic model to JSON dict
   - Add metadata section (export_version, exported_by, exported_at)
   - Return JSON string
3. **Run tests**
   - `pytest tests/unit/modules/timeline/test_export.py::test_json -v`

**Acceptance Criteria**:
- [ ] export_timeline_json method in TimelineExportService
- [ ] Valid JSON string output
- [ ] All timeline data included (documents, concepts, mentions, filters, statistics)
- [ ] Metadata section (export_version, exported_by, exported_at, source_system)
- [ ] JSON schema documented
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 80%
- [ ] JSON parseable by standard tools (jq, Python json module)

**Files Created/Modified**:
- `clinical-care-tools/backend/app/modules/timeline/export.py` - Add JSON export method
- `clinical-care-tools/backend/tests/unit/modules/timeline/test_export.py` - Add JSON tests

**Estimated Time**: 2 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Run JSON tests
pytest tests/unit/modules/timeline/test_export.py::test_json -v --cov=app/modules/timeline/export

# Manual test
python -c "
import json
from app.modules.timeline.export import TimelineExportService
# Generate JSON
json_str = export_service.export_timeline_json(timeline)
# Validate
data = json.loads(json_str)
assert 'documents' in data
assert 'concepts' in data
assert 'metadata' in data
print('JSON export valid!')
"

# Test with jq
echo '$json_output' | jq '.metadata.export_version'
```

---

## Phase 4: Frontend Components (12 hours)

### Task 4.1: Create Timeline Pinia Store

**Goal**: Implement Pinia store for timeline state management and API communication

**Prerequisites**:
- Task 2.3 completed (Timeline API endpoints exist)
- Phase 1 Pinia configured ✅
- Phase 1 auth store exists ✅

**Steps**:
1. **Write store tests first** (TDD)
   - Create `clinical-care-tools/frontend/tests/unit/stores/timeline.test.ts`
   - Test: fetchTimeline calls API with filters
   - Test: fetchTimeline updates state on success
   - Test: fetchTimeline handles errors
   - Test: exportTimeline creates export request
   - Test: saveFilterPreset saves to API
   - Test: loadFilterPresets fetches user's filters
   - Mock axios API client
2. **Implement store**
   - Create `clinical-care-tools/frontend/src/stores/timeline.ts`
   - Add state: timeline (PatientTimeline | null), loading, error, filterPresets
   - Add action: fetchTimeline(patientId, filters)
   - Add action: fetchConceptDetails(patientId, conceptCui)
   - Add action: exportTimeline(patientId, format, filters)
   - Add action: saveFilterPreset(name, description, filters)
   - Add action: loadFilterPresets()
   - Use axios with auth token from auth store
   - Handle errors with user-friendly messages
3. **Run tests**
   - `npm run test:unit stores/timeline.test.ts`

**Acceptance Criteria**:
- [ ] Timeline Pinia store created with defineStore
- [ ] State properties: timeline, loading, error, filterPresets, patient
- [ ] fetchTimeline action calls GET /api/v1/timeline/{id}
- [ ] fetchTimeline updates state.timeline on success
- [ ] fetchTimeline sets state.error on failure
- [ ] exportTimeline action calls POST /api/v1/timeline/{id}/export
- [ ] saveFilterPreset action calls POST /api/v1/timeline/filters
- [ ] loadFilterPresets action calls GET /api/v1/timeline/filters
- [ ] Authorization header included from auth store
- [ ] Unit tests written and passing (8+ tests)
- [ ] Test coverage ≥ 85% for timeline.ts

**Files Created/Modified**:
- `clinical-care-tools/frontend/src/stores/timeline.ts` - Timeline Pinia store
- `clinical-care-tools/frontend/src/types/timeline.ts` - TypeScript interfaces
- `clinical-care-tools/frontend/tests/unit/stores/timeline.test.ts` - Unit tests

**Estimated Time**: 3 hours

**Testing**:
```bash
cd clinical-care-tools/frontend

# Run store tests
npm run test:unit stores/timeline.test.ts

# Expected:
# ✓ fetchTimeline calls API with correct parameters
# ✓ fetchTimeline updates state on success
# ✓ fetchTimeline handles network errors
# ✓ exportTimeline creates export request
# ✓ saveFilterPreset saves filter
# Coverage: 88% (target ≥85%)
```

---

### Task 4.2: Create D3.js Timeline Visualization Component

**Goal**: Build interactive D3.js timeline chart with zoom/pan and concept markers

**Prerequisites**:
- Task 4.1 completed (Timeline store exists)
- D3.js library available

**Steps**:
1. **Write component tests first** (TDD)
   - Create `clinical-care-tools/frontend/tests/unit/components/timeline/TimelineChart.test.ts`
   - Test: Component renders SVG element
   - Test: Timeline displays documents as markers
   - Test: Timeline displays concepts with color coding
   - Test: Zoom/pan functionality works
   - Test: Click on concept emits event
   - Test: Click on document emits event
   - Mock timeline data
2. **Implement component**
   - Create `clinical-care-tools/frontend/src/components/timeline/TimelineChart.vue`
   - Use `<script setup lang="ts">` with Composition API
   - Import d3 modules (d3-scale, d3-axis, d3-zoom, d3-selection)
   - Create SVG with width/height props
   - Implement renderTimeline() function:
     - Create X-axis (time scale)
     - Create Y-axis (document types)
     - Render document markers (circles)
     - Render concept markers (colored by type)
     - Add zoom behavior with d3.zoom()
     - Add click handlers
   - Emit events: concept-click, document-click
   - Add legend for concept types
3. **Run tests**
   - `npm run test:unit components/timeline/TimelineChart.test.ts`

**Acceptance Criteria**:
- [ ] TimelineChart.vue component created
- [ ] Props: timeline (PatientTimeline), loading (boolean), height (number)
- [ ] Emits: concept-click, document-click
- [ ] SVG element rendered with viewBox
- [ ] X-axis (time) rendered with d3.axisBottom
- [ ] Y-axis (document types) rendered with d3.axisLeft
- [ ] Document markers rendered as circles
- [ ] Concept markers rendered with color coding (condition=red, medication=blue, etc.)
- [ ] Zoom behavior with scaleExtent [0.5, 10]
- [ ] Pan behavior within timeline bounds
- [ ] Click handlers emit events with concept/document data
- [ ] Legend showing concept type colors
- [ ] Tooltip on hover showing concept name
- [ ] Unit tests written and passing (8+ tests)
- [ ] Visual test in browser (manual)

**Files Created/Modified**:
- `clinical-care-tools/frontend/src/components/timeline/TimelineChart.vue` - D3.js visualization
- `clinical-care-tools/frontend/tests/unit/components/timeline/TimelineChart.test.ts` - Unit tests
- `clinical-care-tools/frontend/package.json` - Add d3==7.9.0, @types/d3==7.4.3

**Estimated Time**: 5 hours

**Testing**:
```bash
cd clinical-care-tools/frontend

# Install D3.js
npm install d3@7.9.0 date-fns@3.0.6
npm install --save-dev @types/d3@7.4.3

# Run component tests
npm run test:unit components/timeline/TimelineChart.test.ts

# Visual test in browser
npm run dev
# Navigate to http://localhost:8080/timeline/test-patient-id
# Verify:
# - Timeline renders with documents and concepts
# - Zoom in/out works
# - Pan left/right works
# - Click on concept shows details
```

---

### Task 4.3: Create Timeline Filters Component

**Goal**: Build sidebar component for timeline filtering (concepts, dates, meta-annotations)

**Prerequisites**:
- Task 4.1 completed (Timeline store exists)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `clinical-care-tools/frontend/tests/unit/components/timeline/TimelineFilters.test.ts`
   - Test: Component renders filter controls
   - Test: Concept search with autocomplete
   - Test: Date range picker updates filters
   - Test: Meta-annotation checkboxes update filters
   - Test: Apply button emits filter event
   - Test: Clear button resets filters
   - Test: Save preset button saves to store
   - Mock timeline store
2. **Implement component**
   - Create `clinical-care-tools/frontend/src/components/timeline/TimelineFilters.vue`
   - Use Vuetify form components (v-autocomplete, v-date-picker, v-checkbox, v-btn)
   - Add concept search (autocomplete from SNOMED-CT)
   - Add date range picker (start_date, end_date)
   - Add meta-annotation filters (Negation, Experiencer, Temporality)
   - Add document type filter (multi-select)
   - Emit events: apply, clear, save-preset
   - Use v-model for two-way binding with parent
3. **Run tests**
   - `npm run test:unit components/timeline/TimelineFilters.test.ts`

**Acceptance Criteria**:
- [ ] TimelineFilters.vue component created
- [ ] Props: modelValue (TimelineFilters)
- [ ] Emits: update:modelValue, apply, clear, save-preset
- [ ] Concept search autocomplete (v-autocomplete)
- [ ] Date range picker (v-date-picker for start/end dates)
- [ ] Meta-annotation checkboxes (Negation, Experiencer, Temporality)
- [ ] Document type multi-select (v-select with multiple)
- [ ] Apply button emits filters
- [ ] Clear button resets to defaults
- [ ] Save preset button opens dialog for name/description
- [ ] Load preset dropdown (v-select with user's saved filters)
- [ ] Unit tests written and passing (8+ tests)
- [ ] Visual test in browser

**Files Created/Modified**:
- `clinical-care-tools/frontend/src/components/timeline/TimelineFilters.vue` - Filters sidebar
- `clinical-care-tools/frontend/tests/unit/components/timeline/TimelineFilters.test.ts` - Unit tests

**Estimated Time**: 3 hours

**Testing**:
```bash
cd clinical-care-tools/frontend

npm run test:unit components/timeline/TimelineFilters.test.ts

# Visual test
npm run dev
# Navigate to timeline view
# Verify filters:
# - Concept autocomplete searches concepts
# - Date pickers select range
# - Meta-annotation checkboxes toggle
# - Apply button triggers API call
# - Clear button resets form
```

---

### Task 4.4: Create Timeline Main View

**Goal**: Assemble complete timeline page with chart, filters, export toolbar

**Prerequisites**:
- Task 4.1 completed (Timeline store exists)
- Task 4.2 completed (TimelineChart component exists)
- Task 4.3 completed (TimelineFilters component exists)

**Steps**:
1. **Write view tests first** (TDD)
   - Create `clinical-care-tools/frontend/tests/unit/views/TimelineView.test.ts`
   - Test: View renders timeline chart
   - Test: View renders filter drawer
   - Test: Export menu opens
   - Test: Export to PDF triggers action
   - Test: Export to FHIR triggers action
   - Test: Concept click opens details dialog
   - Mock timeline store and router
2. **Implement view**
   - Create `clinical-care-tools/frontend/src/views/TimelineView.vue`
   - Use `<script setup lang="ts">` with Composition API
   - Import TimelineChart, TimelineFilters components
   - Add filter drawer (v-navigation-drawer)
   - Add export menu (v-menu with v-list for PDF/FHIR/JSON)
   - Add concept details dialog (v-dialog)
   - Add document details dialog (v-dialog)
   - Load timeline on mount using store.fetchTimeline
   - Handle export clicks with store.exportTimeline
3. **Add route**
   - Update `clinical-care-tools/frontend/src/router/index.ts` to add /timeline/:patientId route
4. **Run tests**
   - `npm run test:unit views/TimelineView.test.ts`

**Acceptance Criteria**:
- [ ] TimelineView.vue component created
- [ ] Patient ID from route params
- [ ] Timeline loaded on mount via store.fetchTimeline
- [ ] TimelineChart component rendered with timeline data
- [ ] Filter drawer (v-navigation-drawer) with TimelineFilters component
- [ ] Export toolbar with menu (PDF, FHIR, JSON options)
- [ ] Concept details dialog shows concept info on click
- [ ] Document details dialog shows document text on click
- [ ] Loading indicator during API call (v-progress-circular)
- [ ] Error alert if API fails (v-alert)
- [ ] Route registered in router/index.ts
- [ ] Unit tests written and passing (8+ tests)
- [ ] Visual test in browser

**Files Created/Modified**:
- `clinical-care-tools/frontend/src/views/TimelineView.vue` - Main timeline page
- `clinical-care-tools/frontend/src/router/index.ts` - Add timeline route
- `clinical-care-tools/frontend/tests/unit/views/TimelineView.test.ts` - Unit tests

**Estimated Time**: 4 hours (includes additional dialog components)

**Testing**:
```bash
cd clinical-care-tools/frontend

npm run test:unit views/TimelineView.test.ts

# E2E visual test
npm run dev

# Login as clinician
# Navigate to /timeline/550e8400-e29b-41d4-a716-446655440000
# Verify:
# - Timeline chart renders
# - Filter drawer opens/closes
# - Filters apply correctly
# - Export menu works
# - Concept click shows details
# - Document click shows text
```

---

## Phase 5: Integration & Testing (6 hours)

### Task 5.1: Integration Tests for Timeline Feature

**Goal**: Write comprehensive integration tests covering API → Service → Database → Elasticsearch flow

**Prerequisites**:
- All Phase 2 tasks completed (backend services and API)
- All Phase 3 tasks completed (export functionality)

**Steps**:
1. **Write integration tests**
   - Create `clinical-care-tools/backend/tests/integration/modules/timeline/test_timeline_integration.py`
   - Test: Full timeline flow (API → Service → DB → ES → Response)
   - Test: Timeline with filters (concept CUIs, date range, meta-annotations)
   - Test: Timeline with no results (empty timeline)
   - Test: Export to PDF end-to-end
   - Test: Export to FHIR end-to-end
   - Test: Export to JSON end-to-end
   - Test: Filter preset save and load
   - Test: Audit logging for all PHI access
   - Use TestClient with real database and mocked Elasticsearch
2. **Setup test fixtures**
   - Create test patients with documents
   - Create test annotations with meta-annotations
   - Seed Elasticsearch index with test concepts (or mock)
3. **Run tests**
   - `pytest tests/integration/modules/timeline/test_timeline_integration.py -v`

**Acceptance Criteria**:
- [ ] Integration tests covering full timeline API flow
- [ ] Test fixtures for patients, documents, annotations
- [ ] Tests with real PostgreSQL database
- [ ] Tests with mocked Elasticsearch (or real if available)
- [ ] Test all filter combinations
- [ ] Test all export formats (PDF, FHIR, JSON)
- [ ] Test audit logging verification
- [ ] Test RBAC (403 if no access)
- [ ] Test error handling (404, 500)
- [ ] Integration tests written and passing (12+ tests)
- [ ] Test coverage ≥ 70% for integration paths

**Files Created/Modified**:
- `clinical-care-tools/backend/tests/integration/modules/timeline/test_timeline_integration.py` - Integration tests
- `clinical-care-tools/backend/tests/integration/modules/timeline/conftest.py` - Test fixtures

**Estimated Time**: 4 hours

**Testing**:
```bash
cd clinical-care-tools/backend

# Run integration tests with real database
pytest tests/integration/modules/timeline/test_timeline_integration.py -v --cov=app/modules/timeline

# Expected:
# test_full_timeline_flow PASSED
# test_timeline_with_filters PASSED
# test_timeline_empty_results PASSED
# test_export_pdf_end_to_end PASSED
# test_export_fhir_end_to_end PASSED
# test_export_json_end_to_end PASSED
# test_filter_preset_save_load PASSED
# test_audit_logging_verified PASSED
# Coverage: 74% integration paths (target ≥70%)
```

---

### Task 5.2: E2E Tests for Timeline UI

**Goal**: Write Playwright E2E tests for complete user workflows

**Prerequisites**:
- Task 4.4 completed (Timeline view exists)
- Playwright configured (Phase 7 ✅)

**Steps**:
1. **Write E2E tests**
   - Create `clinical-care-tools/frontend/tests/e2e/timeline.spec.ts`
   - Test: Clinician logs in and views patient timeline
   - Test: Clinician applies filters and timeline updates
   - Test: Clinician clicks concept and sees details
   - Test: Clinician exports timeline to PDF
   - Test: Researcher accesses timeline (read-only)
   - Test: Unauthorized user cannot access timeline (403)
   - Use Playwright page object model
2. **Setup test data**
   - Seed database with test patients
   - Seed Elasticsearch with test concepts (or mock)
3. **Run tests**
   - `npx playwright test tests/e2e/timeline.spec.ts`

**Acceptance Criteria**:
- [ ] E2E test: Login → Navigate to timeline → View timeline
- [ ] E2E test: Apply concept filter → Timeline updates
- [ ] E2E test: Apply date range filter → Timeline updates
- [ ] E2E test: Click concept marker → Details dialog opens
- [ ] E2E test: Export to PDF → File downloads
- [ ] E2E test: Unauthorized user → 403 error shown
- [ ] E2E tests written and passing (6+ tests)
- [ ] Tests run in headless mode
- [ ] Screenshots captured on failure

**Files Created/Modified**:
- `clinical-care-tools/frontend/tests/e2e/timeline.spec.ts` - E2E tests

**Estimated Time**: 3 hours

**Testing**:
```bash
cd clinical-care-tools/frontend

# Run E2E tests
npx playwright test tests/e2e/timeline.spec.ts

# Expected:
# ✓ clinician can view patient timeline
# ✓ filters update timeline correctly
# ✓ concept details dialog opens
# ✓ export to PDF downloads file
# ✓ unauthorized user blocked
# 6 passed (25s)

# Run with UI
npx playwright test --ui
```

---

### Task 5.3: Performance Tests for Timeline

**Goal**: Verify timeline meets performance requirements (<2s load, <500ms filter updates)

**Prerequisites**:
- Task 5.1 completed (Integration tests exist)

**Steps**:
1. **Write performance tests**
   - Create `clinical-care-tools/backend/tests/performance/test_timeline_performance.py`
   - Test: Timeline load time for 100 documents (<2 seconds)
   - Test: Timeline load time for 500 documents (<5 seconds)
   - Test: Filter update time (<500ms)
   - Test: Concept frequency aggregation (<1 second)
   - Test: PDF export time (<5 seconds)
   - Test: Concurrent users (10 simultaneous requests)
   - Use pytest-benchmark or time.time()
2. **Create test datasets**
   - Generate 100, 500, 1000 document test datasets
   - Generate concept annotations for each document
3. **Run tests**
   - `pytest tests/performance/test_timeline_performance.py -v`

**Acceptance Criteria**:
- [ ] Performance test: Timeline load <2s for 100 documents
- [ ] Performance test: Timeline load <5s for 500 documents
- [ ] Performance test: Filter update <500ms
- [ ] Performance test: Concept aggregation <1s
- [ ] Performance test: PDF export <5s
- [ ] Performance test: 10 concurrent users handled
- [ ] Performance tests written and passing (6+ tests)
- [ ] Benchmarks documented in TESTING.md

**Files Created/Modified**:
- `clinical-care-tools/backend/tests/performance/test_timeline_performance.py` - Performance tests
- `clinical-care-tools/TESTING.md` - Document performance benchmarks

**Estimated Time**: 3 hours (includes test data generation)

**Testing**:
```bash
cd clinical-care-tools/backend

# Run performance tests
pytest tests/performance/test_timeline_performance.py -v

# Expected:
# test_timeline_load_100_docs PASSED (1.45s < 2s target) ✅
# test_timeline_load_500_docs PASSED (4.23s < 5s target) ✅
# test_filter_update PASSED (0.32s < 0.5s target) ✅
# test_concept_aggregation PASSED (0.78s < 1s target) ✅
# test_pdf_export PASSED (3.21s < 5s target) ✅
# test_concurrent_users_10 PASSED (10 requests in 2.34s) ✅
```

---

## Phase 6: Deployment (6 hours)

### Task 6.1: Setup Elasticsearch Index

**Goal**: Create `clinical_concepts` Elasticsearch index with proper mappings

**Prerequisites**:
- Elasticsearch 8.x available (or documented for setup)

**Steps**:
1. **Create index mapping**
   - Create `clinical-care-tools/scripts/create_es_index.py`
   - Define index mapping for clinical_concepts:
     - patient_id (keyword)
     - document_id (keyword)
     - concept_cui (keyword)
     - concept_name (text)
     - concept_type (keyword)
     - date (date)
     - sentence (text)
     - start_char (integer)
     - end_char (integer)
     - meta_annotations (nested object)
     - confidence (float)
   - Create index with settings (1 shard, 1 replica)
2. **Create data migration script**
   - Create `clinical-care-tools/scripts/migrate_concepts_to_es.py`
   - Read extracted_entities from PostgreSQL
   - Bulk insert into Elasticsearch
   - Update progress bar
3. **Run scripts**
   - `python scripts/create_es_index.py`
   - `python scripts/migrate_concepts_to_es.py`

**Acceptance Criteria**:
- [ ] Elasticsearch index creation script created
- [ ] Index mapping defined with all required fields
- [ ] Nested object for meta_annotations
- [ ] Text analyzer for concept_name (standard analyzer)
- [ ] Keyword fields for filtering (patient_id, concept_cui, concept_type)
- [ ] Date field for temporal queries
- [ ] Migration script reads from PostgreSQL
- [ ] Migration script bulk inserts to Elasticsearch (batch size 1000)
- [ ] Scripts documented in README
- [ ] Index created successfully
- [ ] Sample data migrated successfully

**Files Created/Modified**:
- `clinical-care-tools/scripts/create_es_index.py` - Index creation
- `clinical-care-tools/scripts/migrate_concepts_to_es.py` - Data migration
- `clinical-care-tools/README.md` - Document Elasticsearch setup

**Estimated Time**: 3 hours

**Testing**:
```bash
cd clinical-care-tools

# Create index
python scripts/create_es_index.py

# Verify index created
curl -X GET "localhost:9200/clinical_concepts/_mapping?pretty"

# Migrate data
python scripts/migrate_concepts_to_es.py

# Verify data
curl -X GET "localhost:9200/clinical_concepts/_count?pretty"
# Expected: {"count": 12345}

# Test query
curl -X POST "localhost:9200/clinical_concepts/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"term": {"patient_id": "550e8400-e29b-41d4-a716-446655440000"}},
        {"term": {"meta_annotations.Negation": "Affirmed"}}
      ]
    }
  }
}
'
```

**Environment Note**: If Elasticsearch not available in web environment, document setup steps for local/production deployment and create mock implementation for testing.

---

### Task 6.2: Update Docker Compose Configuration

**Goal**: Add Elasticsearch service and update environment variables for timeline module

**Prerequisites**:
- Task 6.1 completed (Elasticsearch index defined)
- Docker Compose exists (Phase 0 ✅)

**Steps**:
1. **Update docker-compose.yml**
   - Add Elasticsearch 8.x service
   - Add volume for Elasticsearch data persistence
   - Add network configuration
   - Update backend service environment variables
2. **Update .env.example**
   - Add ELASTICSEARCH_URL
   - Add TIMELINE_ENABLED=true
   - Add TIMELINE_EXPORT_DIR
   - Add TIMELINE_EXPORT_RETENTION_DAYS=7
3. **Update docker-compose.prod.yml**
   - Add Elasticsearch production configuration
   - Add resource limits (memory, CPU)
   - Add health checks
4. **Document setup**
   - Update README.md with Elasticsearch startup instructions

**Acceptance Criteria**:
- [ ] Elasticsearch 8.x service added to docker-compose.yml
- [ ] Elasticsearch data volume configured
- [ ] Elasticsearch health check configured
- [ ] Backend environment variables updated (ELASTICSEARCH_URL)
- [ ] Frontend environment variables updated (if needed)
- [ ] .env.example updated with all new variables
- [ ] docker-compose.prod.yml updated with production settings
- [ ] README.md documents Elasticsearch setup
- [ ] docker-compose up starts all services successfully
- [ ] Elasticsearch accessible at http://localhost:9200

**Files Created/Modified**:
- `clinical-care-tools/docker-compose.yml` - Add Elasticsearch service
- `clinical-care-tools/.env.example` - Add environment variables
- `clinical-care-tools/docker-compose.prod.yml` - Production configuration
- `clinical-care-tools/README.md` - Update documentation

**Estimated Time**: 2 hours

**Testing**:
```bash
cd clinical-care-tools

# Start services
docker-compose up -d

# Verify Elasticsearch started
docker-compose ps | grep elasticsearch
# Expected: elasticsearch ... Up (healthy)

# Check logs
docker-compose logs elasticsearch

# Test connection
curl http://localhost:9200/_cluster/health?pretty

# Verify backend can connect
docker-compose logs backend | grep "Elasticsearch connection established"
```

**Environment Note**: In web environment without Docker, document this configuration for local development and note that Elasticsearch tests use mocks.

---

### Task 6.3: Create Production Deployment Guide

**Goal**: Document production deployment steps, monitoring, and maintenance for timeline module

**Prerequisites**:
- All previous tasks completed

**Steps**:
1. **Create deployment guide**
   - Create `clinical-care-tools/docs/deployment/timeline-module-deployment.md`
   - Document prerequisites (Elasticsearch, PostgreSQL, Redis)
   - Document Elasticsearch index creation
   - Document data migration process
   - Document environment variables
   - Document health checks
   - Document rollback procedure
2. **Create monitoring guide**
   - Document metrics to monitor (API latency, export queue depth, ES query performance)
   - Document alerting thresholds
   - Document log aggregation
3. **Create maintenance guide**
   - Document Elasticsearch index optimization
   - Document export file cleanup (7-day retention)
   - Document backup procedures

**Acceptance Criteria**:
- [ ] Deployment guide created with step-by-step instructions
- [ ] Prerequisites section (system requirements, dependencies)
- [ ] Installation steps (Elasticsearch setup, index creation, migrations)
- [ ] Configuration section (environment variables, Docker Compose)
- [ ] Health check procedures
- [ ] Rollback procedures
- [ ] Monitoring guide with key metrics
- [ ] Maintenance guide with recurring tasks
- [ ] Troubleshooting section (common issues + solutions)

**Files Created/Modified**:
- `clinical-care-tools/docs/deployment/timeline-module-deployment.md` - Deployment guide
- `clinical-care-tools/docs/monitoring/timeline-module-monitoring.md` - Monitoring guide
- `clinical-care-tools/docs/maintenance/timeline-module-maintenance.md` - Maintenance guide

**Estimated Time**: 1 hour

---

## Summary

**Total Tasks**: 20
**Total Estimated Time**: 48 hours (6 days × 8 hours)
**Parallel Opportunities**:
- Phase 1 (Tasks 1.1-1.2): Sequential (1.2 depends on 1.1)
- Phase 2 (Tasks 2.1-2.3): Partial parallel (2.1 and 2.2 can be parallel, both needed for 2.3)
- Phase 3 (Tasks 3.1-3.3): All parallel (PDF, FHIR, JSON exports independent)
- Phase 4 (Tasks 4.1-4.4): Partial parallel (4.1 needed for 4.2-4.4, but 4.2-4.3 can be parallel)
- Phase 5 (Tasks 5.1-5.3): Sequential (integration → e2e → performance)
- Phase 6 (Tasks 6.1-6.3): Sequential (ES index → Docker config → docs)

**Critical Path**: Task 1.1 → Task 1.2 → Task 2.1 + 2.2 → Task 2.3 → Task 4.1 → Task 4.2 + 4.3 → Task 4.4 → Task 5.1 → Task 5.2 → Task 5.3 → Task 6.1 → Task 6.2 → Task 6.3

**Maximum Parallelization** (assuming 6 agents):
- **Wave 1** (3 hours): Task 1.1, Task 1.2 (sequential, but 2nd agent can start prep work)
- **Wave 2** (7 hours): Task 2.1, Task 2.2 (parallel)
- **Wave 3** (5 hours): Task 2.3
- **Wave 4** (9 hours): Task 3.1, Task 3.2, Task 3.3 (all 3 parallel)
- **Wave 5** (3 hours): Task 4.1
- **Wave 6** (8 hours): Task 4.2, Task 4.3 (parallel)
- **Wave 7** (4 hours): Task 4.4
- **Wave 8** (10 hours): Task 5.1, Task 5.2, Task 5.3 (sequential, but can overlap slightly)
- **Wave 9** (6 hours): Task 6.1, Task 6.2, Task 6.3 (mostly sequential)

**With parallelization**: ~40 hours (vs 48 hours sequential) = 17% time savings

---

## Environment Adaptations

**Elasticsearch Dependency**:
- If Elasticsearch unavailable in web environment:
  - Mock ElasticsearchTimelineRepository for unit tests
  - Document Elasticsearch setup in README for local development
  - Add note in CONTEXT.md about production requirement
  - Focus development on API contracts, can implement ES queries when available

**Docker Dependency**:
- If Docker unavailable in web environment:
  - PostgreSQL 16 and Redis 7.0 are pre-installed (use natively)
  - Document Docker Compose configuration for production deployment
  - Run backend and frontend natively for testing
  - Add deployment guide for containerized production

**WeasyPrint System Libraries**:
- If cairo/pango unavailable:
  - Create stub PDF export implementation
  - Document system library requirements
  - Add integration test with mocked PDF generation
  - Note in CONTEXT.md for local setup

---

## Next Steps After Task Completion

1. ✅ Update CONTEXT.md with Sprint 2 completion
2. ✅ Update AUDIT.md with HIPAA compliance verification
3. ✅ Run full test suite (unit + integration + e2e)
4. ✅ Create pull request for timeline module
5. ✅ Schedule code review
6. ✅ Deploy to staging environment
7. ✅ User acceptance testing (UAT)
8. ✅ Deploy to production
9. ✅ Monitor performance metrics
10. ✅ Begin Sprint 3 (Full-Text Search Module)

---

**Task Breakdown Status**: ✅ Ready for Implementation
**Next Action**: Begin Task 1.1 (Create Timeline Database Tables)
