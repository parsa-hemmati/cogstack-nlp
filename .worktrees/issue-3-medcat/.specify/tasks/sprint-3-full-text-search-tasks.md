# Tasks: Full-Text Search Enhancement (Sprint 3)

**Plan Reference**: `.specify/plans/sprint-3-full-text-search-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-3-full-text-search.md` (v1.0.0)
**Estimated Total Time**: 90 hours (3 weeks)
**Dependencies**:
- Sprint 1 (Patient Search) completed
- Sprint 2 (Timeline View) completed
- Elasticsearch 8.11 cluster running
- Redis 7.2 running for caching

---

## Phase 3.1: Elasticsearch Integration (30 hours)

### Task 3.1.1: Setup Elasticsearch Index Mapping

**Goal**: Create Elasticsearch index with optimized mapping for document search

**Phase**: Phase 3.1
**Dependencies**: None
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/elasticsearch/test_index_mapping.py`
   - Test: Index mapping includes all fields
   - Test: Analyzers configured correctly
   - Test: Field types correct (text, keyword, date)
2. **Implement**
   - Create `backend/app/services/elasticsearch/index_config.py`
   - Define index mapping with fields: title, content, document_type, author, department, date
   - Configure custom analyzer: `medical_analyzer` (lowercase + stop + snowball)
   - Set keyword sub-fields for faceting
   - Set number_of_shards=2, number_of_replicas=1
3. **Apply mapping**
   - Create script: `scripts/create_es_index.py`
   - Run: `python scripts/create_es_index.py`
4. **Verify**
   - Check index exists: `curl localhost:9200/documents/_mapping`

**Acceptance Criteria**:
- [ ] Index created with correct mapping
- [ ] Custom analyzer configured
- [ ] All fields present (title, content, document_type, author, department, date)
- [ ] Keyword sub-fields for faceting
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 6 tests (mapping structure, analyzers, field types)

**Files Created/Modified**:
- `backend/app/services/elasticsearch/index_config.py` - Index mapping
- `scripts/create_es_index.py` - Index creation script
- `tests/unit/elasticsearch/test_index_mapping.py` - Mapping tests

---

### Task 3.1.2: Create Document Indexing Service

**Goal**: Service to sync PostgreSQL documents to Elasticsearch

**Phase**: Phase 3.1
**Dependencies**: Task 3.1.1
**Estimated Time**: 6 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_document_indexing_service.py`
   - Test: Document indexed to Elasticsearch
   - Test: Document updates propagated
   - Test: Document deletion handled
   - Test: Bulk indexing works
2. **Implement**
   - Create `backend/app/services/document_indexing_service.py`
   - Implement `index_document(document_id)` method
   - Fetch document from PostgreSQL
   - Transform to Elasticsearch document format
   - Index using elasticsearch-py client
   - Implement `index_documents_bulk(document_ids)` for batch indexing
3. **Verify**
   - Run: `pytest tests/unit/services/test_document_indexing_service.py`

**Acceptance Criteria**:
- [ ] Documents indexed successfully
- [ ] Updates propagated
- [ ] Bulk indexing works (1000 docs/minute)
- [ ] Error handling for failed indexing
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 10 tests (index, update, delete, bulk)

**Files Created/Modified**:
- `backend/app/services/document_indexing_service.py` - Indexing service
- `tests/unit/services/test_document_indexing_service.py` - Indexing tests

---

### Task 3.1.3: Implement Background Indexing Task

**Goal**: Celery task to index documents in background

**Phase**: Phase 3.1
**Dependencies**: Task 3.1.2
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests**
   - Create `tests/unit/tasks/test_document_indexing_task.py`
   - Test: Task indexes single document
   - Test: Task handles failures gracefully
2. **Implement**
   - Create `backend/app/tasks/document_indexing.py`
   - Create Celery task: `index_document_task(document_id)`
   - Call `DocumentIndexingService.index_document()`
   - Add retry logic (max 3 retries)
3. **Verify**
   - Run: `pytest tests/unit/tasks/test_document_indexing_task.py`

**Acceptance Criteria**:
- [ ] Celery task created
- [ ] Task indexes document successfully
- [ ] Retry logic works (max 3 retries)
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 5 tests (task execution, retry, error handling)

**Files Created/Modified**:
- `backend/app/tasks/document_indexing.py` - Indexing task
- `tests/unit/tasks/test_document_indexing_task.py` - Task tests

---

### Task 3.1.4: Trigger Indexing on Document Upload

**Goal**: Automatically index documents when uploaded

**Phase**: Phase 3.1
**Dependencies**: Task 3.1.3
**Estimated Time**: 2 hours

**Steps**:
1. **Implement**
   - Update `DocumentService.create_document()` to trigger indexing task
   - Add: `index_document_task.delay(document.id)`
2. **Test**
   - Upload document via API
   - Verify document indexed to Elasticsearch

**Acceptance Criteria**:
- [ ] Document indexed automatically on upload
- [ ] Indexing happens asynchronously (doesn't block upload)
- [ ] Manual verification passes

**Files Created/Modified**:
- `backend/app/services/document_service.py` - Updated to trigger indexing

---

### Task 3.1.5: Create Multi-Field Search Query Builder

**Goal**: Build Elasticsearch multi_match query with BM25 scoring

**Phase**: Phase 3.1
**Dependencies**: Task 3.1.1
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_search_query_builder.py`
   - Test: Query includes all fields (title, content, author)
   - Test: Field boosting applied (title^3, author^2, content^1)
   - Test: Filters added correctly (document_type, date range)
   - Test: Fuzziness enabled (typo tolerance)
2. **Implement**
   - Create `backend/app/services/search_query_builder.py`
   - Implement `build_query(query_params)` method
   - Create multi_match query with boosting
   - Add filters (term, range)
   - Enable fuzziness: AUTO
3. **Verify**
   - Run: `pytest tests/unit/services/test_search_query_builder.py`

**Acceptance Criteria**:
- [ ] Multi-field query built correctly
- [ ] Field boosting applied
- [ ] Filters work (document_type, date range, department, author)
- [ ] Fuzziness enabled
- [ ] Tests passing (≥90% coverage)

**Test Coverage**:
- Unit tests: 12 tests (query structure, boosting, filters, fuzziness)

**Files Created/Modified**:
- `backend/app/services/search_query_builder.py` - Query builder
- `tests/unit/services/test_search_query_builder.py` - Query builder tests

---

### Task 3.1.6: Implement Facet Aggregations

**Goal**: Add facet aggregations for document_type, department, date histogram

**Phase**: Phase 3.1
**Dependencies**: Task 3.1.5
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `test_search_query_builder.py`
   - Test: Document type aggregation included
   - Test: Department aggregation included
   - Test: Date histogram aggregation included
2. **Implement**
   - Update query builder to add aggregations
   - Add terms aggregation for document_type.keyword
   - Add terms aggregation for department.keyword
   - Add date_histogram aggregation for date field (monthly)
3. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Three aggregations included in query
- [ ] Aggregation results returned in response
- [ ] Facet counts accurate
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 5 tests (aggregations structure, facet counts)

**Files Created/Modified**:
- `backend/app/services/search_query_builder.py` - Updated with aggregations
- `tests/unit/services/test_search_query_builder.py` - Updated with aggregation tests

---

### Task 3.1.7: Create SearchService

**Goal**: Service to execute Elasticsearch queries

**Phase**: Phase 3.1
**Dependencies**: Task 3.1.6
**Estimated Time**: 6 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_search_service.py`
   - Test: `search()` calls Elasticsearch with correct query
   - Test: Results parsed correctly
   - Test: Facets parsed correctly
   - Test: Error handling (Elasticsearch unavailable)
2. **Implement**
   - Create `backend/app/services/search_service.py`
   - Create `SearchService` class with async methods
   - Implement `search(query: SearchQuery)` method
   - Build query using query builder
   - Execute search using elasticsearch-py client
   - Parse results into `SearchResult` objects
   - Parse aggregations into facets dict
   - Track execution time
3. **Verify**
   - Run: `pytest tests/unit/services/test_search_service.py`

**Acceptance Criteria**:
- [ ] Search executes successfully
- [ ] Results parsed correctly
- [ ] Facets parsed correctly
- [ ] Execution time tracked
- [ ] Error handling works
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 15 tests (search, parsing, facets, errors)

**Files Created/Modified**:
- `backend/app/services/search_service.py` - Search service
- `tests/unit/services/test_search_service.py` - Service tests

---

### Task 3.1.8: Unit Tests for SearchService

**Goal**: Comprehensive unit test coverage for SearchService

**Phase**: Phase 3.1
**Dependencies**: Task 3.1.7
**Estimated Time**: 2 hours

**Steps**:
1. **Write additional tests**
   - Test: Simple query (1-3 words) returns results
   - Test: Complex query with filters
   - Test: Pagination works (page, page_size)
   - Test: Empty query handled gracefully
   - Test: Zero results query returns empty list
2. **Run tests**
   - Execute: `pytest tests/unit/services/test_search_service.py -v`
   - Verify coverage: `pytest --cov=app/services/search_service`

**Acceptance Criteria**:
- [ ] All test scenarios covered
- [ ] Code coverage ≥85%
- [ ] All tests passing

**Test Coverage**:
- Unit tests: 20+ tests total

**Files Created/Modified**:
- `tests/unit/services/test_search_service.py` - Expanded tests

---

## Phase 3.2: Search Result Highlighting (15 hours)

### Task 3.2.1: Configure Elasticsearch Highlighting

**Goal**: Enable highlighting in Elasticsearch queries

**Phase**: Phase 3.2
**Dependencies**: Task 3.1.7
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `test_search_query_builder.py`
   - Test: Highlighting configuration included in query
   - Test: Fragment size set to 150
   - Test: Number of fragments set to 3
   - Test: Pre/post tags set to <em>/<\em>
2. **Implement**
   - Update query builder to add highlighting config
   - Set fields: title (no fragments), content (3 fragments, 150 chars)
   - Set pre_tags: ["<em>"]
   - Set post_tags: ["</em>"]
3. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Highlighting config in query
- [ ] Title field: no fragments (full text highlighted)
- [ ] Content field: 3 fragments, 150 chars each
- [ ] Tags: <em></em>
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 4 tests (highlighting configuration)

**Files Created/Modified**:
- `backend/app/services/search_query_builder.py` - Updated with highlighting
- `tests/unit/services/test_search_query_builder.py` - Updated with highlighting tests

---

### Task 3.2.2: Parse Highlights in SearchService

**Goal**: Extract highlights from Elasticsearch response

**Phase**: Phase 3.2
**Dependencies**: Task 3.2.1
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `test_search_service.py`
   - Test: Highlights extracted from response
   - Test: Highlights added to SearchResult objects
   - Test: Content snippet uses first highlight if available
2. **Implement**
   - Update `_parse_results()` method to extract highlights
   - Parse highlights from hit['highlight']
   - Add to SearchResult.highlights list
   - Use first highlight as content_snippet
3. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Highlights extracted correctly
- [ ] Highlights in SearchResult objects
- [ ] Content snippet uses highlights
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 5 tests (highlight parsing, snippet generation)

**Files Created/Modified**:
- `backend/app/services/search_service.py` - Updated to parse highlights
- `tests/unit/services/test_search_service.py` - Updated with highlight tests

---

### Task 3.2.3: Display Highlights in SearchView Frontend

**Goal**: Render highlighted text in search results

**Phase**: Phase 3.2
**Dependencies**: Task 3.2.2
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `webapp/tests/unit/views/SearchView.test.ts`
   - Test: Highlights rendered with HTML
   - Test: <em> tags displayed correctly
2. **Implement**
   - Update `SearchView.vue` template
   - Use `v-html` to render highlights
   - Add CSS styling for <em> tags (yellow background)
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Test in browser

**Acceptance Criteria**:
- [ ] Highlights rendered with HTML
- [ ] <em> tags styled (yellow background)
- [ ] XSS protection (sanitize HTML)
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 4 tests (rendering, styling, XSS)

**Files Created/Modified**:
- `webapp/src/views/SearchView.vue` - Updated to render highlights
- `webapp/tests/unit/views/SearchView.test.ts` - View tests

---

### Task 3.2.4: Integration Tests for Highlighting

**Goal**: End-to-end test for search highlighting

**Phase**: Phase 3.2
**Dependencies**: Task 3.2.3
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests**
   - Create `tests/integration/test_search_highlighting.py`
   - Test: Search query returns highlighted results
   - Test: Highlights include query terms
   - Test: Multiple highlights per document
2. **Run tests**
   - Execute: `pytest tests/integration/test_search_highlighting.py`

**Acceptance Criteria**:
- [ ] Integration tests passing
- [ ] Highlights include query terms
- [ ] Multiple highlights returned

**Test Coverage**:
- Integration tests: 5 tests (highlighting end-to-end)

**Files Created/Modified**:
- `tests/integration/test_search_highlighting.py` - Highlighting integration tests

---

### Task 3.2.5: Highlight Styling and UX Polish

**Goal**: Polish highlight display for better UX

**Phase**: Phase 3.2
**Dependencies**: Task 3.2.3
**Estimated Time**: 2 hours

**Steps**:
1. **Implement**
   - Add CSS for highlights (yellow background, bold)
   - Add ellipsis (...) before/after highlights
   - Limit highlights displayed to 2 per result
2. **Manual testing**
   - Test various query terms
   - Test long highlights

**Acceptance Criteria**:
- [ ] Highlights styled well (yellow bg, bold)
- [ ] Ellipsis added for context
- [ ] Max 2 highlights shown per result

**Files Created/Modified**:
- `webapp/src/views/SearchView.vue` - Updated styling

---

## Phase 3.3: Autocomplete Suggestions (15 hours)

### Task 3.3.1: Implement Elasticsearch Phrase Suggester

**Goal**: Add phrase suggester to SearchService

**Phase**: Phase 3.3
**Dependencies**: Task 3.1.7
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_search_suggestions.py`
   - Test: `get_suggestions()` calls Elasticsearch suggester
   - Test: Suggestions parsed correctly
   - Test: Max 5 suggestions returned
2. **Implement**
   - Add `get_suggestions(partial_query, size=5)` method to SearchService
   - Build Elasticsearch suggest query
   - Use phrase suggester with gram_size=3
   - Parse suggestions from response
3. **Verify**
   - Run: `pytest tests/unit/services/test_search_suggestions.py`

**Acceptance Criteria**:
- [ ] Suggestions returned for partial query
- [ ] Max 5 suggestions
- [ ] Suggestions ranked by score
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 8 tests (suggester, parsing, ranking)

**Files Created/Modified**:
- `backend/app/services/search_service.py` - Add suggestions method
- `tests/unit/services/test_search_suggestions.py` - Suggestion tests

---

### Task 3.3.2: Add Redis Caching for Suggestions

**Goal**: Cache autocomplete suggestions in Redis

**Phase**: Phase 3.3
**Dependencies**: Task 3.3.1
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `test_search_suggestions.py`
   - Test: First request hits Elasticsearch
   - Test: Second request uses Redis cache
   - Test: Cache TTL set to 1 hour
2. **Implement**
   - Check Redis cache first: `redis.get(f"suggest:{query}")`
   - If cache hit, return cached suggestions
   - If cache miss, query Elasticsearch and cache result
   - Set TTL: 3600 seconds (1 hour)
3. **Verify**
   - Run tests
   - Measure response time (cached <50ms)

**Acceptance Criteria**:
- [ ] Cache hit on second request
- [ ] TTL set to 1 hour
- [ ] Cached response <50ms
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 5 tests (cache hit/miss, TTL)

**Files Created/Modified**:
- `backend/app/services/search_service.py` - Updated with caching
- `tests/unit/services/test_search_suggestions.py` - Updated with cache tests

---

### Task 3.3.3: Create Suggestions API Endpoint

**Goal**: GET /api/v1/search/suggest endpoint

**Phase**: Phase 3.3
**Dependencies**: Task 3.3.2
**Estimated Time**: 2 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_search_suggest_api.py`
   - Test: GET /api/v1/search/suggest returns suggestions
   - Test: Query parameter required (minimum 2 chars)
   - Test: Size parameter limits results
2. **Implement**
   - Create endpoint in `backend/app/api/v1/endpoints/search.py`
   - Call `search_service.get_suggestions()`
   - Return JSON response
3. **Verify**
   - Run: `pytest tests/integration/test_search_suggest_api.py`

**Acceptance Criteria**:
- [ ] Endpoint returns suggestions
- [ ] Minimum query length: 2 chars
- [ ] Size parameter works
- [ ] Response time <200ms
- [ ] Tests passing

**Test Coverage**:
- Integration tests: 6 tests (suggestions, validation, performance)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/search.py` - Add suggest endpoint
- `tests/integration/test_search_suggest_api.py` - Suggest API tests

---

### Task 3.3.4: Implement Autocomplete UI Component

**Goal**: Autocomplete search input with suggestions

**Phase**: Phase 3.3
**Dependencies**: Task 3.3.3
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `webapp/tests/unit/components/SearchAutocomplete.test.ts`
   - Test: Suggestions fetched on input
   - Test: Suggestions displayed in dropdown
   - Test: Selecting suggestion executes search
2. **Implement**
   - Update SearchView.vue to use v-autocomplete
   - Watch searchInput and call suggestions API
   - Display suggestions in dropdown
   - On select, execute search
3. **Verify**
   - Run: `npm run test:unit`
   - Manual: Test autocomplete

**Acceptance Criteria**:
- [ ] Autocomplete dropdown appears
- [ ] Suggestions fetched on typing (debounced 300ms)
- [ ] Selecting suggestion executes search
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 6 tests (input, fetch, select)

**Files Created/Modified**:
- `webapp/src/views/SearchView.vue` - Updated with autocomplete
- `webapp/tests/unit/components/SearchAutocomplete.test.ts` - Autocomplete tests

---

### Task 3.3.5: Autocomplete Performance Optimization

**Goal**: Ensure autocomplete response <200ms

**Phase**: Phase 3.3
**Dependencies**: Task 3.3.4
**Estimated Time**: 2 hours

**Steps**:
1. **Performance testing**
   - Measure suggestion response time
   - Target: <200ms
2. **Optimize if needed**
   - Increase Redis cache hit rate
   - Reduce suggestion size to 5
3. **Verify**
   - Re-measure response time

**Acceptance Criteria**:
- [ ] Suggestion response <200ms (p95)
- [ ] Cache hit rate >80%

**Files Created/Modified**:
- `tests/performance/test_autocomplete_performance.py` - Performance tests

---

## Phase 3.4: Search Analytics (15 hours)

### Task 3.4.1: Create search_analytics Database Table

**Goal**: Table to track search queries and usage

**Phase**: Phase 3.4
**Dependencies**: None
**Estimated Time**: 2 hours

**Steps**:
1. **Create migration**
   - Run: `alembic revision -m "create search_analytics table"`
   - Define table schema (see technical plan)
   - Add indexes on user_id, created_at, query (GIN index)
2. **Apply migration**
   - Run: `alembic upgrade head`
3. **Verify**
   - Check table exists: `psql -c "\d search_analytics"`

**Acceptance Criteria**:
- [ ] Table created successfully
- [ ] All fields present
- [ ] Indexes created
- [ ] Migration reversible

**Files Created/Modified**:
- `backend/alembic/versions/XXX_create_search_analytics.py` - Migration

---

### Task 3.4.2: Implement Search Tracking in SearchService

**Goal**: Track all search queries in database

**Phase**: Phase 3.4
**Dependencies**: Task 3.4.1
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Add tests to `test_search_service.py`
   - Test: Search query tracked in database
   - Test: Analytics record includes all fields
2. **Implement**
   - Add `_track_search()` method to SearchService
   - Insert analytics record after search execution
   - Include: user_id, query, filters, total_results, execution_time_ms
3. **Verify**
   - Run tests
   - Query analytics table

**Acceptance Criteria**:
- [ ] Search tracked successfully
- [ ] All fields populated correctly
- [ ] Async tracking (doesn't block response)
- [ ] Tests passing

**Test Coverage**:
- Unit tests: 5 tests (tracking, fields, async)

**Files Created/Modified**:
- `backend/app/services/search_service.py` - Updated with tracking
- `tests/unit/services/test_search_service.py` - Updated with tracking tests

---

### Task 3.4.3: Create Search Analytics Service

**Goal**: Service to query and analyze search data

**Phase**: Phase 3.4
**Dependencies**: Task 3.4.2
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_search_analytics_service.py`
   - Test: `get_top_queries()` returns top queries
   - Test: `get_zero_result_queries()` returns zero-result queries
   - Test: Date range filtering works
2. **Implement**
   - Create `backend/app/services/search_analytics_service.py`
   - Implement `get_top_queries(date_from, date_to, limit=50)`
   - Implement `get_zero_result_queries(date_from, date_to, limit=50)`
   - Implement `get_analytics_summary(date_from, date_to)`
3. **Verify**
   - Run: `pytest tests/unit/services/test_search_analytics_service.py`

**Acceptance Criteria**:
- [ ] Top queries returned (ordered by count DESC)
- [ ] Zero-result queries returned
- [ ] Analytics summary calculated (total searches, unique users, avg results)
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 10 tests (queries, aggregations, filters)

**Files Created/Modified**:
- `backend/app/services/search_analytics_service.py` - Analytics service
- `tests/unit/services/test_search_analytics_service.py` - Analytics tests

---

### Task 3.4.4: Create Analytics API Endpoint

**Goal**: GET /api/v1/search/analytics endpoint (admin only)

**Phase**: Phase 3.4
**Dependencies**: Task 3.4.3
**Estimated Time**: 2 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_search_analytics_api.py`
   - Test: GET /api/v1/search/analytics returns analytics
   - Test: Admin only (403 for non-admin)
   - Test: Date range filtering
2. **Implement**
   - Create endpoint in search.py
   - Call analytics service
   - Return JSON response
   - Require admin role
3. **Verify**
   - Run: `pytest tests/integration/test_search_analytics_api.py`

**Acceptance Criteria**:
- [ ] Endpoint returns analytics
- [ ] Admin-only access (403 for non-admin)
- [ ] Date range filtering works
- [ ] Tests passing

**Test Coverage**:
- Integration tests: 5 tests (analytics, auth, filters)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/search.py` - Add analytics endpoint
- `tests/integration/test_search_analytics_api.py` - Analytics API tests

---

### Task 3.4.5: Create Analytics Dashboard UI (Admin)

**Goal**: Admin dashboard to view search analytics

**Phase**: Phase 3.4
**Dependencies**: Task 3.4.4
**Estimated Time**: 4 hours

**Steps**:
1. **Create component**
   - Create `webapp/src/views/admin/SearchAnalyticsView.vue`
   - Fetch analytics data from API
   - Display top queries (table)
   - Display zero-result queries (table)
   - Display summary metrics (cards)
2. **Add route**
   - Add route: `/admin/search-analytics`
   - Require admin role
3. **Manual testing**
   - Test in browser

**Acceptance Criteria**:
- [ ] Dashboard displays top queries
- [ ] Dashboard displays zero-result queries
- [ ] Summary metrics shown (total searches, unique users, avg results)
- [ ] Admin-only access

**Files Created/Modified**:
- `webapp/src/views/admin/SearchAnalyticsView.vue` - Analytics dashboard
- `webapp/src/router/index.ts` - Add analytics route

---

## Phase 3.5: Testing & Performance Tuning (15 hours)

### Task 3.5.1: Integration Tests for Search API

**Goal**: Comprehensive integration tests for search endpoints

**Phase**: Phase 3.5
**Dependencies**: All Phase 3.1-3.4 tasks completed
**Estimated Time**: 5 hours

**Steps**:
1. **Write tests**
   - Create `tests/integration/test_search_api.py`
   - Test: Simple search query
   - Test: Complex search with filters
   - Test: Faceted search
   - Test: Pagination
   - Test: Suggestions
   - Test: Analytics (admin)
2. **Run tests**
   - Execute: `pytest tests/integration/test_search_api.py -v`

**Acceptance Criteria**:
- [ ] All integration tests passing
- [ ] All endpoints tested
- [ ] Error cases tested

**Test Coverage**:
- Integration tests: 20+ tests

**Files Created/Modified**:
- `tests/integration/test_search_api.py` - Search API integration tests

---

### Task 3.5.2: E2E Tests with Playwright

**Goal**: End-to-end tests for search workflow

**Phase**: Phase 3.5
**Dependencies**: All frontend tasks completed
**Estimated Time**: 5 hours

**Steps**:
1. **Write tests**
   - Create `webapp/tests/e2e/search.spec.ts`
   - Test: Navigate to search page
   - Test: Type search query → results shown
   - Test: Autocomplete suggestions appear
   - Test: Apply facet filter → results update
   - Test: Click result → document opens
2. **Run tests**
   - Execute: `npx playwright test`

**Acceptance Criteria**:
- [ ] All E2E tests passing
- [ ] Full search workflow tested

**Test Coverage**:
- E2E tests: 8 tests (search workflow)

**Files Created/Modified**:
- `webapp/tests/e2e/search.spec.ts` - Search E2E tests

---

### Task 3.5.3: Performance Testing (50 Concurrent Users)

**Goal**: Load test search API with 50 concurrent users

**Phase**: Phase 3.5
**Dependencies**: All backend tasks completed
**Estimated Time**: 3 hours

**Steps**:
1. **Setup load testing**
   - Install Locust: `pip install locust`
   - Create `tests/performance/locustfile_search.py`
   - Define search scenario (random queries)
2. **Run load test**
   - Execute: `locust -f tests/performance/locustfile_search.py`
   - Run with 50 users
   - Measure: requests/sec, response time (p50, p95, p99), error rate
3. **Analyze results**
   - Verify: p95 response time <500ms
   - Verify: Error rate <1%

**Acceptance Criteria**:
- [ ] 50 concurrent users supported
- [ ] p95 response time <500ms
- [ ] Error rate <1%
- [ ] Elasticsearch CPU <80%

**Files Created/Modified**:
- `tests/performance/locustfile_search.py` - Load test script

---

### Task 3.5.4: Elasticsearch Query Optimization

**Goal**: Optimize Elasticsearch queries for performance

**Phase**: Phase 3.5
**Dependencies**: Task 3.5.3
**Estimated Time**: 2 hours

**Steps**:
1. **Profile queries**
   - Use Elasticsearch profile API
   - Identify slow queries
2. **Optimize**
   - Tune field boosting
   - Limit aggregation size
   - Use `from`+`size` pagination (not `search_after` for MVP)
3. **Re-test**
   - Run load test again
   - Verify improvements

**Acceptance Criteria**:
- [ ] Query response time improved ≥20%
- [ ] No slow queries (>500ms)

**Files Created/Modified**:
- `backend/app/services/search_query_builder.py` - Optimized queries

---

## Deployment Checklist

### Infrastructure
- [ ] Elasticsearch 8.11 cluster running (2 nodes minimum)
- [ ] Redis 7.2 running (for suggestions cache)
- [ ] PostgreSQL search_analytics table created

### Configuration
- [ ] Environment variables set:
  - `ELASTICSEARCH_URL=http://elasticsearch:9200`
  - `ELASTICSEARCH_INDEX=documents`
  - `REDIS_URL=redis://redis:6379`
  - `SEARCH_ANALYTICS_ENABLED=true`
- [ ] Elasticsearch index created with mapping
- [ ] Initial documents indexed

### Data Migration
- [ ] Existing documents indexed to Elasticsearch:
  ```bash
  python scripts/index_all_documents.py
  ```

### Monitoring
- [ ] Elasticsearch monitoring enabled (CPU, memory, disk)
- [ ] Search analytics dashboard accessible to admins
- [ ] Alert if search response time >1 second

---

## Summary

**Total Tasks**: 30 tasks across 5 phases
**Total Estimated Time**: 90 hours (3 weeks)

**Phase Breakdown**:
- Phase 3.1 (Elasticsearch Integration): 30 hours, 8 tasks
- Phase 3.2 (Highlighting): 15 hours, 5 tasks
- Phase 3.3 (Autocomplete): 15 hours, 5 tasks
- Phase 3.4 (Analytics): 15 hours, 5 tasks
- Phase 3.5 (Testing & Optimization): 15 hours, 4 tasks

**Test Coverage Targets**:
- Unit tests: ≥85%
- Integration tests: ≥80%
- E2E tests: Critical workflows covered
- Performance: 50 concurrent users, p95 <500ms

**Performance Targets Met**:
- Simple search: <300ms
- Complex search: <500ms
- Autocomplete: <200ms
- Load test: 50 users, p95 <500ms
