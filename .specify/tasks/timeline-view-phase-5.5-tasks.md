# Timeline View - Phase 5.5: Zoom, Pan, and Temporal Analysis (Detailed Tasks)

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Ready for Implementation
**Specification**: `.specify/specifications/sprint-2-timeline-view.md` v1.0.0
**Technical Plan**: `.specify/plans/timeline-view-plan.md` v1.0.0 (Phase 5.5 section)

---

## Overview

**Phase Goal**: Add zoom/pan controls and temporal pattern detection for enhanced timeline navigation and concept analysis

**Estimated Duration**: 15 hours (6 tasks, ~2-3 hours each)

**Dependencies**:
- ✅ Phase 5.1 COMPLETE (Backend Timeline Data API)
- ✅ Phase 5.2 COMPLETE (Frontend Timeline Component)
- ✅ Phase 5.3 COMPLETE (Concept Extraction & Display)
- ✅ Phase 5.4 COMPLETE (Filtering & Search)

**Acceptance Criteria**:
- [ ] Zoom in/out works (mouse wheel + buttons)
- [ ] Pan works (mouse drag)
- [ ] Reset zoom button works
- [ ] Zoom/pan operations at 60fps (smooth animations)
- [ ] First mention vs recurring mentions differentiated visually
- [ ] Concept frequency chart renders (bar chart overlay)
- [ ] Frequency chart toggle on/off
- [ ] Temporal relationships highlighted (optional)
- [ ] Unit test coverage ≥80%

---

## Task Breakdown

### Task 5.5.1: Install D3 Zoom Dependencies & Setup (0.5 hours)

**Goal**: Install d3-zoom module and configure TypeScript types

**Prerequisites**:
- Phase 5.2 complete (D3.js already installed)

**Steps**:
1. Verify D3.js v7 includes d3-zoom (it does, installed in Task 5.2.1)
2. Verify TypeScript types for d3-zoom in `@types/d3`
3. Create placeholder for zoom behavior in TimelineView
4. Document zoom/pan requirements in component comments

**Acceptance Criteria**:
- d3-zoom types available in TypeScript
- No additional npm install needed (d3@7.9.0 includes zoom)
- Component ready for zoom implementation

**Files to Verify**:
- `frontend/package.json` (d3@7.9.0 already installed)
- `frontend/src/views/TimelineView.vue` (document zoom plans)

**Estimated Time**: 0.5 hours

---

### Task 5.5.2: Create useTimelineZoom Composable (2 hours)

**Goal**: Create a composable to manage zoom/pan state and D3 zoom behavior

**Prerequisites**:
- Task 5.5.1 complete

**Steps**:
1. Create `frontend/src/composables/useTimelineZoom.ts`:
   - Define `ZoomState` interface:
     - `scale: number` - Current zoom scale (1 = 100%, 2 = 200%, etc.)
     - `translateX: number` - Horizontal pan offset
     - `translateY: number` - Vertical pan offset
     - `minScale: number` - Min zoom (0.1 = 10%)
     - `maxScale: number` - Max zoom (10 = 1000%)
   - State management:
     - `zoomState: Ref<ZoomState>` - Current zoom/pan state
     - `zoomBehavior: Ref<d3.ZoomBehavior | null>` - D3 zoom behavior instance
   - Methods:
     - `initZoom(svgElement: SVGSVGElement, width: number, height: number)` - Initialize D3 zoom behavior
     - `zoomIn()` - Zoom in by factor of 1.5
     - `zoomOut()` - Zoom out by factor of 0.75
     - `resetZoom()` - Reset to scale=1, translate=(0,0)
     - `zoomTo(scale: number, centerX: number, centerY: number)` - Zoom to specific point
     - `handleZoom(event: d3.ZoomEvent)` - Handle D3 zoom events (update state)
   - Debouncing:
     - Debounce zoom events (16ms = 60fps)
     - Throttle pan updates to avoid performance issues
   - Cleanup:
     - `destroy()` - Remove zoom behavior on unmount
2. Write unit tests for `useTimelineZoom`:
   - Test initZoom creates D3 zoom behavior
   - Test zoomIn/zoomOut update scale correctly
   - Test resetZoom returns to default state
   - Test min/max scale limits enforced
   - Test pan translate updates
   - Test debouncing works (zoom events throttled)
   - Test cleanup removes listeners

**Acceptance Criteria**:
- Zoom state managed reactively
- D3 zoom behavior integrated
- Zoom/pan limits enforced (min 0.1x, max 10x)
- Debouncing prevents performance issues
- 8 unit tests passing

**Files to Create**:
- `frontend/src/composables/useTimelineZoom.ts` (~150 lines)
- `frontend/tests/unit/composables/useTimelineZoom.spec.ts` (~250 lines, 8 tests)

**Estimated Time**: 2 hours

---

### Task 5.5.3: Integrate Zoom/Pan into TimelineView (2.5 hours)

**Goal**: Add zoom/pan controls to TimelineView component

**Prerequisites**:
- Task 5.5.2 complete (useTimelineZoom composable ready)

**Steps**:
1. Modify `frontend/src/views/TimelineView.vue`:
   - Import and use `useTimelineZoom` composable
   - Initialize zoom behavior on SVG mount (watch for `timelineSvg` ref)
   - Add zoom control buttons to toolbar:
     - Zoom In button (`<v-btn icon="mdi-magnify-plus">`)
     - Zoom Out button (`<v-btn icon="mdi-magnify-minus">`)
     - Reset Zoom button (`<v-btn icon="mdi-magnify-remove-outline">`)
   - Display current zoom level (e.g., "100%", "150%") in toolbar
   - Apply zoom/pan transform to SVG group wrapping timeline content:
     - Wrap `<TimelineAxis>`, `<TimelineDocuments>`, `<TimelineConcepts>` in `<g>` element
     - Bind `transform` attribute to `zoomState` (e.g., `transform="translate(${zoomState.translateX}, ${zoomState.translateY}) scale(${zoomState.scale})"`)
   - Enable mouse wheel zoom (d3-zoom handles this automatically)
   - Enable mouse drag pan (d3-zoom handles this automatically)
   - Add keyboard shortcuts:
     - `+` / `=` for zoom in
     - `-` / `_` for zoom out
     - `0` for reset zoom
   - Add smooth transitions for zoom/pan (300ms ease-in-out)
   - Cleanup zoom behavior on component unmount
2. Update TimelineAxis to respect zoom scale:
   - Adjust tick density based on zoom level (more ticks when zoomed in)
   - Recalculate axis when zoom changes (watch `zoomState.scale`)
3. Write integration tests for zoom/pan:
   - Test zoom in button increases scale
   - Test zoom out button decreases scale
   - Test reset zoom button returns to 100%
   - Test zoom level displayed correctly
   - Test mouse wheel zoom works (simulate wheel event)
   - Test mouse drag pan works (simulate drag event)
   - Test keyboard shortcuts work
   - Test zoom limits enforced (can't zoom beyond min/max)

**Acceptance Criteria**:
- Zoom in/out buttons work
- Reset zoom button works
- Current zoom level displayed (e.g., "100%")
- Mouse wheel zoom works
- Mouse drag pan works
- Keyboard shortcuts work
- Zoom/pan operations smooth (60fps target)
- 8 integration tests passing

**Files to Modify/Create**:
- `frontend/src/views/TimelineView.vue` (add zoom controls, apply transform)
- `frontend/src/components/TimelineAxis.vue` (adjust ticks for zoom)
- `frontend/tests/integration/TimelineZoom.integration.spec.ts` (new file, 8 tests)

**Estimated Time**: 2.5 hours

---

### Task 5.5.4: Differentiate First Mention vs Recurring Mentions (2 hours)

**Goal**: Visually differentiate first occurrence vs recurring occurrences of concepts

**Prerequisites**:
- Phase 5.3 complete (concept markers rendering)

**Steps**:
1. Update backend `TimelineService` to mark first mentions:
   - In `get_patient_timeline()` method, after aggregating concepts:
     - For each concept, find earliest mention by date
     - Add `is_first_mention: bool` field to each mention in `mentions` array
     - First mention = `True`, all others = `False`
2. Update Pydantic schema `ConceptMention` in `backend/app/schemas/timeline.py`:
   - Add `is_first_mention: bool` field (default False)
3. Write backend unit tests:
   - Test first mention identified correctly (earliest date marked True)
   - Test recurring mentions marked False
   - Test single mention marked True
4. Update `TimelineConcepts.vue` component:
   - Modify marker rendering to use different sizes:
     - First mention: `r="8"` (large marker)
     - Recurring mention: `r="4"` (small marker)
   - Add tooltip text differentiation:
     - First mention: "First mentioned: {date}"
     - Recurring mention: "Also mentioned: {date}"
   - Add CSS classes for styling:
     - `.concept-marker-first` (larger, bold stroke)
     - `.concept-marker-recurring` (smaller, thinner stroke)
5. Write frontend unit tests:
   - Test first mention renders with r=8
   - Test recurring mention renders with r=4
   - Test tooltip text correct for first vs recurring
   - Test CSS classes applied correctly

**Acceptance Criteria**:
- Backend marks first mentions correctly
- First mention markers larger (r=8)
- Recurring mention markers smaller (r=4)
- Tooltip differentiated (first vs recurring)
- 6 unit tests passing (3 backend, 3 frontend)

**Files to Modify/Create**:
- `backend/app/services/timeline_service.py` (mark first mentions)
- `backend/app/schemas/timeline.py` (add is_first_mention field)
- `backend/tests/unit/services/test_timeline_service.py` (add 3 tests)
- `frontend/src/components/TimelineConcepts.vue` (render differentiation)
- `frontend/tests/unit/components/TimelineConcepts.spec.ts` (add 3 tests)

**Estimated Time**: 2 hours

---

### Task 5.5.5: Create Concept Frequency Chart Component (3.5 hours)

**Goal**: Add bar chart overlay showing concept mention frequency over time

**Prerequisites**:
- Task 5.5.4 complete (first vs recurring mentions available)

**Steps**:
1. Create `frontend/src/components/ConceptFrequencyChart.vue`:
   - Component structure (Vuetify + D3.js):
     - Accept props:
       - `concepts: TimelineConcept[]` - Concepts to analyze
       - `dateRange: { start: Date, end: Date }` - Timeline date range
       - `width: number` - Chart width
       - `height: number` - Chart height (default 100px)
       - `binSize: 'month' | 'quarter' | 'year'` - Aggregation period (default 'month')
     - Render bar chart using D3.js:
       - X-axis: Time bins (months/quarters/years)
       - Y-axis: Mention count (number of concept occurrences)
       - Bars: Stacked by concept type (conditions=red, medications=blue, etc.)
       - Tooltip on hover: "Jan 2023: 5 mentions (3 conditions, 2 medications)"
     - Toggle button to show/hide chart
   - Data processing:
     - Aggregate concept mentions into time bins:
       - Group mentions by month/quarter/year
       - Count total mentions per bin
       - Count mentions by concept type per bin
     - Calculate bin edges based on `dateRange`
   - Rendering:
     - Use D3.js scales (`d3.scaleTime`, `d3.scaleLinear`)
     - Use D3.js stacked bar chart (`d3.stack`)
     - Add X-axis labels (month names, year labels)
     - Add Y-axis labels (mention counts)
     - Color bars by concept type (match timeline concept colors)
   - Interactions:
     - Hover on bar → show tooltip with details
     - Click on bar → filter timeline to that time period (optional)
   - Performance:
     - Debounce chart updates (300ms)
     - Only render when visible (toggle on/off)
2. Integrate into TimelineView:
   - Add "Show Frequency Chart" toggle button in toolbar
   - Render `<ConceptFrequencyChart>` above or below timeline axis
   - Pass `concepts`, `dateRange`, `width` from TimelineView state
   - Show/hide based on toggle state
3. Write unit tests for ConceptFrequencyChart:
   - Test frequency aggregation (mentions grouped by month)
   - Test bar chart rendering (correct number of bars)
   - Test stacking by concept type (colors correct)
   - Test tooltip display (shows count and breakdown)
   - Test toggle on/off works
   - Test bin size change (month → quarter → year)
   - Test empty data handling (no concepts)
4. Write integration tests:
   - Test frequency chart renders when toggled on
   - Test chart updates when filters applied
   - Test click on bar filters timeline to that period (optional)

**Acceptance Criteria**:
- Bar chart renders with correct bins
- Bars stacked by concept type (colored correctly)
- Tooltip shows breakdown on hover
- Toggle on/off works
- Chart updates when filters change
- 7 unit tests passing
- 3 integration tests passing

**Files to Create**:
- `frontend/src/components/ConceptFrequencyChart.vue` (~250 lines)
- `frontend/tests/unit/components/ConceptFrequencyChart.spec.ts` (~300 lines, 7 tests)
- `frontend/tests/integration/ConceptFrequencyChart.integration.spec.ts` (~150 lines, 3 tests)

**Files to Modify**:
- `frontend/src/views/TimelineView.vue` (add toggle button, integrate chart)

**Estimated Time**: 3.5 hours

---

### Task 5.5.6: Integration Tests & Performance Validation (2.5 hours)

**Goal**: Comprehensive integration tests for zoom/pan + frequency chart + performance validation

**Prerequisites**:
- All previous Phase 5.5 tasks complete

**Steps**:
1. Create `frontend/tests/integration/TimelineInteractions.integration.spec.ts`:
   - Test full zoom workflow:
     1. Load timeline
     2. Click zoom in button
     3. Verify scale increased
     4. Drag to pan
     5. Verify translateX/Y changed
     6. Click reset zoom
     7. Verify scale back to 1
   - Test zoom + filter interaction:
     - Apply filter
     - Zoom in
     - Verify filtered markers visible and zoomed
   - Test frequency chart + zoom interaction:
     - Toggle frequency chart on
     - Zoom in
     - Verify chart scales with timeline
   - Test keyboard shortcuts:
     - Press `+` key → zoom in
     - Press `-` key → zoom out
     - Press `0` key → reset zoom
   - Test mouse wheel zoom:
     - Simulate wheel event
     - Verify zoom level changed
   - Test mouse drag pan:
     - Simulate drag event
     - Verify pan offset changed
   - Test first mention vs recurring:
     - Load timeline
     - Verify first mention has r=8
     - Verify recurring mention has r=4
   - Test frequency chart:
     - Toggle chart on
     - Hover on bar
     - Verify tooltip shows count
2. Create `backend/tests/performance/test_timeline_zoom_performance.py`:
   - Test zoom render performance:
     - 100 documents, 1000 concepts
     - Apply zoom (scale=2)
     - Measure render time (target: <100ms)
   - Test pan render performance:
     - 100 documents, 1000 concepts
     - Apply pan (translateX=100)
     - Measure render time (target: <100ms)
   - Test frequency chart performance:
     - 1000 concepts across 5 years
     - Aggregate into monthly bins (60 bins)
     - Measure aggregation + render time (target: <500ms)
3. Add performance optimization notes in CONTEXT.md if targets not met:
   - Canvas rendering instead of SVG for large datasets
   - Virtual rendering for offscreen markers
   - Memoization for frequency aggregation
   - Debouncing for zoom/pan updates

**Acceptance Criteria**:
- 8 frontend integration tests passing
- 3 backend performance tests passing (or optimization notes documented)
- Zoom/pan at 60fps (16.67ms per frame)
- Frequency chart renders in <500ms

**Files to Create**:
- `frontend/tests/integration/TimelineInteractions.integration.spec.ts` (new file, 8 tests)
- `backend/tests/performance/test_timeline_zoom_performance.py` (new file, 3 tests)

**Estimated Time**: 2.5 hours

---

## Summary

**Total Tasks**: 6 tasks
**Estimated Duration**: 15 hours (matches plan estimate)
**Files Created**: 7 new files
**Files Modified**: 6 existing files
**Tests**: 39 unit + integration + performance tests

**Phase 5.5 Dependencies**:
- ✅ Phase 5.1 COMPLETE (Backend Timeline Data API)
- ✅ Phase 5.2 COMPLETE (Frontend Timeline Component)
- ✅ Phase 5.3 COMPLETE (Concept Extraction & Display)
- ✅ Phase 5.4 COMPLETE (Filtering & Search)

**Next Phase**: Phase 5.6 (Export & Analytics) - PDF export, FHIR export, usage analytics

---

**Ready to implement!** Start with Task 5.5.1 (Install D3 Zoom Dependencies & Setup).
