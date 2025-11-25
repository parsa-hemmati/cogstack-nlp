# Technical Plan: Timeline View Module (Sprint 2)

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Specification**: `.specify/specifications/sprint-2-timeline-view.md` v1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Choices](#technology-choices)
4. [Implementation Phases](#implementation-phases)
5. [API Design](#api-design)
6. [Data Model](#data-model)
7. [Frontend Components](#frontend-components)
8. [Backend Services](#backend-services)
9. [Integration Points](#integration-points)
10. [Testing Strategy](#testing-strategy)
11. [Performance Optimization](#performance-optimization)
12. [Security Considerations](#security-considerations)
13. [Deployment](#deployment)
14. [Risks and Mitigation](#risks-and-mitigation)

---

## Overview

### Purpose

Build a comprehensive timeline visualization module that enables clinicians to:
- View patient history chronologically (documents + clinical concepts)
- Identify temporal patterns and disease progression
- Filter by concepts, meta-annotations, date ranges, document types
- Export to PDF/FHIR/JSON for referrals, audits, research

### Scope

**Sprint Duration**: 4 weeks (~120 hours)
**Implementation Phases**: 8 phases (15 hours each)
**Dependencies**: Base Application (MVP), Patient Search Module (Sprint 1 complete)

### Success Criteria

- Timeline loads in <2 seconds for <100 documents
- Filter updates in <500ms
- Zoom/pan at 60fps
- PDF export in <5 seconds
- 80% unit test coverage, 70% integration test coverage
- HIPAA/GDPR compliant audit logging
- WCAG 2.1 AA accessibility

---

## Architecture

### High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3 + Vuetify)                   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  TimelineView.vue (Main Component)                         │ │
│  │  - D3.js timeline visualization (horizontal SVG)           │ │
│  │  - Zoom/pan controls (d3-zoom)                             │ │
│  │  - Concept markers (color-coded by type)                   │ │
│  │  - Document markers (chronological)                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────┐  ┌─────────────────┐  ┌───────────────────┐    │
│  │ Concept    │  │ Timeline        │  │ Export            │    │
│  │ Filter     │  │ Toolbar         │  │ Toolbar           │    │
│  │ Sidebar    │  │ (zoom/orient)   │  │ (PDF/FHIR/JSON)   │    │
│  └────────────┘  └─────────────────┘  └───────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Popover Components                                        │ │
│  │  - ConceptPopover (concept details + meta-annotations)     │ │
│  │  - DocumentModal (full document view)                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                             ↓ ↑ REST API
┌──────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API Endpoints (app/api/v1/endpoints/timeline.py)         │ │
│  │  - GET    /timeline/{patient_id}                          │ │
│  │  - GET    /timeline/{patient_id}/concepts                 │ │
│  │  - POST   /timeline/{patient_id}/export                   │ │
│  │  - GET    /timeline/exports/{export_id}/download          │ │
│  │  - POST   /timeline/filters (save preset)                 │ │
│  │  - GET    /timeline/filters (load presets)                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓ ↑                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Service Layer (app/services/timeline_service.py)         │ │
│  │  - TimelineService (timeline aggregation)                 │ │
│  │  - TimelineExportService (PDF/FHIR/JSON generation)       │ │
│  │  - TimelineFilterService (preset management)              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓ ↑                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Repository Layer                                          │ │
│  │  - PostgreSQLTimelineRepo (documents, audit logs)         │ │
│  │  - ElasticsearchTimelineRepo (concepts, temporal queries) │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                             ↓ ↑
┌──────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  PostgreSQL      │  │  Elasticsearch   │  │  CogStack-   │  │
│  │  - documents     │  │  - clinical_     │  │  ModelServe  │  │
│  │  - annotations   │  │    concepts      │  │  (concepts)  │  │
│  │  - audit_logs    │  │  - temporal      │  │              │  │
│  │  - timeline_*    │  │    aggregations  │  │              │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow: Timeline Rendering

```
User Opens Timeline
       ↓
Frontend (TimelineView.vue)
       ↓
GET /api/v1/timeline/{patient_id}?filters={...}
       ↓
Backend TimelineService
       ↓
1. Audit Log Access (WHO viewed WHICH patient WHEN)
       ↓
2. PostgreSQL: Fetch documents for patient
   - Filter by document_type (if specified)
   - Filter by date_range (if specified)
   - Order by date ASC
       ↓
3. Elasticsearch: Fetch concepts for patient
   - Filter by concept CUI (if specified)
   - Filter by meta_annotations (Negation, Experiencer, Temporality)
   - Filter by date_range
   - Aggregate by concept (first mention, frequency)
       ↓
4. Merge documents + concepts chronologically
       ↓
5. Return PatientTimeline response
       ↓
Frontend renders timeline with D3.js
```

### Data Flow: Export to PDF

```
User Clicks "Export to PDF"
       ↓
Frontend sends POST /api/v1/timeline/{patient_id}/export
       ↓
Backend TimelineExportService
       ↓
1. Fetch timeline data (documents + concepts)
       ↓
2. Render HTML template (Jinja2)
   - Patient demographics
   - Timeline visualization (SVG embedded)
   - Key concepts list (chronological)
   - Document list
   - Export metadata (user, timestamp)
       ↓
3. Convert HTML to PDF (WeasyPrint)
       ↓
4. Add watermark: "Clinical Summary - Do Not Share Without Authorization"
       ↓
5. Save to timeline_exports table
   - Store file_path
   - Set expires_at (30 days)
       ↓
6. Audit log export (format=pdf, user, patient, timestamp)
       ↓
7. Return export_id + download_url
       ↓
Frontend downloads PDF via GET /timeline/exports/{export_id}/download
```

---

## Technology Choices

### Frontend Technologies

#### D3.js v7 (Timeline Visualization)

**Choice**: D3.js v7 for SVG-based timeline rendering

**Rationale**:
- ✅ Industry-standard data visualization library
- ✅ Fine-grained control over SVG elements (zoom, pan, animations)
- ✅ Powerful axis generation (time scales, date formatting)
- ✅ Excellent performance (60fps with 500+ elements)
- ✅ Large ecosystem (d3-zoom, d3-axis, d3-selection)

**Alternatives Considered**:
- ❌ Vis.js Timeline - Less flexible, heavier bundle size
- ❌ Timeline.js - Limited customization, no zoom/pan
- ❌ Chart.js - Not designed for timeline visualizations

**Implementation**:
- `d3-selection` - DOM manipulation
- `d3-scale` - Time scales for x-axis
- `d3-axis` - Date axis rendering
- `d3-zoom` - Zoom/pan interactions
- `d3-shape` - SVG path generation

#### Vue 3 Composables (State Management)

**Choice**: Vue 3 Composition API with composables (no Pinia for this module)

**Rationale**:
- ✅ Simple state management (timeline data, filters, zoom state)
- ✅ No global state needed (timeline is patient-specific)
- ✅ Easier testing (composables are pure functions)
- ✅ Better TypeScript support

**Composables**:
- `useTimeline()` - Fetch and manage timeline data
- `useTimelineFilters()` - Filter state and URL sync
- `useTimelineZoom()` - Zoom/pan state
- `useTimelineExport()` - Export functionality

#### Vuetify 3 (UI Components)

**Choice**: Vuetify 3 for filters, buttons, dialogs

**Rationale**:
- ✅ Consistent with base app and Patient Search module
- ✅ Material Design components (date pickers, autocomplete)
- ✅ Accessibility built-in (WCAG 2.1 AA)

**Components Used**:
- `v-autocomplete` - Concept search with SNOMED-CT suggestions
- `v-date-picker` - Date range selection
- `v-checkbox` - Meta-annotation filters
- `v-btn` - Export buttons
- `v-dialog` - Export options modal
- `v-chip` - Concept tags

---

### Backend Technologies

#### WeasyPrint (PDF Generation)

**Choice**: WeasyPrint for HTML-to-PDF conversion

**Rationale**:
- ✅ Pure Python (no external dependencies like wkhtmltopdf)
- ✅ CSS support (embed SVG, apply watermarks)
- ✅ Fast rendering (<5 seconds for 100-page PDFs)
- ✅ Production-ready (used by Mozilla, Wikimedia)

**Alternatives Considered**:
- ❌ wkhtmltopdf - Deprecated, requires Qt installation
- ❌ ReportLab - Low-level API, harder to style
- ❌ Puppeteer (Pyppeteer) - Requires headless Chrome, heavyweight

**Installation**:
```bash
pip install weasyprint
```

**Usage**:
```python
from weasyprint import HTML, CSS

html = HTML(string=html_template)
pdf_bytes = html.write_pdf(stylesheets=[CSS(string=watermark_css)])
```

#### fhir.resources (FHIR R4 Models)

**Choice**: `fhir.resources` Python library for FHIR R4 export

**Rationale**:
- ✅ Pydantic-based models (type safety)
- ✅ Complete FHIR R4 coverage (Composition, Observation, Condition, Provenance)
- ✅ Validation (ensures FHIR compliance)

**Installation**:
```bash
pip install fhir.resources
```

**Usage**:
```python
from fhir.resources.composition import Composition
from fhir.resources.observation import Observation

composition = Composition(
    status="final",
    type={"coding": [{"system": "...", "code": "..."}]},
    subject={"reference": f"Patient/{patient_id}"},
    section=[...]
)
```

#### Jinja2 (HTML Templating)

**Choice**: Jinja2 for PDF HTML templates

**Rationale**:
- ✅ FastAPI default templating engine
- ✅ Powerful template inheritance
- ✅ Safe escaping (prevents XSS)

**Template Structure**:
```
backend/app/templates/timeline/
  - base.html (layout with watermark)
  - timeline_pdf.html (timeline content)
```

---

### Database Technologies

#### PostgreSQL (Timeline Filters & Exports)

**New Tables**:
- `timeline_filters` - Save/load filter presets
- `timeline_exports` - Track exports for audit

**Rationale**:
- ✅ ACID compliance (audit trail integrity)
- ✅ JSON column support (flexible filter storage)
- ✅ Foreign keys (referential integrity)

#### Elasticsearch (Temporal Concept Queries)

**Index**: `clinical_concepts` (new index for timeline)

**Rationale**:
- ✅ Fast range queries (date filtering)
- ✅ Aggregations (concept frequency over time)
- ✅ Full-text search (concept name autocomplete)
- ✅ Boolean queries (meta-annotation filtering)

**Index Mapping**:
```json
{
  "mappings": {
    "properties": {
      "patient_id": { "type": "keyword" },
      "document_id": { "type": "keyword" },
      "concept_cui": { "type": "keyword" },
      "concept_name": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "concept_type": { "type": "keyword" },
      "date": { "type": "date" },
      "meta_annotations": {
        "properties": {
          "Negation": { "type": "keyword" },
          "Temporality": { "type": "keyword" },
          "Experiencer": { "type": "keyword" },
          "Certainty": { "type": "keyword" }
        }
      },
      "confidence": { "type": "float" },
      "sentence": { "type": "text" }
    }
  }
}
```

---

## Implementation Phases

### Phase 5.1: Backend Timeline Data API (Week 1, 15 hours)

**Goal**: Build backend API to serve timeline data (documents + concepts)

**Tasks**:
1. Create database schema (timeline_filters, timeline_exports tables)
2. Create Elasticsearch index (clinical_concepts)
3. Implement TimelineService:
   - `get_patient_timeline()` - Fetch documents + concepts
   - `get_timeline_concepts()` - Fetch specific concepts
4. Implement ElasticsearchTimelineRepository:
   - `query_concepts_by_patient()` - Temporal + meta-annotation filtering
   - `aggregate_concepts_by_date()` - Concept frequency
5. Create API endpoint: GET /api/v1/timeline/{patient_id}
6. Add audit logging (WHO viewed WHICH patient timeline WHEN)
7. Write unit tests (TimelineService methods)
8. Write integration tests (API endpoint)

**Acceptance Criteria**:
- [x] GET /api/v1/timeline/{patient_id} returns PatientTimeline response
- [x] Filters work: concepts, date_range, meta_annotations, document_types
- [x] Audit log entry created for every timeline access
- [x] Response time <2 seconds for <100 documents
- [x] Unit test coverage ≥80%

**Files Created**:
- `backend/app/api/v1/endpoints/timeline.py`
- `backend/app/services/timeline_service.py`
- `backend/app/repositories/elasticsearch_timeline_repo.py`
- `backend/app/schemas/timeline.py`
- `backend/alembic/versions/{hash}_add_timeline_tables.py`
- `backend/tests/unit/services/test_timeline_service.py`
- `backend/tests/integration/api/test_timeline_api.py`

---

### Phase 5.2: Frontend Timeline Component (D3.js) (Week 1, 15 hours)

**Goal**: Build basic timeline visualization with D3.js

**Tasks**:
1. Create TimelineView.vue component:
   - SVG canvas setup
   - D3.js time scale (x-axis)
   - Date axis rendering (month/year labels)
   - Document markers (circles on timeline)
   - Tooltip on hover (document title + date)
2. Create useTimeline composable:
   - Fetch timeline data from API
   - Handle loading/error states
   - Cache timeline data (avoid re-fetching)
3. Add routing: /timeline/:patientId
4. Write unit tests (TimelineView component)

**Acceptance Criteria**:
- [x] Timeline renders with horizontal date axis
- [x] Document markers positioned by date
- [x] Hover shows document title + date
- [x] Loading spinner while fetching data
- [x] Error message if fetch fails
- [x] Unit test coverage ≥80%

**Files Created**:
- `frontend/src/views/TimelineView.vue`
- `frontend/src/components/TimelineAxis.vue`
- `frontend/src/components/TimelineDocuments.vue`
- `frontend/src/composables/useTimeline.ts`
- `frontend/src/api/timeline.ts`
- `frontend/tests/unit/views/TimelineView.spec.ts`

---

### Phase 5.3: Concept Extraction & Display (Week 2, 15 hours)

**Goal**: Extract clinical concepts and display as color-coded markers

**Tasks**:
1. Implement concept extraction:
   - CogStack-ModelServe integration (reuse from Patient Search)
   - Extract concepts for all patient documents
   - Store in Elasticsearch clinical_concepts index
2. Update TimelineView to display concept markers:
   - Color-code by concept type (red=condition, blue=medication, green=procedure)
   - Position by date (align with documents)
   - Click to show ConceptPopover
3. Create ConceptPopover component:
   - Display concept name, CUI, confidence
   - Show sentence where concept was mentioned
   - Show meta-annotations (chips: green/red/grey)
   - Link to source document
4. Write unit tests (ConceptPopover)

**Acceptance Criteria**:
- [x] Concepts extracted using CogStack-ModelServe
- [x] Concepts displayed as color-coded markers
- [x] Click concept → popover shows details
- [x] Meta-annotations visible in popover
- [x] Unit test coverage ≥80%

**Files Created**:
- `frontend/src/components/TimelineConcepts.vue`
- `frontend/src/components/ConceptPopover.vue`
- `backend/app/services/concept_extraction_service.py` (reuse from Sprint 1)
- `frontend/tests/unit/components/ConceptPopover.spec.ts`

---

### Phase 5.4: Filtering & Search (Week 2, 15 hours)

**Goal**: Add concept filters, date range, meta-annotations, document type filters

**Tasks**:
1. Create ConceptFilterSidebar component:
   - Search box with SNOMED-CT autocomplete
   - Multi-select concept chips
   - Date range picker (absolute or relative)
   - Meta-annotation checkboxes (Affirmed, Patient, Current/Recent)
   - Document type checkboxes (clinical notes, discharge summaries, etc.)
2. Create useTimelineFilters composable:
   - Manage filter state
   - Sync filters with URL query params (shareable links)
   - Apply filters to API request
3. Update GET /api/v1/timeline/{patient_id} to accept filters
4. Add filter persistence:
   - POST /api/v1/timeline/filters (save preset)
   - GET /api/v1/timeline/filters (load presets)
5. Write unit tests (ConceptFilterSidebar, useTimelineFilters)

**Acceptance Criteria**:
- [x] Concept search with autocomplete works
- [x] Multi-select concepts filters timeline
- [x] Date range filters timeline
- [x] Meta-annotation filters work (exclude negated, family, etc.)
- [x] Document type filters work
- [x] Filter presets can be saved/loaded
- [x] Filters synced with URL (shareable links)
- [x] Filter updates <500ms
- [x] Unit test coverage ≥80%

**Files Created**:
- `frontend/src/components/ConceptFilterSidebar.vue`
- `frontend/src/composables/useTimelineFilters.ts`
- `backend/app/api/v1/endpoints/timeline.py` (add filter endpoints)
- `backend/app/services/timeline_filter_service.py`
- `frontend/tests/unit/components/ConceptFilterSidebar.spec.ts`

---

### Phase 5.5: Zoom, Pan, and Temporal Analysis (Week 3, 15 hours)

**Goal**: Add zoom/pan controls and temporal pattern detection

**Tasks**:
1. Add D3.js zoom/pan:
   - `d3-zoom` integration
   - Zoom in/out buttons (+/-)
   - Pan with mouse drag
   - Reset zoom button
   - Smooth animations (60fps)
2. Add temporal pattern detection:
   - Identify first mention of concept (large marker)
   - Identify recurring mentions (small markers)
   - Concept frequency chart (bar chart overlay)
   - Highlight temporal relationships (e.g., medication start → symptom onset within 30 days)
3. Create useTimelineZoom composable:
   - Manage zoom state (scale, translate)
   - Debounce zoom events (performance)
4. Write unit tests (zoom/pan, frequency chart)

**Acceptance Criteria**:
- [x] Zoom in/out works (buttons + mouse wheel)
- [x] Pan works (mouse drag)
- [x] Zoom/pan at 60fps
- [x] First mention vs recurring differentiated
- [x] Concept frequency chart toggleable
- [x] Unit test coverage ≥80%

**Files Created**:
- `frontend/src/composables/useTimelineZoom.ts`
- `frontend/src/components/TimelineFrequencyChart.vue`
- `frontend/src/components/TimelineToolbar.vue` (zoom buttons)
- `frontend/tests/unit/composables/useTimelineZoom.spec.ts`

---

### Phase 5.6: Export Capabilities (PDF, FHIR, JSON) (Week 3, 15 hours)

**Goal**: Implement export to PDF, FHIR R4, and JSON

**Tasks**:
1. Create TimelineExportService:
   - `export_timeline_pdf()` - HTML → PDF with WeasyPrint
   - `export_timeline_fhir()` - Map to FHIR R4 Composition
   - `export_timeline_json()` - Serialize timeline data
2. Create HTML template for PDF:
   - Patient demographics
   - Timeline visualization (embed SVG)
   - Key concepts list
   - Document list
   - Watermark: "Clinical Summary - Confidential"
3. Add API endpoints:
   - POST /api/v1/timeline/{patient_id}/export
   - GET /api/v1/timeline/exports/{export_id}/download
4. Create TimelineExportToolbar component:
   - Export buttons (PDF, FHIR, JSON)
   - Export options dialog (filters, watermark)
   - Progress indicator
   - Download link
5. Add audit logging for exports
6. Write unit tests (TimelineExportService)
7. Write integration tests (export endpoints)

**Acceptance Criteria**:
- [x] Export to PDF works (<5 seconds)
- [x] PDF includes timeline visualization, concepts, documents
- [x] PDF watermarked: "Clinical Summary - Confidential"
- [x] Export to FHIR R4 works (valid Composition resource)
- [x] Export to JSON works (machine-readable)
- [x] Audit log entry created for all exports
- [x] Exports expire after 30 days (automatic cleanup)
- [x] Unit test coverage ≥80%

**Files Created**:
- `backend/app/services/timeline_export_service.py`
- `backend/app/templates/timeline/timeline_pdf.html`
- `backend/app/api/v1/endpoints/timeline.py` (add export endpoints)
- `frontend/src/components/TimelineExportToolbar.vue`
- `frontend/src/composables/useTimelineExport.ts`
- `backend/tests/unit/services/test_timeline_export_service.py`
- `backend/tests/integration/api/test_timeline_export_api.py`

**Dependencies**:
- WeasyPrint: `pip install weasyprint`
- fhir.resources: `pip install fhir.resources`

---

### Phase 5.7: Integration Tests & E2E Tests (Week 4, 15 hours)

**Goal**: Comprehensive testing (integration + E2E + performance)

**Tasks**:
1. Write integration tests:
   - Timeline API endpoints (GET /timeline, POST /export)
   - Filter endpoints (save/load presets)
   - Elasticsearch queries (concept aggregation)
   - PDF/FHIR/JSON export formats
2. Write E2E tests (Playwright):
   - Full timeline workflow (open → filter → export)
   - Zoom/pan interactions
   - Concept popover display
   - Export download
3. Write performance tests:
   - Timeline load time (<2 seconds for 100 documents)
   - Filter update time (<500ms)
   - Concurrent user access (10 users)
   - PDF export time (<5 seconds)
4. Write security tests:
   - Authentication required for all endpoints
   - RBAC (clinicians see assigned patients only)
   - Audit logging verification
   - XSS prevention in concept rendering

**Acceptance Criteria**:
- [x] Integration test coverage ≥70%
- [x] E2E test covers full workflow
- [x] Performance tests verify targets
- [x] Security tests pass
- [x] All tests passing in CI/CD

**Files Created**:
- `backend/tests/integration/api/test_timeline_integration.py`
- `frontend/tests/e2e/timeline-workflow.spec.ts`
- `backend/tests/performance/test_timeline_performance.py`
- `backend/tests/security/test_timeline_security.py`

---

### Phase 5.8: Documentation, Deployment & Polish (Week 4, 15 hours)

**Goal**: Complete documentation, deployment, accessibility, and polish

**Tasks**:
1. Update DEVELOPMENT.md:
   - Timeline API documentation (all 6 endpoints)
   - cURL examples
   - Error responses
   - Performance targets
2. Update CONTEXT.md:
   - Add Phase 5 completion entry
   - Document architecture decisions (D3.js choice, WeasyPrint choice)
   - Update sprint progress
3. Create database migration:
   - `alembic revision -m "Add timeline tables"`
   - Create timeline_filters and timeline_exports tables
   - Create Elasticsearch clinical_concepts index
4. Update docker-compose.yml:
   - Add timeline_exports volume
   - Add environment variables (TIMELINE_ENABLED, TIMELINE_PDF_EXPORT_DIR)
5. Accessibility audit:
   - Keyboard navigation (tab through timeline, press Enter to open popover)
   - Screen reader support (ARIA labels for timeline elements)
   - Color contrast check (WCAG 2.1 AA)
   - Focus indicators visible
6. UI polish:
   - Loading skeletons (better UX than spinners)
   - Empty states (no documents, no concepts)
   - Error states (API failures)
   - Responsive design (1920x1080, 1366x768)
7. Performance optimization:
   - Debounce filter updates
   - Lazy-load offscreen timeline segments
   - Elasticsearch query optimization (use cached aggregations)
   - Frontend virtualization (render visible timeline only)
8. Create admin panel for timeline settings:
   - Default timeline orientation (horizontal/vertical)
   - Default date range (all time, last year, last 3 months)
   - Max documents to load (performance tuning)

**Acceptance Criteria**:
- [x] DEVELOPMENT.md updated with complete API docs
- [x] CONTEXT.md updated with Phase 5 completion
- [x] Database migrations created and tested
- [x] Docker deployment works
- [x] WCAG 2.1 AA compliance verified
- [x] All UI polish complete
- [x] Performance optimization complete
- [x] Admin panel functional

**Files Created**:
- `docs/DEVELOPMENT.md` (updated)
- `CONTEXT.md` (updated)
- `backend/alembic/versions/{hash}_add_timeline_tables.py`
- `docker-compose.yml` (updated)
- `frontend/src/components/TimelineLoadingSkeleton.vue`
- `frontend/src/components/TimelineEmptyState.vue`
- `frontend/src/views/admin/TimelineSettingsView.vue`

---

## API Design

### Endpoint Specifications (OpenAPI)

#### GET `/api/v1/timeline/{patient_id}`

**Summary**: Get patient timeline with documents and concepts

**Parameters**:
- `patient_id` (path, required): Patient UUID
- `concepts` (query, optional): Comma-separated SNOMED CUIs (e.g., "C0011849,C0020538")
- `date_start` (query, optional): Start date (ISO 8601: "2023-01-01T00:00:00Z")
- `date_end` (query, optional): End date (ISO 8601: "2023-12-31T23:59:59Z")
- `meta_negation` (query, optional): "Affirmed" | "Negated" | "all" (default: "Affirmed")
- `meta_experiencer` (query, optional): "Patient" | "Family" | "all" (default: "Patient")
- `meta_temporality` (query, optional): "Current,Recent" | "Historical" | "all" (default: "Current,Recent")
- `document_types` (query, optional): Comma-separated types (e.g., "clinical_note,discharge_summary")

**Request Example**:
```bash
GET /api/v1/timeline/patient-123?concepts=C0011849,C0020538&date_start=2023-01-01T00:00:00Z&date_end=2023-12-31T23:59:59Z&meta_negation=Affirmed&meta_experiencer=Patient
```

**Response** (200 OK):
```json
{
  "patient_id": "patient-123",
  "documents": [
    {
      "document_id": "doc-456",
      "title": "Diabetes Clinic Note",
      "document_type": "clinical_note",
      "date": "2023-06-15T10:30:00Z",
      "author": "Dr. Smith",
      "concepts": ["C0011849", "C0020538"]
    }
  ],
  "concepts": [
    {
      "concept_cui": "C0011849",
      "concept_name": "Diabetes Mellitus",
      "concept_type": "condition",
      "first_mention_date": "2022-03-10T00:00:00Z",
      "mention_count": 12,
      "mentions": [
        {
          "document_id": "doc-123",
          "date": "2022-03-10T00:00:00Z",
          "sentence": "Patient diagnosed with Type 2 Diabetes.",
          "meta_annotations": {
            "Negation": "Affirmed",
            "Temporality": "Recent",
            "Experiencer": "Patient",
            "Certainty": "High"
          },
          "confidence": 0.95
        }
      ]
    }
  ],
  "date_range": {
    "start": "2022-01-01T00:00:00Z",
    "end": "2023-12-31T23:59:59Z"
  },
  "filters_applied": {
    "concepts": ["C0011849", "C0020538"],
    "meta_annotations": {
      "Negation": "Affirmed",
      "Experiencer": "Patient",
      "Temporality": ["Current", "Recent"]
    }
  }
}
```

**Error Responses**:
- 400 Bad Request: Invalid date format or filters
- 401 Unauthorized: Missing or invalid session token
- 403 Forbidden: User not authorized to view this patient
- 404 Not Found: Patient not found
- 500 Internal Server Error: Database or Elasticsearch failure

---

#### POST `/api/v1/timeline/{patient_id}/export`

**Summary**: Export timeline to PDF, FHIR R4, or JSON

**Parameters**:
- `patient_id` (path, required): Patient UUID

**Request Body**:
```json
{
  "format": "pdf",  // "pdf" | "fhir" | "json"
  "filters": {
    "concepts": ["C0011849"],
    "date_range": {
      "start": "2023-01-01T00:00:00Z",
      "end": "2023-12-31T23:59:59Z"
    },
    "meta_annotations": {
      "Negation": "Affirmed",
      "Experiencer": "Patient"
    }
  },
  "options": {
    "include_provenance": true,  // Include source documents in FHIR
    "watermark": "Clinical Summary - Confidential"  // PDF watermark text
  }
}
```

**Response** (200 OK):
```json
{
  "export_id": "export-789",
  "format": "pdf",
  "download_url": "/api/v1/timeline/exports/export-789/download",
  "expires_at": "2023-12-17T12:00:00Z",  // 30 days from now
  "audit_log_id": "audit-101112"
}
```

**Error Responses**:
- 400 Bad Request: Invalid format or filters
- 401 Unauthorized: Missing or invalid session token
- 403 Forbidden: User not authorized to export this patient timeline
- 500 Internal Server Error: Export generation failed

---

#### GET `/api/v1/timeline/exports/{export_id}/download`

**Summary**: Download exported timeline file

**Parameters**:
- `export_id` (path, required): Export UUID

**Response** (200 OK):
- Content-Type: `application/pdf` | `application/fhir+json` | `application/json`
- Content-Disposition: `attachment; filename="timeline-patient-123-2023-11-17.pdf"`

**Error Responses**:
- 404 Not Found: Export not found or expired
- 401 Unauthorized: Missing or invalid session token

---

#### POST `/api/v1/timeline/filters`

**Summary**: Save timeline filter preset

**Request Body**:
```json
{
  "name": "Diabetes Management View",
  "description": "Timeline filtered for diabetes-related concepts",
  "filters": {
    "concepts": ["C0011849", "C0020538"],
    "meta_annotations": {
      "Negation": "Affirmed",
      "Experiencer": "Patient"
    }
  },
  "is_default": false
}
```

**Response** (201 Created):
```json
{
  "id": "filter-456",
  "name": "Diabetes Management View",
  "description": "Timeline filtered for diabetes-related concepts",
  "filters": { /* ... */ },
  "is_default": false,
  "created_at": "2023-11-17T10:30:00Z"
}
```

**Error Responses**:
- 400 Bad Request: Invalid filter format
- 409 Conflict: Filter name already exists for this user

---

#### GET `/api/v1/timeline/filters`

**Summary**: Get user's saved filter presets

**Response** (200 OK):
```json
{
  "filters": [
    {
      "id": "filter-456",
      "name": "Diabetes Management View",
      "description": "Timeline filtered for diabetes-related concepts",
      "filters": { /* ... */ },
      "is_default": false,
      "created_at": "2023-11-17T10:30:00Z"
    }
  ]
}
```

---

## Data Model

### Database Schema (PostgreSQL)

#### `timeline_filters` Table

```sql
CREATE TABLE timeline_filters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    filters JSONB NOT NULL,  -- Stored filter configuration
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)
);

CREATE INDEX idx_timeline_filters_user ON timeline_filters(user_id);
```

**Purpose**: Save user-defined filter presets (e.g., "Diabetes Management View")

**Example Row**:
```json
{
  "id": "filter-456",
  "user_id": "user-123",
  "name": "Diabetes Management View",
  "description": "Timeline filtered for diabetes-related concepts",
  "filters": {
    "concepts": ["C0011849", "C0020538"],
    "meta_annotations": {
      "Negation": "Affirmed",
      "Experiencer": "Patient"
    }
  },
  "is_default": false,
  "created_at": "2023-11-17T10:30:00Z",
  "updated_at": "2023-11-17T10:30:00Z"
}
```

---

#### `timeline_exports` Table

```sql
CREATE TABLE timeline_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    user_id UUID NOT NULL REFERENCES users(id),
    format VARCHAR(10) NOT NULL,  -- "pdf", "fhir", "json"
    filters JSONB NOT NULL,
    file_path VARCHAR(500),  -- Path to exported file
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    audit_log_id UUID REFERENCES audit_logs(id)
);

CREATE INDEX idx_timeline_exports_patient ON timeline_exports(patient_id);
CREATE INDEX idx_timeline_exports_user ON timeline_exports(user_id);
CREATE INDEX idx_timeline_exports_created ON timeline_exports(created_at);
CREATE INDEX idx_timeline_exports_expires ON timeline_exports(expires_at);
```

**Purpose**: Track timeline exports for audit and automatic cleanup

**Example Row**:
```json
{
  "id": "export-789",
  "patient_id": "patient-123",
  "user_id": "user-456",
  "format": "pdf",
  "filters": { /* ... */ },
  "file_path": "/app/exports/timeline/export-789.pdf",
  "download_count": 3,
  "expires_at": "2023-12-17T12:00:00Z",  // 30 days from creation
  "created_at": "2023-11-17T12:00:00Z",
  "audit_log_id": "audit-101112"
}
```

---

### Elasticsearch Index Schema

#### `clinical_concepts` Index

```json
PUT /clinical_concepts
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "5s"
  },
  "mappings": {
    "properties": {
      "patient_id": {
        "type": "keyword"
      },
      "document_id": {
        "type": "keyword"
      },
      "concept_cui": {
        "type": "keyword"
      },
      "concept_name": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "concept_type": {
        "type": "keyword"  // "condition", "medication", "procedure", "symptom", "lab_result"
      },
      "date": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "meta_annotations": {
        "properties": {
          "Negation": { "type": "keyword" },  // "Affirmed", "Negated"
          "Temporality": { "type": "keyword" },  // "Current", "Recent", "Historical"
          "Experiencer": { "type": "keyword" },  // "Patient", "Family", "Other"
          "Certainty": { "type": "keyword" }  // "High", "Medium", "Low"
        }
      },
      "confidence": {
        "type": "float"  // 0.0 to 1.0
      },
      "sentence": {
        "type": "text"
      }
    }
  }
}
```

**Purpose**: Store clinical concepts with temporal and meta-annotation data for fast querying

**Example Document**:
```json
{
  "patient_id": "patient-123",
  "document_id": "doc-456",
  "concept_cui": "C0011849",
  "concept_name": "Diabetes Mellitus",
  "concept_type": "condition",
  "date": "2023-06-15T10:30:00Z",
  "meta_annotations": {
    "Negation": "Affirmed",
    "Temporality": "Current",
    "Experiencer": "Patient",
    "Certainty": "High"
  },
  "confidence": 0.95,
  "sentence": "Patient diagnosed with Type 2 Diabetes. HbA1c 8.5%."
}
```

**Indexing Strategy**:
- Populated during document upload (reuse concept extraction from Sprint 1)
- Updated when documents are annotated
- Bulk indexing for large patient cohorts

---

### Pydantic Models (API Schemas)

#### `PatientTimeline` (Response Model)

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TimelineDocument(BaseModel):
    document_id: str
    title: str
    document_type: str  # "clinical_note", "discharge_summary", "lab_report", etc.
    date: datetime
    author: Optional[str] = None
    concepts: List[str]  # List of concept CUIs mentioned

class MetaAnnotations(BaseModel):
    Negation: str  # "Affirmed" | "Negated"
    Temporality: str  # "Current" | "Recent" | "Historical"
    Experiencer: str  # "Patient" | "Family" | "Other"
    Certainty: str  # "High" | "Medium" | "Low"

class ConceptMention(BaseModel):
    document_id: str
    date: datetime
    sentence: str
    meta_annotations: MetaAnnotations
    confidence: float

class TimelineConcept(BaseModel):
    concept_cui: str
    concept_name: str
    concept_type: str  # "condition" | "medication" | "procedure"
    first_mention_date: datetime
    mention_count: int
    mentions: List[ConceptMention]

class DateRange(BaseModel):
    start: datetime
    end: datetime

class TimelineFilters(BaseModel):
    concepts: Optional[List[str]] = None
    date_range: Optional[DateRange] = None
    meta_annotations: Optional[dict] = None
    document_types: Optional[List[str]] = None

class PatientTimeline(BaseModel):
    patient_id: str
    documents: List[TimelineDocument]
    concepts: List[TimelineConcept]
    date_range: DateRange
    filters_applied: TimelineFilters
```

---

## Frontend Components

### Component Hierarchy

```
TimelineView.vue (Main View)
├── TimelineToolbar.vue (Zoom controls, export buttons)
├── ConceptFilterSidebar.vue (Filters)
│   ├── ConceptSearch.vue (Autocomplete)
│   ├── DateRangePicker.vue (Date filters)
│   └── MetaAnnotationFilters.vue (Checkboxes)
├── TimelineVisualization.vue (D3.js SVG)
│   ├── TimelineAxis.vue (Date axis)
│   ├── TimelineDocuments.vue (Document markers)
│   ├── TimelineConcepts.vue (Concept markers)
│   └── TimelineFrequencyChart.vue (Bar chart overlay)
├── ConceptPopover.vue (Concept details)
└── TimelineExportToolbar.vue (Export buttons)
    └── ExportOptionsDialog.vue (Export settings)
```

### Key Components

#### `TimelineView.vue` (Main Component)

**Responsibilities**:
- Fetch timeline data from API
- Manage timeline state (documents, concepts, filters, zoom)
- Coordinate child components
- Handle routing (patient_id param)

**Template**:
```vue
<template>
  <v-container fluid class="timeline-view">
    <v-row>
      <!-- Filter Sidebar -->
      <v-col cols="3">
        <ConceptFilterSidebar
          v-model="filters"
          @update:filters="applyFilters"
        />
      </v-col>

      <!-- Timeline Main Area -->
      <v-col cols="9">
        <!-- Toolbar -->
        <TimelineToolbar
          :zoom="zoom"
          @zoom-in="handleZoomIn"
          @zoom-out="handleZoomOut"
          @reset-zoom="handleResetZoom"
        />

        <!-- Timeline Visualization -->
        <TimelineVisualization
          :timeline="timeline"
          :filters="filters"
          :zoom="zoom"
          @concept-click="showConceptPopover"
          @document-click="showDocumentModal"
        />

        <!-- Export Toolbar -->
        <TimelineExportToolbar
          :patient-id="patientId"
          :filters="filters"
        />
      </v-col>
    </v-row>

    <!-- Concept Popover -->
    <ConceptPopover
      v-model="popoverVisible"
      :concept="selectedConcept"
      :position="popoverPosition"
    />
  </v-container>
</template>
```

**Script** (Composition API):
```typescript
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTimeline } from '@/composables/useTimeline'
import { useTimelineFilters } from '@/composables/useTimelineFilters'
import { useTimelineZoom } from '@/composables/useTimelineZoom'

const route = useRoute()
const patientId = computed(() => route.params.patientId as string)

// Composables
const { timeline, isLoading, error, fetchTimeline } = useTimeline()
const { filters, applyFilters } = useTimelineFilters()
const { zoom, handleZoomIn, handleZoomOut, handleResetZoom } = useTimelineZoom()

// Popover state
const popoverVisible = ref(false)
const selectedConcept = ref(null)
const popoverPosition = ref({ x: 0, y: 0 })

const showConceptPopover = (concept, position) => {
  selectedConcept.value = concept
  popoverPosition.value = position
  popoverVisible.value = true
}

onMounted(async () => {
  await fetchTimeline(patientId.value, filters.value)
})
</script>
```

---

#### `TimelineVisualization.vue` (D3.js Component)

**Responsibilities**:
- Render SVG timeline using D3.js
- Handle zoom/pan interactions
- Position documents and concepts by date
- Emit events on click

**Template**:
```vue
<template>
  <div ref="timelineContainer" class="timeline-container">
    <svg ref="timelineSvg" :width="width" :height="height">
      <g :transform="`translate(${margin.left}, ${margin.top})`">
        <!-- Date Axis -->
        <g ref="xAxis" class="x-axis"></g>

        <!-- Document Markers -->
        <g class="documents">
          <circle
            v-for="doc in visibleDocuments"
            :key="doc.document_id"
            :cx="xScale(new Date(doc.date))"
            :cy="documentY"
            :r="5"
            class="document-marker"
            @click="handleDocumentClick(doc)"
          />
        </g>

        <!-- Concept Markers -->
        <g class="concepts">
          <circle
            v-for="mention in visibleConceptMentions"
            :key="`${mention.concept_cui}-${mention.document_id}`"
            :cx="xScale(new Date(mention.date))"
            :cy="conceptY(mention.concept_type)"
            :r="mention.is_first_mention ? 8 : 4"
            :fill="conceptColor(mention.concept_type)"
            class="concept-marker"
            @click="handleConceptClick(mention, $event)"
          />
        </g>
      </g>
    </svg>
  </div>
</template>
```

**Script**:
```typescript
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps<{
  timeline: PatientTimeline
  filters: TimelineFilters
  zoom: { scale: number; translateX: number }
}>()

const emit = defineEmits<{
  conceptClick: [concept: TimelineConcept, event: MouseEvent]
  documentClick: [document: TimelineDocument]
}>()

const timelineSvg = ref<SVGSVGElement | null>(null)
const xAxis = ref<SVGGElement | null>(null)

const width = 1200
const height = 600
const margin = { top: 20, right: 20, bottom: 30, left: 50 }

// D3 scales
const xScale = d3.scaleTime()
  .domain([
    new Date(props.timeline.date_range.start),
    new Date(props.timeline.date_range.end)
  ])
  .range([0, width - margin.left - margin.right])

const conceptY = (conceptType: string) => {
  const yPositions = {
    condition: 100,
    medication: 200,
    procedure: 300,
    symptom: 400,
    lab_result: 500
  }
  return yPositions[conceptType] || 300
}

const conceptColor = (conceptType: string) => {
  const colors = {
    condition: '#f44336',  // red
    medication: '#2196f3',  // blue
    procedure: '#4caf50',  // green
    symptom: '#ffeb3b',  // yellow
    lab_result: '#9c27b0'  // purple
  }
  return colors[conceptType] || '#757575'
}

// Apply zoom transform
watch(() => props.zoom, (newZoom) => {
  if (timelineSvg.value) {
    const g = d3.select(timelineSvg.value).select('g')
    g.attr('transform', `translate(${margin.left + newZoom.translateX}, ${margin.top}) scale(${newZoom.scale}, 1)`)
  }
}, { deep: true })

onMounted(() => {
  // Render x-axis
  const xAxisGenerator = d3.axisBottom(xScale).ticks(10)
  d3.select(xAxis.value).call(xAxisGenerator)

  // Setup zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([1, 10])
    .on('zoom', (event) => {
      emit('zoom', { scale: event.transform.k, translateX: event.transform.x })
    })

  d3.select(timelineSvg.value).call(zoom)
})
</script>
```

---

## Backend Services

### Service Layer Architecture

```
TimelineService (timeline aggregation)
├── get_patient_timeline() - Fetch documents + concepts
├── get_timeline_concepts() - Fetch specific concepts
└── _audit_timeline_access() - Log access

TimelineExportService (export generation)
├── export_timeline_pdf() - HTML → PDF with WeasyPrint
├── export_timeline_fhir() - Map to FHIR R4
├── export_timeline_json() - Serialize to JSON
└── _cleanup_expired_exports() - Delete old exports (30 days)

TimelineFilterService (filter management)
├── save_filter_preset() - Save user filter
├── get_filter_presets() - Fetch user filters
└── delete_filter_preset() - Delete user filter

ElasticsearchTimelineRepository (concept queries)
├── query_concepts_by_patient() - Temporal + meta-annotation filtering
├── aggregate_concepts_by_date() - Concept frequency
└── get_concept_autocomplete() - SNOMED-CT suggestions
```

---

### Key Service: `TimelineService`

```python
# backend/app/services/timeline_service.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.timeline import (
    PatientTimeline, TimelineFilters, TimelineDocument, TimelineConcept
)
from app.repositories.elasticsearch_timeline_repo import ElasticsearchTimelineRepository
from app.services.audit_service import AuditService

class TimelineService:
    """Timeline data aggregation and processing"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.es_repo = ElasticsearchTimelineRepository()
        self.audit_service = AuditService(db)

    async def get_patient_timeline(
        self,
        patient_id: UUID,
        filters: TimelineFilters,
        user: User
    ) -> PatientTimeline:
        """Fetch patient timeline with documents and concepts"""

        # 1. Audit log access
        await self.audit_service.log_timeline_access(
            user_id=user.id,
            patient_id=patient_id,
            filters=filters
        )

        # 2. Query documents from PostgreSQL
        documents = await self._get_documents(patient_id, filters)

        # 3. Query concepts from Elasticsearch
        concepts = await self.es_repo.query_concepts_by_patient(
            patient_id=str(patient_id),
            concept_filter=filters.concepts,
            date_range=filters.date_range,
            meta_annotations=filters.meta_annotations
        )

        # 4. Aggregate concepts (first mention, frequency)
        aggregated_concepts = self._aggregate_concepts(concepts)

        # 5. Determine date range
        date_range = self._calculate_date_range(documents)

        return PatientTimeline(
            patient_id=str(patient_id),
            documents=documents,
            concepts=aggregated_concepts,
            date_range=date_range,
            filters_applied=filters
        )

    async def _get_documents(
        self,
        patient_id: UUID,
        filters: TimelineFilters
    ) -> List[TimelineDocument]:
        """Fetch documents from PostgreSQL with filters"""

        query = (
            select(Document)
            .where(Document.patient_id == patient_id)
        )

        # Apply date range filter
        if filters.date_range:
            query = query.where(
                Document.date >= filters.date_range.start,
                Document.date <= filters.date_range.end
            )

        # Apply document type filter
        if filters.document_types:
            query = query.where(Document.document_type.in_(filters.document_types))

        # Order by date ascending
        query = query.order_by(Document.date.asc())

        result = await self.db.execute(query)
        documents = result.scalars().all()

        return [
            TimelineDocument(
                document_id=str(doc.id),
                title=doc.title,
                document_type=doc.document_type,
                date=doc.date,
                author=doc.author,
                concepts=[]  # Filled later
            )
            for doc in documents
        ]

    def _aggregate_concepts(
        self,
        concept_mentions: List[ConceptMention]
    ) -> List[TimelineConcept]:
        """Aggregate concept mentions (first mention, frequency)"""

        concept_map = {}
        for mention in concept_mentions:
            cui = mention.concept_cui

            if cui not in concept_map:
                concept_map[cui] = TimelineConcept(
                    concept_cui=cui,
                    concept_name=mention.concept_name,
                    concept_type=mention.concept_type,
                    first_mention_date=mention.date,
                    mention_count=0,
                    mentions=[]
                )

            concept_map[cui].mention_count += 1
            concept_map[cui].mentions.append(mention)

            # Update first mention if earlier
            if mention.date < concept_map[cui].first_mention_date:
                concept_map[cui].first_mention_date = mention.date

        return list(concept_map.values())
```

---

### Key Service: `TimelineExportService`

```python
# backend/app/services/timeline_export_service.py

from weasyprint import HTML, CSS
from jinja2 import Template
from pathlib import Path
from datetime import datetime, timedelta
from app.schemas.timeline import PatientTimeline, TimelineFilters

class TimelineExportService:
    """Timeline export to PDF, FHIR, JSON"""

    EXPORT_DIR = Path("/app/exports/timeline")
    EXPORT_RETENTION_DAYS = 30

    async def export_timeline_pdf(
        self,
        patient_id: UUID,
        timeline: PatientTimeline,
        user: User
    ) -> tuple[UUID, str]:
        """Export timeline to PDF with watermark"""

        # 1. Render HTML template
        template_path = Path("app/templates/timeline/timeline_pdf.html")
        template = Template(template_path.read_text())

        html_content = template.render(
            patient=timeline.patient_id,
            documents=timeline.documents,
            concepts=timeline.concepts,
            export_date=datetime.now().isoformat(),
            exported_by=user.username
        )

        # 2. Convert HTML to PDF
        pdf = HTML(string=html_content)
        watermark_css = CSS(string="""
            @page {
                @bottom-center {
                    content: "Clinical Summary - Confidential";
                    font-size: 10pt;
                    color: #cccccc;
                }
            }
        """)
        pdf_bytes = pdf.write_pdf(stylesheets=[watermark_css])

        # 3. Save to disk
        export_id = uuid4()
        file_path = self.EXPORT_DIR / f"{export_id}.pdf"
        file_path.write_bytes(pdf_bytes)

        # 4. Save to database
        export_record = TimelineExport(
            id=export_id,
            patient_id=patient_id,
            user_id=user.id,
            format="pdf",
            filters=timeline.filters_applied.dict(),
            file_path=str(file_path),
            expires_at=datetime.now() + timedelta(days=self.EXPORT_RETENTION_DAYS)
        )
        self.db.add(export_record)
        await self.db.commit()

        # 5. Audit log export
        await self.audit_service.log_timeline_export(
            user_id=user.id,
            patient_id=patient_id,
            format="pdf",
            export_id=export_id
        )

        return export_id, f"/api/v1/timeline/exports/{export_id}/download"

    async def export_timeline_fhir(
        self,
        patient_id: UUID,
        timeline: PatientTimeline,
        user: User
    ) -> dict:
        """Export timeline to FHIR R4 Composition"""

        from fhir.resources.composition import Composition, CompositionSection
        from fhir.resources.observation import Observation

        composition = Composition(
            status="final",
            type={
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "11503-0",
                    "display": "Medical records"
                }]
            },
            subject={"reference": f"Patient/{patient_id}"},
            date=datetime.now().isoformat(),
            author=[{"reference": f"Practitioner/{user.id}"}],
            title="Patient Timeline Summary",
            section=[]
        )

        # Add concepts as Observations
        for concept in timeline.concepts:
            observation = Observation(
                status="final",
                code={
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": concept.concept_cui,
                        "display": concept.concept_name
                    }]
                },
                subject={"reference": f"Patient/{patient_id}"},
                effectiveDateTime=concept.first_mention_date.isoformat()
            )

            section = CompositionSection(
                title=concept.concept_name,
                entry=[{"reference": f"Observation/{concept.concept_cui}"}]
            )
            composition.section.append(section)

        # Save and audit log
        export_id = uuid4()
        await self._save_export(export_id, patient_id, user.id, "fhir", composition.dict())

        return composition.dict()
```

---

## Integration Points

### CogStack-ModelServe Integration

**Purpose**: Extract clinical concepts from documents

**Endpoint**: `POST http://cogstack-modelserve:8000/api/process`

**Request**:
```json
{
  "text": "Patient diagnosed with Type 2 Diabetes. HbA1c 8.5%.",
  "model": "medcat_snomed"
}
```

**Response**:
```json
{
  "entities": [
    {
      "cui": "C0011849",
      "pretty_name": "Diabetes Mellitus",
      "types": ["condition"],
      "start": 22,
      "end": 38,
      "meta_anns": {
        "Negation": "Affirmed",
        "Temporality": "Recent",
        "Experiencer": "Patient",
        "Certainty": "High"
      },
      "confidence": 0.95
    }
  ]
}
```

**Integration**:
- Reuse `ConceptExtractionService` from Sprint 1
- Index concepts in Elasticsearch `clinical_concepts` index
- Cache results (avoid re-processing same documents)

---

### Elasticsearch Queries

**Temporal Range Query** (Documents in date range):
```json
GET /clinical_concepts/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "patient_id": "patient-123" } },
        { "range": { "date": { "gte": "2023-01-01", "lte": "2023-12-31" } } }
      ]
    }
  },
  "sort": [{ "date": "asc" }]
}
```

**Meta-Annotation Filtering** (Affirmed, Patient, Current):
```json
GET /clinical_concepts/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "patient_id": "patient-123" } },
        { "term": { "meta_annotations.Negation": "Affirmed" } },
        { "term": { "meta_annotations.Experiencer": "Patient" } },
        { "terms": { "meta_annotations.Temporality": ["Current", "Recent"] } }
      ]
    }
  }
}
```

**Concept Frequency Aggregation** (Bar chart data):
```json
GET /clinical_concepts/_search
{
  "query": { "term": { "patient_id": "patient-123" } },
  "aggs": {
    "concepts_by_month": {
      "date_histogram": {
        "field": "date",
        "calendar_interval": "month"
      },
      "aggs": {
        "concept_counts": {
          "terms": { "field": "concept_cui", "size": 10 }
        }
      }
    }
  }
}
```

---

## Testing Strategy

### Unit Tests (60% of test effort)

**Backend Unit Tests** (pytest):
- TimelineService methods (get_patient_timeline, aggregate_concepts)
- TimelineExportService methods (export_pdf, export_fhir, export_json)
- ElasticsearchTimelineRepository queries
- TimelineFilterService CRUD operations

**Frontend Unit Tests** (Vitest):
- TimelineView component (renders timeline, applies filters)
- TimelineVisualization component (D3.js rendering, zoom/pan)
- ConceptFilterSidebar component (filter state management)
- TimelineExportToolbar component (export actions)
- Composables (useTimeline, useTimelineFilters, useTimelineZoom)

**Target**: 80% unit test coverage

---

### Integration Tests (30% of test effort)

**API Integration Tests**:
- GET /api/v1/timeline/{patient_id} (with various filters)
- POST /api/v1/timeline/{patient_id}/export (PDF, FHIR, JSON)
- GET /api/v1/timeline/exports/{export_id}/download
- POST /api/v1/timeline/filters (save preset)
- GET /api/v1/timeline/filters (load presets)

**Database Integration Tests**:
- PostgreSQL timeline_filters CRUD
- PostgreSQL timeline_exports CRUD
- Elasticsearch clinical_concepts queries

**Target**: 70% integration test coverage

---

### E2E Tests (10% of test effort)

**Full Timeline Workflow** (Playwright):
```typescript
test('clinician can view and export patient timeline', async ({ page }) => {
  // 1. Login as clinician
  await loginAsClinician(page)

  // 2. Navigate to Patient Search
  await page.goto('/patients/search')
  await page.fill('input[name="concept"]', 'diabetes')
  await page.click('button:has-text("Search")')

  // 3. Open patient timeline
  await page.click('button:has-text("Open Timeline")')
  await page.waitForSelector('.timeline-axis')

  // 4. Apply filters
  await page.fill('input[name="concept-search"]', 'diabetes')
  await page.click('text=Diabetes Mellitus (C0011849)')
  await page.waitForSelector('.concept-marker')

  // 5. Zoom timeline
  await page.click('button[aria-label="Zoom In"]')
  await page.waitForTimeout(500)  // Animation

  // 6. Click concept marker
  await page.click('.concept-marker:first-of-type')
  await page.waitForSelector('.concept-popover')

  // 7. Export to PDF
  await page.click('button:has-text("Export")')
  await page.click('text=Export to PDF')
  const downloadPromise = page.waitForEvent('download')
  await page.click('button:has-text("Download")')
  const download = await downloadPromise
  expect(download.suggestedFilename()).toContain('timeline')
  expect(download.suggestedFilename()).toContain('.pdf')
})
```

---

### Performance Tests

**Load Time Test**:
```python
@pytest.mark.performance
async def test_timeline_load_time_under_2_seconds():
    """Timeline should load in <2 seconds for 100 documents"""
    start = time.time()

    timeline = await timeline_service.get_patient_timeline(
        "patient-with-100-docs", TimelineFilters(), mock_user
    )

    elapsed = time.time() - start
    assert elapsed < 2.0
    assert len(timeline.documents) == 100
```

**Concurrent User Test**:
```python
@pytest.mark.performance
async def test_concurrent_timeline_access():
    """Support 10 concurrent users"""
    async def access_timeline(user_id):
        return await timeline_service.get_patient_timeline(
            "patient-123", TimelineFilters(), User(id=user_id)
        )

    tasks = [access_timeline(f"user-{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 10
    assert all(r.patient_id == "patient-123" for r in results)
```

---

## Performance Optimization

### Backend Optimization

1. **Elasticsearch Query Caching**:
   - Cache concept aggregations (5-minute TTL)
   - Use Redis for cache storage
   - Cache key: `timeline:{patient_id}:{filters_hash}`

2. **Database Query Optimization**:
   - Indexes on `documents(patient_id, date)`
   - Indexes on `timeline_exports(patient_id, expires_at)`
   - Use LIMIT for large result sets

3. **Lazy Loading**:
   - Load visible timeline range first (e.g., last 1 year)
   - Lazy-load older data on scroll/zoom

---

### Frontend Optimization

1. **D3.js Virtualization**:
   - Render only visible timeline segment (viewBox)
   - Cull offscreen elements
   - Use `requestAnimationFrame` for smooth animations

2. **Debounce Filter Updates**:
   - Debounce filter changes (300ms)
   - Cancel in-flight API requests on filter change

3. **Component Lazy Loading**:
   - Lazy-load export dialog (not needed initially)
   - Code-splitting for timeline route

4. **Memoization**:
   - Memoize concept color calculation
   - Cache D3 scale functions

---

## Security Considerations

### Authentication & Authorization

- **Session Token Required**: All timeline endpoints require valid session token
- **RBAC**: Clinicians can only view timelines for assigned patients
- **Admin Override**: Admins can view all timelines (audit logged)

### Audit Logging

- **Timeline Access**: Log every GET /timeline/{patient_id} (user, patient, timestamp, IP)
- **Filter Changes**: Log filters applied (what concepts were searched)
- **Exports**: Log all exports (format, user, patient, timestamp)
- **Retention**: Audit logs retained for 8 years (NHS compliance)

### Data Privacy

- **Export Watermarks**: All PDFs watermarked "Clinical Summary - Confidential"
- **Export Expiration**: Exports auto-deleted after 30 days
- **No PHI in Logs**: Application logs contain patient_id only (no names, MRNs)
- **HTTPS Only**: TLS 1.3 for data in transit
- **AES-256 at Rest**: Encrypted database storage

### Input Validation

- **Date Formats**: Validate ISO 8601 format
- **Concept CUIs**: Validate SNOMED-CT format (C followed by 7 digits)
- **SQL Injection**: Use parameterized queries (SQLAlchemy ORM)
- **XSS Prevention**: Sanitize concept names in HTML templates (Jinja2 auto-escaping)

---

## Deployment

### Docker Compose Updates

**Add timeline exports volume**:
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - TIMELINE_ENABLED=true
      - TIMELINE_PDF_EXPORT_DIR=/app/exports/timeline
      - TIMELINE_EXPORT_RETENTION_DAYS=30
      - TIMELINE_MAX_DOCUMENTS=500
      - TIMELINE_CACHE_TTL=300  # 5 minutes
    volumes:
      - timeline_exports:/app/exports/timeline

volumes:
  timeline_exports:
    driver: local
```

### Database Migrations

**Create timeline tables**:
```bash
# Generate migration
alembic revision --autogenerate -m "Add timeline_filters and timeline_exports tables"

# Apply migration
alembic upgrade head
```

### Elasticsearch Index Creation

**Create clinical_concepts index**:
```bash
curl -X PUT "localhost:9200/clinical_concepts" -H 'Content-Type: application/json' -d'
{
  "settings": { "number_of_shards": 1, "number_of_replicas": 0 },
  "mappings": { /* ... */ }
}
'
```

### Environment Variables

```bash
# .env
TIMELINE_ENABLED=true
TIMELINE_PDF_EXPORT_DIR=/app/exports/timeline
TIMELINE_EXPORT_RETENTION_DAYS=30
TIMELINE_MAX_DOCUMENTS=500
TIMELINE_CACHE_TTL=300
```

---

## Risks and Mitigation

### Technical Risks

#### Risk 1: D3.js Performance with Large Datasets

**Risk**: Rendering >500 documents/concepts may cause lag (< 60fps)

**Probability**: Medium
**Impact**: High (poor user experience)

**Mitigation**:
- ✅ Virtualization (render visible timeline only)
- ✅ Lazy loading (load older data on demand)
- ✅ Debounce zoom/pan events
- ✅ Performance testing with 500+ documents

---

#### Risk 2: PDF Export Timeout for Large Timelines

**Risk**: WeasyPrint may take >5 seconds for patients with 500+ documents

**Probability**: Low
**Impact**: Medium (violates performance requirement)

**Mitigation**:
- ✅ Limit PDF to visible timeline range (not all documents)
- ✅ Async export with progress indicator
- ✅ Background job queue (Celery) for large exports
- ✅ Performance testing with large datasets

---

#### Risk 3: Elasticsearch Query Performance

**Risk**: Concept aggregation queries may be slow for large patient cohorts

**Probability**: Low
**Impact**: Medium (timeline load >2 seconds)

**Mitigation**:
- ✅ Elasticsearch query optimization (use filters instead of queries)
- ✅ Index caching (5-minute TTL)
- ✅ Limit aggregation buckets (max 100)
- ✅ Performance testing with 100+ documents

---

### Timeline Risks

#### Risk 4: Scope Creep (Adding Features Not in Spec)

**Risk**: Team adds features like predictive analytics, multi-patient comparison

**Probability**: Medium
**Impact**: High (delays sprint, increases bugs)

**Mitigation**:
- ✅ Strict adherence to spec (constitution principle)
- ✅ "Non-Goals" section clearly defined
- ✅ User stories frozen before implementation
- ✅ Code review checks for out-of-scope features

---

#### Risk 5: Integration Delays (CogStack-ModelServe Unavailable)

**Risk**: CogStack-ModelServe service unavailable during development

**Probability**: Low
**Impact**: High (blocks concept extraction)

**Mitigation**:
- ✅ Mock CogStack-ModelServe responses for development
- ✅ Fallback: Show documents only (no concepts)
- ✅ Graceful degradation in UI
- ✅ Reuse working integration from Sprint 1

---

## Appendix

### Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend Visualization | D3.js v7 | Timeline SVG rendering, zoom/pan |
| Frontend Framework | Vue 3 + Composition API | Reactive UI components |
| Frontend UI Library | Vuetify 3 | Material Design components |
| Backend Framework | FastAPI | REST API endpoints |
| PDF Generation | WeasyPrint | HTML-to-PDF conversion |
| FHIR Export | fhir.resources | FHIR R4 Pydantic models |
| Database | PostgreSQL 15 | Timeline filters, exports, audit logs |
| Search Engine | Elasticsearch 8 | Temporal concept queries |
| NLP Service | CogStack-ModelServe | Concept extraction (SNOMED-CT) |
| Templating | Jinja2 | HTML templates for PDF export |

---

### Implementation Checklist

**Phase 5.1: Backend Timeline Data API**
- [ ] Create database schema (timeline_filters, timeline_exports)
- [ ] Create Elasticsearch index (clinical_concepts)
- [ ] Implement TimelineService (get_patient_timeline, get_timeline_concepts)
- [ ] Implement ElasticsearchTimelineRepository (query_concepts_by_patient)
- [ ] Create API endpoint: GET /api/v1/timeline/{patient_id}
- [ ] Add audit logging for timeline access
- [ ] Write unit tests (80% coverage)
- [ ] Write integration tests (70% coverage)

**Phase 5.2: Frontend Timeline Component (D3.js)**
- [ ] Create TimelineView.vue component
- [ ] Create useTimeline composable
- [ ] Add routing: /timeline/:patientId
- [ ] Render timeline with D3.js (date axis, document markers)
- [ ] Add tooltip on hover
- [ ] Write unit tests (80% coverage)

**Phase 5.3: Concept Extraction & Display**
- [ ] Integrate CogStack-ModelServe for concept extraction
- [ ] Store concepts in Elasticsearch clinical_concepts index
- [ ] Update TimelineView to display concept markers
- [ ] Create ConceptPopover component
- [ ] Color-code concepts by type
- [ ] Write unit tests (80% coverage)

**Phase 5.4: Filtering & Search**
- [ ] Create ConceptFilterSidebar component
- [ ] Create useTimelineFilters composable
- [ ] Add SNOMED-CT autocomplete
- [ ] Add date range picker
- [ ] Add meta-annotation filters
- [ ] Add document type filters
- [ ] Implement filter presets (save/load)
- [ ] Sync filters with URL query params
- [ ] Write unit tests (80% coverage)

**Phase 5.5: Zoom, Pan, and Temporal Analysis**
- [ ] Add D3.js zoom/pan (d3-zoom)
- [ ] Create useTimelineZoom composable
- [ ] Differentiate first mention vs recurring
- [ ] Add concept frequency chart (bar chart)
- [ ] Highlight temporal relationships
- [ ] Write unit tests (80% coverage)

**Phase 5.6: Export Capabilities**
- [ ] Create TimelineExportService (PDF, FHIR, JSON)
- [ ] Create HTML template for PDF
- [ ] Add watermark to PDF exports
- [ ] Implement FHIR R4 export (Composition)
- [ ] Implement JSON export
- [ ] Add export endpoints (POST /export, GET /exports/{id}/download)
- [ ] Create TimelineExportToolbar component
- [ ] Add audit logging for exports
- [ ] Write unit tests (80% coverage)
- [ ] Write integration tests (70% coverage)

**Phase 5.7: Integration Tests & E2E Tests**
- [ ] Write integration tests (timeline API, filter API, export API)
- [ ] Write E2E tests (full timeline workflow)
- [ ] Write performance tests (load time, concurrent users)
- [ ] Write security tests (authentication, RBAC, audit logging)

**Phase 5.8: Documentation, Deployment & Polish**
- [ ] Update DEVELOPMENT.md (API documentation)
- [ ] Update CONTEXT.md (Phase 5 completion)
- [ ] Create database migrations
- [ ] Update docker-compose.yml
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] UI polish (loading states, empty states, error states)
- [ ] Performance optimization (debounce, lazy loading, caching)
- [ ] Create admin panel for timeline settings

---

**Status**: Ready for review and approval
**Next Steps**: Create task breakdown after technical plan approval
**Dependencies**: Base Application (MVP), Patient Search Module (Sprint 1 complete)
**Estimated Effort**: 120 hours over 4 weeks (8 phases × 15 hours)
