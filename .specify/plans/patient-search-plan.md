# Technical Plan: Patient Search & Discovery

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-11-18
**Phase**: 4 (Patient Search)
**Specification**: [patient-search.md](../specifications/patient-search.md)

---

## Executive Summary

**Goal**: Implement concept-based patient search using existing Phase 3 infrastructure (patients, extracted_entities tables) and MedCAT NLP.

**Key Achievements**:
- Fast search (<500ms) using PostgreSQL with optimized indexes
- 90%+ precision using meta-annotation filters
- HIPAA-compliant audit logging
- Reusable service layer for future features

**Technology Stack**:
- Backend: FastAPI (async), SQLAlchemy (async ORM), Pydantic (validation)
- Frontend: Vue 3 (Composition API), Vuetify 3 (Material Design), TypeScript
- Database: PostgreSQL 15 (existing tables + indexes)
- NLP: MedCAT Service (existing, medcat_snomed.zip)
- Caching: Redis (search history)

**Timeline**: 4-6 hours (8 tasks)

---

## Architecture

### High-Level System Diagram

```
┌─────────────────┐
│   Vue 3 UI      │
│ PatientSearch   │──────┐
│   Component     │      │
└─────────────────┘      │
                         │ HTTP/JSON
                         ▼
┌──────────────────────────────────────────┐
│       FastAPI Backend                    │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  API Router                        │ │
│  │  /api/v1/patients/search           │ │
│  │  - Input validation (Pydantic)     │ │
│  │  - Authorization (RBAC decorator)  │ │
│  │  - Audit logging                   │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │  PatientSearchService              │ │
│  │  - Query builder (meta-filters)    │ │
│  │  - Result ranking                  │ │
│  │  - Concept highlight extraction    │ │
│  └────────────────────────────────────┘ │
│                 │                        │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │  Database Layer (SQLAlchemy)       │ │
│  │  - extracted_entities table        │ │
│  │  - patients table                  │ │
│  │  - documents table                 │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│     PostgreSQL Database                  │
│  - extracted_entities (CUI, meta_anns)   │
│  - patients (demographics)               │
│  - documents (encrypted content)         │
│  - audit_logs (immutable)                │
└──────────────────────────────────────────┘
```

### Component Interaction Flow

```
1. User enters search query: "atrial flutter"
   ↓
2. Frontend (PatientSearch.vue) sends POST /api/v1/patients/search
   {
     "query": "atrial flutter",
     "filters": {
       "negation": "Affirmed",
       "temporality": "Current",
       "experiencer": "Patient"
     },
     "page": 1,
     "page_size": 20
   }
   ↓
3. Backend API validates input (Pydantic schema)
   ↓
4. Authorization check (RBAC decorator)
   ↓
5. PatientSearchService.search():
   a. Parse query → extract CUI (if not provided)
   b. Build SQL query with meta-annotation filters
   c. Execute query against extracted_entities table
   d. Join with patients table for demographics
   e. Rank results by document_count (desc)
   f. Paginate results
   ↓
6. Audit log created (user_id, query, filters, result_count)
   ↓
7. Response returned:
   {
     "results": [
       {
         "patient_id": "uuid",
         "nhs_number": "XXX-XXX-1234",
         "full_name": "John Smith",
         "date_of_birth": "1965-03-15",
         "age": 58,
         "document_count": 15,
         "concept_document_count": 3
       },
       ...
     ],
     "total_count": 42,
     "page": 1,
     "page_size": 20
   }
   ↓
8. Frontend displays results in data table
   ↓
9. User clicks "3 documents" to expand
   ↓
10. Frontend sends GET /api/v1/patients/{id}/concept-highlights?cui={cui}
    ↓
11. Backend returns document list with snippets
    {
      "documents": [
        {
          "document_id": "uuid",
          "title": "Discharge Summary 2023-05-10",
          "date": "2023-05-10",
          "snippet": "...patient presents with <b>atrial flutter</b> and rapid ventricular...",
          "meta_annotations": {
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Confirmed"
          }
        },
        ...
      ]
    }
    ↓
12. Frontend displays highlights in expandable panel
```

---

## Technology Choices

### Backend Framework: FastAPI (Existing)

**Rationale**:
- Already used in Phase 1-3 (consistency)
- Async support for concurrent searches
- Automatic OpenAPI documentation
- Pydantic validation (type-safe)

**Alternatives Considered**:
- Django: Too heavy, synchronous by default
- Flask: No async support, manual validation

---

### Database: PostgreSQL 15 (Existing)

**Rationale**:
- Phase 3 infrastructure already in place
- JSONB support for meta_anns filtering
- Sufficient performance for 10,000 patients
- Migration path to Elasticsearch in Phase 5

**Alternatives Considered**:
- Elasticsearch: Better for 100k+ patients, but adds complexity (deferred to Phase 5)
- MongoDB: Poor fit for structured patient data

**Performance Strategy**:
- Composite indexes on (cui, negation, temporality, experiencer)
- GIN index on meta_anns JSONB column
- Materialized view for frequent queries (if needed)

---

### Frontend: Vue 3 + Vuetify 3 (Existing)

**Rationale**:
- Consistent with Phase 2 (User Management UI)
- Composition API for reusable logic
- Vuetify 3 Material Design components (v-data-table, v-autocomplete)

**Alternatives Considered**:
- React: Team unfamiliar, higher learning curve
- Angular: Too heavy for this project

---

### Caching: Redis (Existing)

**Rationale**:
- Already used for sessions in Phase 1
- Store search history (last 10 searches per user)
- Fast retrieval (<1ms)

**Data Structure**:
```
Key: "search_history:{user_id}"
Value: LIST of JSON objects
[
  {
    "query": "atrial flutter",
    "filters": {...},
    "timestamp": "2023-05-10T14:30:00Z"
  },
  ...
]
TTL: 7 days
```

---

## API Design

### Endpoint: POST /api/v1/patients/search

**Request**:
```json
{
  "query": "atrial flutter",           // Free-text or SNOMED-CT CUI
  "filters": {
    "negation": "Affirmed",            // Affirmed | Negated | Any
    "temporality": "Current",          // Current | Historical | Any
    "experiencer": "Patient",          // Patient | Family | Other | Any
    "certainty": "Confirmed"           // Confirmed | Suspected | Any
  },
  "sort_by": "relevance",              // relevance | name | last_updated
  "page": 1,
  "page_size": 20
}
```

**Response (200)**:
```json
{
  "results": [
    {
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "nhs_number": "XXX-XXX-1234",
      "full_name": "John Smith",
      "date_of_birth": "1965-03-15",
      "age": 58,
      "document_count": 15,
      "concept_document_count": 3,
      "last_updated": "2023-05-10T14:30:00Z"
    }
  ],
  "total_count": 42,
  "page": 1,
  "page_size": 20,
  "query_time_ms": 234
}
```

**Error Responses**:
- 400: Invalid query (empty string, invalid CUI)
- 401: Not authenticated
- 403: Insufficient permissions
- 500: Database error

**OpenAPI Spec**:
```yaml
/api/v1/patients/search:
  post:
    summary: Search patients by medical concept
    tags: [Patients]
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PatientSearchRequest'
    responses:
      '200':
        description: Search results
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatientSearchResponse'
```

---

### Endpoint: GET /api/v1/patients/{patient_id}/concept-highlights

**Purpose**: Retrieve documents containing specific concept for a patient

**Request**:
```
GET /api/v1/patients/550e8400-e29b-41d4-a716-446655440000/concept-highlights?cui=C0004238
```

**Query Parameters**:
- `cui` (required): SNOMED-CT CUI
- `filters` (optional): Same as search filters

**Response (200)**:
```json
{
  "documents": [
    {
      "document_id": "uuid",
      "title": "Discharge Summary",
      "date": "2023-05-10",
      "snippet": "...patient presents with <b>atrial flutter</b> and rapid ventricular...",
      "meta_annotations": {
        "Negation": "Affirmed",
        "Temporality": "Current",
        "Experiencer": "Patient",
        "Certainty": "Confirmed"
      },
      "start_char": 45,
      "end_char": 59
    }
  ],
  "total_count": 3
}
```

---

## Data Model

### No New Tables Required

Phase 3 tables are sufficient:
- `patients`: Demographics, NHS number, DOB
- `documents`: Encrypted content, processing status
- `extracted_entities`: CUI, pretty_name, meta_anns JSONB

### Database Indexes (New)

**Performance optimization for search queries**:

```sql
-- Composite index for filtered searches
CREATE INDEX idx_entities_cui_meta
ON extracted_entities (cui, (meta_anns->>'Negation'), (meta_anns->>'Temporality'), (meta_anns->>'Experiencer'));

-- GIN index for JSONB meta_anns (flexible filtering)
CREATE INDEX idx_entities_meta_anns_gin
ON extracted_entities USING GIN (meta_anns);

-- Index for patient lookups
CREATE INDEX idx_entities_patient_id
ON extracted_entities (patient_id);

-- Index for document lookups
CREATE INDEX idx_entities_document_id
ON extracted_entities (document_id);
```

**Query Plan Optimization**:
```sql
EXPLAIN ANALYZE
SELECT
  p.id, p.nhs_number, p.full_name, p.date_of_birth,
  COUNT(DISTINCT e.document_id) as concept_document_count
FROM extracted_entities e
JOIN patients p ON e.patient_id = p.id
WHERE
  e.cui = 'C0004238'
  AND e.meta_anns->>'Negation' = 'Affirmed'
  AND e.meta_anns->>'Temporality' = 'Current'
  AND e.meta_anns->>'Experiencer' = 'Patient'
GROUP BY p.id, p.nhs_number, p.full_name, p.date_of_birth
ORDER BY concept_document_count DESC
LIMIT 20;

-- Expected: Index Scan (< 10ms for 10k patients)
```

---

## Implementation Phases

### Phase 4.1: Database Indexes (30 minutes)

**Goal**: Optimize database for search queries

**Steps**:
1. Create migration: `006_add_patient_search_indexes.py`
2. Add composite index on (cui, meta_anns)
3. Add GIN index on meta_anns JSONB
4. Test query performance (before/after benchmarks)

**Acceptance**:
- Indexes created without errors
- Query time <50ms for 10,000 patients
- EXPLAIN ANALYZE shows index usage

---

### Phase 4.2: Backend API - Search Endpoint (1.5 hours)

**Goal**: Implement POST /api/v1/patients/search

**Steps**:
1. Create Pydantic schemas:
   - `PatientSearchRequest` (query, filters, pagination)
   - `PatientSearchResponse` (results, total_count, query_time_ms)
   - `PatientSearchResult` (patient demographics + concept_document_count)

2. Create `PatientSearchService`:
   - `search(query, filters, pagination)` method
   - Build SQL query with meta-annotation filters
   - Execute query, rank results
   - Return paginated results

3. Create API router:
   - `POST /api/v1/patients/search`
   - Input validation (Pydantic)
   - Authorization (RBAC decorator: Clinician, Researcher, Admin)
   - Audit logging
   - Error handling

4. Unit tests:
   - Test filter combinations (negation, temporality, experiencer)
   - Test pagination
   - Test empty results
   - Test invalid query

**Acceptance**:
- Endpoint returns results within 500ms (P95)
- Filters work correctly (90%+ precision)
- Audit log created for each search
- 12 unit tests passing

---

### Phase 4.3: Backend API - Concept Highlights Endpoint (1 hour)

**Goal**: Implement GET /api/v1/patients/{id}/concept-highlights

**Steps**:
1. Create Pydantic schemas:
   - `ConceptHighlightRequest` (cui, filters)
   - `ConceptHighlightResponse` (documents, total_count)
   - `DocumentHighlight` (document_id, title, date, snippet, meta_annotations)

2. Update `PatientSearchService`:
   - `get_concept_highlights(patient_id, cui, filters)` method
   - Query extracted_entities for patient + CUI
   - Join with documents table
   - Extract snippet (100 chars before/after concept)
   - Return document list

3. Create API router:
   - `GET /api/v1/patients/{id}/concept-highlights`
   - Authorization (RBAC + patient access check)
   - Audit logging (document view)

4. Unit tests:
   - Test snippet extraction
   - Test meta-annotation display
   - Test empty results

**Acceptance**:
- Endpoint returns highlights within 300ms
- Snippets show context (100 chars before/after)
- Meta-annotations displayed correctly
- 8 unit tests passing

---

### Phase 4.4: Frontend - Search Component (2 hours)

**Goal**: Implement PatientSearch.vue component

**Steps**:
1. Create Vue component:
   - Search box (v-text-field with autocomplete)
   - Filter chips (v-chip-group for meta-annotations)
   - Results table (v-data-table)
   - Pagination (v-pagination)

2. Create composable:
   - `usePatientSearch()` composable
   - `search(query, filters, page)` method
   - State management (results, loading, error)
   - API integration (Axios client)

3. Create API client:
   - `patientSearchApi.ts`
   - `search()` method
   - `getConceptHighlights()` method

4. Add to router:
   - Route: `/patients/search`
   - Navigation link in App.vue

**Acceptance**:
- Search box functional
- Filters work (3 meta-annotations)
- Results displayed in table
- Pagination works
- Loading spinner shown during search

---

### Phase 4.5: Frontend - Concept Highlights (1 hour)

**Goal**: Expandable concept highlights panel

**Steps**:
1. Add expandable row to v-data-table:
   - Click "X documents" to expand
   - Show document list in expansion panel

2. Create DocumentHighlight component:
   - Display title, date, snippet
   - Highlight concept (bold)
   - Show meta-annotation badges (color-coded)
   - Click document to open modal

3. Create DocumentModal component:
   - Display full document content
   - Close button

**Acceptance**:
- Expandable rows work
- Highlights displayed correctly
- Meta-annotations color-coded (green=Affirmed, red=Negated, etc.)
- Modal opens with full document

---

### Phase 4.6: Search History (Redis Cache) (45 minutes)

**Goal**: Track recent searches per user

**Steps**:
1. Update `PatientSearchService`:
   - `save_search_history(user_id, query, filters)` method
   - Store in Redis LIST (max 10 items)
   - `get_search_history(user_id)` method

2. Create API endpoint:
   - `GET /api/v1/patients/search/history`
   - Returns last 10 searches

3. Update frontend:
   - Autocomplete dropdown shows recent searches
   - Click to re-run search

**Acceptance**:
- Search history saved to Redis
- Last 10 searches displayed
- Click re-runs search instantly
- TTL: 7 days

---

### Phase 4.7: Integration Tests (1 hour)

**Goal**: End-to-end tests for patient search

**Steps**:
1. Create test fixtures:
   - 100 patients with diverse conditions
   - 500 documents with extracted entities
   - Meta-annotations coverage (negated, historical, family)

2. Create integration tests:
   - Test search with filters
   - Test concept highlights
   - Test pagination
   - Test search history
   - Test audit logging

3. Performance tests:
   - Measure search response time
   - Verify <500ms for 10,000 patients

**Acceptance**:
- 15 integration tests passing
- Performance target met (<500ms)
- Test coverage: 90%+

---

### Phase 4.8: Documentation & Deployment (30 minutes)

**Goal**: Document API and deploy

**Steps**:
1. Update OpenAPI spec (auto-generated)
2. Add usage examples to DEVELOPMENT.md
3. Update CONTEXT.md with Phase 4 completion
4. Deploy to development environment
5. Manual smoke testing

**Acceptance**:
- OpenAPI docs complete
- DEVELOPMENT.md updated
- CONTEXT.md updated
- All services healthy

---

## Testing Strategy

### Unit Tests (60% of tests)

**Backend** (`tests/unit/services/test_patient_search_service.py`):
- Filter combinations (negation, temporality, experiencer)
- Query builder logic
- Snippet extraction
- Pagination logic
- Empty results handling

**Frontend** (`tests/unit/composables/usePatientSearch.test.ts`):
- API integration
- State management
- Error handling
- Loading states

**Target**: 40 unit tests

---

### Integration Tests (30% of tests)

**Backend** (`tests/integration/test_patient_search_api.py`):
- POST /api/v1/patients/search (full workflow)
- GET /api/v1/patients/{id}/concept-highlights
- Audit logging verification
- Authorization checks

**Target**: 15 integration tests

---

### E2E Tests (10% of tests)

**Frontend** (`tests/e2e/patient-search.spec.ts`):
- Search flow (enter query → filter → view results)
- Concept highlights expansion
- Document modal
- Search history

**Target**: 5 E2E tests

---

### Performance Tests

**Load Test** (Apache Bench or Locust):
```bash
ab -n 1000 -c 10 http://localhost:8000/api/v1/patients/search \
  -p search_payload.json \
  -T 'application/json' \
  -H 'Authorization: Bearer <token>'
```

**Acceptance**:
- P95 response time: <500ms
- Throughput: 20 requests/second
- No errors under load

---

## Deployment

### Development Environment

**Steps**:
1. Run database migrations: `alembic upgrade head`
2. Restart backend: `docker-compose restart backend`
3. Clear frontend cache: `docker-compose restart frontend`
4. Verify health: `curl http://localhost:8000/health`

---

### Production Hardening

**Already in place from Option B**:
- Resource limits (docker-compose.prod.yml)
- Capability dropping
- Audit logging
- Backup/restore scripts

**Additional for Phase 4**:
- Monitor search response times (Prometheus metrics)
- Alert if P95 > 500ms
- Log slow queries (PostgreSQL pg_stat_statements)

---

## Risks & Mitigations

### Risk 1: PostgreSQL Performance Degrades Beyond 10k Patients

**Likelihood**: Medium
**Impact**: High (search >500ms)

**Mitigation**:
- Add composite indexes (already planned)
- Monitor query performance (pg_stat_statements)
- Elasticsearch migration plan ready (Phase 5)

---

### Risk 2: Meta-Annotation Accuracy Lower Than Expected

**Likelihood**: Low-Medium
**Impact**: Medium (precision <90%)

**Mitigation**:
- Use production-proven MedCAT models (medcat_snomed.zip)
- Provide concept highlights for manual verification
- Collect user feedback on false positives

---

### Risk 3: Snippet Extraction Errors (Context Missing)

**Likelihood**: Low
**Impact**: Low (usability issue)

**Mitigation**:
- Test snippet extraction with edge cases (concept at document start/end)
- Fallback: Display full sentence if snippet extraction fails

---

## Performance Benchmarks

| Operation | Target (P95) | Expected (MVP) | Notes |
|-----------|--------------|----------------|-------|
| Search query | <500ms | ~250ms | 10k patients, 100k entities |
| Concept highlights | <300ms | ~150ms | 3-5 documents per patient |
| Pagination | <200ms | ~100ms | Cached results |
| Search history | <50ms | ~10ms | Redis lookup |

**Scalability Path**:
- 10k patients: PostgreSQL (Phase 4) ✓
- 100k patients: Elasticsearch (Phase 5)
- 1M patients: Elasticsearch + sharding (Phase 6)

---

## Monitoring & Observability

### Metrics to Track

1. **Performance Metrics**:
   - Search response time (P50, P95, P99)
   - Database query time
   - Cache hit rate (Redis)

2. **Usage Metrics**:
   - Searches per day
   - Most common queries
   - Filter usage (which meta-annotations used most)

3. **Error Metrics**:
   - 4xx errors (validation failures)
   - 5xx errors (database errors)
   - Search timeouts

### Logging

**Application Logs** (backend):
- Log level: INFO
- Include: user_id, query, filters, result_count, query_time_ms
- Exclude: PHI (patient names, NHS numbers)

**Audit Logs** (PostgreSQL):
- Every search logged
- Include: user_id, query, filters, result_count, timestamp, ip_address
- Immutable (cannot be modified/deleted)

---

## References

- **Specification**: `.specify/specifications/patient-search.md`
- **Sprint Plan**: `docs/PROJECT_PLAN.md` (Sprint 1)
- **MedCAT Meta-Annotations Guide**: `docs/advanced/meta-annotations-guide.md`
- **Phase 3 Implementation**: `.specify/specifications/document-management.md`
- **Skills**: `.claude/skills/medcat-meta-annotations/`

---

**Plan Status**: Draft
**Next Steps**: Create task breakdown, get user approval
**Estimated Timeline**: 4-6 hours (8 tasks)
