# Timeline View - Phase 5.4: Filtering & Search (Detailed Tasks)

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Ready for Implementation
**Specification**: `.specify/specifications/sprint-2-timeline-view.md` v1.0.0
**Technical Plan**: `.specify/plans/timeline-view-plan.md` v1.0.0 (Phase 5.4 section)

---

## Overview

**Phase Goal**: Add comprehensive filtering capabilities to timeline view (concept filters, date range, meta-annotations, document types, filter presets)

**Estimated Duration**: 15 hours (8 tasks, ~2 hours each)

**Dependencies**:
- ✅ Phase 5.1 COMPLETE (Backend Timeline Data API)
- ✅ Phase 5.2 COMPLETE (Frontend Timeline Component)
- ✅ Phase 5.3 COMPLETE (Concept Extraction & Display)

**Acceptance Criteria**:
- [ ] Concept search with SNOMED-CT autocomplete works
- [ ] Multi-select concepts filters timeline
- [ ] Date range filters timeline (absolute and relative)
- [ ] Meta-annotation filters work (exclude negated, family, historical)
- [ ] Document type filters work
- [ ] Filter presets can be saved and loaded
- [ ] Filters synced with URL query params (shareable links)
- [ ] Filter updates render in <500ms
- [ ] Unit test coverage ≥80%

---

## Task Breakdown

### Task 5.4.1: Backend - Update Timeline API with Filter Parameters (2 hours)

**Goal**: Enhance GET /api/v1/timeline/{patient_id} endpoint to accept filter parameters

**Prerequisites**:
- Phase 5.1 backend API complete
- Elasticsearch index with concepts populated

**Steps**:
1. Update `backend/app/schemas/timeline.py`:
   - Add `TimelineFilterRequest` Pydantic model:
     - `concept_cuis: Optional[List[str]]` - Filter by SNOMED-CT CUIs
     - `date_from: Optional[datetime]` - Start date
     - `date_to: Optional[datetime]` - End date
     - `meta_annotations: Optional[Dict[str, List[str]]]` - Meta-annotation filters
       - Example: `{"Negation": ["Affirmed"], "Experiencer": ["Patient"], "Temporality": ["Current", "Recent"]}`
     - `document_types: Optional[List[str]]` - Document type filters
     - `include_documents: bool = True` - Include document markers
     - `include_concepts: bool = True` - Include concept markers
2. Update `backend/app/api/v1/endpoints/timeline.py`:
   - Modify `get_patient_timeline` endpoint:
     - Accept `TimelineFilterRequest` as query parameters (Depends())
     - Pass filters to `TimelineService.get_patient_timeline()`
3. Update `backend/app/services/timeline_service.py`:
   - Modify `get_patient_timeline()` to accept `filters: TimelineFilterRequest`
   - Pass filters to `ElasticsearchTimelineRepository.get_clinical_concepts()`
4. Update `backend/app/repositories/elasticsearch_timeline_repository.py`:
   - Modify `get_clinical_concepts()` to build Elasticsearch query with filters:
     - Add `terms` query for `concept_cui` if `concept_cuis` provided
     - Add `range` query for `date` if `date_from` or `date_to` provided
     - Add `terms` queries for meta_annotations (nested fields)
     - Add `terms` query for `document_type` if `document_types` provided
5. Write unit tests for `TimelineFilterRequest` validation
6. Write integration tests for filtered timeline API:
   - Test concept CUI filtering (returns only matching concepts)
   - Test date range filtering (returns concepts within range)
   - Test meta-annotation filtering (excludes negated, family, historical)
   - Test document type filtering (returns only matching documents)
   - Test combined filters (all filters applied simultaneously)
   - Test empty result sets (no matches)

**Acceptance Criteria**:
- GET /api/v1/timeline/{patient_id}?concept_cuis=C0011849&date_from=2023-01-01 returns filtered results
- Meta-annotation filtering excludes negated/family/historical concepts correctly
- Response time <500ms for filtered queries
- 6 integration tests passing

**Files to Modify/Create**:
- `backend/app/schemas/timeline.py` (add TimelineFilterRequest)
- `backend/app/api/v1/endpoints/timeline.py` (update endpoint)
- `backend/app/services/timeline_service.py` (update service)
- `backend/app/repositories/elasticsearch_timeline_repository.py` (update repository)
- `backend/tests/integration/test_timeline_filters.py` (new file, 6 tests)

**Estimated Time**: 2 hours

---

### Task 5.4.2: Frontend - Create useTimelineFilters Composable (1.5 hours)

**Goal**: Create a composable to manage timeline filter state and API integration

**Prerequisites**:
- Task 5.4.1 complete (backend filter API ready)

**Steps**:
1. Create `frontend/src/composables/useTimelineFilters.ts`:
   - Define `TimelineFilters` interface matching backend schema:
     - `conceptCuis: string[]`
     - `dateFrom: Date | null`
     - `dateTo: Date | null`
     - `metaAnnotations: Record<string, string[]>`
     - `documentTypes: string[]`
     - `includeDocuments: boolean`
     - `includeConcepts: boolean`
   - State management:
     - `filters: Ref<TimelineFilters>` - Current filter state
     - `isLoading: Ref<boolean>` - API call in progress
     - `error: Ref<string | null>` - Error message
   - Methods:
     - `setConceptFilter(cuis: string[])` - Add/remove concept CUIs
     - `setDateRange(from: Date | null, to: Date | null)` - Set date filter
     - `setMetaAnnotationFilter(key: string, values: string[])` - Set meta-annotation filter
     - `setDocumentTypeFilter(types: string[])` - Set document type filter
     - `clearFilters()` - Reset all filters
     - `applyFilters(patientId: string)` - Fetch filtered timeline
   - URL sync:
     - Use `vue-router` to sync filters with query params
     - `syncFiltersToURL()` - Update URL with current filters
     - `loadFiltersFromURL()` - Load filters from URL on mount
2. Write unit tests for `useTimelineFilters`:
   - Test filter state updates (setConceptFilter, setDateRange, etc.)
   - Test clearFilters resets state
   - Test applyFilters calls API with correct params
   - Test URL sync (filters → URL, URL → filters)
   - Test error handling

**Acceptance Criteria**:
- Filter state managed reactively
- API integration working (applyFilters calls backend)
- URL sync working (shareable links)
- 8 unit tests passing

**Files to Create**:
- `frontend/src/composables/useTimelineFilters.ts` (~120 lines)
- `frontend/tests/unit/composables/useTimelineFilters.spec.ts` (~200 lines, 8 tests)

**Estimated Time**: 1.5 hours

---

### Task 5.4.3: Frontend - Create ConceptFilterSidebar Component (2.5 hours)

**Goal**: Create a sidebar component with all filter controls

**Prerequisites**:
- Task 5.4.2 complete (useTimelineFilters composable ready)

**Steps**:
1. Create `frontend/src/components/ConceptFilterSidebar.vue`:
   - Component structure (Vuetify components):
     - `<v-navigation-drawer>` (sidebar container, right-side, width="350px")
     - `<v-text-field>` (concept search with autocomplete)
     - `<v-chip-group>` (selected concept chips, removable)
     - `<v-date-picker>` or `<v-text-field type="date">` (date range)
     - `<v-select>` (relative date ranges: "Last 3 months", "Last year", "All time")
     - `<v-checkbox>` group for meta-annotations:
       - Negation: [x] Affirmed, [ ] Negated
       - Experiencer: [x] Patient, [ ] Family, [ ] Other
       - Temporality: [x] Current, [x] Recent, [ ] Historical
       - Certainty: [x] Certain, [x] Probable, [ ] Hypothetical
     - `<v-checkbox>` group for document types:
       - [ ] Clinical Notes, [ ] Discharge Summaries, [ ] Lab Reports, [ ] Radiology
     - `<v-btn>` (Apply Filters - primary)
     - `<v-btn>` (Clear Filters - secondary)
     - `<v-btn>` (Save Preset - outlined)
   - Concept autocomplete:
     - Debounced search (300ms)
     - Fetch from `/api/v1/concepts/search?q={query}` (assumes endpoint exists or mock for now)
     - Display: concept name + CUI
     - Add to `conceptCuis` on selection
   - Date range:
     - Absolute dates: Use date pickers
     - Relative dates: Dropdown with presets (compute date_from/date_to)
   - Filter application:
     - Call `applyFilters(patientId)` from useTimelineFilters composable
     - Emit "filters-applied" event to parent (TimelineView)
   - Props:
     - `modelValue: boolean` (v-model for drawer visibility)
     - `patientId: string` (for applying filters)
   - Emits:
     - `update:modelValue: [boolean]` (v-model binding)
     - `filters-applied: [filters: TimelineFilters]` (when Apply Filters clicked)
2. Write unit tests for ConceptFilterSidebar:
   - Test concept search autocomplete
   - Test concept chip addition/removal
   - Test date range selection (absolute and relative)
   - Test meta-annotation checkbox toggling
   - Test document type checkbox toggling
   - Test Apply Filters emits event with correct data
   - Test Clear Filters resets all inputs
   - Test Save Preset (future: integration with backend)

**Acceptance Criteria**:
- Sidebar renders with all filter controls
- Concept autocomplete works (debounced search)
- Date range controls work (absolute and relative)
- Meta-annotation checkboxes work (correct defaults)
- Apply Filters emits event with correct filter object
- Clear Filters resets all controls
- 10 unit tests passing

**Files to Create**:
- `frontend/src/components/ConceptFilterSidebar.vue` (~300 lines)
- `frontend/tests/unit/components/ConceptFilterSidebar.spec.ts` (~350 lines, 10 tests)

**Estimated Time**: 2.5 hours

---

### Task 5.4.4: Frontend - Integrate Filters into TimelineView (1.5 hours)

**Goal**: Add ConceptFilterSidebar to TimelineView and wire up filter application

**Prerequisites**:
- Task 5.4.3 complete (ConceptFilterSidebar component ready)

**Steps**:
1. Modify `frontend/src/views/TimelineView.vue`:
   - Import ConceptFilterSidebar
   - Add filter toggle button (Vuetify `<v-btn icon="mdi-filter-variant">` in toolbar)
   - Add state for sidebar visibility: `showFilters: Ref<boolean>`
   - Add ConceptFilterSidebar component:
     - `v-model="showFilters"`
     - `:patient-id="patientId"`
     - `@filters-applied="onFiltersApplied"`
   - Implement `onFiltersApplied(filters)`:
     - Update `useTimeline` composable call with filters
     - Refetch timeline data with filters applied
     - Show loading indicator during refetch
   - Update Timeline API call:
     - Pass filters from useTimelineFilters to API request
     - Update timeline rendering with filtered data
2. Add filter indicators:
   - Show active filter count badge on filter button
   - Display active filters as chips in toolbar (removable)
   - Example: "Diabetes (C0011849) x" "Last 3 months x" "Affirmed only x"
3. Write integration tests for filtered timeline:
   - Test filter button opens sidebar
   - Test applying filters refetches timeline
   - Test active filter chips displayed
   - Test removing filter chip re-filters timeline
   - Test timeline updates with filtered concepts

**Acceptance Criteria**:
- Filter button in toolbar opens ConceptFilterSidebar
- Applying filters refetches and updates timeline
- Active filters displayed as chips in toolbar
- Removing filter chip re-filters timeline
- Loading indicator shown during refetch
- 5 integration tests passing

**Files to Modify**:
- `frontend/src/views/TimelineView.vue` (add sidebar, wire up events)
- `frontend/tests/integration/TimelineFilters.integration.spec.ts` (new file, 5 tests)

**Estimated Time**: 1.5 hours

---

### Task 5.4.5: Backend - Create Filter Preset API (2 hours)

**Goal**: Allow users to save and load filter presets

**Prerequisites**:
- Task 5.4.1 complete (filter schema defined)

**Steps**:
1. Create database migration for `timeline_filter_presets` table:
   - `id` (UUID primary key)
   - `user_id` (UUID foreign key → users)
   - `name` (VARCHAR 100, NOT NULL) - Preset name (e.g., "Diabetes Management")
   - `filters` (JSONB, NOT NULL) - Serialized TimelineFilterRequest
   - `is_default` (BOOLEAN default FALSE) - Default preset for user
   - `created_at` (TIMESTAMP default NOW())
   - `updated_at` (TIMESTAMP default NOW())
   - Indexes: (user_id, name) unique, (user_id, is_default)
2. Create `backend/app/models/timeline_filter_preset.py` (SQLAlchemy model)
3. Create `backend/app/schemas/timeline_filter_preset.py`:
   - `FilterPresetCreate` (name, filters)
   - `FilterPresetUpdate` (name, filters, is_default)
   - `FilterPresetResponse` (id, name, filters, is_default, created_at)
4. Create `backend/app/api/v1/endpoints/timeline_filter_presets.py`:
   - `POST /api/v1/timeline/filters` - Create preset
   - `GET /api/v1/timeline/filters` - List user's presets
   - `GET /api/v1/timeline/filters/{preset_id}` - Get preset by ID
   - `PUT /api/v1/timeline/filters/{preset_id}` - Update preset
   - `DELETE /api/v1/timeline/filters/{preset_id}` - Delete preset
5. Write integration tests for preset API:
   - Test create preset (returns 201 with preset)
   - Test list presets (returns user's presets only)
   - Test get preset by ID (returns preset or 404)
   - Test update preset (updates name/filters/is_default)
   - Test delete preset (soft delete or hard delete)
   - Test default preset (only one is_default=True per user)

**Acceptance Criteria**:
- Preset CRUD API working
- User can only access their own presets (RBAC enforced)
- Only one default preset per user enforced
- 6 integration tests passing

**Files to Create/Modify**:
- `backend/alembic/versions/010_create_timeline_filter_presets.py` (migration)
- `backend/app/models/timeline_filter_preset.py` (SQLAlchemy model)
- `backend/app/schemas/timeline_filter_preset.py` (Pydantic schemas)
- `backend/app/api/v1/endpoints/timeline_filter_presets.py` (new endpoints)
- `backend/tests/integration/test_timeline_filter_presets.py` (new file, 6 tests)

**Estimated Time**: 2 hours

---

### Task 5.4.6: Frontend - Add Filter Preset UI (1.5 hours)

**Goal**: Add save/load preset UI to ConceptFilterSidebar

**Prerequisites**:
- Task 5.4.5 complete (preset API ready)

**Steps**:
1. Modify `frontend/src/components/ConceptFilterSidebar.vue`:
   - Add preset dropdown at top of sidebar:
     - `<v-select>` with label "Load Preset"
     - Options: User's saved presets (fetch from API)
     - On selection: Load filters from preset
   - Add "Save Preset" button:
     - Opens dialog with `<v-text-field>` for preset name
     - Checkbox: "Set as default"
     - Calls `POST /api/v1/timeline/filters` on save
   - Add preset management:
     - "Manage Presets" button opens dialog
     - List of presets with edit/delete buttons
     - Default preset indicator (star icon)
2. Create API client methods:
   - `getFilterPresets()` - Fetch user's presets
   - `createFilterPreset(name, filters, isDefault)` - Save preset
   - `updateFilterPreset(id, data)` - Update preset
   - `deleteFilterPreset(id)` - Delete preset
3. Write unit tests for preset UI:
   - Test load preset populates filters
   - Test save preset dialog opens
   - Test create preset calls API
   - Test delete preset calls API
   - Test default preset indicator shown

**Acceptance Criteria**:
- Load preset dropdown works
- Save preset dialog works
- Manage presets dialog works (edit/delete)
- Default preset loaded on mount (if exists)
- 5 unit tests passing

**Files to Modify/Create**:
- `frontend/src/components/ConceptFilterSidebar.vue` (add preset UI)
- `frontend/src/api/timeline.ts` (add preset API methods)
- `frontend/tests/unit/components/ConceptFilterSidebar.spec.ts` (add 5 tests)

**Estimated Time**: 1.5 hours

---

### Task 5.4.7: Frontend - URL Query Param Sync (1 hour)

**Goal**: Sync filters with URL query params for shareable links

**Prerequisites**:
- Task 5.4.2 complete (useTimelineFilters composable)

**Steps**:
1. Enhance `frontend/src/composables/useTimelineFilters.ts`:
   - Add `syncFiltersToURL()` method:
     - Use `router.push({ query: { ...serializeFilters() } })`
     - Serialize filters to URL-safe format:
       - `conceptCuis` → `concepts=C0011849,C0020538`
       - `dateFrom` → `from=2023-01-01`
       - `dateTo` → `to=2023-12-31`
       - `metaAnnotations` → `negation=Affirmed&experiencer=Patient`
       - `documentTypes` → `types=note,discharge`
   - Add `loadFiltersFromURL()` method:
     - Parse query params from `route.query`
     - Deserialize into filters object
     - Apply filters automatically on mount
   - Call `syncFiltersToURL()` after every filter change
   - Call `loadFiltersFromURL()` on composable initialization
2. Write unit tests for URL sync:
   - Test filters → URL (query params updated)
   - Test URL → filters (filters loaded from query params)
   - Test empty query params (no filters)
   - Test invalid query params (graceful handling)
   - Test shareable link workflow (copy URL, open in new tab, filters applied)

**Acceptance Criteria**:
- Filters encoded in URL query params
- URL can be shared (recipient sees same filtered view)
- Filters loaded from URL on mount
- Invalid query params handled gracefully
- 5 unit tests passing

**Files to Modify**:
- `frontend/src/composables/useTimelineFilters.ts` (add URL sync)
- `frontend/tests/unit/composables/useTimelineFilters.spec.ts` (add 5 tests)

**Estimated Time**: 1 hour

---

### Task 5.4.8: Integration Tests & Performance Validation (2 hours)

**Goal**: Comprehensive integration tests for full filter workflow + performance validation

**Prerequisites**:
- All previous Phase 5.4 tasks complete

**Steps**:
1. Create `frontend/tests/integration/TimelineFiltering.integration.spec.ts`:
   - Test full filter workflow:
     1. Load timeline view
     2. Open filter sidebar
     3. Search for concept ("diabetes")
     4. Select concept from autocomplete
     5. Apply filters
     6. Verify timeline updates with filtered data
     7. Verify URL updated with query params
     8. Clear filters
     9. Verify timeline shows all data again
   - Test multi-filter combination:
     - Apply concept + date range + meta-annotation filters
     - Verify all filters applied correctly (backend query)
     - Verify timeline updates in <500ms
   - Test filter presets:
     - Save preset
     - Load preset
     - Verify filters applied from preset
   - Test shareable link:
     - Apply filters
     - Copy URL
     - Navigate to URL in new instance
     - Verify filters loaded from URL
2. Create `backend/tests/performance/test_timeline_filter_performance.py`:
   - Test filter query performance:
     - 100 patients, 1000 concepts each
     - Apply concept filter (10 CUIs)
     - Measure query time (target: <500ms)
   - Test combined filter performance:
     - Concept + date range + meta-annotation filters
     - Measure query time (target: <500ms)
   - Test preset load performance:
     - 50 presets per user
     - Load preset and apply filters
     - Measure total time (target: <1s)
3. Write performance optimization notes in CONTEXT.md if targets not met

**Acceptance Criteria**:
- Full filter workflow integration test passing
- Multi-filter combination test passing
- Filter preset integration test passing
- Shareable link test passing
- Performance tests passing (or optimization notes documented)
- 8 integration tests + 3 performance tests passing

**Files to Create**:
- `frontend/tests/integration/TimelineFiltering.integration.spec.ts` (new file, 8 tests)
- `backend/tests/performance/test_timeline_filter_performance.py` (new file, 3 tests)

**Estimated Time**: 2 hours

---

## Summary

**Total Tasks**: 8 tasks
**Estimated Duration**: 15 hours
**Files Created**: 14 new files
**Files Modified**: 6 existing files
**Tests**: 58 unit + integration + performance tests

**Phase 5.4 Dependencies**:
- ✅ Phase 5.1 COMPLETE (Backend Timeline Data API)
- ✅ Phase 5.2 COMPLETE (Frontend Timeline Component)
- ✅ Phase 5.3 COMPLETE (Concept Extraction & Display)

**Next Phase**: Phase 5.5 (Zoom, Pan, and Temporal Analysis)

---

**Ready to implement!** Start with Task 5.4.1 (Backend filter API).
