# Specification: Patient Search & Discovery (Sprint 1)

**Version**: 1.0.0
**Date**: 2025-11-25
**Status**: Implemented
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 2 weeks (~60 hours)
**Story Points**: 13

**Version History**:
- **1.0.0** (2025-11-25): Initial specification extracted from PRD

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [API Design](#api-design)
8. [Database Schema](#database-schema)
9. [UI/UX Design](#uiux-design)
10. [Integration Points](#integration-points)
11. [Performance Requirements](#performance-requirements)
12. [Constraints](#constraints)
13. [Acceptance Criteria](#acceptance-criteria)
14. [Alignment with Constitution](#alignment-with-constitution)
15. [Testing Strategy](#testing-strategy)
16. [Open Questions](#open-questions)

---

## Context

### Background

Sprint 1 establishes the **foundation** for the Clinical Care Tools platform. Patient Search & Discovery is the first clinical module, providing concept-based search capabilities powered by MedCAT NLP.

**CogStack Product Alignment**: Enterprise-grade Search

### The Problem

Currently, finding patients with specific medical conditions requires:
- Manual chart review (time-consuming, error-prone)
- Reliance on structured data codes (incomplete, often outdated)
- No ability to search free-text clinical notes

This leads to:
- Missed patients for clinical pathways
- Inability to identify cohorts for quality improvement
- Delayed identification of safety issues

### Solution

Leverage MedCAT's NLP capabilities to:
1. Extract medical concepts from clinical notes
2. Enable search across unstructured clinical text
3. Filter by temporal context (current vs historical)
4. Distinguish patient vs family history

### Business Value

- **Time Savings**: Reduce patient identification time from hours to seconds
- **Quality Improvement**: Identify all relevant patients, not just coded ones
- **Clinical Pathways**: Enable automated pathway enrollment
- **Research**: Foundation for cohort building

---

## Goals

### Primary Goals

1. **Concept-based Patient Search** (P0)
   - Search patients by medical concept (SNOMED-CT, ICD-10)
   - MedCAT-powered NLP extraction from clinical notes
   - Sub-500ms response time (p95)
   - Results include patient demographics + matching concepts

2. **Meta-Annotation Filtering** (P0)
   - Temporal filter: Current vs Historical conditions
   - Negation filter: Exclude "No history of X"
   - Experiencer filter: Exclude family history
   - Certainty filter: Definite vs Possible vs Probable

3. **Document Context** (P1)
   - View source documents containing concepts
   - Highlight matching terms in document text
   - Character-level position tracking

4. **Advanced Filters** (P2)
   - Date range filtering
   - Department filtering
   - Document type filtering

### Secondary Goals

- Search autocomplete with recent queries
- Caching for repeated searches
- Export search results

---

## Non-Goals

- **Document upload** (handled by base application)
- **NLP model training** (MedCAT handled separately)
- **Patient demographics management** (assumed from EHR)
- **Multi-site search** (single instance for Sprint 1)

---

## User Stories

### US-1.1: Core Search Functionality (P0)

**As a** clinician
**I want to** search for patients by medical condition/concept
**So that** I can quickly identify relevant patients for review

**Acceptance Criteria**:
- Given I enter "atrial flutter" in search box
- When I click Search
- Then I see list of patients with that concept in their notes
- And results appear within 500ms
- And each result shows patient demographics + concept highlights

### US-1.2: Temporal Filtering (P0)

**As a** clinician
**I want to** filter by current vs historical conditions
**So that** I find patients with active conditions only

**Acceptance Criteria**:
- Given search results for "diabetes"
- When I apply filter "Current conditions only"
- Then I see only patients with recent/ongoing diabetes mentions
- And historical/resolved diabetes is excluded
- And filter updates results within 200ms

### US-1.3: Meta-Annotation Filtering (P0)

**As a** clinician
**I want to** exclude family history and negated conditions
**So that** I find patients with actual diagnoses

**Acceptance Criteria**:
- Given search for "myocardial infarction"
- When I check "Exclude family history"
- Then I see only patients where MI refers to patient (not relatives)
- And when I check "Exclude negated"
- Then "No history of MI" mentions are excluded

### US-1.4: Document Context (P1)

**As a** clinician
**I want to** see which documents contain the concepts
**So that** I can verify findings in original context

**Acceptance Criteria**:
- Given patient in search results
- When I click on concept tag (e.g., "atrial flutter")
- Then I see list of documents containing that concept
- And clicking document shows full text with concept highlighted
- And highlight includes character position in text

### US-1.5: Advanced Filters (P2)

**As a** clinician
**I want to** filter by date range, department, and provider
**So that** I narrow results to relevant scope

**Acceptance Criteria**:
- Filter by date range (e.g., "Last 30 days", "Last year", custom range)
- Filter by department (e.g., "Cardiology", "Emergency")
- Filter by document type (e.g., "Discharge summary", "Progress notes")
- Multiple filters combine with AND logic
- Clear all filters button resets to all results

---

## Requirements

### Functional Requirements

#### FR-1: Search Input Schema

```typescript
interface PatientSearchQuery {
  concept: string                    // Required: Medical concept to search
  filters?: {
    temporal?: 'current' | 'historical' | 'all'  // Default: 'all'
    includeNegated?: boolean         // Default: false
    includeFamily?: boolean          // Default: false
    dateRange?: {
      start: string                  // ISO 8601 date
      end: string                    // ISO 8601 date
    }
    departments?: string[]           // Department IDs
    documentTypes?: string[]         // Document type IDs
  }
  pagination?: {
    page: number                     // Default: 1
    pageSize: number                 // Default: 20, max: 100
  }
  sort?: 'relevance' | 'date' | 'name'  // Default: 'relevance'
}
```

**Validation Rules**:
- `concept` is required, minimum 3 characters
- `concept` maximum 100 characters
- `dateRange.start` must be before `dateRange.end`
- `pagination.pageSize` between 1 and 100
- Invalid input returns 400 Bad Request with error details

#### FR-2: Search Output Schema

```typescript
interface PatientSearchResponse {
  results: Patient[]
  pagination: {
    page: number
    pageSize: number
    totalResults: number
    totalPages: number
  }
  performance: {
    searchTime: number              // milliseconds
    source: 'cache' | 'live'        // indicate if cached
  }
  filters: AppliedFilters           // Echo applied filters
}

interface Patient {
  mrn: string                       // Medical Record Number (de-identified in logs)
  demographics: {
    age: number
    gender: string
    department: string
  }
  annotations: Annotation[]         // Matching concepts from MedCAT
  lastUpdated: string               // ISO 8601 timestamp
}

interface Annotation {
  cui: string                       // Concept Unique Identifier
  conceptName: string               // Human-readable name
  sourceValue: string               // Actual text in document
  documentId: string
  documentType: string
  documentDate: string
  startChar: number                 // Character position in document
  endChar: number
  confidence: number                // 0.0 to 1.0
  metaAnnotations: {
    temporality?: 'current' | 'historical' | 'future'
    negated?: boolean
    experiencer?: 'patient' | 'family' | 'other'
    certainty?: 'definite' | 'probable' | 'possible'
  }
  snomedCT?: string[]               // SNOMED-CT codes
  icd10?: string[]                  // ICD-10 codes
}
```

### Non-Functional Requirements

#### NFR-1: Performance

- **Search Response Time**: < 500ms (p95)
- **Acceptable**: < 1000ms (p95)
- **Unacceptable**: > 2000ms
- Support 100 concurrent users
- 1000 searches per hour

#### NFR-2: Security

- JWT tokens required for all API calls
- Role-based access control (RBAC)
- Audit log all patient searches (user, timestamp, query)
- NO PHI in logs: Log query parameters but not patient identifiers
- Rate limiting: 100 requests per minute per user

#### NFR-3: Reliability

- Uptime: 99.9% (excluding planned maintenance)
- MedCAT service failure: Return cached results if available
- Elasticsearch failure: Return error with retry suggestion

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                         │
│  - PatientSearch.vue (search input, filters)                │
│  - PatientList.vue (results display)                        │
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

### Component Responsibilities

**PatientSearchService** (`app/services/patient_search_service.py`):
- Receive search query from API endpoint
- Call MedCAT service to find matching concepts
- Query Elasticsearch for patients with matching annotations
- Apply filters (temporal, negation, family, date)
- Sort and paginate results
- Return formatted response

**MedCATClient** (`app/clients/medcat/medcat_client.py`):
- HTTP client for MedCAT service
- Concept normalization (search term → CUIs)
- Error handling and retries
- Response parsing

**ElasticsearchService** (`app/services/elasticsearch_service.py`):
- Build Elasticsearch query from search parameters
- Execute query against patient index
- Parse Elasticsearch response
- Handle aggregations (for counts, facets)

---

## API Design

### POST /api/v1/patients/search

**Request Headers**:
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body**: See `PatientSearchQuery` schema

**Response**: See `PatientSearchResponse` schema

**Status Codes**:
- `200 OK`: Search successful
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid auth token
- `403 Forbidden`: User lacks permission
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: MedCAT service down

### GET /api/v1/patients/{mrn}

**Purpose**: Retrieve full patient information with all annotations

**Response**: Single `Patient` object with full annotation history

### GET /api/v1/documents/{documentId}

**Purpose**: Retrieve document text with specific concept highlighted

**Query Params**: `?highlightCUI={cui}`

**Response**:
```typescript
interface DocumentResponse {
  documentId: string
  text: string
  highlights: {
    startChar: number
    endChar: number
    cui: string
    conceptName: string
  }[]
  metadata: {
    documentType: string
    author: string
    date: string
    department: string
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
          "sourceValue": { "type": "text" },
          "documentId": { "type": "keyword" },
          "documentType": { "type": "keyword" },
          "documentDate": { "type": "date" },
          "startChar": { "type": "integer" },
          "endChar": { "type": "integer" },
          "confidence": { "type": "float" },
          "metaAnnotations": {
            "properties": {
              "temporality": { "type": "keyword" },
              "negated": { "type": "boolean" },
              "experiencer": { "type": "keyword" },
              "certainty": { "type": "keyword" }
            }
          },
          "snomedCT": { "type": "keyword" },
          "icd10": { "type": "keyword" }
        }
      },
      "lastUpdated": { "type": "date" }
    }
  }
}
```

---

## UI/UX Design

### Frontend Components

#### PatientSearch.vue

**Location**: `frontend/src/components/clinical/PatientSearch.vue`

**Responsibilities**:
- Search input field with autocomplete (suggest recent searches)
- Filter panel (temporal, negation, family history, date range)
- Search button with loading state
- Display search results in table/card view
- Pagination controls

#### PatientList.vue

**Location**: `frontend/src/components/clinical/PatientList.vue`

**Responsibilities**:
- Display patient cards/rows with demographics
- Show matching concepts with badges
- Click to view patient details
- Highlight matching terms

#### FilterPanel.vue

**Location**: `frontend/src/components/clinical/FilterPanel.vue`

**Responsibilities**:
- Temporal filter (radio buttons: All / Current / Historical)
- Checkboxes (Include negated, Include family history)
- Date range picker
- Department multi-select
- Document type multi-select
- Clear filters button

---

## Integration Points

### External Services

**MedCAT Service**:
- **Required**: Yes (critical path)
- **Version**: >= 2.0
- **Endpoint**: `http://medcat-service:5000/api/process`
- **Performance**: < 200ms per document
- **Fallback**: Cached concept mappings (read-only)

**Elasticsearch**:
- **Required**: Yes (critical path)
- **Version**: >= 8.0
- **Cluster**: 3 nodes minimum
- **Index**: `patients` with mapping defined
- **Fallback**: None (service unavailable if ES down)

**PostgreSQL**:
- **Required**: Yes (for user auth, audit logs)
- **Version**: >= 14
- **Tables**: `users`, `audit_logs`

**Redis**:
- **Required**: No (nice to have)
- **Purpose**: Caching search results
- **Fallback**: Direct database queries (slower)

---

## Performance Requirements

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| Search Response | <500ms (p95) | <1000ms | >2000ms |
| Concurrent Users | 100 | 50 | <25 |
| Searches/Hour | 1000 | 500 | <100 |

**Optimization Strategies**:
- Redis caching (5-minute TTL for identical queries)
- Elasticsearch query optimization (indexes, filters vs queries)
- Pagination (max 100 results per page)
- Debounce search input (500ms delay)

---

## Constraints

### Technical Constraints

- Must integrate with existing MedCAT v2.3 service
- Elasticsearch cluster required (not optional)
- Single-site deployment (no multi-tenant)

### Regulatory Constraints

- HIPAA compliance for PHI access
- Audit logging mandatory
- No PHI in application logs

### Resource Constraints

- 2-week sprint duration
- Single developer implementation

---

## Acceptance Criteria

### Functional Acceptance

- [ ] **Search by concept**: Enter "atrial flutter", get relevant patients
- [ ] **Temporal filter**: "Current only" excludes historical mentions
- [ ] **Negation filter**: "Exclude negated" removes "No history of X"
- [ ] **Family history filter**: Excludes "Mother has diabetes"
- [ ] **Date range filter**: Only results from specified date range
- [ ] **Pagination**: Navigate through results (20 per page)
- [ ] **Sorting**: Sort by relevance, date, or name
- [ ] **Document view**: Click concept to see source document
- [ ] **Highlighting**: Concept highlighted in document text

### Non-Functional Acceptance

- [ ] **Performance**: 95% of searches complete within 500ms
- [ ] **Load**: Supports 100 concurrent users without degradation
- [ ] **Security**: All searches require authentication
- [ ] **Audit**: All searches logged with user + timestamp
- [ ] **Error handling**: Graceful failures with user-friendly messages
- [ ] **Caching**: Identical queries return cached results

### Testing Acceptance

- [ ] **Unit tests**: 85%+ coverage for all services
- [ ] **Integration tests**: API endpoints tested with mock MedCAT
- [ ] **E2E tests**: Full search workflow tested in browser
- [ ] **Performance tests**: Load test with 100 concurrent users
- [ ] **Security tests**: Penetration testing passed

---

## Alignment with Constitution

| Principle | How This Sprint Addresses It |
|-----------|------------------------------|
| Patient Safety First | Meta-annotation filtering prevents false positives |
| Privacy by Design | Audit logging, no PHI in logs |
| Evidence-Based Development | MedCAT NLP backed by medical ontologies |
| Transparency | Confidence scores displayed |
| Performance | Sub-500ms response targets |

---

## Testing Strategy

### Unit Tests (85%+ coverage)

**Backend**:
- `test_patient_search_service.py`: Search logic, filtering
- `test_medcat_client.py`: Concept resolution
- `test_elasticsearch_service.py`: Query building

**Frontend**:
- `PatientSearch.test.ts`: Component behavior
- `PatientList.test.ts`: Result display
- `FilterPanel.test.ts`: Filter interactions

### Integration Tests

- API endpoint tests with mock MedCAT
- Elasticsearch query integration
- Authentication flow

### E2E Tests (Playwright)

- Complete search workflow
- Filter application
- Document viewing with highlights

### Performance Tests

- 100 concurrent users
- 1000 searches over 1 hour
- P95 latency < 500ms

---

## Open Questions

1. **Concept disambiguation**: How to handle ambiguous terms (e.g., "MI" = Myocardial Infarction vs Mental Illness)?
   - Proposed: Show all matching concepts, allow user selection

2. **Result relevance ranking**: How to rank results when multiple concepts match?
   - Proposed: Score by confidence, recency, and match count

3. **Offline mode**: Should cached results be available when services are down?
   - Proposed: Yes, with "cached results" indicator

---

## References

- PRD: `docs/prd/sprint-1/patient-search-discovery.md`
- MedCAT Documentation: https://github.com/CogStack/MedCAT
- FHIR Patient Resource: https://www.hl7.org/fhir/patient.html
