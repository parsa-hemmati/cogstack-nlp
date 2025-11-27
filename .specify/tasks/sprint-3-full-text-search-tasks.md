# Tasks: Sprint 3 - Full-Text Search Enhancement

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Ready for Implementation
**Plan Reference**: `.specify/plans/sprint-3-full-text-search-plan.md` v1.0.0
**Specification**: `.specify/specifications/sprint-3-full-text-search.md` v1.0.0

**Total Estimated Time**: 120 hours (4 weeks)
**Total Tasks**: 65 tasks
**Dependencies**:
- Sprint 2 Timeline View COMPLETE
- PostgreSQL 15+ running
- Docker Compose configured
- Alembic migrations set up

---

## Task Execution Strategy

**Parallel Opportunities**:
- Phase 1 Tasks 1-5 can run in parallel with Tasks 6-8 (infrastructure vs backend service)
- Phase 2 and Phase 3 can partially overlap (backend query parsing + frontend UI)
- Phase 4 and Phase 5 can run in parallel (saved searches + analytics)

**Critical Path**:
Task 1 (Elasticsearch setup) → Task 6 (SearchIndexer) → Task 9 (Basic search) → Rest of implementation

**Test-First Approach**:
Every task follows TDD: Write tests → Run tests (fail) → Implement → Run tests (pass) → Refactor

---

## Phase 1: Core Search Infrastructure (Week 1, 30 hours)

**Objective**: Set up Elasticsearch, basic search, and indexing

### Task 1.1: Add Elasticsearch to Docker Compose (2 hours)

**Goal**: Configure Elasticsearch 8.11 service in Docker Compose with health checks and volume persistence

**Prerequisites**:
- Docker Compose file exists (`docker-compose.yml`)
- Understand existing service configuration

**Steps**:
1. **Add Elasticsearch service to docker-compose.yml**
   - Add elasticsearch service (docker.elastic.co/elasticsearch/elasticsearch:8.11.0)
   - Configure environment variables (discovery.type=single-node, xpack.security.enabled=false)
   - Set Java heap size (ES_JAVA_OPTS=-Xms2g -Xmx2g)
   - Configure ulimits for memory lock
   - Add volume (es_data:/usr/share/elasticsearch/data)
   - Expose port 9200
   - Add health check (curl cluster health)
2. **Add Redis service to docker-compose.yml**
   - Add redis service (redis:7-alpine)
   - Expose port 6379
   - Add volume (redis_data:/data)
   - Configure persistence (appendonly yes)
3. **Test services**
   - Run `docker-compose up elasticsearch redis`
   - Verify Elasticsearch: `curl http://localhost:9200/_cluster/health`
   - Verify Redis: `redis-cli ping`
   - Run `docker-compose down`

**Acceptance Criteria**:
- [ ] Elasticsearch service added to docker-compose.yml
- [ ] Redis service added to docker-compose.yml
- [ ] Environment variables configured correctly
- [ ] Health checks defined for both services
- [ ] Volumes configured for data persistence
- [ ] Services start successfully: `docker-compose up -d elasticsearch redis`
- [ ] Elasticsearch health check returns "green" or "yellow"
- [ ] Redis responds to PING command
- [ ] Services stop cleanly: `docker-compose down`

**Files Created/Modified**:
- `docker-compose.yml` - Add elasticsearch and redis services
- `.env.example` - Add ELASTICSEARCH_URL, REDIS_URL

**Estimated Time**: 2 hours

**Testing**:
```bash
# Start services
docker-compose up -d elasticsearch redis

# Test Elasticsearch
curl http://localhost:9200/_cluster/health

# Test Redis
docker-compose exec redis redis-cli ping
# Expected: PONG

# Cleanup
docker-compose down
```

---

### Task 1.2: Create Elasticsearch Index Mapping (3 hours)

**Goal**: Define Elasticsearch documents index schema with custom analyzer for clinical text

**Prerequisites**:
- Task 1.1 completed (Elasticsearch running)

**Steps**:
1. **Create mapping JSON file**
   - Create `backend/elasticsearch/documents-mapping.json`
   - Define index settings (shards=2, replicas=1, refresh_interval=30s)
   - Define custom analyzer (clinical_analyzer with english stop words, stemmer, synonyms)
   - Define synonym filter (MI→myocardial infarction, CAD→coronary artery disease, etc.)
   - Define field mappings (document_id, title, content, document_type, author, department, date, patient_id, concepts, indexed_at)
   - Set field types (text with analyzer, keyword, date, nested for concepts)
   - Add title.raw field for sorting
2. **Create index creation script**
   - Create `backend/scripts/create_search_index.py`
   - Read mapping from JSON file
   - Delete existing index if exists
   - Create index with mapping
   - Verify index created
3. **Test index creation**
   - Run `python backend/scripts/create_search_index.py`
   - Verify index: `curl http://localhost:9200/documents`

**Acceptance Criteria**:
- [ ] documents-mapping.json created with complete schema
- [ ] Custom clinical_analyzer defined with synonyms
- [ ] All required fields defined (document_id, title, content, document_type, author, department, date, patient_id, concepts, indexed_at)
- [ ] Field types correct (text vs keyword vs date)
- [ ] Nested concepts field for concept array
- [ ] create_search_index.py script created
- [ ] Script successfully creates index
- [ ] Index mapping verified: `curl http://localhost:9200/documents/_mapping`
- [ ] Script is idempotent (can run multiple times)

**Files Created/Modified**:
- `backend/elasticsearch/documents-mapping.json` - Elasticsearch index mapping (~150 lines)
- `backend/scripts/create_search_index.py` - Index creation script (~50 lines)
- `backend/requirements.txt` - Add elasticsearch[async]>=8.11.0

**Estimated Time**: 3 hours

**Testing**:
```bash
# Create index
cd backend
python scripts/create_search_index.py

# Verify index
curl http://localhost:9200/documents
curl http://localhost:9200/documents/_mapping

# Test analyzer
curl -X POST "http://localhost:9200/documents/_analyze" -H 'Content-Type: application/json' -d '{
  "analyzer": "clinical_analyzer",
  "text": "Patient diagnosed with MI (myocardial infarction)"
}'
# Expected: tokens for "patient", "diagnose", "mi", "myocardial", "infarction"
```

---

### Task 1.3: Create Elasticsearch Client Module (2 hours)

**Goal**: Create async Elasticsearch client wrapper for application use

**Prerequisites**:
- Task 1.2 completed (index created)

**Steps**:
1. **Write client tests first** (TDD)
   - Create `backend/tests/unit/clients/test_elasticsearch_client.py`
   - Test: `get_client()` returns AsyncElasticsearch instance
   - Test: `health_check()` returns cluster health status
   - Test: `close()` closes client connection
2. **Implement Elasticsearch client**
   - Create `backend/app/clients/elasticsearch_client.py`
   - Add `get_es_client()` function (returns AsyncElasticsearch with URL from env)
   - Add `health_check()` async function
   - Add context manager support (`async with get_es_client()`)
3. **Run tests**
   - `pytest backend/tests/unit/clients/test_elasticsearch_client.py -v`

**Acceptance Criteria**:
- [ ] elasticsearch_client.py module created
- [ ] `get_es_client()` function returns AsyncElasticsearch instance
- [ ] ELASTICSEARCH_URL loaded from environment variable
- [ ] Context manager support (async with)
- [ ] Unit tests written and passing (3 tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `backend/app/clients/elasticsearch_client.py` - ES client module (~40 lines)
- `backend/app/clients/__init__.py` - Export get_es_client
- `backend/tests/unit/clients/test_elasticsearch_client.py` - Unit tests (~60 lines)

**Estimated Time**: 2 hours

**Testing**:
```bash
pytest backend/tests/unit/clients/test_elasticsearch_client.py -v --cov=app/clients/elasticsearch_client
```

---

### Task 1.4: Create Database Migration for Search Tables (2 hours)

**Goal**: Create saved_searches and search_analytics tables with indexes

**Prerequisites**:
- PostgreSQL database running
- Alembic configured

**Steps**:
1. **Create migration file**
   - Run `cd backend && alembic revision -m "add_search_tables"`
   - Add saved_searches table (id, user_id, name, description, query, filters, is_shared, execution_count, created_at, updated_at)
   - Add search_analytics table (id, user_id, query, filters, results_count, execution_time_ms, clicked_documents, created_at)
   - Add indexes (user_id, query GIN tsvector, created_at DESC, results_count)
   - Add unique constraint (user_id, name) for saved_searches
   - Add indexed and last_indexed_at columns to documents table
2. **Test migration**
   - Run `alembic upgrade head`
   - Verify tables: `docker-compose exec postgres psql -U clinicaltools -d clinical_care_tools -c "\dt"`
   - Verify indexes: `\di`
   - Run `alembic downgrade -1`
   - Verify tables dropped

**Acceptance Criteria**:
- [ ] Migration file created (010_add_search_tables.py)
- [ ] saved_searches table created with all fields
- [ ] search_analytics table created with all fields
- [ ] documents table updated (indexed, last_indexed_at columns)
- [ ] All indexes created correctly
- [ ] Unique constraint on (user_id, name) for saved_searches
- [ ] upgrade() runs successfully
- [ ] downgrade() runs successfully
- [ ] Foreign keys to users table work

**Files Created/Modified**:
- `backend/alembic/versions/010_add_search_tables.py` - Database migration (~150 lines)

**Estimated Time**: 2 hours

**Testing**:
```bash
cd backend

# Run migration
alembic upgrade head

# Verify tables
docker-compose exec postgres psql -U clinicaltools -d clinical_care_tools \
  -c "\d saved_searches"
docker-compose exec postgres psql -U clinicaltools -d clinical_care_tools \
  -c "\d search_analytics"

# Test downgrade
alembic downgrade -1

# Re-upgrade for next tasks
alembic upgrade head
```

---

### Task 1.5: Create SQLAlchemy Models for Search Tables (2 hours)

**Goal**: Create SavedSearch and SearchAnalytics SQLAlchemy models

**Prerequisites**:
- Task 1.4 completed (tables exist)

**Steps**:
1. **Write model tests first** (TDD)
   - Create `backend/tests/unit/models/test_saved_search.py`
   - Test: Create SavedSearch with valid data
   - Test: Unique constraint enforced (user_id, name)
   - Test: Relationship to User model works
   - Create `backend/tests/unit/models/test_search_analytics.py`
   - Test: Create SearchAnalytics with valid data
   - Test: clicked_documents array field works
2. **Implement models**
   - Create `backend/app/models/saved_search.py`
   - Add SavedSearch class (inherits Base)
   - Add all fields matching database schema
   - Add relationship to User
   - Create `backend/app/models/search_analytics.py`
   - Add SearchAnalytics class
   - Add relationship to User
3. **Run tests**
   - `pytest backend/tests/unit/models/test_saved_search.py -v`
   - `pytest backend/tests/unit/models/test_search_analytics.py -v`

**Acceptance Criteria**:
- [ ] SavedSearch model created
- [ ] SearchAnalytics model created
- [ ] All fields match database schema
- [ ] Relationships to User model defined
- [ ] Models exported from app/models/__init__.py
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `backend/app/models/saved_search.py` - SavedSearch model (~40 lines)
- `backend/app/models/search_analytics.py` - SearchAnalytics model (~35 lines)
- `backend/app/models/__init__.py` - Export new models
- `backend/tests/unit/models/test_saved_search.py` - Unit tests (~80 lines)
- `backend/tests/unit/models/test_search_analytics.py` - Unit tests (~60 lines)

**Estimated Time**: 2 hours

**Testing**:
```bash
pytest backend/tests/unit/models/test_saved_search.py -v --cov=app/models/saved_search
pytest backend/tests/unit/models/test_search_analytics.py -v --cov=app/models/search_analytics
```

---

### Task 1.6: Implement SearchIndexer Service (5 hours)

**Goal**: Create service to batch index documents from PostgreSQL to Elasticsearch

**Prerequisites**:
- Task 1.2 completed (Elasticsearch index created)
- Task 1.3 completed (ES client available)
- Task 1.4 completed (indexed column added to documents)

**Steps**:
1. **Write SearchIndexer tests first** (TDD)
   - Create `backend/tests/unit/services/test_search_indexer.py`
   - Test: `_get_unindexed_documents()` returns documents where indexed=False
   - Test: `_decrypt_content()` decrypts document content
   - Test: `_extract_concepts()` extracts concepts from document entities
   - Test: `index_documents_batch()` indexes documents to ES
   - Test: `index_documents_batch()` marks documents as indexed=True
   - Test: `index_documents_batch()` handles errors gracefully
2. **Implement SearchIndexer service**
   - Create `backend/app/services/search_indexer.py`
   - Add SearchIndexer class (`__init__(es, db)`)
   - Add `_get_unindexed_documents(batch_size)` → List[Document]
   - Add `_decrypt_content(encrypted_content)` → str
   - Add `_extract_concepts(document)` → List[Dict] (from extracted_entities)
   - Add `index_documents_batch(batch_size=1000)` → int (count indexed)
   - Use `helpers.async_bulk()` for batch indexing
   - Handle errors (log and continue)
3. **Run tests**
   - `pytest backend/tests/unit/services/test_search_indexer.py -v`

**Acceptance Criteria**:
- [ ] SearchIndexer class created
- [ ] Batch indexing implemented (default 1000 docs per batch)
- [ ] Document content decrypted before indexing
- [ ] Concepts extracted from extracted_entities table
- [ ] Documents marked as indexed=True after successful indexing
- [ ] Elasticsearch bulk API used for performance
- [ ] Error handling for indexing failures
- [ ] Unit tests written and passing (6+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `backend/app/services/search_indexer.py` - SearchIndexer service (~150 lines)
- `backend/app/services/__init__.py` - Export SearchIndexer
- `backend/tests/unit/services/test_search_indexer.py` - Unit tests (~200 lines)

**Estimated Time**: 5 hours

**Testing**:
```bash
pytest backend/tests/unit/services/test_search_indexer.py -v --cov=app/services/search_indexer
```

---

### Task 1.7: Create Background Indexer Job (3 hours)

**Goal**: Create background job to continuously index documents every 5 minutes

**Prerequisites**:
- Task 1.6 completed (SearchIndexer service exists)

**Steps**:
1. **Create background job script**
   - Create `backend/app/jobs/search_indexer_job.py`
   - Add `run_indexer()` async function
   - Continuous loop: index batch → sleep 5 minutes → repeat
   - Load SEARCH_BATCH_INTERVAL_MINUTES from env (default 5)
   - Error handling and logging
   - Graceful shutdown on SIGTERM
2. **Add indexer service to docker-compose.yml**
   - Add indexer service
   - Use same backend image
   - Override command: `python -m app.jobs.search_indexer_job`
   - Depend on postgres, elasticsearch
   - Same environment as backend
3. **Test background job**
   - Create test document in database (indexed=False)
   - Run indexer job manually
   - Verify document indexed in Elasticsearch
   - Verify document.indexed=True in PostgreSQL

**Acceptance Criteria**:
- [ ] search_indexer_job.py created with continuous loop
- [ ] Batch interval configurable via environment variable
- [ ] Error handling and logging implemented
- [ ] Graceful shutdown on SIGTERM
- [ ] Indexer service added to docker-compose.yml
- [ ] Job runs successfully: `docker-compose up indexer`
- [ ] Documents indexed every 5 minutes
- [ ] Job logs indexing activity

**Files Created/Modified**:
- `backend/app/jobs/search_indexer_job.py` - Background job (~80 lines)
- `backend/app/jobs/__init__.py` - Create jobs package
- `docker-compose.yml` - Add indexer service
- `.env.example` - Add SEARCH_BATCH_INTERVAL_MINUTES

**Estimated Time**: 3 hours

**Testing**:
```bash
# Manual test
cd backend
python -m app.jobs.search_indexer_job

# In another terminal, add test document
docker-compose exec postgres psql -U clinicaltools -d clinical_care_tools \
  -c "INSERT INTO documents (filename, content, indexed) VALUES ('test.txt', 'test content', FALSE);"

# Wait 5 minutes or check logs

# Verify indexed
curl http://localhost:9200/documents/_search?q=test
```

---

### Task 1.8: Create Pydantic Search Schemas (3 hours)

**Goal**: Create request/response schemas for search API

**Prerequisites**:
- None (schemas are independent)

**Steps**:
1. **Write schema tests first** (TDD)
   - Create `backend/tests/unit/schemas/test_search_schemas.py`
   - Test: SearchRequest validates query field (required)
   - Test: SearchRequest accepts filters (optional)
   - Test: SearchRequest validates page_size (max 100)
   - Test: SearchResponse includes all required fields
   - Test: SearchResultDocument includes highlights
   - Test: Facets structure correct
2. **Implement search schemas**
   - Create `backend/app/schemas/search.py`
   - Add SearchFilters (document_types, authors, departments, date_range)
   - Add SearchRequest (query, filters, page, page_size, sort)
   - Add Highlight (field, snippets)
   - Add SearchResultDocument (document_id, title, document_type, author, date, department, relevance_score, highlights)
   - Add FacetValue (value, count)
   - Add Facets (document_types, authors, departments, date_range)
   - Add SearchResponse (query, total_results, page, page_size, documents, facets, execution_time_ms)
   - Add SavedSearchCreate, SavedSearchResponse
   - Add SearchAnalyticsResponse
3. **Run tests**
   - `pytest backend/tests/unit/schemas/test_search_schemas.py -v`

**Acceptance Criteria**:
- [ ] All search schemas created (10+ schemas)
- [ ] SearchRequest validates query (required, max 1000 chars)
- [ ] SearchRequest validates page_size (max 100)
- [ ] SearchRequest validates sort enum (relevance, date, title)
- [ ] SearchResultDocument includes highlights array
- [ ] Facets structure matches ES aggregations response
- [ ] Unit tests written and passing (6+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `backend/app/schemas/search.py` - Search schemas (~250 lines)
- `backend/app/schemas/__init__.py` - Export search schemas
- `backend/tests/unit/schemas/test_search_schemas.py` - Unit tests (~150 lines)

**Estimated Time**: 3 hours

**Testing**:
```bash
pytest backend/tests/unit/schemas/test_search_schemas.py -v --cov=app/schemas/search
```

---

### Task 1.9: Implement Basic SearchService (5 hours)

**Goal**: Create SearchService with basic keyword search (no boolean operators yet)

**Prerequisites**:
- Task 1.3 completed (ES client available)
- Task 1.8 completed (schemas exist)

**Steps**:
1. **Write SearchService tests first** (TDD)
   - Create `backend/tests/unit/services/test_search_service.py`
   - Test: `search_documents()` returns SearchResponse
   - Test: `search_documents()` queries Elasticsearch
   - Test: `search_documents()` applies filters (document_type)
   - Test: `search_documents()` paginates results
   - Test: `search_documents()` logs audit trail
   - Test: `search_documents()` tracks analytics
2. **Implement SearchService**
   - Create `backend/app/services/search_service.py`
   - Add SearchService class (`__init__(es, db, audit)`)
   - Add `search_documents(request, user, ip_address)` → SearchResponse
   - Build simple Elasticsearch query (multi_match on title/content)
   - Apply filters (document_type, author, department, date_range)
   - Add field boosting (title^10, content^1)
   - Execute search with highlighting
   - Parse ES response to SearchResponse
   - Track analytics (search_analytics table)
   - Audit log search
3. **Run tests**
   - `pytest backend/tests/unit/services/test_search_service.py -v`

**Acceptance Criteria**:
- [ ] SearchService class created
- [ ] `search_documents()` method implemented
- [ ] Simple keyword search working (multi_match)
- [ ] Field boosting applied (title^10, content^1)
- [ ] Filters implemented (document_type, author, department, date_range)
- [ ] Pagination working (page, page_size)
- [ ] Highlighting configured (title, content)
- [ ] Analytics tracked (search_analytics table)
- [ ] Audit log created (action=SEARCH_EXECUTED)
- [ ] Unit tests written and passing (6+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `backend/app/services/search_service.py` - SearchService (~200 lines)
- `backend/app/services/__init__.py` - Export SearchService
- `backend/tests/unit/services/test_search_service.py` - Unit tests (~250 lines)

**Estimated Time**: 5 hours

**Testing**:
```bash
pytest backend/tests/unit/services/test_search_service.py -v --cov=app/services/search_service
```

---

### Task 1.10: Create Basic Search API Endpoint (3 hours)

**Goal**: Implement POST /api/v1/search endpoint with authentication

**Prerequisites**:
- Task 1.9 completed (SearchService exists)

**Steps**:
1. **Write endpoint tests first** (TDD)
   - Create `backend/tests/integration/test_search_api.py`
   - Test: POST /search with valid query returns 200
   - Test: POST /search without auth returns 401
   - Test: POST /search with filters returns filtered results
   - Test: POST /search validates request (query required)
2. **Implement search endpoint**
   - Create `backend/app/api/v1/endpoints/search.py`
   - Add `POST /api/v1/search` route
   - Add authentication dependency (get_current_user)
   - Validate request (SearchRequest schema)
   - Call SearchService.search_documents()
   - Return SearchResponse
   - Handle errors (400, 500)
3. **Add to main app**
   - Include search router in `app/main.py`
4. **Test endpoint**
   - `pytest backend/tests/integration/test_search_api.py -v`
   - Manual curl test

**Acceptance Criteria**:
- [ ] POST /api/v1/search endpoint created
- [ ] Authentication required (JWT token)
- [ ] Request body validated (SearchRequest)
- [ ] Calls SearchService.search_documents()
- [ ] Returns SearchResponse (200)
- [ ] Error handling (400 for validation, 401 for auth, 500 for server)
- [ ] Integration tests written and passing (4+ tests)
- [ ] Manual curl test successful

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/search.py` - Search endpoints (~100 lines)
- `backend/app/api/v1/__init__.py` - Create v1 package if not exists
- `backend/app/main.py` - Include search router
- `backend/tests/integration/test_search_api.py` - Integration tests (~150 lines)

**Estimated Time**: 3 hours

**Testing**:
```bash
# Integration tests
pytest backend/tests/integration/test_search_api.py -v

# Manual test (get token first)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' | jq -r '.access_token')

# Execute search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"diabetes","page":1,"page_size":20}'
```

---

## Phase 2: Advanced Query Parsing (Week 2, 30 hours)

**Objective**: Boolean operators, phrase search, field-specific search, relevance ranking

### Task 2.1: Create QueryBuilder Basic Structure (2 hours)

**Goal**: Create QueryBuilder class with query type detection

**Prerequisites**:
- None (standalone module)

**Steps**:
1. **Write QueryBuilder tests first** (TDD)
   - Create `backend/tests/unit/search/test_query_builder.py`
   - Test: `_is_phrase_query()` detects quoted strings
   - Test: `_is_boolean_query()` detects AND/OR/NOT keywords
   - Test: `_is_field_query()` detects field:value syntax
   - Test: `build_query()` returns dict with query structure
2. **Implement QueryBuilder**
   - Create `backend/app/search/query_builder.py`
   - Add QueryBuilder class
   - Add `_is_phrase_query(query)` → bool
   - Add `_is_boolean_query(query)` → bool
   - Add `_is_field_query(query)` → bool
   - Add `build_query(query, filters, page, page_size, sort)` → Dict
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py -v`

**Acceptance Criteria**:
- [ ] QueryBuilder class created
- [ ] Query type detection methods implemented
- [ ] `build_query()` returns Elasticsearch DSL dict
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `backend/app/search/query_builder.py` - QueryBuilder class (~60 lines)
- `backend/app/search/__init__.py` - Create search package
- `backend/tests/unit/search/test_query_builder.py` - Unit tests (~100 lines)

**Estimated Time**: 2 hours

**Testing**:
```bash
pytest backend/tests/unit/search/test_query_builder.py -v --cov=app/search/query_builder
```

---

### Task 2.2: Implement Simple Keyword Query Building (2 hours)

**Goal**: Build Elasticsearch query for simple keyword search with field boosting

**Prerequisites**:
- Task 2.1 completed (QueryBuilder structure exists)

**Steps**:
1. **Write tests first** (TDD)
   - Add to `backend/tests/unit/search/test_query_builder.py`
   - Test: `_build_simple_query("diabetes")` returns multi_match query
   - Test: Field boosting applied (title^10, content^1, author^2)
   - Test: minimum_should_match=1
2. **Implement simple query builder**
   - Add `_build_simple_query(query)` → Dict to QueryBuilder
   - Build bool query with should clauses
   - Add match queries for title (boost 10), content (boost 1), author (boost 2)
   - Set minimum_should_match=1
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_build_simple_query -v`

**Acceptance Criteria**:
- [ ] `_build_simple_query()` implemented
- [ ] Returns bool query with should clauses
- [ ] Field boosting correct (title^10, content^1, author^2)
- [ ] minimum_should_match=1
- [ ] Unit tests written and passing (3+ tests)
- [ ] Test coverage ≥ 90%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add _build_simple_query method (~15 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~50 lines)

**Estimated Time**: 2 hours

---

### Task 2.3: Implement Phrase Query Building (2 hours)

**Goal**: Build Elasticsearch query for phrase search (exact match)

**Prerequisites**:
- Task 2.2 completed (simple query works)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `_build_phrase_query('"chest pain"')` returns phrase query
   - Test: Multiple phrases supported ("diabetes" AND "chest pain")
   - Test: Phrase extracted from quotes correctly
2. **Implement phrase query builder**
   - Add `_build_phrase_query(query)` → Dict
   - Extract phrases using regex (`r'"([^"]*)"'`)
   - Build multi_match queries with type=phrase
   - Return bool query with must clauses for each phrase
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_build_phrase_query -v`

**Acceptance Criteria**:
- [ ] `_build_phrase_query()` implemented
- [ ] Extracts phrases from double quotes
- [ ] Builds multi_match queries with type=phrase
- [ ] Multiple phrases supported (AND logic)
- [ ] Unit tests written and passing (3+ tests)
- [ ] Test coverage ≥ 90%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add _build_phrase_query method (~20 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~60 lines)

**Estimated Time**: 2 hours

---

### Task 2.4: Implement Boolean Query Parsing (Basic) (4 hours)

**Goal**: Parse AND/OR/NOT operators (no nested queries yet)

**Prerequisites**:
- Task 2.3 completed (phrase query works)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `_build_boolean_query("diabetes AND hypertension")` uses must clauses
   - Test: "diabetes OR hypertension" uses should clauses
   - Test: "diabetes NOT type1" uses must_not clauses
   - Test: Multiple operators: "(diabetes OR hypertension) AND medication"
2. **Implement boolean query parser**
   - Add `_build_boolean_query(query)` → Dict
   - Split query by AND/OR/NOT operators (regex)
   - Build bool query with must/should/must_not clauses
   - Handle operator precedence (AND before OR)
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_build_boolean_query -v`

**Acceptance Criteria**:
- [ ] `_build_boolean_query()` implemented
- [ ] AND operator → must clauses
- [ ] OR operator → should clauses
- [ ] NOT operator → must_not clauses
- [ ] Multiple operators supported
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 85%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add _build_boolean_query method (~40 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~100 lines)

**Estimated Time**: 4 hours

---

### Task 2.5: Implement Field-Specific Query Parsing (2 hours)

**Goal**: Parse field:value syntax (author:"Dr. Smith", document_type:"clinical_note")

**Prerequisites**:
- Task 2.4 completed (boolean parsing works)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `_build_field_query('author:"Dr. Smith"')` returns match on author field
   - Test: `document_type:"clinical_note"` uses term query (keyword field)
   - Test: Multiple field queries: `author:"Dr. Smith" AND document_type:"clinical_note"`
2. **Implement field query parser**
   - Add `_build_field_query(query)` → Dict
   - Extract field:value pairs using regex
   - Build match queries for text fields
   - Build term queries for keyword fields (document_type, author, department)
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_build_field_query -v`

**Acceptance Criteria**:
- [ ] `_build_field_query()` implemented
- [ ] Parses field:value syntax correctly
- [ ] Uses match for text fields
- [ ] Uses term for keyword fields
- [ ] Quoted values supported (field:"value with spaces")
- [ ] Unit tests written and passing (3+ tests)
- [ ] Test coverage ≥ 90%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add _build_field_query method (~25 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~70 lines)

**Estimated Time**: 2 hours

---

### Task 2.6: Install and Configure Lark Parser (3 hours)

**Goal**: Set up Lark parser for nested boolean queries with proper precedence

**Prerequisites**:
- Task 2.4 completed (basic boolean parsing works)

**Steps**:
1. **Add Lark dependency**
   - Add `lark>=1.1.9` to `backend/requirements.txt`
   - Install: `pip install lark`
2. **Create query grammar**
   - Create `backend/app/search/query_grammar.py`
   - Define Lark grammar for search queries (AND, OR, NOT, parentheses, field:value, phrases)
   - Support operator precedence (NOT > AND > OR)
3. **Write parser tests**
   - Create `backend/tests/unit/search/test_query_parser.py`
   - Test: Parse simple query "diabetes"
   - Test: Parse AND query "diabetes AND hypertension"
   - Test: Parse nested query "(diabetes OR hypertension) AND medication"
   - Test: Parse NOT query "diabetes NOT type1"
4. **Implement QueryParser**
   - Create `backend/app/search/query_parser.py`
   - Add QueryParser class
   - Add parse() method using Lark
   - Add QueryTransformer to convert parse tree to Elasticsearch DSL
5. **Run tests**
   - `pytest backend/tests/unit/search/test_query_parser.py -v`

**Acceptance Criteria**:
- [ ] Lark installed and importable
- [ ] Query grammar defined (AND, OR, NOT, parentheses, phrases, field queries)
- [ ] Operator precedence correct (NOT > AND > OR)
- [ ] QueryParser class created
- [ ] QueryTransformer converts parse tree to ES DSL
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `backend/requirements.txt` - Add lark>=1.1.9
- `backend/app/search/query_grammar.py` - Lark grammar definition (~50 lines)
- `backend/app/search/query_parser.py` - QueryParser with Lark (~80 lines)
- `backend/tests/unit/search/test_query_parser.py` - Unit tests (~120 lines)

**Estimated Time**: 3 hours

**Testing**:
```bash
pytest backend/tests/unit/search/test_query_parser.py -v --cov=app/search/query_parser
```

---

### Task 2.7: Integrate QueryParser into QueryBuilder (2 hours)

**Goal**: Use QueryParser for boolean queries in QueryBuilder

**Prerequisites**:
- Task 2.6 completed (QueryParser exists)

**Steps**:
1. **Update QueryBuilder to use QueryParser**
   - Modify `_build_boolean_query()` to use QueryParser instead of regex
   - Fallback to simple query on parse error
   - Update tests to verify QueryParser integration
2. **Test integration**
   - Run existing QueryBuilder tests
   - Add test for complex nested query
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py -v`

**Acceptance Criteria**:
- [ ] QueryBuilder uses QueryParser for boolean queries
- [ ] Fallback to simple query if parse error
- [ ] Existing tests still pass
- [ ] New test for complex nested query passes
- [ ] Test coverage maintained ≥ 85%

**Files Modified**:
- `backend/app/search/query_builder.py` - Use QueryParser in _build_boolean_query (~10 lines changed)
- `backend/tests/unit/search/test_query_builder.py` - Add complex query test (~30 lines)

**Estimated Time**: 2 hours

---

### Task 2.8: Implement Filter Application (2 hours)

**Goal**: Apply filters to Elasticsearch query (document_type, author, department, date_range)

**Prerequisites**:
- Task 2.1 completed (QueryBuilder exists)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `_apply_filters()` adds filter clauses to query
   - Test: document_type filter uses terms query
   - Test: author filter uses terms query
   - Test: department filter uses terms query
   - Test: date_range filter uses range query
   - Test: Multiple filters combined with AND logic
2. **Implement filter application**
   - Add `_apply_filters(query, filters)` → Dict to QueryBuilder
   - Add filter clauses to bool query
   - Build terms queries for array filters (document_types, authors, departments)
   - Build range query for date_range filter
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_apply_filters -v`

**Acceptance Criteria**:
- [ ] `_apply_filters()` implemented
- [ ] document_types filter uses terms query
- [ ] authors filter uses terms query
- [ ] departments filter uses terms query
- [ ] date_range filter uses range query (gte, lte)
- [ ] Filters combined with AND logic
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 90%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add _apply_filters method (~30 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~120 lines)

**Estimated Time**: 2 hours

---

### Task 2.9: Implement Recency Boost (2 hours)

**Goal**: Add recency boost using Elasticsearch function_score

**Prerequisites**:
- Task 2.8 completed (filters work)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `build_query()` includes function_score wrapper
   - Test: Gaussian decay function configured (scale=30d, decay=0.5)
   - Test: Recent documents boosted higher than old documents
2. **Implement recency boost**
   - Modify `build_query()` to wrap query in function_score
   - Add Gaussian decay function on date field
   - Configure: scale=30d (half-decay at 30 days), weight=1.5
   - Set score_mode=multiply, boost_mode=multiply
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_recency_boost -v`

**Acceptance Criteria**:
- [ ] function_score wrapper added to query
- [ ] Gaussian decay function on date field
- [ ] Decay parameters: scale=30d, decay=0.5, weight=1.5
- [ ] score_mode and boost_mode set to multiply
- [ ] Unit tests written and passing (3+ tests)
- [ ] Test coverage ≥ 85%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add recency boost to build_query (~15 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~60 lines)

**Estimated Time**: 2 hours

---

### Task 2.10: Implement Highlighting Configuration (1.5 hours)

**Goal**: Add highlighting to Elasticsearch query for keyword context snippets

**Prerequisites**:
- Task 2.9 completed (recency boost works)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `build_query()` includes highlight configuration
   - Test: title field highlighted (full content, no fragments)
   - Test: content field highlighted (150 char fragments, max 3)
   - Test: pre_tags and post_tags configured (<em>, </em>)
2. **Implement highlighting**
   - Add highlight configuration to `build_query()`
   - Configure title: number_of_fragments=0 (full highlight)
   - Configure content: fragment_size=150, number_of_fragments=3
   - Set pre_tags=["<em>"], post_tags=["</em>"]
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_highlighting -v`

**Acceptance Criteria**:
- [ ] Highlighting added to query
- [ ] title field: full content highlighted
- [ ] content field: 150 char fragments, max 3
- [ ] HTML tags: <em></em>
- [ ] Unit tests written and passing (3+ tests)
- [ ] Test coverage ≥ 90%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add highlighting to build_query (~12 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~50 lines)

**Estimated Time**: 1.5 hours

---

### Task 2.11: Implement Aggregations for Faceted Search (2 hours)

**Goal**: Add aggregations to Elasticsearch query for facet counts

**Prerequisites**:
- Task 2.10 completed (highlighting works)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `build_query()` includes aggregations
   - Test: document_types aggregation (terms, size=50)
   - Test: authors aggregation (terms, size=50)
   - Test: departments aggregation (terms, size=50)
   - Test: date_range aggregation (date_histogram, month interval)
2. **Implement aggregations**
   - Add aggs section to `build_query()`
   - Add terms aggregations (document_types, authors, departments)
   - Add date_histogram aggregation (date field, monthly interval)
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_aggregations -v`

**Acceptance Criteria**:
- [ ] Aggregations added to query
- [ ] Terms aggregations for document_types, authors, departments (size=50)
- [ ] Date histogram aggregation for date field (monthly)
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 90%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add aggregations to build_query (~20 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~80 lines)

**Estimated Time**: 2 hours

---

### Task 2.12: Implement Sorting Options (1.5 hours)

**Goal**: Add sort parameter support (relevance, date, title)

**Prerequisites**:
- Task 2.11 completed (aggregations work)

**Steps**:
1. **Write tests first** (TDD)
   - Add tests: `build_query(sort="relevance")` no explicit sort (default by score)
   - Test: `sort="date"` adds sort by date DESC
   - Test: `sort="title"` adds sort by title.raw ASC
2. **Implement sorting**
   - Modify `build_query()` to accept sort parameter
   - Add sort clauses based on sort value
   - Default: sort by relevance (score)
3. **Run tests**
   - `pytest backend/tests/unit/search/test_query_builder.py::test_sorting -v`

**Acceptance Criteria**:
- [ ] Sorting parameter supported
- [ ] relevance: sort by score (default)
- [ ] date: sort by date DESC
- [ ] title: sort by title.raw ASC
- [ ] Unit tests written and passing (3+ tests)
- [ ] Test coverage ≥ 90%

**Files Modified**:
- `backend/app/search/query_builder.py` - Add sorting to build_query (~15 lines)
- `backend/tests/unit/search/test_query_builder.py` - Add tests (~50 lines)

**Estimated Time**: 1.5 hours

---

### Task 2.13: Update SearchService to Use QueryBuilder (2 hours)

**Goal**: Integrate QueryBuilder into SearchService

**Prerequisites**:
- Task 2.12 completed (QueryBuilder complete)
- Task 1.9 completed (SearchService exists)

**Steps**:
1. **Update SearchService**
   - Import QueryBuilder in SearchService
   - Replace manual query building with `query_builder.build_query()`
   - Update tests to verify QueryBuilder integration
2. **Test integration**
   - Run existing SearchService tests
   - Add test for complex boolean query
3. **Run tests**
   - `pytest backend/tests/unit/services/test_search_service.py -v`

**Acceptance Criteria**:
- [ ] SearchService uses QueryBuilder.build_query()
- [ ] Manual query building code removed
- [ ] Existing tests still pass
- [ ] New test for complex query passes
- [ ] Test coverage maintained ≥ 85%

**Files Modified**:
- `backend/app/services/search_service.py` - Use QueryBuilder (~10 lines changed)
- `backend/tests/unit/services/test_search_service.py` - Add complex query test (~40 lines)

**Estimated Time**: 2 hours

---

### Task 2.14: Implement Score Explanation API (2.5 hours)

**Goal**: Add GET /api/v1/search/{document_id}/explain endpoint

**Prerequisites**:
- Task 2.13 completed (SearchService uses QueryBuilder)

**Steps**:
1. **Write tests first** (TDD)
   - Add to `backend/tests/integration/test_search_api.py`
   - Test: GET /search/{doc_id}/explain?query=diabetes returns explanation
   - Test: Explanation includes BM25 score, matching terms
   - Test: Requires authentication
2. **Implement explain_score method in SearchService**
   - Add `explain_score(document_id, query)` → Dict to SearchService
   - Use ES explain API
   - Parse explanation (BM25 score, field boosts, matching terms)
3. **Implement explain endpoint**
   - Add GET /search/{document_id}/explain to search.py
   - Call SearchService.explain_score()
   - Return explanation
4. **Run tests**
   - `pytest backend/tests/integration/test_search_api.py::test_explain_score -v`

**Acceptance Criteria**:
- [ ] `explain_score()` method implemented in SearchService
- [ ] GET /search/{document_id}/explain endpoint created
- [ ] Explanation includes total_score, bm25_score, matching_terms
- [ ] Matching terms include term name, field, score
- [ ] Authentication required
- [ ] Integration tests written and passing (3+ tests)
- [ ] Manual curl test successful

**Files Modified**:
- `backend/app/services/search_service.py` - Add explain_score method (~40 lines)
- `backend/app/api/v1/endpoints/search.py` - Add explain endpoint (~25 lines)
- `backend/tests/integration/test_search_api.py` - Add tests (~70 lines)

**Estimated Time**: 2.5 hours

**Testing**:
```bash
# Get document ID from search results first
# Then explain score
curl "http://localhost:8000/api/v1/search/{doc_id}/explain?query=diabetes" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Phase 3: Frontend Search UI (Week 2, 30 hours)

**Objective**: Build search interface with faceted filters and results display

### Task 3.1: Create useSearch Composable (3 hours)

**Goal**: Create reusable search composable for state management

**Prerequisites**:
- Frontend project structure exists

**Steps**:
1. **Write composable tests first** (TDD)
   - Create `frontend/tests/unit/composables/useSearch.spec.ts`
   - Test: `executeSearch()` calls API and updates results
   - Test: Loading state managed correctly
   - Test: Error state managed correctly
   - Test: Query state reactive
2. **Implement useSearch composable**
   - Create `frontend/src/composables/useSearch.ts`
   - Add reactive state (query, results, loading, error)
   - Add `executeSearch(request)` method
   - Add `getSuggestions(partial)` method
   - Add `clearResults()` method
3. **Run tests**
   - `npm run test:unit composables/useSearch.spec.ts`

**Acceptance Criteria**:
- [ ] useSearch composable created
- [ ] Reactive state (query, results, loading, error)
- [ ] `executeSearch()` method calls search API
- [ ] `getSuggestions()` method for autocomplete
- [ ] `clearResults()` resets state
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `frontend/src/composables/useSearch.ts` - Search composable (~120 lines)
- `frontend/tests/unit/composables/useSearch.spec.ts` - Unit tests (~180 lines)

**Estimated Time**: 3 hours

**Testing**:
```bash
cd frontend
npm run test:unit composables/useSearch.spec.ts
```

---

### Task 3.2: Create SearchInput Component (2.5 hours)

**Goal**: Create search input with autocomplete suggestions

**Prerequisites**:
- Task 3.1 completed (useSearch composable exists)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `frontend/tests/unit/components/search/SearchInput.spec.ts`
   - Test: Renders v-text-field
   - Test: v-model binds to query prop
   - Test: Emits search event on Enter key
   - Test: Autocomplete shows suggestions
   - Test: Debounces suggestions (300ms)
2. **Implement SearchInput component**
   - Create `frontend/src/components/search/SearchInput.vue`
   - Add v-text-field with clearable
   - Add autocomplete dropdown (v-list)
   - Debounce suggestions (300ms)
   - Emit search event on Enter
3. **Run tests**
   - `npm run test:unit components/search/SearchInput.spec.ts`

**Acceptance Criteria**:
- [ ] SearchInput component created
- [ ] v-text-field with clearable
- [ ] Autocomplete dropdown displays suggestions
- [ ] Debouncing (300ms) for suggestion requests
- [ ] Emits search event on Enter key
- [ ] Props: modelValue, suggestions
- [ ] Emits: update:modelValue, search, input
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `frontend/src/components/search/SearchInput.vue` - Search input (~150 lines)
- `frontend/tests/unit/components/search/SearchInput.spec.ts` - Unit tests (~120 lines)

**Estimated Time**: 2.5 hours

---

### Task 3.3: Create FacetFilters Component (5 hours)

**Goal**: Create faceted filters sidebar with checkboxes

**Prerequisites**:
- None (standalone component)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `frontend/tests/unit/components/search/FacetFilters.spec.ts`
   - Test: Renders facet sections (document_types, authors, departments)
   - Test: Displays facet counts
   - Test: Emits filter change on checkbox click
   - Test: Clear all filters button works
   - Test: Date range picker works
2. **Implement FacetFilters component**
   - Create `frontend/src/components/search/FacetFilters.vue`
   - Add v-card with sections for each facet type
   - Add v-checkbox-group for document_types
   - Add v-checkbox-group for authors
   - Add v-checkbox-group for departments
   - Add date range picker (v-date-picker or custom)
   - Add "Clear All" button
   - Emit filters-changed event
3. **Run tests**
   - `npm run test:unit components/search/FacetFilters.spec.ts`

**Acceptance Criteria**:
- [ ] FacetFilters component created
- [ ] Sections for document_types, authors, departments
- [ ] Facet counts displayed (e.g., "Clinical Notes (45)")
- [ ] Checkboxes for multi-select
- [ ] Date range picker
- [ ] "Clear All" button
- [ ] Props: facets, activeFilters
- [ ] Emits: update:filters
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `frontend/src/components/search/FacetFilters.vue` - Facet filters (~300 lines)
- `frontend/tests/unit/components/search/FacetFilters.spec.ts` - Unit tests (~200 lines)

**Estimated Time**: 5 hours

---

### Task 3.4: Create SearchResult Component (3 hours)

**Goal**: Create search result item component with highlighting

**Prerequisites**:
- None (standalone component)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `frontend/tests/unit/components/search/SearchResult.spec.ts`
   - Test: Renders document title
   - Test: Renders metadata (type, author, date, department)
   - Test: Renders relevance score
   - Test: Renders highlighted snippets
   - Test: Click emits document-click event
2. **Implement SearchResult component**
   - Create `frontend/src/components/search/SearchResult.vue`
   - Add v-card with document info
   - Display title (with highlighting if present)
   - Display metadata (type, author, date, department)
   - Display relevance score (0-100)
   - Display highlighted snippets (content field)
   - Add "View Document" button
   - Emit document-click event
3. **Run tests**
   - `npm run test:unit components/search/SearchResult.spec.ts`

**Acceptance Criteria**:
- [ ] SearchResult component created
- [ ] Displays document title with highlighting
- [ ] Displays metadata (type, author, date, department)
- [ ] Displays relevance score with visual indicator (progress bar)
- [ ] Displays highlighted snippets (HTML <em> tags rendered)
- [ ] "View Document" button
- [ ] Props: document
- [ ] Emits: document-click
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `frontend/src/components/search/SearchResult.vue` - Search result (~200 lines)
- `frontend/tests/unit/components/search/SearchResult.spec.ts` - Unit tests (~150 lines)

**Estimated Time**: 3 hours

---

### Task 3.5: Create QueryBuilder Component (6 hours)

**Goal**: Create visual query builder for advanced queries

**Prerequisites**:
- None (standalone component)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `frontend/tests/unit/components/search/QueryBuilder.spec.ts`
   - Test: Renders query builder interface
   - Test: Add condition button works
   - Test: Remove condition button works
   - Test: AND/OR operator selector works
   - Test: Field selector works
   - Test: Value input works
   - Test: Emits query string
2. **Implement QueryBuilder component**
   - Create `frontend/src/components/search/QueryBuilder.vue`
   - Add drag-and-drop interface (Vue.Draggable)
   - Add condition rows (field, operator, value)
   - Add AND/OR operator selectors
   - Add "Add Condition" button
   - Add "Remove Condition" button
   - Build query string from conditions
   - Emit query event
3. **Run tests**
   - `npm run test:unit components/search/QueryBuilder.spec.ts`

**Acceptance Criteria**:
- [ ] QueryBuilder component created
- [ ] Visual interface for building queries
- [ ] Add/remove condition buttons
- [ ] Field selectors (title, content, author, document_type, department)
- [ ] Operator selectors (contains, equals, starts with, ends with)
- [ ] Value inputs
- [ ] AND/OR operator selectors
- [ ] Query string generated from conditions
- [ ] Props: modelValue (query string)
- [ ] Emits: update:modelValue, close
- [ ] Unit tests written and passing (7+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `frontend/src/components/search/QueryBuilder.vue` - Query builder (~400 lines)
- `frontend/tests/unit/components/search/QueryBuilder.spec.ts` - Unit tests (~250 lines)
- `frontend/package.json` - Add vuedraggable dependency

**Estimated Time**: 6 hours

---

### Task 3.6: Create SearchView Main Component (5 hours)

**Goal**: Create main search view integrating all search components

**Prerequisites**:
- Tasks 3.1-3.5 completed (all search components exist)

**Steps**:
1. **Write view tests first** (TDD)
   - Create `frontend/tests/unit/views/SearchView.spec.ts`
   - Test: Renders SearchInput, FacetFilters, search results
   - Test: Search execution on Enter key
   - Test: Filter change triggers search
   - Test: Pagination works
   - Test: Loading state displayed
   - Test: Error state displayed
2. **Implement SearchView**
   - Create `frontend/src/views/SearchView.vue`
   - Add 3-column layout (filters, results, saved searches)
   - Integrate SearchInput
   - Integrate FacetFilters
   - Integrate SearchResult (v-for over results)
   - Add v-pagination
   - Add QueryBuilder toggle button
   - Add loading/error states
   - Use useSearch composable
3. **Run tests**
   - `npm run test:unit views/SearchView.spec.ts`

**Acceptance Criteria**:
- [ ] SearchView created with 3-column layout
- [ ] SearchInput integrated
- [ ] FacetFilters integrated (left sidebar)
- [ ] Search results displayed (center)
- [ ] Pagination working
- [ ] QueryBuilder toggle button
- [ ] Loading indicator (v-progress-linear)
- [ ] Error alert (v-alert)
- [ ] Results count displayed
- [ ] Execution time displayed
- [ ] Unit tests written and passing (6+ tests)
- [ ] Test coverage ≥ 80%

**Files Created/Modified**:
- `frontend/src/views/SearchView.vue` - Main search view (~350 lines)
- `frontend/src/router/index.ts` - Add /search route
- `frontend/tests/unit/views/SearchView.spec.ts` - Unit tests (~200 lines)

**Estimated Time**: 5 hours

---

### Task 3.7: Implement Autocomplete Suggestions API Integration (2 hours)

**Goal**: Connect SearchInput to GET /api/v1/search/suggestions endpoint

**Prerequisites**:
- Task 3.2 completed (SearchInput exists)
- Backend suggestions endpoint exists

**Steps**:
1. **Update useSearch composable**
   - Add `getSuggestions(partial_query)` method
   - Call GET /api/v1/search/suggestions
   - Return array of suggestion strings
2. **Update SearchInput to use suggestions**
   - Call useSearch().getSuggestions() on input
   - Display suggestions in dropdown
   - Click suggestion updates query
3. **Test integration**
   - Manual testing with browser
   - Type "diabet" → verify suggestions appear

**Acceptance Criteria**:
- [ ] `getSuggestions()` implemented in useSearch
- [ ] SearchInput calls getSuggestions on input
- [ ] Suggestions displayed in dropdown
- [ ] Click suggestion updates query input
- [ ] Debouncing works (300ms)
- [ ] Manual test successful

**Files Modified**:
- `frontend/src/composables/useSearch.ts` - Add getSuggestions (~20 lines)
- `frontend/src/components/search/SearchInput.vue` - Use suggestions (~15 lines)

**Estimated Time**: 2 hours

**Testing**:
```
Manual test in browser:
1. Navigate to /search
2. Type "diabet" in search input
3. Wait 300ms
4. Verify suggestions appear (diabetes, diabetic, diabetes mellitus, etc.)
5. Click suggestion
6. Verify query input updated
```

---

### Task 3.8: Add Keyboard Shortcuts (1.5 hours)

**Goal**: Add keyboard shortcuts (Ctrl+K for search, Esc to close)

**Prerequisites**:
- Task 3.6 completed (SearchView exists)

**Steps**:
1. **Implement keyboard shortcuts**
   - Add keydown event listener in SearchView
   - Ctrl+K → focus search input
   - Esc → close query builder, clear results
   - +/- → next/previous page (pagination)
2. **Test shortcuts**
   - Manual testing with keyboard

**Acceptance Criteria**:
- [ ] Ctrl+K focuses search input
- [ ] Esc closes query builder
- [ ] Esc clears results (if no query builder open)
- [ ] Keyboard shortcuts work across all browsers
- [ ] Manual test successful

**Files Modified**:
- `frontend/src/views/SearchView.vue` - Add keyboard event handlers (~30 lines)

**Estimated Time**: 1.5 hours

---

### Task 3.9: Add Accessibility Features (2 hours)

**Goal**: Ensure WCAG 2.1 AA compliance for search interface

**Prerequisites**:
- Task 3.6 completed (SearchView exists)

**Steps**:
1. **Add ARIA labels**
   - Add aria-label to search input
   - Add role="search" to search form
   - Add aria-live for results count
   - Add aria-label to filter checkboxes
2. **Test with screen reader**
   - Test with NVDA/JAWS (Windows) or VoiceOver (Mac)
   - Verify all interactive elements announced
3. **Test keyboard navigation**
   - Verify Tab order logical
   - Verify all interactive elements reachable via keyboard
4. **Check color contrast**
   - Verify all text has sufficient contrast (4.5:1)

**Acceptance Criteria**:
- [ ] ARIA labels added to all interactive elements
- [ ] role="search" on search form
- [ ] aria-live region for results count
- [ ] Screen reader announces search results
- [ ] Keyboard navigation works (Tab, Enter, Space, Arrow keys)
- [ ] Color contrast ≥ 4.5:1 for all text
- [ ] Focus indicators visible

**Files Modified**:
- `frontend/src/views/SearchView.vue` - Add ARIA labels (~10 lines)
- `frontend/src/components/search/SearchInput.vue` - Add ARIA labels (~5 lines)
- `frontend/src/components/search/FacetFilters.vue` - Add ARIA labels (~8 lines)
- `frontend/src/components/search/SearchResult.vue` - Add ARIA labels (~5 lines)

**Estimated Time**: 2 hours

**Testing**:
```
Accessibility checklist:
□ All form inputs have labels (visible or aria-label)
□ role="search" on search form
□ aria-live region announces results count
□ Tab order is logical
□ All interactive elements keyboard accessible
□ Focus indicators visible
□ Color contrast ≥ 4.5:1
□ Screen reader announces all content correctly
```

---

## Phase 4: Saved Searches & Export (Week 3, 15 hours)

**Objective**: Implement saved searches and export functionality

### Task 4.1: Create Saved Searches API Endpoints (3 hours)

**Goal**: Implement CRUD endpoints for saved searches

**Prerequisites**:
- Task 1.5 completed (SavedSearch model exists)

**Steps**:
1. **Write endpoint tests first** (TDD)
   - Add to `backend/tests/integration/test_search_api.py`
   - Test: POST /search/saved creates saved search
   - Test: GET /search/saved lists user's saved searches
   - Test: DELETE /search/saved/{id} deletes saved search
   - Test: Saved searches require authentication
2. **Implement endpoints**
   - Add to `backend/app/api/v1/endpoints/search.py`
   - Add POST /api/v1/search/saved (create)
   - Add GET /api/v1/search/saved (list)
   - Add DELETE /api/v1/search/saved/{id} (delete)
   - Add audit logging for save/delete
3. **Run tests**
   - `pytest backend/tests/integration/test_search_api.py::test_saved_searches -v`

**Acceptance Criteria**:
- [ ] POST /search/saved endpoint creates saved search
- [ ] GET /search/saved endpoint lists user's saved searches
- [ ] DELETE /search/saved/{id} endpoint deletes saved search
- [ ] Authentication required for all endpoints
- [ ] User can only delete own saved searches
- [ ] Audit logs created (SEARCH_SAVED, SEARCH_DELETED)
- [ ] Integration tests written and passing (4+ tests)
- [ ] Manual curl test successful

**Files Modified**:
- `backend/app/api/v1/endpoints/search.py` - Add saved search endpoints (~80 lines)
- `backend/tests/integration/test_search_api.py` - Add tests (~120 lines)

**Estimated Time**: 3 hours

**Testing**:
```bash
# Create saved search
curl -X POST http://localhost:8000/api/v1/search/saved \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Diabetes Notes","query":"diabetes","filters":{"document_types":["clinical_note"]}}'

# List saved searches
curl http://localhost:8000/api/v1/search/saved \
  -H "Authorization: Bearer $TOKEN"
```

---

### Task 4.2: Create SavedSearches Component (3 hours)

**Goal**: Create saved searches sidebar component

**Prerequisites**:
- Task 4.1 completed (saved searches API exists)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `frontend/tests/unit/components/search/SavedSearches.spec.ts`
   - Test: Renders list of saved searches
   - Test: Click saved search emits execute event
   - Test: Delete button emits delete event
   - Test: Save button opens dialog
2. **Implement SavedSearches component**
   - Create `frontend/src/components/search/SavedSearches.vue`
   - Add v-list with saved searches
   - Add click handler to execute saved search
   - Add delete button (v-icon with confirmation)
   - Add "Save Current Search" button
   - Emit execute and delete events
3. **Run tests**
   - `npm run test:unit components/search/SavedSearches.spec.ts`

**Acceptance Criteria**:
- [ ] SavedSearches component created
- [ ] Displays list of saved searches (name, description)
- [ ] Click saved search emits execute event
- [ ] Delete button with confirmation dialog
- [ ] "Save Current Search" button
- [ ] Props: savedSearches
- [ ] Emits: execute, delete, save
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `frontend/src/components/search/SavedSearches.vue` - Saved searches component (~200 lines)
- `frontend/tests/unit/components/search/SavedSearches.spec.ts` - Unit tests (~120 lines)

**Estimated Time**: 3 hours

---

### Task 4.3: Create SaveSearchDialog Component (2 hours)

**Goal**: Create dialog for saving current search

**Prerequisites**:
- None (standalone component)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `frontend/tests/unit/components/search/SaveSearchDialog.spec.ts`
   - Test: Renders dialog with form
   - Test: Name field required
   - Test: Save button calls API
   - Test: Close button closes dialog
2. **Implement SaveSearchDialog component**
   - Create `frontend/src/components/search/SaveSearchDialog.vue`
   - Add v-dialog with v-form
   - Add name input (required)
   - Add description textarea (optional)
   - Add Save button (calls POST /search/saved)
   - Add Close button
   - Emit saved event on success
3. **Run tests**
   - `npm run test:unit components/search/SaveSearchDialog.spec.ts`

**Acceptance Criteria**:
- [ ] SaveSearchDialog component created
- [ ] v-dialog with form
- [ ] Name input (required, validation)
- [ ] Description textarea (optional)
- [ ] Save button calls API
- [ ] Success snackbar on save
- [ ] Error alert on failure
- [ ] Props: modelValue (show), query, filters
- [ ] Emits: update:modelValue, saved
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `frontend/src/components/search/SaveSearchDialog.vue` - Save search dialog (~180 lines)
- `frontend/tests/unit/components/search/SaveSearchDialog.spec.ts` - Unit tests (~100 lines)

**Estimated Time**: 2 hours

---

### Task 4.4: Implement Export Service (4 hours)

**Goal**: Create ExportService for CSV, JSON, FHIR export

**Prerequisites**:
- Sprint 2 Export patterns (can reuse from Timeline export)

**Steps**:
1. **Write ExportService tests first** (TDD)
   - Create `backend/tests/unit/services/test_export_service.py`
   - Test: `export_to_csv()` generates CSV with headers
   - Test: `export_to_json()` serializes results to JSON
   - Test: `export_to_fhir()` creates DocumentReference bundle
   - Test: Audit log created for exports
2. **Implement ExportService**
   - Create `backend/app/services/export_service.py`
   - Add ExportService class
   - Add `export_to_csv(results, filename)` → bytes
   - Add `export_to_json(results, filename)` → bytes
   - Add `export_to_fhir(results, filename)` → bytes (DocumentReference bundle)
   - Add audit logging
3. **Run tests**
   - `pytest backend/tests/unit/services/test_export_service.py -v`

**Acceptance Criteria**:
- [ ] ExportService class created
- [ ] `export_to_csv()` generates CSV with document metadata
- [ ] `export_to_json()` serializes search results to JSON
- [ ] `export_to_fhir()` creates FHIR R4 DocumentReference bundle
- [ ] Audit log created (action=SEARCH_EXPORTED)
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `backend/app/services/export_service.py` - Export service (~200 lines)
- `backend/tests/unit/services/test_export_service.py` - Unit tests (~180 lines)

**Estimated Time**: 4 hours

---

### Task 4.5: Create Export API Endpoint (2 hours)

**Goal**: Implement POST /api/v1/search/export endpoint

**Prerequisites**:
- Task 4.4 completed (ExportService exists)

**Steps**:
1. **Write endpoint tests first** (TDD)
   - Add to `backend/tests/integration/test_search_api.py`
   - Test: POST /search/export with format=csv returns CSV file
   - Test: POST /search/export with format=json returns JSON file
   - Test: POST /search/export with format=fhir returns FHIR bundle
   - Test: Requires authentication
2. **Implement export endpoint**
   - Add to `backend/app/api/v1/endpoints/search.py`
   - Add POST /api/v1/search/export
   - Accept query, filters, format (csv/json/fhir)
   - Execute search (get all results, no pagination)
   - Call ExportService based on format
   - Return file as response (StreamingResponse)
3. **Run tests**
   - `pytest backend/tests/integration/test_search_api.py::test_export -v`

**Acceptance Criteria**:
- [ ] POST /search/export endpoint created
- [ ] Supports format=csv, json, fhir
- [ ] Executes search with no pagination (all results)
- [ ] Returns file as StreamingResponse
- [ ] Correct Content-Type header for each format
- [ ] Content-Disposition header with filename
- [ ] Authentication required
- [ ] Integration tests written and passing (4+ tests)
- [ ] Manual curl test successful

**Files Modified**:
- `backend/app/api/v1/endpoints/search.py` - Add export endpoint (~60 lines)
- `backend/tests/integration/test_search_api.py` - Add tests (~100 lines)

**Estimated Time**: 2 hours

**Testing**:
```bash
# Export to CSV
curl -X POST "http://localhost:8000/api/v1/search/export" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"diabetes","format":"csv"}' \
  --output search_results.csv

# Export to JSON
curl -X POST "http://localhost:8000/api/v1/search/export" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"diabetes","format":"json"}' \
  --output search_results.json
```

---

### Task 4.6: Integrate Export into SearchView (1 hour)

**Goal**: Add export buttons to SearchView

**Prerequisites**:
- Task 4.5 completed (export API exists)
- Task 3.6 completed (SearchView exists)

**Steps**:
1. **Add export buttons to SearchView**
   - Add toolbar with export buttons (CSV, JSON, FHIR)
   - Call export API on button click
   - Download file using Blob API
   - Show success/error snackbar
2. **Test integration**
   - Manual testing with browser

**Acceptance Criteria**:
- [ ] Export buttons added to SearchView toolbar
- [ ] CSV export button downloads CSV file
- [ ] JSON export button downloads JSON file
- [ ] FHIR export button downloads FHIR bundle
- [ ] Success snackbar on export
- [ ] Error alert on failure
- [ ] Manual test successful

**Files Modified**:
- `frontend/src/views/SearchView.vue` - Add export buttons (~40 lines)

**Estimated Time**: 1 hour

**Testing**:
```
Manual test in browser:
1. Navigate to /search
2. Execute search
3. Click "Export CSV" button
4. Verify CSV file downloads
5. Repeat for JSON and FHIR
```

---

## Phase 5: Search Analytics & Admin (Week 3, 15 hours)

**Objective**: Search analytics tracking and admin dashboard

### Task 5.1: Implement AnalyticsService (4 hours)

**Goal**: Create service to aggregate search analytics

**Prerequisites**:
- Task 1.5 completed (SearchAnalytics model exists)

**Steps**:
1. **Write AnalyticsService tests first** (TDD)
   - Create `backend/tests/unit/services/test_analytics_service.py`
   - Test: `get_top_queries()` returns most frequent queries
   - Test: `get_zero_result_queries()` returns queries with 0 results
   - Test: `get_slow_queries()` returns queries >2s execution time
   - Test: `get_search_trends()` returns daily search counts
   - Test: Filters by date range and user
2. **Implement AnalyticsService**
   - Create `backend/app/services/analytics_service.py`
   - Add AnalyticsService class
   - Add `get_top_queries(limit, start_date, end_date, user_id)` → List[QueryStat]
   - Add `get_zero_result_queries(limit, start_date, end_date)` → List[str]
   - Add `get_slow_queries(limit, threshold_ms, start_date, end_date)` → List[SlowQuery]
   - Add `get_search_trends(start_date, end_date)` → List[TrendPoint]
   - Use SQLAlchemy aggregations (GROUP BY, COUNT, etc.)
3. **Run tests**
   - `pytest backend/tests/unit/services/test_analytics_service.py -v`

**Acceptance Criteria**:
- [ ] AnalyticsService class created
- [ ] `get_top_queries()` returns query, count pairs sorted by count
- [ ] `get_zero_result_queries()` returns queries with results_count=0
- [ ] `get_slow_queries()` returns queries with execution_time_ms > threshold
- [ ] `get_search_trends()` returns date, count pairs
- [ ] All methods support date range filtering
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 85%

**Files Created/Modified**:
- `backend/app/services/analytics_service.py` - Analytics service (~180 lines)
- `backend/tests/unit/services/test_analytics_service.py` - Unit tests (~200 lines)

**Estimated Time**: 4 hours

---

### Task 5.2: Create Analytics API Endpoint (2 hours)

**Goal**: Implement GET /api/v1/search/analytics endpoint (admin only)

**Prerequisites**:
- Task 5.1 completed (AnalyticsService exists)

**Steps**:
1. **Write endpoint tests first** (TDD)
   - Add to `backend/tests/integration/test_search_api.py`
   - Test: GET /search/analytics returns analytics data (admin user)
   - Test: GET /search/analytics with date range filters results
   - Test: GET /search/analytics returns 403 for non-admin users
2. **Implement analytics endpoint**
   - Add to `backend/app/api/v1/endpoints/search.py`
   - Add GET /api/v1/search/analytics
   - Require admin role permission
   - Accept query params (start_date, end_date, user_id)
   - Call AnalyticsService methods
   - Return SearchAnalyticsResponse
3. **Run tests**
   - `pytest backend/tests/integration/test_search_api.py::test_analytics -v`

**Acceptance Criteria**:
- [ ] GET /search/analytics endpoint created
- [ ] Admin role required (403 for non-admin)
- [ ] Returns top_queries, zero_result_queries, slow_queries, search_trends
- [ ] Date range filtering works (start_date, end_date params)
- [ ] User filtering works (user_id param)
- [ ] Integration tests written and passing (3+ tests)
- [ ] Manual curl test successful

**Files Modified**:
- `backend/app/api/v1/endpoints/search.py` - Add analytics endpoint (~50 lines)
- `backend/tests/integration/test_search_api.py` - Add tests (~80 lines)

**Estimated Time**: 2 hours

**Testing**:
```bash
# Get analytics (admin user)
curl "http://localhost:8000/api/v1/search/analytics?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### Task 5.3: Create SearchAnalytics Component (5 hours)

**Goal**: Create admin analytics dashboard component

**Prerequisites**:
- Task 5.2 completed (analytics API exists)

**Steps**:
1. **Write component tests first** (TDD)
   - Create `frontend/tests/unit/components/search/SearchAnalytics.spec.ts`
   - Test: Renders analytics dashboard
   - Test: Top queries chart displayed
   - Test: Search trends chart displayed
   - Test: Zero result queries list displayed
   - Test: Slow queries list displayed
2. **Implement SearchAnalytics component**
   - Create `frontend/src/components/search/SearchAnalytics.vue`
   - Add date range picker (v-date-picker)
   - Add top queries chart (bar chart with Chart.js or Vuetify)
   - Add search trends chart (line chart)
   - Add zero result queries table (v-data-table)
   - Add slow queries table (v-data-table)
   - Add export to CSV button
   - Use useSearch composable or create useAnalytics
3. **Run tests**
   - `npm run test:unit components/search/SearchAnalytics.spec.ts`

**Acceptance Criteria**:
- [ ] SearchAnalytics component created
- [ ] Date range picker for filtering
- [ ] Top queries bar chart (query, count)
- [ ] Search trends line chart (date, count)
- [ ] Zero result queries table
- [ ] Slow queries table (query, execution_time_ms)
- [ ] Export to CSV button
- [ ] Admin access only (role check)
- [ ] Unit tests written and passing (5+ tests)
- [ ] Test coverage ≥ 80%

**Files Created/Modified**:
- `frontend/src/components/search/SearchAnalytics.vue` - Analytics dashboard (~400 lines)
- `frontend/src/composables/useAnalytics.ts` - Analytics composable (~80 lines)
- `frontend/tests/unit/components/search/SearchAnalytics.spec.ts` - Unit tests (~150 lines)
- `frontend/package.json` - Add chart.js dependency

**Estimated Time**: 5 hours

---

### Task 5.4: Create Admin Analytics View (2 hours)

**Goal**: Create /admin/search-analytics route and view

**Prerequisites**:
- Task 5.3 completed (SearchAnalytics component exists)

**Steps**:
1. **Create AdminSearchAnalyticsView**
   - Create `frontend/src/views/admin/SearchAnalyticsView.vue`
   - Add page header and description
   - Integrate SearchAnalytics component
   - Add breadcrumbs
2. **Add route**
   - Add /admin/search-analytics route to router
   - Add navigation guard (admin only)
3. **Test view**
   - Manual testing with admin user

**Acceptance Criteria**:
- [ ] SearchAnalyticsView created
- [ ] Route /admin/search-analytics added
- [ ] Navigation guard requires admin role
- [ ] Breadcrumbs displayed
- [ ] SearchAnalytics component integrated
- [ ] Manual test successful (admin can access, non-admin cannot)

**Files Created/Modified**:
- `frontend/src/views/admin/SearchAnalyticsView.vue` - Admin analytics view (~100 lines)
- `frontend/src/router/index.ts` - Add route (~10 lines)

**Estimated Time**: 2 hours

**Testing**:
```
Manual test:
1. Login as admin user
2. Navigate to /admin/search-analytics
3. Verify analytics dashboard displays
4. Logout
5. Login as non-admin user
6. Attempt to navigate to /admin/search-analytics
7. Verify redirect to unauthorized page
```

---

### Task 5.5: Add Search Analytics Link to Admin Menu (1 hour)

**Goal**: Add "Search Analytics" link to admin navigation

**Prerequisites**:
- Task 5.4 completed (analytics view exists)

**Steps**:
1. **Update admin navigation**
   - Add "Search Analytics" link to admin menu/sidebar
   - Icon: mdi-chart-line
   - Route: /admin/search-analytics
   - Visible only to admin users
2. **Test navigation**
   - Manual test with admin user

**Acceptance Criteria**:
- [ ] "Search Analytics" link added to admin menu
- [ ] Link visible only to admin users
- [ ] Clicking link navigates to /admin/search-analytics
- [ ] Icon displayed (mdi-chart-line)
- [ ] Manual test successful

**Files Modified**:
- `frontend/src/components/AdminNav.vue` or similar - Add analytics link (~8 lines)

**Estimated Time**: 1 hour

---

### Task 5.6: Add Rate Limiting to Search Endpoint (1 hour)

**Goal**: Implement rate limiting (60 searches per minute per user)

**Prerequisites**:
- Redis service running (from Task 1.1)

**Steps**:
1. **Create rate limit middleware**
   - Create `backend/app/middleware/rate_limit.py`
   - Add `rate_limit_search()` dependency
   - Use Redis INCR with TTL
   - Raise HTTPException(429) if limit exceeded
2. **Apply to search endpoint**
   - Add rate_limit_search dependency to POST /search
   - Add rate_limit_search dependency to POST /search/export
3. **Test rate limiting**
   - Manual test: make 61 requests in 1 minute
   - Verify 61st request returns 429

**Acceptance Criteria**:
- [ ] rate_limit_search() dependency created
- [ ] Uses Redis for rate limiting
- [ ] Limit: 60 requests per minute per user
- [ ] Returns 429 when limit exceeded
- [ ] Applied to POST /search and POST /search/export
- [ ] Manual test successful

**Files Created/Modified**:
- `backend/app/middleware/rate_limit.py` - Rate limiting middleware (~50 lines)
- `backend/app/api/v1/endpoints/search.py` - Apply rate limiting (~5 lines)

**Estimated Time**: 1 hour

**Testing**:
```bash
# Test rate limiting
for i in {1..61}; do
  curl -X POST http://localhost:8000/api/v1/search \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query":"test"}' &
done
wait

# Verify 61st request returns 429
```

---

## Phase 6: Testing & Hardening (Week 4, 25 hours)

**Objective**: Comprehensive testing, performance validation, security audit

### Task 6.1: Write Integration Tests for Full Search Workflow (5 hours)

**Goal**: Create comprehensive integration tests for end-to-end search workflow

**Prerequisites**:
- All backend implementation complete

**Steps**:
1. **Create integration test fixtures**
   - Create `backend/tests/integration/fixtures/search_fixtures.py`
   - Add fixture for Elasticsearch with test data (es_with_search_data)
   - Add fixture for test user with saved searches
2. **Write full workflow integration tests**
   - Add to `backend/tests/integration/test_search_workflow.py`
   - Test: Full search workflow (search → filter → save → export)
   - Test: Boolean query workflow (AND, OR, NOT)
   - Test: Phrase search workflow
   - Test: Field-specific search workflow
   - Test: Faceted search workflow
   - Test: Saved search execution workflow
   - Test: Export workflow (CSV, JSON, FHIR)
   - Test: Analytics tracking workflow
3. **Run tests**
   - `pytest backend/tests/integration/test_search_workflow.py -v`

**Acceptance Criteria**:
- [ ] Test fixtures created (es_with_search_data)
- [ ] 8+ integration tests covering full workflows
- [ ] All workflows tested end-to-end
- [ ] Tests verify database state changes
- [ ] Tests verify Elasticsearch state changes
- [ ] All integration tests passing
- [ ] Test coverage ≥ 85% for integration paths

**Files Created/Modified**:
- `backend/tests/integration/fixtures/search_fixtures.py` - Test fixtures (~150 lines)
- `backend/tests/integration/test_search_workflow.py` - Integration tests (~400 lines)

**Estimated Time**: 5 hours

---

### Task 6.2: Write Frontend E2E Tests (5 hours)

**Goal**: Create E2E tests with Playwright for search interface

**Prerequisites**:
- Frontend implementation complete

**Steps**:
1. **Write E2E test scenarios**
   - Create `frontend/tests/e2e/search.spec.ts`
   - Test: Full search workflow (login → search → view results)
   - Test: Filter workflow (apply filters → verify results)
   - Test: Saved search workflow (save → execute saved)
   - Test: Export workflow (export CSV → download file)
   - Test: Analytics workflow (admin → view analytics)
2. **Run E2E tests**
   - `npm run test:e2e`

**Acceptance Criteria**:
- [ ] 5 E2E test scenarios written
- [ ] All critical user journeys covered
- [ ] Tests run in headless mode
- [ ] Tests run in multiple browsers (Chromium, Firefox, WebKit)
- [ ] Screenshots captured on failure
- [ ] All E2E tests passing

**Files Created/Modified**:
- `frontend/tests/e2e/search.spec.ts` - E2E tests (~300 lines)
- `frontend/playwright.config.ts` - Playwright config (~50 lines)

**Estimated Time**: 5 hours

**Testing**:
```bash
cd frontend
npm run test:e2e
```

---

### Task 6.3: Performance Testing with Locust (4 hours)

**Goal**: Load test search API with 20 concurrent users

**Prerequisites**:
- Backend search API complete

**Steps**:
1. **Create Locust test script**
   - Create `backend/tests/performance/search_load_test.py`
   - Define search tasks (simple query, complex query, filters, autocomplete)
   - Configure user spawn rate and wait time
2. **Run load tests**
   - Run Locust: `locust -f search_load_test.py --host=http://localhost:8000 --users=20 --spawn-rate=2`
   - Monitor response times
   - Verify <1s for simple queries, <2s for complex queries
3. **Document results**
   - Create `backend/tests/performance/LOAD_TEST_RESULTS.md`
   - Document response times, failure rates, bottlenecks

**Acceptance Criteria**:
- [ ] Locust test script created
- [ ] Load test runs with 20 concurrent users
- [ ] Simple queries: avg response time <1s
- [ ] Complex queries: avg response time <2s
- [ ] Autocomplete: avg response time <200ms
- [ ] No failures under normal load
- [ ] Results documented

**Files Created/Modified**:
- `backend/tests/performance/search_load_test.py` - Locust test (~100 lines)
- `backend/tests/performance/LOAD_TEST_RESULTS.md` - Results documentation (~30 lines)

**Estimated Time**: 4 hours

**Testing**:
```bash
cd backend
locust -f tests/performance/search_load_test.py --host=http://localhost:8000 --users=20 --spawn-rate=2 --run-time=5m
```

---

### Task 6.4: Security Audit - Query Injection Testing (3 hours)

**Goal**: Test for query injection vulnerabilities

**Prerequisites**:
- Search API complete

**Steps**:
1. **Create security test script**
   - Create `backend/tests/security/test_query_injection.py`
   - Test: Elasticsearch injection attempts
   - Test: SQL injection attempts (filters)
   - Test: XSS attempts (query strings)
   - Test: Script tag injection
2. **Test input sanitization**
   - Verify dangerous characters stripped
   - Verify query length limits enforced
   - Verify no code execution possible
3. **Document findings**
   - Create `backend/tests/security/SECURITY_AUDIT.md`
   - Document vulnerabilities found (if any)
   - Document mitigations applied

**Acceptance Criteria**:
- [ ] Security test script created
- [ ] Elasticsearch injection prevented
- [ ] SQL injection prevented
- [ ] XSS injection prevented
- [ ] Script tag injection prevented
- [ ] All security tests passing
- [ ] No critical vulnerabilities found
- [ ] Findings documented

**Files Created/Modified**:
- `backend/tests/security/test_query_injection.py` - Security tests (~150 lines)
- `backend/tests/security/SECURITY_AUDIT.md` - Audit documentation (~50 lines)

**Estimated Time**: 3 hours

---

### Task 6.5: Security Audit - Rate Limiting Validation (2 hours)

**Goal**: Verify rate limiting works correctly

**Prerequisites**:
- Task 5.6 completed (rate limiting implemented)

**Steps**:
1. **Test rate limiting**
   - Create `backend/tests/security/test_rate_limiting.py`
   - Test: 60 requests in 1 minute succeed
   - Test: 61st request returns 429
   - Test: Rate limit resets after 1 minute
   - Test: Different users have separate limits
2. **Test bypass attempts**
   - Test: Cannot bypass by changing IP (user_id-based)
   - Test: Cannot bypass by changing user-agent
3. **Document findings**
   - Add to `backend/tests/security/SECURITY_AUDIT.md`

**Acceptance Criteria**:
- [ ] Rate limiting tests created
- [ ] 60 requests succeed, 61st fails (429)
- [ ] Rate limit resets after 1 minute
- [ ] Per-user limits enforced
- [ ] Bypass attempts fail
- [ ] All security tests passing
- [ ] Findings documented

**Files Created/Modified**:
- `backend/tests/security/test_rate_limiting.py` - Rate limit tests (~80 lines)
- `backend/tests/security/SECURITY_AUDIT.md` - Update with findings (~20 lines)

**Estimated Time**: 2 hours

---

### Task 6.6: Audit Logging Verification (2 hours)

**Goal**: Verify all search operations logged correctly

**Prerequisites**:
- Search API complete with audit logging

**Steps**:
1. **Create audit logging tests**
   - Create `backend/tests/integration/test_search_audit_logging.py`
   - Test: Search execution creates audit log (action=SEARCH_EXECUTED)
   - Test: Saved search creates audit log (action=SEARCH_SAVED)
   - Test: Export creates audit log (action=SEARCH_EXPORTED)
   - Test: Audit logs include required fields (user_id, query, IP, timestamp)
2. **Verify audit log immutability**
   - Test: Cannot UPDATE audit_logs rows
   - Test: Cannot DELETE audit_logs rows
3. **Run tests**
   - `pytest backend/tests/integration/test_search_audit_logging.py -v`

**Acceptance Criteria**:
- [ ] Audit logging tests created
- [ ] All search operations logged (execute, save, export)
- [ ] Audit logs include user_id, action, query, IP, timestamp
- [ ] Audit logs immutable (no UPDATE/DELETE)
- [ ] All tests passing
- [ ] Test coverage ≥ 90% for audit paths

**Files Created/Modified**:
- `backend/tests/integration/test_search_audit_logging.py` - Audit tests (~120 lines)

**Estimated Time**: 2 hours

---

### Task 6.7: API Documentation Update (2 hours)

**Goal**: Update OpenAPI documentation for all search endpoints

**Prerequisites**:
- All search endpoints implemented

**Steps**:
1. **Update OpenAPI spec**
   - Verify all search endpoints documented in OpenAPI
   - Add request/response examples
   - Add error response schemas (400, 401, 403, 429, 500)
   - Add description for each endpoint
2. **Generate API docs**
   - Run FastAPI app and verify /docs endpoint
   - Verify all schemas visible
   - Verify "Try it out" works
3. **Create API usage guide**
   - Create `docs/api/SEARCH_API_GUIDE.md`
   - Document search query syntax (boolean operators, phrases, field queries)
   - Document filter options
   - Document export formats
   - Add curl examples

**Acceptance Criteria**:
- [ ] All search endpoints documented in OpenAPI
- [ ] Request/response examples added
- [ ] Error responses documented
- [ ] /docs endpoint accessible and complete
- [ ] Search API guide created
- [ ] Query syntax documented with examples

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/search.py` - Update docstrings (~30 lines)
- `docs/api/SEARCH_API_GUIDE.md` - API usage guide (~200 lines)

**Estimated Time**: 2 hours

---

### Task 6.8: User Guide Creation (2 hours)

**Goal**: Create end-user search guide

**Prerequisites**:
- Frontend search UI complete

**Steps**:
1. **Create user guide**
   - Create `docs/user/SEARCH_USER_GUIDE.md`
   - Document basic search
   - Document advanced search (boolean operators)
   - Document filters
   - Document saved searches
   - Document export features
   - Add screenshots
2. **Create quick reference card**
   - Create `docs/user/SEARCH_QUICK_REFERENCE.md`
   - One-page cheat sheet for search syntax
   - Boolean operators (AND, OR, NOT)
   - Phrase search ("exact match")
   - Field search (author:"Dr. Smith")
   - Wildcards (diabet*)

**Acceptance Criteria**:
- [ ] User guide created with sections for all features
- [ ] Screenshots added for clarity
- [ ] Quick reference card created (1-page)
- [ ] Examples included for all query types
- [ ] Guide reviewed for clarity

**Files Created/Modified**:
- `docs/user/SEARCH_USER_GUIDE.md` - User guide (~300 lines)
- `docs/user/SEARCH_QUICK_REFERENCE.md` - Quick reference (~50 lines)

**Estimated Time**: 2 hours

---

## Summary

**Total Tasks**: 65 tasks
**Total Estimated Time**: 120 hours (4 weeks)

**Phase Breakdown**:
- Phase 1: Core Infrastructure (10 tasks, 30 hours)
- Phase 2: Advanced Query Parsing (14 tasks, 30 hours)
- Phase 3: Frontend UI (9 tasks, 30 hours)
- Phase 4: Saved Searches & Export (6 tasks, 15 hours)
- Phase 5: Analytics & Admin (6 tasks, 15 hours)
- Phase 6: Testing & Hardening (8 tasks, 25 hours)

**Parallelization Opportunities**:
- Phase 1 infrastructure tasks (1-5) can run parallel with backend service tasks (6-10)
- Phase 2 backend parsing can overlap with Phase 3 frontend UI
- Phase 4 and 5 can run in parallel
- Phase 6 testing can start as soon as Phase 3 completes

**Test Coverage Target**: ≥85% overall
- Unit tests: ~90 tests
- Integration tests: ~45 tests
- E2E tests: ~15 tests
- Performance tests: 1 load test suite
- Security tests: 2 security test suites

**Key Deliverables**:
- Full-text search with Boolean operators, phrase search, field-specific search
- BM25 relevance ranking with field boosting and recency boost
- Faceted search (document type, author, department, date)
- Search result highlighting and context snippets
- Saved searches (save, share, execute)
- Export capabilities (CSV, JSON, FHIR R4)
- Search analytics dashboard (admin only)
- Comprehensive audit logging (HIPAA compliant)
- Rate limiting (60 searches/minute/user)
- Complete API and user documentation

**Next Steps**:
1. **Review task breakdown with user**
2. **Prioritize critical path tasks** (Phase 1 → Phase 2 → Phase 3)
3. **Begin implementation** with Task 1.1 (Elasticsearch setup)
4. **Update CONTEXT.md** with each completed task
5. **Track progress** using TodoWrite tool

---

**Ready to implement!** Start with Phase 1, Task 1.1: Add Elasticsearch to Docker Compose
