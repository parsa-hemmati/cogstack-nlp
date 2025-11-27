# Tasks: Timeline View Module (Sprint 2)

**Plan Reference**: `.specify/plans/sprint-2-timeline-view-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-2-timeline-view.md` (v1.0.0)
**Estimated Total Time**: 144 hours (5 weeks, 20% buffer included)
**Dependencies**:
- Base Application (MVP) completed
- Patient Search Module operational
- PostgreSQL with documents/annotations tables
- Redis cache running
- CogStack-ModelServe operational

---

## Phase 1: Core Timeline API (30 hours)

### Task 1.1: Create Timeline Pydantic Schemas

**Goal**: Define request/response schemas for timeline API using Pydantic

**Phase**: Phase 1
**Dependencies**: None
**Estimated Time**: 2 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/schemas/test_timeline_schemas.py`
   - Test: TimelineQueryParams validation (patient_id, date ranges)
   - Test: TimelineDocument schema with all fields
   - Test: TimelineConcept schema with meta-annotations
   - Test: TimelineResponse schema structure
2. **Implement**
   - Create `backend/app/schemas/timeline.py`
   - Define `TimelineQueryParams` with Optional filters
   - Define `TimelineDocument` schema
   - Define `TimelineConcept` with ConceptOccurrence
   - Define `TimelineResponse` with metadata
3. **Verify**
   - Run: `pytest tests/unit/schemas/test_timeline_schemas.py`

**Acceptance Criteria**:
- [ ] TimelineQueryParams validates date format (ISO 8601)
- [ ] TimelineDocument includes all required fields (id, title, type, date)
- [ ] TimelineConcept includes meta_annotations dict
- [ ] TimelineResponse includes date_range calculation
- [ ] Tests passing (≥90% coverage)

**Test Coverage**:
- Unit tests: 12 tests (validation, serialization, edge cases)

**Files Created/Modified**:
- `backend/app/schemas/timeline.py` - Timeline schemas
- `tests/unit/schemas/test_timeline_schemas.py` - Schema tests

---

### Task 1.2: Create Timeline Service - Document Retrieval

**Goal**: Implement service method to fetch documents for patient timeline

**Phase**: Phase 1
**Dependencies**: Task 1.1
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_timeline_service.py`
   - Test: Get documents for valid patient (returns list)
   - Test: Filter by date range
   - Test: Filter by document type
   - Test: Document count aggregation
   - Test: Empty result for patient with no documents
2. **Implement**
   - Create `backend/app/services/timeline_service.py`
   - Create `TimelineService` class with async methods
   - Implement `_get_timeline_documents()` method
   - Build SQL query with JOINs (Document → Task → Project)
   - Apply filters (date range, document type)
   - Aggregate annotation count
3. **Verify**
   - Run: `pytest tests/unit/services/test_timeline_service.py`

**Acceptance Criteria**:
- [ ] Service returns documents for valid patient_id
- [ ] Date range filter works correctly
- [ ] Document type filter works correctly
- [ ] Annotation count aggregated correctly
- [ ] Empty list returned for patient with no documents
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 8 tests (retrieval, filters, edge cases)
- Integration tests: None yet (will add in Task 1.5)

**Files Created/Modified**:
- `backend/app/services/timeline_service.py` - Timeline service
- `tests/unit/services/test_timeline_service.py` - Service tests

---

### Task 1.3: Create Timeline Service - Concept Retrieval

**Goal**: Implement service method to fetch clinical concepts for patient timeline

**Phase**: Phase 1
**Dependencies**: Task 1.2
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `tests/unit/services/test_timeline_service.py`
   - Test: Get concepts for patient (returns aggregated concepts)
   - Test: Filter by concept type
   - Test: Meta-annotation filtering (exclude negated/family)
   - Test: First/last mentioned dates calculated correctly
   - Test: Occurrence count accurate
2. **Implement**
   - Add `_get_timeline_concepts()` method to `TimelineService`
   - Build SQL query with aggregations (MIN/MAX dates, COUNT)
   - Apply meta-annotation filters (default: exclude negated/family)
   - Group by CUI, preferred_name, concept_type
   - Order by first mentioned date
3. **Verify**
   - Run: `pytest tests/unit/services/test_timeline_service.py`

**Acceptance Criteria**:
- [ ] Service returns aggregated concepts (CUI grouped)
- [ ] First/last mentioned dates correct
- [ ] Occurrence count matches database
- [ ] Meta-annotation filters applied (include_negated=False works)
- [ ] Concept type filter works
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 8 tests (retrieval, aggregation, filters)

**Files Created/Modified**:
- `backend/app/services/timeline_service.py` - Updated with concept retrieval
- `tests/unit/services/test_timeline_service.py` - Updated with concept tests

---

### Task 1.4: Create Timeline Service - Main Timeline Method

**Goal**: Orchestrate document and concept retrieval into complete timeline response

**Phase**: Phase 1
**Dependencies**: Task 1.3
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `tests/unit/services/test_timeline_service.py`
   - Test: `get_patient_timeline()` returns complete TimelineResponse
   - Test: Date range calculated from documents
   - Test: Metadata includes counts
   - Test: All filters applied correctly
2. **Implement**
   - Add `get_patient_timeline()` method to `TimelineService`
   - Call `_get_timeline_documents()` and `_get_timeline_concepts()`
   - Calculate date_range from documents
   - Build metadata (document_count, concept_count, generated_at)
   - Return `TimelineResponse` schema
3. **Verify**
   - Run: `pytest tests/unit/services/test_timeline_service.py`

**Acceptance Criteria**:
- [ ] Returns complete TimelineResponse
- [ ] Date range calculated correctly (earliest/latest)
- [ ] Metadata counts accurate
- [ ] All query parameters passed to sub-methods
- [ ] Tests passing (≥90% coverage)

**Test Coverage**:
- Unit tests: 6 tests (orchestration, metadata, integration)

**Files Created/Modified**:
- `backend/app/services/timeline_service.py` - Updated with main method
- `tests/unit/services/test_timeline_service.py` - Updated with orchestration tests

---

### Task 1.5: Create Timeline API Endpoint

**Goal**: FastAPI endpoint for GET /api/timeline/{patient_id}

**Phase**: Phase 1
**Dependencies**: Task 1.4
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_timeline_api.py`
   - Test: GET /api/timeline/{patient_id} returns 200
   - Test: Response matches TimelineResponse schema
   - Test: Query parameters applied (date range, filters)
   - Test: 404 for invalid patient_id
   - Test: 403 for unauthorized user
2. **Implement**
   - Create `backend/app/api/v1/endpoints/timeline.py`
   - Define `router = APIRouter()`
   - Create `GET /api/timeline/{patient_id}` endpoint
   - Inject dependencies: `TimelineService`, `current_user`
   - Validate patient_id exists
   - Call `timeline_service.get_patient_timeline()`
   - Return JSON response
3. **Register Router**
   - Add router to `backend/app/api/v1/api.py`
4. **Verify**
   - Run: `pytest tests/integration/test_timeline_api.py`

**Acceptance Criteria**:
- [ ] Endpoint returns 200 for valid patient
- [ ] Response matches TimelineResponse schema
- [ ] Query parameters work (start_date, end_date, document_types)
- [ ] 404 returned for non-existent patient
- [ ] Authentication required (403 if not logged in)
- [ ] Tests passing (≥80% coverage)

**Test Coverage**:
- Integration tests: 8 tests (happy path, error cases, auth)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/timeline.py` - Timeline API endpoint
- `backend/app/api/v1/api.py` - Register timeline router
- `tests/integration/test_timeline_api.py` - API integration tests

---

### Task 1.6: Add Timeline Audit Logging

**Goal**: Log all timeline API requests for HIPAA/GDPR compliance

**Phase**: Phase 1
**Dependencies**: Task 1.5
**Estimated Time**: 2 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `tests/integration/test_timeline_api.py`
   - Test: Audit log entry created on timeline access
   - Test: Log includes user_id, patient_id, timestamp
   - Test: Log includes query parameters used
2. **Implement**
   - Update timeline endpoint to call audit service
   - Create audit log entry with action="VIEW_TIMELINE"
   - Include patient_id, user_id, filters used
3. **Verify**
   - Run: `pytest tests/integration/test_timeline_api.py`
   - Verify audit_logs table has entries

**Acceptance Criteria**:
- [ ] Audit log created on every timeline request
- [ ] Log includes all required fields
- [ ] Tests verify audit log creation
- [ ] No performance impact (<10ms overhead)

**Test Coverage**:
- Integration tests: 3 tests (audit log verification)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/timeline.py` - Updated with audit logging
- `tests/integration/test_timeline_api.py` - Updated with audit tests

---

### Task 1.7: Add Redis Caching for Timeline Data

**Goal**: Cache timeline responses to reduce database queries

**Phase**: Phase 1
**Dependencies**: Task 1.5
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `tests/integration/test_timeline_api.py`
   - Test: First request hits database
   - Test: Second request uses cache (faster response)
   - Test: Cache TTL respected (5 minutes)
   - Test: Cache key includes patient_id and filters
2. **Implement**
   - Update `TimelineService` to check Redis cache first
   - Cache key format: `timeline:{patient_id}:{filters_hash}`
   - Cache TTL: 300 seconds (5 minutes)
   - Store JSON-serialized TimelineResponse
   - Cache invalidation on new document upload
3. **Verify**
   - Run: `pytest tests/integration/test_timeline_api.py`
   - Measure response time difference (cached vs non-cached)

**Acceptance Criteria**:
- [ ] Cache hit on second request
- [ ] Cache key includes patient_id and filters
- [ ] TTL set to 5 minutes
- [ ] Cache invalidated on document upload
- [ ] Tests verify caching behavior
- [ ] Response time <100ms for cached requests

**Test Coverage**:
- Integration tests: 5 tests (cache hit/miss, TTL, invalidation)

**Files Created/Modified**:
- `backend/app/services/timeline_service.py` - Updated with caching
- `tests/integration/test_timeline_api.py` - Updated with cache tests

---

### Task 1.8: Create OpenAPI Documentation for Timeline API

**Goal**: Generate API documentation for timeline endpoints

**Phase**: Phase 1
**Dependencies**: Task 1.5
**Estimated Time**: 1 hour

**Steps**:
1. **Add OpenAPI metadata**
   - Add docstrings to timeline endpoint
   - Add response model: `response_model=TimelineResponse`
   - Add status codes: `status.HTTP_200_OK`, `status.HTTP_404_NOT_FOUND`
   - Add tags: `tags=["timeline"]`
   - Add description and examples
2. **Verify**
   - Visit http://localhost:8000/docs
   - Check timeline endpoint visible
   - Check request/response schemas documented

**Acceptance Criteria**:
- [ ] Timeline endpoint appears in Swagger UI
- [ ] Request parameters documented
- [ ] Response schema documented
- [ ] Examples provided
- [ ] Error responses documented (404, 403, 500)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/timeline.py` - Updated with OpenAPI metadata

---

### Task 1.9: Performance Testing - Timeline API

**Goal**: Verify timeline API meets performance requirements

**Phase**: Phase 1
**Dependencies**: Task 1.7
**Estimated Time**: 2 hours

**Steps**:
1. **Create performance test script**
   - Create `tests/performance/test_timeline_performance.py`
   - Seed database with 100 documents, 500 annotations
   - Measure response time for timeline query
   - Test with different document counts (10, 100, 500, 1000)
2. **Run tests**
   - Execute: `pytest tests/performance/test_timeline_performance.py`
   - Record response times
3. **Verify targets**
   - <1 second for <100 documents
   - <3 seconds for 100-500 documents
   - <5 seconds for >500 documents

**Acceptance Criteria**:
- [ ] Timeline query <1 second for 100 documents
- [ ] Timeline query <3 seconds for 500 documents
- [ ] Cached requests <100ms
- [ ] Performance test script automated

**Test Coverage**:
- Performance tests: 4 tests (different dataset sizes)

**Files Created/Modified**:
- `tests/performance/test_timeline_performance.py` - Performance tests

---

### Task 1.10: Database Index Optimization for Timeline Queries

**Goal**: Add database indexes to optimize timeline queries

**Phase**: Phase 1
**Dependencies**: Task 1.9
**Estimated Time**: 2 hours

**Steps**:
1. **Analyze query performance**
   - Run EXPLAIN ANALYZE on timeline queries
   - Identify slow queries (seq scans)
2. **Create migration**
   - Create Alembic migration: `alembic revision -m "add timeline indexes"`
   - Add index on `documents.uploaded_at`
   - Add index on `documents.processing_status`
   - Add composite index on `annotations(cui, concept_type)`
3. **Apply migration**
   - Run: `alembic upgrade head`
4. **Verify improvement**
   - Re-run EXPLAIN ANALYZE
   - Verify index scans instead of seq scans
   - Re-run performance tests

**Acceptance Criteria**:
- [ ] Indexes created successfully
- [ ] Query plans use indexes (no seq scans)
- [ ] Performance improved (≥30% faster)
- [ ] Migration reversible

**Files Created/Modified**:
- `backend/alembic/versions/XXX_add_timeline_indexes.py` - Migration

---

## Phase 2: Frontend Timeline Visualization (40 hours)

### Task 2.1: Create TimelineView Component Structure

**Goal**: Create Vue 3 component structure for timeline view

**Phase**: Phase 2
**Dependencies**: Phase 1 completed
**Estimated Time**: 2 hours

**Steps**:
1. **Create component files**
   - Create `webapp/src/views/TimelineView.vue`
   - Create `webapp/src/components/timeline/TimelineChart.vue`
   - Create `webapp/src/components/timeline/TimelineControls.vue`
   - Create `webapp/src/components/timeline/PatientHeader.vue`
2. **Setup basic structure**
   - Add Vue template, script setup, style sections
   - Add props/emits definitions
   - Add Composition API imports
3. **Register routes**
   - Add route in `webapp/src/router/index.ts`: `/timeline/:patientId`

**Acceptance Criteria**:
- [ ] All component files created
- [ ] Route registered
- [ ] Components accessible at /timeline/:patientId
- [ ] No console errors

**Files Created/Modified**:
- `webapp/src/views/TimelineView.vue` - Main timeline view
- `webapp/src/components/timeline/TimelineChart.vue` - D3.js chart component
- `webapp/src/components/timeline/TimelineControls.vue` - Filter controls
- `webapp/src/components/timeline/PatientHeader.vue` - Patient info header
- `webapp/src/router/index.ts` - Add timeline route

---

### Task 2.2: Create Timeline Pinia Store

**Goal**: Pinia store for timeline state management

**Phase**: Phase 2
**Dependencies**: Task 2.1
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `webapp/tests/unit/stores/timeline.test.ts`
   - Test: `fetchTimeline()` action calls API
   - Test: State updated after successful fetch
   - Test: Error handling
   - Test: Filters applied correctly
2. **Implement**
   - Create `webapp/src/stores/timeline.ts`
   - Define state: `timelineData`, `loading`, `error`, `filters`
   - Define actions: `fetchTimeline()`, `applyFilters()`, `clearFilters()`
   - Define getters: `filteredDocuments`, `filteredConcepts`
3. **Verify**
   - Run: `npm run test:unit`

**Acceptance Criteria**:
- [ ] Store created with state/actions/getters
- [ ] `fetchTimeline()` calls API correctly
- [ ] State updates on success
- [ ] Error state set on failure
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 10 tests (actions, state mutations, getters)

**Files Created/Modified**:
- `webapp/src/stores/timeline.ts` - Timeline Pinia store
- `webapp/tests/unit/stores/timeline.test.ts` - Store tests

---

### Task 2.3: Implement TimelineView Main Component

**Goal**: Main timeline view component with API integration

**Phase**: Phase 2
**Dependencies**: Task 2.2
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `webapp/tests/unit/views/TimelineView.test.ts`
   - Test: Component mounts without errors
   - Test: Fetches timeline on mount
   - Test: Loading state shown during fetch
   - Test: Error state shown on failure
2. **Implement**
   - Add template structure (patient header, controls, chart)
   - Add script setup with Composition API
   - Use `useTimelineStore()` to fetch data
   - Use `useRoute()` to get patientId from URL
   - Add loading/error states
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Visit /timeline/:patientId in browser

**Acceptance Criteria**:
- [ ] Component renders without errors
- [ ] Timeline data fetched on mount
- [ ] Loading spinner shown during fetch
- [ ] Error message shown on failure
- [ ] Tests passing (≥80% coverage)

**Test Coverage**:
- Unit tests: 8 tests (mount, fetch, states)

**Files Created/Modified**:
- `webapp/src/views/TimelineView.vue` - Implemented view
- `webapp/tests/unit/views/TimelineView.test.ts` - View tests

---

### Task 2.4: Install and Configure D3.js

**Goal**: Install D3.js and create timeline chart foundation

**Phase**: Phase 2
**Dependencies**: Task 2.3
**Estimated Time**: 2 hours

**Steps**:
1. **Install D3.js**
   - Run: `npm install d3 @types/d3`
   - Add to `package.json` dependencies
2. **Create chart composable**
   - Create `webapp/src/composables/useTimelineChart.ts`
   - Import D3: `import * as d3 from 'd3'`
   - Create SVG setup function
   - Create time scale function
   - Export composable hooks
3. **Test D3 import**
   - Create simple test chart
   - Verify no import errors

**Acceptance Criteria**:
- [ ] D3.js installed (v7+)
- [ ] TypeScript types available
- [ ] Chart composable created
- [ ] No import errors

**Files Created/Modified**:
- `webapp/package.json` - Add D3 dependency
- `webapp/src/composables/useTimelineChart.ts` - Chart composable

---

### Task 2.5: Implement D3.js Time Scale and Axis

**Goal**: Render time scale axis for timeline

**Phase**: Phase 2
**Dependencies**: Task 2.4
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `webapp/tests/unit/components/TimelineChart.test.ts`
   - Test: SVG canvas created
   - Test: Time scale domain set from data
   - Test: X-axis rendered with date ticks
2. **Implement**
   - Update `TimelineChart.vue` to use D3
   - Create SVG element in template
   - Setup D3 time scale: `d3.scaleTime()`
   - Calculate domain from timeline date range
   - Create x-axis: `d3.axisBottom(xScale)`
   - Render axis to SVG
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Check axis visible in browser

**Acceptance Criteria**:
- [ ] SVG canvas rendered (width 1000px, height 400px)
- [ ] Time scale domain matches timeline data
- [ ] X-axis shows date ticks (monthly intervals)
- [ ] Axis labels formatted (e.g., "Jan 2023")
- [ ] Tests passing (≥80% coverage)

**Test Coverage**:
- Unit tests: 6 tests (SVG, scale, axis)

**Files Created/Modified**:
- `webapp/src/components/timeline/TimelineChart.vue` - Updated with D3 axis
- `webapp/tests/unit/components/TimelineChart.test.ts` - Chart tests

---

### Task 2.6: Render Document Markers on Timeline

**Goal**: Render document events as circles on timeline

**Phase**: Phase 2
**Dependencies**: Task 2.5
**Estimated Time**: 5 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `TimelineChart.test.ts`
   - Test: Document markers rendered (circles)
   - Test: Marker position matches date
   - Test: Marker color matches document type
   - Test: Click event emitted
2. **Implement**
   - Add `renderDocuments()` function to chart
   - Use `d3.selectAll('.document-marker').data(documents)`
   - Create circles with `.enter().append('circle')`
   - Set cx position using `xScale(new Date(d.date))`
   - Set cy position: 100 (fixed row)
   - Set radius: 8px
   - Set fill color based on document type
   - Add click handler: `emit('select-document', document)`
   - Add mouseover tooltip
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Check markers visible and clickable

**Acceptance Criteria**:
- [ ] Document markers rendered as circles
- [ ] Marker positions match dates
- [ ] Colors match document types (blue=note, green=lab, red=discharge)
- [ ] Click event emitted with document data
- [ ] Tooltip shows document title on hover
- [ ] Tests passing (≥80% coverage)

**Test Coverage**:
- Unit tests: 8 tests (rendering, positioning, events)

**Files Created/Modified**:
- `webapp/src/components/timeline/TimelineChart.vue` - Updated with document rendering
- `webapp/tests/unit/components/TimelineChart.test.ts` - Updated with document tests

---

### Task 2.7: Render Concept Event Bars on Timeline

**Goal**: Render clinical concept events as horizontal bars

**Phase**: Phase 2
**Dependencies**: Task 2.6
**Estimated Time**: 5 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `TimelineChart.test.ts`
   - Test: Concept bars rendered (rectangles)
   - Test: Bar start/end positions match first/last mentioned dates
   - Test: Bar color matches concept type
   - Test: Bars stacked by type (conditions=row1, meds=row2, procedures=row3)
   - Test: Click event emitted
2. **Implement**
   - Add `renderConcepts()` function to chart
   - Use `d3.selectAll('.concept-marker').data(concepts)`
   - Create rectangles with `.enter().append('rect')`
   - Set x position: `xScale(new Date(d.first_mentioned))`
   - Set width: `xScale(new Date(d.last_mentioned)) - xScale(new Date(d.first_mentioned))`
   - Set y position based on concept type (condition=150, medication=200, procedure=250)
   - Set height: 20px
   - Set fill color based on type (red=condition, blue=medication, green=procedure)
   - Add opacity: 0.7
   - Add click handler: `emit('select-concept', concept)`
   - Add tooltip with concept name
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Check concept bars visible

**Acceptance Criteria**:
- [ ] Concept bars rendered as rectangles
- [ ] Bar width matches time span (first to last mentioned)
- [ ] Colors match concept types
- [ ] Bars stacked by type (no overlap within type)
- [ ] Click event emitted with concept data
- [ ] Tooltip shows concept name on hover
- [ ] Tests passing (≥80% coverage)

**Test Coverage**:
- Unit tests: 10 tests (rendering, positioning, stacking, events)

**Files Created/Modified**:
- `webapp/src/components/timeline/TimelineChart.vue` - Updated with concept rendering
- `webapp/tests/unit/components/TimelineChart.test.ts` - Updated with concept tests

---

### Task 2.8: Implement Zoom and Pan Controls

**Goal**: Add D3 zoom behavior for interactive timeline navigation

**Phase**: Phase 2
**Dependencies**: Task 2.7
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `TimelineChart.test.ts`
   - Test: Zoom behavior attached to SVG
   - Test: Scale extent limits (1x to 10x)
   - Test: Zoom updates marker positions
2. **Implement**
   - Create D3 zoom behavior: `d3.zoom()`
   - Set scale extent: `.scaleExtent([1, 10])`
   - Attach to SVG: `svg.call(zoom)`
   - On zoom event: update xScale and re-render markers/bars
   - Debounce zoom events (100ms) for performance
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Test mouse wheel zoom and pan

**Acceptance Criteria**:
- [ ] Zoom behavior enabled (mouse wheel)
- [ ] Pan behavior enabled (click and drag)
- [ ] Scale limited to 1x-10x
- [ ] Markers/bars update on zoom
- [ ] Performance acceptable (no lag)
- [ ] Tests passing (≥75% coverage)

**Test Coverage**:
- Unit tests: 5 tests (zoom behavior, scale limits)

**Files Created/Modified**:
- `webapp/src/components/timeline/TimelineChart.vue` - Updated with zoom
- `webapp/tests/unit/components/TimelineChart.test.ts` - Updated with zoom tests

---

### Task 2.9: Implement TimelineControls Component

**Goal**: Filter controls for timeline (date range, document type, concept type)

**Phase**: Phase 2
**Dependencies**: Task 2.8
**Estimated Time**: 5 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `webapp/tests/unit/components/TimelineControls.test.ts`
   - Test: Component renders all filter controls
   - Test: Date range inputs emit update
   - Test: Document type filter emits update
   - Test: Concept type filter emits update
   - Test: Meta-annotation checkboxes emit update
2. **Implement**
   - Create template with Vuetify components
   - Add date range inputs (v-text-field type="date")
   - Add document type filter (v-select)
   - Add concept type filter (v-select)
   - Add meta-annotation checkboxes (include_negated, include_family)
   - Emit events on filter changes
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Test filter interactions

**Acceptance Criteria**:
- [ ] All filter controls rendered
- [ ] Date range inputs work
- [ ] Multi-select filters work
- [ ] Checkboxes work
- [ ] Events emitted with filter values
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 10 tests (rendering, interactions, events)

**Files Created/Modified**:
- `webapp/src/components/timeline/TimelineControls.vue` - Implemented controls
- `webapp/tests/unit/components/TimelineControls.test.ts` - Controls tests

---

### Task 2.10: Connect Filters to Timeline Store

**Goal**: Wire filter controls to Pinia store and API

**Phase**: Phase 2
**Dependencies**: Task 2.9
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `webapp/tests/unit/stores/timeline.test.ts`
   - Test: `applyFilters()` updates store state
   - Test: Timeline re-fetched with new filters
2. **Implement**
   - Update TimelineView to listen to filter events
   - Call `timelineStore.applyFilters()` on filter change
   - Re-fetch timeline data with new parameters
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Test filter changes update timeline

**Acceptance Criteria**:
- [ ] Filter changes trigger API re-fetch
- [ ] Timeline updates with filtered data
- [ ] Loading state shown during re-fetch
- [ ] Tests passing

**Test Coverage**:
- Integration tests: 5 tests (filter → API → update)

**Files Created/Modified**:
- `webapp/src/views/TimelineView.vue` - Updated with filter handling
- `webapp/tests/unit/stores/timeline.test.ts` - Updated with filter tests

---

### Task 2.11: Add View Mode Toggle (Document/Concept/Combined)

**Goal**: Toggle between document-only, concept-only, and combined views

**Phase**: Phase 2
**Dependencies**: Task 2.10
**Estimated Time**: 2 hours

**Steps**:
1. **Write tests**
   - Test: View mode toggle renders
   - Test: Document-only view hides concepts
   - Test: Concept-only view hides documents
   - Test: Combined view shows both
2. **Implement**
   - Add v-btn-toggle to TimelineControls
   - Emit view-mode event
   - Update TimelineChart to conditionally render markers/bars
3. **Verify**
   - Manual: Test view mode toggle

**Acceptance Criteria**:
- [ ] View mode toggle works
- [ ] Document-only view shows only documents
- [ ] Concept-only view shows only concepts
- [ ] Combined view shows both

**Files Created/Modified**:
- `webapp/src/components/timeline/TimelineControls.vue` - Add view mode toggle
- `webapp/src/components/timeline/TimelineChart.vue` - Conditional rendering

---

## Phase 3: Export Functionality (30 hours)

### Task 3.1: Create Timeline Export Service (Backend)

**Goal**: Service to generate timeline exports in PDF/JSON/FHIR

**Phase**: Phase 3
**Dependencies**: Phase 1 completed
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests**
   - Create `tests/unit/services/test_timeline_export_service.py`
   - Test: PDF export generates valid PDF
   - Test: JSON export matches schema
   - Test: FHIR export generates Bundle
2. **Implement**
   - Create `backend/app/services/timeline_export_service.py`
   - Implement `export_pdf()` using ReportLab
   - Implement `export_json()` with JSON serialization
   - Implement `export_fhir()` using fhir.resources
3. **Verify**
   - Run: `pytest tests/unit/services/test_timeline_export_service.py`

**Acceptance Criteria**:
- [ ] PDF export generates valid PDF (verified with PyPDF2)
- [ ] JSON export valid JSON
- [ ] FHIR export valid FHIR R4 Bundle
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 12 tests (PDF, JSON, FHIR generation)

**Files Created/Modified**:
- `backend/app/services/timeline_export_service.py` - Export service
- `tests/unit/services/test_timeline_export_service.py` - Export tests

---

### Task 3.2: Implement PDF Export with ReportLab

**Goal**: Generate PDF timeline report with documents and concepts

**Phase**: Phase 3
**Dependencies**: Task 3.1
**Estimated Time**: 6 hours

**Steps**:
1. **Install dependencies**
   - Add `reportlab` to `requirements.txt`
   - Run: `pip install reportlab`
2. **Implement PDF generation**
   - Create PDF template with header/footer
   - Add patient information section
   - Add documents section (table format)
   - Add concepts section (grouped by type)
   - Add page numbering
3. **Test**
   - Generate sample PDF
   - Verify layout and formatting

**Acceptance Criteria**:
- [ ] PDF generated successfully
- [ ] Header includes patient ID, date range
- [ ] Documents table formatted correctly
- [ ] Concepts grouped by type
- [ ] Page numbers on all pages
- [ ] PDF opens without errors

**Files Created/Modified**:
- `backend/app/services/timeline_export_service.py` - Updated with PDF logic
- `backend/requirements.txt` - Add reportlab

---

### Task 3.3: Implement FHIR R4 Export

**Goal**: Generate FHIR R4 Bundle with DocumentReference and Condition resources

**Phase**: Phase 3
**Dependencies**: Task 3.1
**Estimated Time**: 6 hours

**Steps**:
1. **Install dependencies**
   - Add `fhir.resources` to `requirements.txt`
   - Run: `pip install fhir.resources`
2. **Implement FHIR export**
   - Create `FHIRExportService` class
   - Map documents to DocumentReference resources
   - Map concepts to Condition/MedicationStatement resources
   - Create Bundle with all resources
3. **Validate FHIR output**
   - Use FHIR validator
   - Verify resource structure

**Acceptance Criteria**:
- [ ] FHIR Bundle generated
- [ ] DocumentReference resources valid
- [ ] Condition resources valid
- [ ] FHIR validation passes

**Files Created/Modified**:
- `backend/app/services/fhir_export_service.py` - FHIR export service
- `backend/requirements.txt` - Add fhir.resources

---

### Task 3.4: Create Export API Endpoint

**Goal**: POST /api/timeline/{patient_id}/export endpoint

**Phase**: Phase 3
**Dependencies**: Task 3.3
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests**
   - Create `tests/integration/test_timeline_export_api.py`
   - Test: POST export returns download URL
   - Test: Different export formats (PDF, JSON, FHIR)
   - Test: Export includes filters
2. **Implement**
   - Add `POST /api/timeline/{patient_id}/export` endpoint
   - Accept format parameter
   - Call export service
   - Store export file temporarily
   - Return download URL
3. **Verify**
   - Run: `pytest tests/integration/test_timeline_export_api.py`

**Acceptance Criteria**:
- [ ] Endpoint returns 200 with export_id
- [ ] Download URL valid for 24 hours
- [ ] All formats supported (PDF, JSON, FHIR)
- [ ] Tests passing

**Test Coverage**:
- Integration tests: 6 tests (formats, filters, errors)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/timeline.py` - Add export endpoint
- `tests/integration/test_timeline_export_api.py` - Export API tests

---

### Task 3.5: Implement Frontend Export UI

**Goal**: Export buttons in TimelineControls component

**Phase**: Phase 3
**Dependencies**: Task 3.4
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests**
   - Add tests to `TimelineControls.test.ts`
   - Test: Export buttons render
   - Test: Click triggers API call
   - Test: Download initiated
2. **Implement**
   - Add export buttons to TimelineControls
   - Add `exportTimeline(format)` method
   - Call export API
   - Trigger file download
3. **Verify**
   - Manual: Test export buttons

**Acceptance Criteria**:
- [ ] Export buttons visible
- [ ] PDF export downloads file
- [ ] JSON export downloads file
- [ ] FHIR export downloads file
- [ ] Loading state shown during export

**Files Created/Modified**:
- `webapp/src/components/timeline/TimelineControls.vue` - Add export buttons
- `webapp/src/stores/timeline.ts` - Add export action

---

### Task 3.6: Export File Cleanup Background Task

**Goal**: Celery task to clean up expired exports

**Phase**: Phase 3
**Dependencies**: Task 3.4
**Estimated Time**: 2 hours

**Steps**:
1. **Create Celery task**
   - Create `backend/app/tasks/cleanup_exports.py`
   - Implement `cleanup_expired_exports()` task
   - Delete files older than 24 hours
   - Schedule task to run hourly
2. **Test**
   - Manual: Create export, wait 25 hours, verify deleted

**Acceptance Criteria**:
- [ ] Celery task created
- [ ] Task deletes files >24 hours old
- [ ] Scheduled to run hourly

**Files Created/Modified**:
- `backend/app/tasks/cleanup_exports.py` - Cleanup task
- `backend/app/core/celery_app.py` - Schedule task

---

### Task 3.7: Export Audit Logging

**Goal**: Log all export operations

**Phase**: Phase 3
**Dependencies**: Task 3.4
**Estimated Time**: 2 hours

**Steps**:
1. **Implement audit logging**
   - Add audit log entry on export
   - Include user_id, patient_id, format, timestamp
2. **Test**
   - Verify audit logs created

**Acceptance Criteria**:
- [ ] Audit log entry created on export
- [ ] All required fields included

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/timeline.py` - Add audit logging

---

### Task 3.8: Export Performance Testing

**Goal**: Verify export generation meets performance targets

**Phase**: Phase 3
**Dependencies**: Task 3.7
**Estimated Time**: 3 hours

**Steps**:
1. **Create performance tests**
   - Test PDF generation time (target: <3 seconds)
   - Test JSON generation time (target: <1 second)
   - Test FHIR generation time (target: <2 seconds)
2. **Optimize if needed**
   - Profile slow operations
   - Add caching where applicable

**Acceptance Criteria**:
- [ ] PDF export <3 seconds
- [ ] JSON export <1 second
- [ ] FHIR export <2 seconds

**Files Created/Modified**:
- `tests/performance/test_export_performance.py` - Performance tests

---

## Phase 4: Testing & Polish (24 hours)

### Task 4.1: E2E Testing with Playwright

**Goal**: End-to-end tests for complete timeline workflow

**Phase**: Phase 4
**Dependencies**: Phase 2, Phase 3 completed
**Estimated Time**: 8 hours

**Steps**:
1. **Setup Playwright**
   - Install: `npm install -D @playwright/test`
   - Create `playwright.config.ts`
2. **Create E2E tests**
   - Create `webapp/tests/e2e/timeline.spec.ts`
   - Test: Navigate to timeline view
   - Test: Timeline loads with data
   - Test: Filter timeline by date range
   - Test: Click document marker → details shown
   - Test: Export timeline to PDF
3. **Run tests**
   - Execute: `npx playwright test`

**Acceptance Criteria**:
- [ ] E2E tests passing
- [ ] Full workflow tested (load → filter → export)
- [ ] Tests run in CI/CD pipeline

**Test Coverage**:
- E2E tests: 8 tests (navigation, interactions, export)

**Files Created/Modified**:
- `webapp/tests/e2e/timeline.spec.ts` - E2E tests
- `playwright.config.ts` - Playwright configuration

---

### Task 4.2: Accessibility Audit (WCAG 2.1 AA)

**Goal**: Ensure timeline UI meets WCAG 2.1 AA standards

**Phase**: Phase 4
**Dependencies**: Phase 2 completed
**Estimated Time**: 4 hours

**Steps**:
1. **Run automated audit**
   - Use axe-core or similar
   - Fix issues found
2. **Manual audit**
   - Test keyboard navigation
   - Test screen reader compatibility
   - Check color contrast ratios
3. **Document results**
   - Create accessibility report

**Acceptance Criteria**:
- [ ] No critical accessibility issues
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast ≥4.5:1

**Files Created/Modified**:
- `docs/accessibility-audit-timeline.md` - Audit report

---

### Task 4.3: Performance Testing (100, 500, 1000 Documents)

**Goal**: Validate timeline performance with large datasets

**Phase**: Phase 4
**Dependencies**: Phase 1 completed
**Estimated Time**: 6 hours

**Steps**:
1. **Create test datasets**
   - Seed database with 100, 500, 1000 documents
   - Add annotations for each document
2. **Run performance tests**
   - Measure API response time
   - Measure frontend render time
3. **Optimize if needed**
   - Add pagination if >500 documents
   - Add virtualization for markers

**Acceptance Criteria**:
- [ ] API response <1s for 100 docs
- [ ] API response <3s for 500 docs
- [ ] API response <5s for 1000 docs
- [ ] Frontend render <2s for all datasets

**Files Created/Modified**:
- `tests/performance/test_timeline_large_datasets.py` - Performance tests

---

### Task 4.4: Bug Fixes and Polish

**Goal**: Address any bugs found during testing

**Phase**: Phase 4
**Dependencies**: Tasks 4.1-4.3
**Estimated Time**: 6 hours

**Steps**:
1. **Review bug reports**
   - Check GitHub issues
   - Check QA feedback
2. **Fix bugs**
   - Prioritize critical/high bugs
   - Add regression tests
3. **Verify fixes**
   - Re-run all tests

**Acceptance Criteria**:
- [ ] All critical bugs fixed
- [ ] All high priority bugs fixed
- [ ] Regression tests added

---

## Phase 5: Deployment & Monitoring (20 hours)

### Task 5.1: Deploy to Staging Environment

**Goal**: Deploy timeline module to staging for UAT

**Phase**: Phase 5
**Dependencies**: Phase 4 completed
**Estimated Time**: 4 hours

**Steps**:
1. **Build and deploy**
   - Build frontend: `npm run build`
   - Deploy backend to staging
   - Run database migrations
2. **Smoke tests**
   - Verify timeline loads
   - Verify exports work
3. **UAT with pilot users**
   - Schedule UAT sessions
   - Collect feedback

**Acceptance Criteria**:
- [ ] Deployment successful
- [ ] Smoke tests passing
- [ ] UAT scheduled

---

### Task 5.2: Configure Monitoring (Prometheus + Grafana)

**Goal**: Set up monitoring for timeline API

**Phase**: Phase 5
**Dependencies**: Task 5.1
**Estimated Time**: 6 hours

**Steps**:
1. **Add Prometheus metrics**
   - Add counter: `timeline_requests_total`
   - Add histogram: `timeline_request_duration_seconds`
   - Add gauge: `timeline_cache_hit_rate`
2. **Create Grafana dashboard**
   - Panel: Timeline request rate
   - Panel: Timeline response time (p50, p95, p99)
   - Panel: Cache hit rate
   - Panel: Error rate
3. **Configure alerts**
   - Alert: Error rate >5% for 5 minutes
   - Alert: Response time p95 >3 seconds

**Acceptance Criteria**:
- [ ] Metrics exposed at /metrics
- [ ] Grafana dashboard created
- [ ] Alerts configured

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/timeline.py` - Add metrics
- `grafana/dashboards/timeline.json` - Dashboard config

---

### Task 5.3: User Documentation

**Goal**: Create user guide for timeline feature

**Phase**: Phase 5
**Dependencies**: Phase 4 completed
**Estimated Time**: 4 hours

**Steps**:
1. **Create user guide**
   - Document timeline navigation
   - Document filters
   - Document export functionality
   - Add screenshots
2. **Create video tutorial** (optional)
   - Record 5-minute walkthrough

**Acceptance Criteria**:
- [ ] User guide published
- [ ] Screenshots included
- [ ] Clear instructions

**Files Created/Modified**:
- `docs/user-guides/timeline-view.md` - User guide

---

### Task 5.4: Deploy to Production

**Goal**: Production deployment of timeline module

**Phase**: Phase 5
**Dependencies**: Task 5.1, UAT approval
**Estimated Time**: 4 hours

**Steps**:
1. **Pre-deployment checklist**
   - All tests passing
   - UAT sign-off received
   - Rollback plan documented
2. **Deploy**
   - Deploy backend
   - Deploy frontend
   - Run migrations
3. **Post-deployment verification**
   - Run smoke tests
   - Monitor for 48 hours

**Acceptance Criteria**:
- [ ] Production deployment successful
- [ ] Smoke tests passing
- [ ] Monitoring active

---

### Task 5.5: User Training Session

**Goal**: Train clinicians on timeline feature

**Phase**: Phase 5
**Dependencies**: Task 5.4
**Estimated Time**: 2 hours

**Steps**:
1. **Prepare training materials**
   - Slides
   - Demo scenarios
2. **Conduct training**
   - Live demo
   - Q&A session
3. **Collect feedback**
   - Survey users

**Acceptance Criteria**:
- [ ] Training session completed
- [ ] Feedback collected
- [ ] User satisfaction ≥80%

---

## Summary

**Total Tasks**: 45 tasks across 5 phases
**Total Estimated Time**: 144 hours (5 weeks with 20% buffer)

**Phase Breakdown**:
- Phase 1 (API): 30 hours, 10 tasks
- Phase 2 (Frontend): 40 hours, 11 tasks
- Phase 3 (Export): 30 hours, 8 tasks
- Phase 4 (Testing): 24 hours, 4 tasks
- Phase 5 (Deployment): 20 hours, 5 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%
- E2E tests: Critical workflows covered

**Performance Targets Met**:
- API response: <1s for <100 docs, <3s for 500 docs
- Frontend render: <2s
- Export generation: <3s (PDF), <2s (FHIR), <1s (JSON)

**Dependencies Satisfied**:
- Base Application (MVP)
- Patient Search Module
- PostgreSQL, Redis, CogStack-ModelServe
