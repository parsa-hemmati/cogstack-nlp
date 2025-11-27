# Technical Plan: Patient Search & Discovery (Sprint 1)

**Version**: 1.0.0
**Date**: 2025-11-25
**Sprint Duration**: 2 weeks (~60 hours)
**Dependencies**: Base Application (Phase 0)

---

## Overview

### Goals

Sprint 1 establishes the **core patient search capability**:
- **Concept-based search** using MedCAT NLP
- **Meta-annotation filtering** (Negation, Temporality, Experiencer, Certainty)
- **Document context** with concept highlighting
- **Performance optimization** (< 500ms response)

### Success Criteria

- [ ] Search patients by medical concept works
- [ ] Temporal filter excludes historical conditions
- [ ] Negation filter excludes "No history of X"
- [ ] Experiencer filter excludes family history
- [ ] Response time < 500ms (p95)
- [ ] All searches require authentication
- [ ] All searches logged to audit trail
- [ ] 85% test coverage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                         │
│  - PatientSearch.vue (search input, filters)                │
│  - PatientList.vue (results display)                        │
│  - FilterPanel.vue (meta-annotation filters)                │
│  - DocumentViewer.vue (document with highlights)            │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│  - POST /api/v1/patients/search                             │
│  - GET /api/v1/patients/{mrn}                               │
│  - GET /api/v1/documents/{documentId}                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer                              │
│  - PatientSearchService (search orchestration)              │
│  - MedCATClient (concept resolution)                        │
│  - ElasticsearchService (patient query)                     │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌────────────────┬────────────────┬────────────────┐
│   MedCAT       │  Elasticsearch │   PostgreSQL   │
│   Service      │   Cluster      │   Database     │
│   (NLP)        │   (Index)      │   (Auth/Audit) │
└────────────────┴────────────────┴────────────────┘
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Backend API | FastAPI | 0.100+ | REST API |
| Frontend | Vue 3 | 3.3+ | UI Framework |
| Search | Elasticsearch | 8.0+ | Patient index |
| NLP | MedCAT | 2.3+ | Concept extraction |
| Cache | Redis | 7.2+ | Query caching |
| Auth | JWT | - | Authentication |
| Database | PostgreSQL | 14+ | Users, Audit logs |

---

## API Design

### POST /api/v1/patients/search

**Request**:
```json
{
  "concept": "atrial flutter",
  "filters": {
    "temporal": "current",
    "includeNegated": false,
    "includeFamily": false,
    "dateRange": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  },
  "pagination": {
    "page": 1,
    "pageSize": 20
  },
  "sort": "relevance"
}
```

**Response**:
```json
{
  "results": [
    {
      "mrn": "MRN123456",
      "demographics": {
        "age": 72,
        "gender": "Male",
        "department": "Cardiology"
      },
      "annotations": [
        {
          "cui": "C0004239",
          "conceptName": "Atrial Flutter",
          "sourceValue": "atrial flutter",
          "documentId": "DOC789",
          "confidence": 0.95,
          "metaAnnotations": {
            "temporality": "current",
            "negated": false,
            "experiencer": "patient"
          }
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalResults": 47,
    "totalPages": 3
  },
  "performance": {
    "searchTime": 245,
    "source": "live"
  }
}
```

---

## Database Schema

### Elasticsearch Index: `patients`

```json
{
  "mappings": {
    "properties": {
      "mrn": { "type": "keyword" },
      "demographics": {
        "properties": {
          "age": { "type": "integer" },
          "gender": { "type": "keyword" },
          "department": { "type": "keyword" }
        }
      },
      "annotations": {
        "type": "nested",
        "properties": {
          "cui": { "type": "keyword" },
          "conceptName": { "type": "text" },
          "documentId": { "type": "keyword" },
          "documentDate": { "type": "date" },
          "confidence": { "type": "float" },
          "metaAnnotations": {
            "properties": {
              "temporality": { "type": "keyword" },
              "negated": { "type": "boolean" },
              "experiencer": { "type": "keyword" },
              "certainty": { "type": "keyword" }
            }
          }
        }
      }
    }
  }
}
```

---

## Component Design

### Backend: PatientSearchService

```python
class PatientSearchService:
    """Orchestrates patient search with MedCAT and Elasticsearch."""

    async def search(
        self,
        query: PatientSearchQuery,
        user: User
    ) -> PatientSearchResponse:
        """
        Execute patient search.

        1. Resolve concept to CUIs via MedCAT
        2. Build Elasticsearch query with filters
        3. Execute search
        4. Log to audit trail
        5. Return formatted response
        """
        # Resolve concept to CUIs
        cuis = await self.medcat_client.get_concepts_for_term(query.concept)

        # Build ES query
        es_query = self.es_service.build_search_query(cuis, query.filters)

        # Execute search
        results = await self.es_service.search(es_query)

        # Audit log
        await self.audit_service.log_search(user, query, len(results))

        return PatientSearchResponse(results=results, ...)
```

### Backend: MedCATClient

```python
class MedCATClient:
    """HTTP client for MedCAT concept resolution."""

    async def get_concepts_for_term(self, term: str) -> List[Concept]:
        """
        Resolve search term to CUIs.

        Example:
            "MI" → [C0027051 (Myocardial Infarction), C0340280 (Myocardial Ischemia)]
        """
        response = await self.http.post(
            f"{self.base_url}/api/process",
            json={"text": term}
        )
        return self._parse_concepts(response.json())
```

### Frontend: PatientSearch.vue

```typescript
// Composition API setup
const { results, isLoading, error, search } = usePatientSearch()

// Search handler
const handleSearch = async () => {
  await search(searchQuery.value, filters.value)
}

// Template structure
<template>
  <div class="patient-search">
    <SearchInput v-model="searchQuery" @search="handleSearch" />
    <FilterPanel v-model="filters" />
    <PatientList :patients="results" :loading="isLoading" />
    <Pagination v-model="page" :total="totalPages" />
  </div>
</template>
```

---

## Implementation Phases

### Phase 1.1: Backend API (0.5 week, 15h)
- PatientSearchService
- MedCATClient
- ElasticsearchService
- API endpoints (search, patient details, document)
- Unit tests

### Phase 1.2: Meta-Annotation Filtering (0.5 week, 15h)
- Temporal filter (current/historical)
- Negation filter
- Experiencer filter (patient/family)
- Elasticsearch query builder
- Filter tests

### Phase 1.3: Frontend Components (0.5 week, 15h)
- PatientSearch.vue
- PatientList.vue
- FilterPanel.vue
- DocumentViewer.vue
- Component tests

### Phase 1.4: Integration & Testing (0.5 week, 15h)
- Integration tests
- E2E tests
- Performance testing
- Bug fixes
- Documentation

---

## Testing Strategy

### Unit Tests (60%)

```python
def test_search_patients_by_concept():
    """Test basic concept search."""
    service = PatientSearchService()
    query = PatientSearchQuery(concept="atrial flutter")

    results = await service.search(query)

    assert len(results.results) > 0
    assert results.performance.searchTime < 500

def test_temporal_filter_excludes_historical():
    """Test temporal filtering."""
    service = PatientSearchService()
    query = PatientSearchQuery(
        concept="diabetes",
        filters=SearchFilters(temporal="current")
    )

    results = await service.search(query)

    for patient in results.results:
        for ann in patient.annotations:
            assert ann.metaAnnotations.temporality == "current"
```

### Integration Tests (30%)

```python
def test_search_api_endpoint():
    """Test full search API."""
    response = client.post(
        "/api/v1/patients/search",
        json={"concept": "atrial flutter"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["performance"]["searchTime"] < 500
```

### E2E Tests (10%)

```typescript
test('patient search workflow', async ({ page }) => {
  await page.fill('[data-testid="search-input"]', 'atrial flutter')
  await page.click('[data-testid="search-btn"]')

  await expect(page.locator('[data-testid="result-count"]'))
    .toContainText('patients found')
})
```

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Search Response (p95) | < 500ms |
| Concurrent Users | 100 |
| Searches/Hour | 1000 |
| MedCAT Response | < 200ms |
| ES Query | < 200ms |

---

## Security Requirements

- JWT authentication required
- RBAC authorization enforced
- Audit logging for all searches
- No PHI in application logs
- Rate limiting (100 req/min)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| MedCAT latency | Caching, concept precomputation |
| ES query complexity | Query optimization, indexes |
| Ambiguous concepts | Show multiple matches |
| False positives | Confidence thresholds |

---

## Deployment Checklist

- [ ] MedCAT service deployed and healthy
- [ ] Elasticsearch index created with mapping
- [ ] Redis cache configured
- [ ] JWT authentication configured
- [ ] Audit logging verified
- [ ] Load testing completed

---

**Document Version**: 1.0.0
**Status**: Ready for implementation
**Estimated Effort**: 60 hours over 2 weeks
