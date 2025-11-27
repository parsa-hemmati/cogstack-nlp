---
name: sprint-2-timeline
status: completed
created: 2025-11-25T19:22:50Z
progress: 100%
prd: .claude/prds/sprint-2-timeline.md
github: https://github.com/parsa-hemmati/cogstack-nlp/issues/12
---

# Epic: Sprint 2 - Timeline View Module

## Overview

Implement a chronological patient timeline visualization that displays documents, clinical concepts, and temporal patterns. The module enables clinicians to understand disease trajectories, identify temporal relationships, and export clinical summaries.

**Key Capabilities**:
- Chronological document timeline with zoom/pan
- Clinical concept markers (conditions, medications, procedures)
- Meta-annotation filtering (Negation, Temporality, Experiencer)
- Export to PDF, FHIR R4, and JSON
- Comprehensive audit logging

## Architecture Decisions

### Core Technical Decisions
- **Visualization Library**: D3.js v7 for SVG timeline rendering (best-in-class for temporal data)
- **State Management**: Pinia store for timeline data caching
- **Backend API**: FastAPI endpoints following existing patterns from Sprint 1
- **Caching**: Redis for timeline data (patient histories can be large)
- **Export**: Server-side PDF generation with WeasyPrint, FHIR with fhir.resources

### Technology Choices
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Timeline Rendering | D3.js v7 | Industry standard, excellent time scales |
| Frontend Framework | Vue 3 + Vuetify | Consistent with base app |
| Backend | FastAPI | Async support, existing patterns |
| PDF Export | WeasyPrint | Python-native, HTML-to-PDF |
| FHIR Export | fhir.resources | Validated FHIR R4 resources |

### Design Patterns
- **Composable Pattern**: `useTimeline()`, `useTimelineFilters()`, `useTimelineExport()`
- **Service Layer**: `TimelineService` for data aggregation
- **Repository Pattern**: Elasticsearch queries for temporal data

## Technical Approach

### Frontend Components
1. **TimelineView.vue** - Main container with D3 timeline canvas
2. **TimelineChart.vue** - D3.js SVG timeline with zoom/pan (EXISTS - extend)
3. **TimelineControls.vue** - Filter panel, date range, concept filters (EXISTS - extend)
4. **PatientHeader.vue** - Patient demographics display (EXISTS)
5. **DocumentPreview.vue** - Click-to-view document modal
6. **ExportPanel.vue** - PDF/FHIR/JSON export controls

### Backend Services
1. **GET /api/v1/timeline/{patient_id}** - Fetch timeline data with filters
2. **GET /api/v1/timeline/{patient_id}/documents** - Document list with dates
3. **GET /api/v1/timeline/{patient_id}/concepts** - Clinical concepts over time
4. **POST /api/v1/timeline/{patient_id}/export** - Generate export (PDF/FHIR/JSON)
5. **TimelineService** - Aggregation logic, temporal pattern detection
6. **TimelineExportService** - PDF, FHIR, JSON generation

### Infrastructure
- Leverage existing PostgreSQL (documents, annotations tables)
- Leverage existing Redis (query caching)
- Leverage existing audit logging service
- No new infrastructure required

## Implementation Strategy

### Development Phases
1. **Phase 2.1**: Backend API (timeline data retrieval, filtering)
2. **Phase 2.2**: Frontend Timeline (D3.js visualization, zoom/pan)
3. **Phase 2.3**: Concept Timeline (clinical markers, meta-annotation filters)
4. **Phase 2.4**: Export Capabilities (PDF, FHIR, JSON)
5. **Phase 2.5**: Integration & Testing

### Risk Mitigation
- **D3.js Complexity**: Start with existing TimelineChart.vue, extend incrementally
- **Large Datasets**: Implement pagination and lazy loading for 10+ year histories
- **Export Performance**: Generate exports asynchronously with status polling

### Testing Approach
- Unit tests: Timeline service, export service
- Integration tests: API endpoints with mock data
- E2E tests: Full timeline workflow in Playwright
- Visual regression: D3.js timeline rendering

## Task Breakdown Preview

High-level task categories (max 10 tasks):

- [ ] **Task 1: Timeline API Endpoints** - Backend routes, schemas, service layer
- [ ] **Task 2: Timeline Data Service** - Document/concept aggregation, caching
- [ ] **Task 3: D3.js Timeline Component** - Extend TimelineChart.vue with full zoom/pan
- [ ] **Task 4: Concept Markers** - Clinical concept rendering on timeline
- [ ] **Task 5: Filter Panel** - Date range, concept type, meta-annotation filters
- [ ] **Task 6: Document Preview** - Click document to view full text
- [ ] **Task 7: PDF Export** - Timeline to PDF with WeasyPrint
- [ ] **Task 8: FHIR Export** - Timeline to FHIR Composition resource
- [ ] **Task 9: Audit Logging** - Timeline view/export logging
- [ ] **Task 10: Integration Testing** - E2E tests, performance validation

## Dependencies

### External Service Dependencies
- PostgreSQL (documents, annotations) - EXISTS
- Redis (caching) - EXISTS
- Elasticsearch (temporal queries) - EXISTS

### Internal Team Dependencies
- Sprint 1 Patient Search must be complete (patient selection)
- Base application audit logging must be functional

### Prerequisite Work
- Patient search returns patient_id for timeline navigation
- Documents are indexed with document_date field
- Annotations include meta-annotation fields

## Success Criteria (Technical)

### Performance Benchmarks
- Timeline load: < 2 seconds for 5-year patient history
- Zoom/pan: < 100ms response (60fps smooth scrolling)
- Export generation: < 10 seconds for PDF, < 5 seconds for JSON/FHIR

### Quality Gates
- Test coverage: ≥ 85% backend, ≥ 80% frontend
- All P0 requirements implemented
- Audit logging verified for all PHI access
- WCAG 2.1 AA accessibility compliance

### Acceptance Criteria
- [ ] Clinician can view chronological patient timeline
- [ ] Timeline shows document markers and clinical concepts
- [ ] Filters work for date range, concept type, meta-annotations
- [ ] PDF export generates readable clinical summary
- [ ] FHIR export produces valid R4 Composition resource
- [ ] All timeline views logged to audit trail

## Estimated Effort

### Overall Timeline
- **Total Duration**: 4 weeks (~120 hours)
- **Parallel Tasks**: 5 (Tasks 1-2 backend, Tasks 3-6 frontend, parallel)
- **Critical Path**: API → Timeline Component → Export

### Resource Requirements
- 1 Backend developer (Python/FastAPI)
- 1 Frontend developer (Vue 3/D3.js)
- Shared QA for testing

### Critical Path Items
1. Timeline API must be complete before frontend integration
2. D3.js timeline must work before export can render
3. Audit logging must be verified before production deployment

## Tasks Created
- [ ] 001.md - Timeline API Endpoints (parallel: false)
- [ ] 002.md - Timeline Data Service (parallel: false, depends: 001)
- [ ] 003.md - D3.js Timeline Component (parallel: true)
- [ ] 004.md - Concept Markers (parallel: true, depends: 003)
- [ ] 005.md - Filter Panel (parallel: true)
- [ ] 006.md - Document Preview (parallel: true)
- [ ] 007.md - PDF Export (parallel: false, depends: 002)
- [ ] 008.md - FHIR Export (parallel: false, depends: 002)
- [ ] 009.md - Audit Logging Integration (parallel: true)
- [ ] 010.md - Integration Testing (parallel: false, depends: all)

Total tasks: 10
Parallel tasks: 5
Sequential tasks: 5
Estimated total effort: 120 hours
