# Tasks: Patient Search & Discovery (Sprint 1)

**Sprint**: 1
**Duration**: 2 weeks (~60 hours)
**Total Tasks**: 16

---

## Phase 1.1: Backend API (15 hours)

### Task 1.1.1: PatientSearchService

**Goal**: Implement core search orchestration service

**Prerequisites**: Base application setup complete

**Steps**:
1. Create `app/services/patient_search_service.py`
2. Implement `PatientSearchService` class
3. Add `search()` method with query validation
4. Add `get_patient_details()` method
5. Add audit logging calls
6. Write unit tests (5+ tests)

**Acceptance**:
- Service instantiates without errors
- Search method accepts PatientSearchQuery
- Returns PatientSearchResponse schema
- Unit tests pass with 90%+ coverage

**Estimated Time**: 3 hours

---

### Task 1.1.2: MedCATClient

**Goal**: Implement HTTP client for MedCAT concept resolution

**Prerequisites**: MedCAT service running

**Steps**:
1. Create `app/clients/medcat/medcat_client.py`
2. Implement `MedCATClient` class with httpx
3. Add `get_concepts_for_term()` method
4. Add error handling and retries
5. Add response parsing
6. Write unit tests with mocked responses

**Acceptance**:
- Client connects to MedCAT service
- Returns list of Concept objects
- Handles network errors gracefully
- Unit tests pass

**Estimated Time**: 2 hours

---

### Task 1.1.3: ElasticsearchService

**Goal**: Implement Elasticsearch query builder and executor

**Prerequisites**: Elasticsearch cluster running

**Steps**:
1. Create `app/services/elasticsearch_service.py`
2. Implement `ElasticsearchService` class
3. Add `build_search_query()` method
4. Add `search()` method
5. Add response parsing
6. Write unit tests with mocked ES

**Acceptance**:
- Service connects to Elasticsearch
- Builds valid ES queries
- Returns formatted results
- Unit tests pass

**Estimated Time**: 3 hours

---

### Task 1.1.4: Search API Endpoint

**Goal**: Create REST API endpoint for patient search

**Prerequisites**: Tasks 1.1.1-1.1.3 complete

**Steps**:
1. Create `app/api/v1/patients.py`
2. Add `POST /api/v1/patients/search` endpoint
3. Add request validation (Pydantic)
4. Add authentication dependency
5. Add rate limiting
6. Write integration tests

**Acceptance**:
- Endpoint accepts POST with JSON body
- Returns 200 with results on success
- Returns 400 on validation error
- Returns 401 without auth
- Integration tests pass

**Estimated Time**: 3 hours

---

### Task 1.1.5: Patient Details Endpoint

**Goal**: Create endpoint for single patient details

**Prerequisites**: Task 1.1.1 complete

**Steps**:
1. Add `GET /api/v1/patients/{mrn}` endpoint
2. Add authentication
3. Add audit logging
4. Write integration tests

**Acceptance**:
- Returns full patient with annotations
- Returns 404 if not found
- Logs access to audit trail
- Integration tests pass

**Estimated Time**: 2 hours

---

### Task 1.1.6: Document Endpoint

**Goal**: Create endpoint for document retrieval with highlighting

**Prerequisites**: Task 1.1.1 complete

**Steps**:
1. Add `GET /api/v1/documents/{documentId}` endpoint
2. Add `highlightCUI` query parameter
3. Add concept highlighting logic
4. Write integration tests

**Acceptance**:
- Returns document with text
- Highlights specified CUI
- Returns 404 if not found
- Integration tests pass

**Estimated Time**: 2 hours

---

## Phase 1.2: Meta-Annotation Filtering (15 hours)

### Task 1.2.1: Temporal Filter

**Goal**: Implement current vs historical condition filtering

**Prerequisites**: Task 1.1.3 complete

**Steps**:
1. Update `build_search_query()` for temporal filter
2. Add ES nested query for `metaAnnotations.temporality`
3. Test with sample data
4. Write unit tests

**Acceptance**:
- "current" filter returns only current conditions
- "historical" filter returns only historical
- "all" returns everything
- Unit tests pass

**Estimated Time**: 3 hours

---

### Task 1.2.2: Negation Filter

**Goal**: Implement negated condition filtering

**Prerequisites**: Task 1.1.3 complete

**Steps**:
1. Update `build_search_query()` for negation filter
2. Add ES nested query for `metaAnnotations.negated`
3. Test with "No history of X" examples
4. Write unit tests

**Acceptance**:
- `includeNegated: false` excludes negated mentions
- `includeNegated: true` includes all
- "No history of MI" excluded when filter active
- Unit tests pass

**Estimated Time**: 3 hours

---

### Task 1.2.3: Experiencer Filter

**Goal**: Implement patient vs family history filtering

**Prerequisites**: Task 1.1.3 complete

**Steps**:
1. Update `build_search_query()` for experiencer filter
2. Add ES nested query for `metaAnnotations.experiencer`
3. Test with "Mother has diabetes" examples
4. Write unit tests

**Acceptance**:
- `includeFamily: false` excludes family mentions
- `includeFamily: true` includes all
- "Mother has diabetes" excluded when filter active
- Unit tests pass

**Estimated Time**: 3 hours

---

### Task 1.2.4: Date Range Filter

**Goal**: Implement date range filtering

**Prerequisites**: Task 1.1.3 complete

**Steps**:
1. Update `build_search_query()` for date range
2. Add ES range query for `documentDate`
3. Test with various date ranges
4. Write unit tests

**Acceptance**:
- Returns only documents within date range
- Handles missing dates gracefully
- Unit tests pass

**Estimated Time**: 3 hours

---

### Task 1.2.5: Combined Filters

**Goal**: Ensure all filters work together

**Prerequisites**: Tasks 1.2.1-1.2.4 complete

**Steps**:
1. Test combined filter scenarios
2. Verify AND logic between filters
3. Performance test with all filters
4. Fix any issues

**Acceptance**:
- All filters combine correctly
- No performance degradation
- Integration tests pass

**Estimated Time**: 3 hours

---

## Phase 1.3: Frontend Components (15 hours)

### Task 1.3.1: PatientSearch Component

**Goal**: Create main search component

**Prerequisites**: API endpoints complete

**Steps**:
1. Create `frontend/src/components/clinical/PatientSearch.vue`
2. Add search input with debounce
3. Add search button with loading state
4. Add Pinia store for state management
5. Write component tests

**Acceptance**:
- Search input captures query
- Debounce delays API call (500ms)
- Loading state shown during search
- Component tests pass

**Estimated Time**: 4 hours

---

### Task 1.3.2: FilterPanel Component

**Goal**: Create filter controls

**Prerequisites**: None

**Steps**:
1. Create `frontend/src/components/clinical/FilterPanel.vue`
2. Add temporal filter (radio buttons)
3. Add negation checkbox
4. Add family history checkbox
5. Add date range picker
6. Emit filter changes
7. Write component tests

**Acceptance**:
- All filters render correctly
- Filter changes emit events
- Clear filters button works
- Component tests pass

**Estimated Time**: 3 hours

---

### Task 1.3.3: PatientList Component

**Goal**: Create results display

**Prerequisites**: None

**Steps**:
1. Create `frontend/src/components/clinical/PatientList.vue`
2. Add patient card/row layout
3. Add concept badges with colors
4. Add click handler for patient details
5. Add loading skeleton
6. Write component tests

**Acceptance**:
- Displays patient demographics
- Shows matching concepts as badges
- Click navigates to details
- Loading state works
- Component tests pass

**Estimated Time**: 4 hours

---

### Task 1.3.4: DocumentViewer Component

**Goal**: Create document display with highlighting

**Prerequisites**: Document endpoint complete

**Steps**:
1. Create `frontend/src/components/clinical/DocumentViewer.vue`
2. Add document text display
3. Add concept highlighting
4. Add scroll to highlight
5. Write component tests

**Acceptance**:
- Document text displays correctly
- Concepts highlighted with background color
- Can scroll to specific highlight
- Component tests pass

**Estimated Time**: 4 hours

---

## Phase 1.4: Integration & Testing (15 hours)

### Task 1.4.1: Integration Tests

**Goal**: Test full API flow

**Prerequisites**: All API endpoints complete

**Steps**:
1. Write integration test for search flow
2. Write integration test for filters
3. Write integration test for authentication
4. Write integration test for audit logging

**Acceptance**:
- All integration tests pass
- 90%+ code coverage
- No flaky tests

**Estimated Time**: 5 hours

---

### Task 1.4.2: E2E Tests

**Goal**: Test complete user workflow

**Prerequisites**: Frontend complete

**Steps**:
1. Write Playwright test for search workflow
2. Write test for filter application
3. Write test for document viewing
4. Run tests in CI

**Acceptance**:
- E2E tests pass locally
- E2E tests pass in CI
- Coverage of main workflows

**Estimated Time**: 4 hours

---

### Task 1.4.3: Performance Testing

**Goal**: Validate performance requirements

**Prerequisites**: All features complete

**Steps**:
1. Set up Locust/JMeter test
2. Run load test (100 concurrent users)
3. Measure p95 response time
4. Identify and fix bottlenecks

**Acceptance**:
- Search response < 500ms (p95)
- System handles 100 concurrent users
- No errors under load

**Estimated Time**: 4 hours

---

### Task 1.4.4: Documentation & Cleanup

**Goal**: Complete sprint documentation

**Prerequisites**: All features complete

**Steps**:
1. Update API documentation (OpenAPI)
2. Update CONTEXT.md
3. Write release notes
4. Code cleanup and refactoring

**Acceptance**:
- API docs complete and accurate
- CONTEXT.md updated
- Code review approved

**Estimated Time**: 2 hours

---

## Summary

| Phase | Tasks | Hours |
|-------|-------|-------|
| 1.1 Backend API | 6 | 15 |
| 1.2 Meta-Annotation Filtering | 5 | 15 |
| 1.3 Frontend Components | 4 | 15 |
| 1.4 Integration & Testing | 4 | 15 |
| **Total** | **19** | **60** |

---

## Definition of Done

- [ ] All tasks completed
- [ ] All tests passing (unit, integration, E2E)
- [ ] 85%+ code coverage
- [ ] Performance targets met
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Deployed to staging
