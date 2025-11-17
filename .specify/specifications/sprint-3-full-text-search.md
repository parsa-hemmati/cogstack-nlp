# Specification: Full-Text Search Enhancement (Sprint 3)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 4 weeks (~120 hours)

**Version History**:
- **1.0.0** (2025-11-17): Initial specification for Full-Text Search Enhancement

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [Database Schema](#database-schema)
8. [Search Query Language](#search-query-language)
9. [Relevance Ranking Algorithm](#relevance-ranking-algorithm)
10. [Integration Points](#integration-points)
11. [Performance Requirements](#performance-requirements)
12. [Constraints](#constraints)
13. [Acceptance Criteria](#acceptance-criteria)
14. [Alignment with Constitution](#alignment-with-constitution)
15. [Testing Strategy](#testing-strategy)
16. [Deployment Considerations](#deployment-considerations)
17. [Open Questions](#open-questions)

---

## Context

### Background

**Sprint 1** delivered Patient Search: search for patients by clinical concepts (SNOMED-CT) with meta-annotation filtering.

**Sprint 2** delivered Timeline View: chronological visualization of patient history with concept extraction.

**Sprint 3** extends search capabilities to **full-text document search**, enabling clinicians to find specific information within millions of clinical records.

**CogStack Product Alignment**: Enterprise-grade Search (full-text search across millions of clinical records)

### The Problem

Current limitations:
1. **Patient-level search only**: Can't search for specific text within documents
2. **No structured field search**: Can't filter by document type, author, date range, department
3. **No advanced queries**: Can't combine multiple search criteria (e.g., "diabetes AND chest pain")
4. **No relevance ranking**: Results not sorted by relevance (most relevant first)
5. **No search analytics**: No insights into what clinicians are searching for

### Why Full-Text Search Matters

**Clinical Value**:
- **Fast information retrieval**: Find specific information in seconds (vs manual chart review)
- **Comprehensive search**: Search across millions of documents
- **Structured exploration**: Filter by document metadata (type, date, author, department)
- **Advanced queries**: Combine concepts, keywords, and filters
- **Research enablement**: Cohort identification, case finding, audit queries

**Example Use Case**:
A clinician suspects a patient with chest pain might have coronary artery disease. They search:
```
"chest pain" AND ("CAD" OR "coronary artery disease")
  AND document_type:"cardiology_note"
  AND date:[2023-01-01 TO 2023-12-31]
```

Results show 3 cardiology notes from 2023 mentioning both chest pain and CAD, ranked by relevance.

### Deployment Context

- **Platform**: Extends Clinical Care Tools Base Application (MVP)
- **Users**: Clinicians (search documents), Researchers (cohort identification), Admin (search analytics)
- **Data Source**: Documents from base application (clinical notes, reports, letters)
- **Integration**: Elasticsearch for full-text search, CogStack-ModelServe for concept extraction

---

## Goals

### Primary Goals

1. **Document-Level Full-Text Search** (P0)
   - Search within document content (not just patient-level)
   - Keyword search with highlighting
   - Phrase search ("chest pain" vs chest AND pain)
   - Wildcard search (diabet* matches diabetes, diabetic, diabetic)
   - Proximity search (diabetes NEAR/5 insulin = within 5 words)

2. **Structured Field Exploration** (P0)
   - Filter by document type (clinical notes, discharge summaries, lab reports, radiology)
   - Filter by author (Dr. Smith, Dr. Jones)
   - Filter by department (cardiology, endocrinology, emergency)
   - Filter by date range (absolute or relative)
   - Faceted search (show counts for each filter value)

3. **Advanced Query Builder** (P0)
   - Boolean operators (AND, OR, NOT)
   - Nested queries (grouping with parentheses)
   - Field-specific search (author:"Dr. Smith", document_type:"discharge_summary")
   - Visual query builder (drag-and-drop interface)
   - Query validation (syntax checking, suggestions)

4. **Relevance Ranking** (P0)
   - BM25 scoring (industry-standard relevance algorithm)
   - Boosting (increase relevance for specific fields: title > content)
   - Recency boost (recent documents ranked higher)
   - Custom scoring (admin-configurable weights)
   - Explain score (show why document ranked highly)

5. **Comprehensive Audit Logging** (P0)
   - Log all searches (query, user, timestamp, results count)
   - Log clicked results (which documents clinicians opened)
   - Search analytics dashboard (top queries, zero-result queries, slow queries)
   - Query audit logs for compliance

### Secondary Goals

6. **Search Result Highlighting** (P1)
   - Highlight matching keywords in search results
   - Context snippets (show surrounding text)
   - Multiple highlights per document (show all matches)
   - Highlight color-coding (keyword vs concept)

7. **Saved Searches** (P1)
   - Save complex queries for reuse
   - Name and describe saved searches
   - Share saved searches with team
   - Execute saved search with one click

8. **Search Suggestions** (P1)
   - Autocomplete search queries (suggest concepts, keywords)
   - Did you mean? (spelling corrections)
   - Related searches (queries similar to current search)
   - Search history (show recent searches)

9. **Export Search Results** (P1)
   - Export to CSV (document list with metadata)
   - Export to JSON (machine-readable)
   - Export to FHIR R4 (DocumentReference bundle)
   - Audit log entry for exports

---

## Non-Goals

1. **External Data Sources** - Only search documents in base application (no HL7/FHIR import yet)
2. **Natural Language Queries** - Structured queries only (no "show me patients with diabetes and chest pain")
3. **Machine Learning Relevance** - BM25 only (no ML-based ranking in this sprint)
4. **Real-Time Indexing** - Batch indexing only (documents indexed every 5 minutes)
5. **Multi-Language Search** - English only
6. **Fuzzy Search** - Exact match and wildcards only (no Levenshtein distance)
7. **Search Analytics ML** - Basic analytics only (no anomaly detection, trending)

---

## User Stories

### Clinician User Stories

#### US-C1: Full-Text Keyword Search
**As a** clinician
**I want to** search for specific keywords within documents
**So that** I can quickly find relevant clinical information

**Acceptance Criteria**:
- [ ] Search box accepts free-text keywords
- [ ] Results show documents containing keywords
- [ ] Matching keywords highlighted in results
- [ ] Context snippets show surrounding text
- [ ] Results returned in <1 second for simple queries

---

#### US-C2: Advanced Query with Boolean Operators
**As a** clinician
**I want to** combine multiple search terms with AND/OR/NOT
**So that** I can create precise queries

**Acceptance Criteria**:
- [ ] Query: `diabetes AND hypertension` (documents with both)
- [ ] Query: `chest pain OR angina` (documents with either)
- [ ] Query: `diabetes NOT type 1` (diabetes but exclude type 1)
- [ ] Query: `(diabetes OR hypertension) AND medication` (nested queries)
- [ ] Query validation (syntax errors highlighted)

---

#### US-C3: Filter by Document Metadata
**As a** clinician
**I want to** filter search results by document type, author, date, department
**So that** I can narrow results to relevant documents

**Acceptance Criteria**:
- [ ] Faceted filters sidebar showing:
  - Document types with counts (e.g., "Clinical Notes (45)")
  - Authors with counts
  - Departments with counts
  - Date range slider
- [ ] Select filter → results update in <500ms
- [ ] Multi-select filters (combine multiple types, authors)
- [ ] Clear all filters button

---

#### US-C4: View Relevance Score Explanation
**As a** clinician
**I want to** see why a document was ranked highly
**So that** I can understand search relevance

**Acceptance Criteria**:
- [ ] Each result shows relevance score (0-100)
- [ ] Click "Explain Score" → show:
  - BM25 score breakdown
  - Field boosts applied
  - Recency boost applied
  - Matching terms and their weights
- [ ] Visual indicator (5-star rating based on score)

---

#### US-C5: Save and Reuse Complex Queries
**As a** clinician
**I want to** save complex search queries
**So that** I can reuse them without retyping

**Acceptance Criteria**:
- [ ] "Save Search" button after executing query
- [ ] Name and describe saved search
- [ ] Saved searches list in sidebar
- [ ] Click saved search → execute immediately
- [ ] Edit/delete saved searches

---

### Researcher User Stories

#### US-R1: Cohort Identification with Advanced Filters
**As a** researcher
**I want to** search for documents matching complex criteria
**So that** I can identify patient cohorts

**Acceptance Criteria**:
- [ ] Query: `(diabetes OR "HbA1c > 7%") AND medication:"metformin" AND date:[2023-01-01 TO 2023-12-31]`
- [ ] Results show matching documents
- [ ] Extract patient IDs from results (deduplicated)
- [ ] Export patient cohort to CSV
- [ ] Audit log entry created

---

#### US-R2: Search Analytics for Research Insights
**As a** researcher
**I want to** analyze search patterns
**So that** I can understand common clinical queries

**Acceptance Criteria**:
- [ ] Search analytics dashboard showing:
  - Top 20 queries (by frequency)
  - Zero-result queries (searches with no matches)
  - Slow queries (>2 seconds)
  - Search trends over time (line chart)
- [ ] Filter analytics by user, date range
- [ ] Export analytics to CSV

---

### Admin User Stories

#### US-A1: Configure Search Settings
**As an** admin
**I want to** configure search relevance and indexing
**So that** search results are optimized

**Acceptance Criteria**:
- [ ] Admin panel for search configuration:
  - Relevance weights (title boost, recency boost)
  - Indexing schedule (batch every 5 minutes, 10 minutes, 30 minutes)
  - Max results per page (20, 50, 100)
  - Highlight settings (color, max snippets)
- [ ] Settings saved to database
- [ ] Settings apply immediately (no restart required)

---

#### US-A2: View Search Audit Logs
**As an** admin
**I want to** view audit logs for search access
**So that** I can ensure compliance

**Acceptance Criteria**:
- [ ] Admin panel shows search audit logs:
  - User who executed search
  - Query executed
  - Results count
  - Clicked results (documents opened)
  - Timestamp
- [ ] Filter logs by user, query, date range
- [ ] Export logs to CSV for compliance reporting

---

## Requirements

### Functional Requirements

#### FR1: Full-Text Search
- **FR1.1**: Keyword search across document content
- **FR1.2**: Phrase search (exact match: "chest pain")
- **FR1.3**: Wildcard search (diabet* matches diabetes, diabetic)
- **FR1.4**: Proximity search (diabetes NEAR/5 insulin)
- **FR1.5**: Boolean operators (AND, OR, NOT)
- **FR1.6**: Nested queries (parentheses grouping)
- **FR1.7**: Field-specific search (author:"Dr. Smith")

#### FR2: Structured Field Search
- **FR2.1**: Filter by document type (clinical notes, discharge summaries, lab reports, radiology, pathology)
- **FR2.2**: Filter by author (autocomplete from user database)
- **FR2.3**: Filter by department (cardiology, endocrinology, emergency, etc.)
- **FR2.4**: Filter by date range (absolute: 2023-01-01 to 2023-12-31, relative: last 3 months)
- **FR2.5**: Faceted search (show counts for each filter value)

#### FR3: Advanced Query Builder
- **FR3.1**: Visual query builder (drag-and-drop interface)
- **FR3.2**: Query validation (syntax checking, error highlighting)
- **FR3.3**: Query suggestions (autocomplete, spelling corrections)
- **FR3.4**: Query templates (pre-built queries for common use cases)
- **FR3.5**: Query history (show recent searches)

#### FR4: Relevance Ranking
- **FR4.1**: BM25 scoring algorithm
- **FR4.2**: Field boosting (title:10, content:1)
- **FR4.3**: Recency boost (recent documents ranked higher)
- **FR4.4**: Custom scoring weights (admin-configurable)
- **FR4.5**: Explain score (show breakdown of relevance calculation)

#### FR5: Search Result Presentation
- **FR5.1**: Highlight matching keywords in results
- **FR5.2**: Context snippets (surrounding text)
- **FR5.3**: Multiple highlights per document (show all matches)
- **FR5.4**: Pagination (20, 50, 100 results per page)
- **FR5.5**: Sort options (relevance, date, title)

#### FR6: Saved Searches
- **FR6.1**: Save complex queries with name and description
- **FR6.2**: Execute saved search with one click
- **FR6.3**: Share saved searches with project team
- **FR6.4**: Edit/delete saved searches
- **FR6.5**: Saved search permissions (private, shared)

#### FR7: Export Capabilities
- **FR7.1**: Export search results to CSV (document list with metadata)
- **FR7.2**: Export to JSON (machine-readable)
- **FR7.3**: Export to FHIR R4 (DocumentReference bundle)
- **FR7.4**: Export patient cohort (deduplicated patient IDs from results)
- **FR7.5**: Audit log entry for all exports

#### FR8: Search Analytics
- **FR8.1**: Track top queries (by frequency)
- **FR8.2**: Track zero-result queries
- **FR8.3**: Track slow queries (>2 seconds)
- **FR8.4**: Search trends over time (line chart)
- **FR8.5**: Analytics dashboard with filters (user, date range)

#### FR9: Audit Logging
- **FR9.1**: Log all searches (query, user, timestamp, results count, IP address)
- **FR9.2**: Log clicked results (documents opened from search)
- **FR9.3**: Log saved searches created/executed
- **FR9.4**: Log exports
- **FR9.5**: Query audit logs (filter by user, query, date range)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Simple queries (<3 terms) return results in <1 second
- **NFR1.2**: Complex queries (>3 terms, filters) return results in <2 seconds
- **NFR1.3**: Faceted search updates in <500ms
- **NFR1.4**: Autocomplete suggestions in <200ms
- **NFR1.5**: Concurrent searches: 20 users searching simultaneously

#### NFR2: Scalability
- **NFR2.1**: Search across 10 million documents
- **NFR2.2**: Index 10,000 documents per minute (batch indexing)
- **NFR2.3**: Support 100,000 searches per day
- **NFR2.4**: Elasticsearch index size: <2x source document size

#### NFR3: Usability
- **NFR3.1**: Intuitive search interface (Google-like simplicity)
- **NFR3.2**: Query builder visual and accessible (drag-and-drop)
- **NFR3.3**: Keyboard shortcuts (Ctrl+K for search, Esc to close)
- **NFR3.4**: WCAG 2.1 AA compliance (screen readers, keyboard navigation)

#### NFR4: Security
- **NFR4.1**: All searches require authentication
- **NFR4.2**: Row-level security (users see documents for assigned patients only)
- **NFR4.3**: Audit logging for all PHI access
- **NFR4.4**: Query injection prevention (sanitize inputs)
- **NFR4.5**: Rate limiting (max 60 searches per minute per user)

#### NFR5: Reliability
- **NFR5.1**: 99.5% uptime for search service
- **NFR5.2**: Graceful degradation if Elasticsearch unavailable (show cached results)
- **NFR5.3**: Error messages user-friendly
- **NFR5.4**: Automatic retry for transient failures

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  SearchView.vue                                       │  │
│  │  - Search input with autocomplete                     │  │
│  │  - Advanced query builder (visual)                    │  │
│  │  - Faceted filters sidebar                            │  │
│  │  - Search results with highlighting                   │  │
│  │  - Saved searches panel                               │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    REST API (FastAPI)
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Search Service                                       │  │
│  │  - POST /api/v1/search                                │  │
│  │  - GET /api/v1/search/suggestions                     │  │
│  │  - GET /api/v1/search/saved                           │  │
│  │  - POST /api/v1/search/export                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Elasticsearch Query Builder                          │  │
│  │  - Parse user query                                   │  │
│  │  - Build Elasticsearch DSL query                      │  │
│  │  - Apply filters, boosts, aggregations                │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    Elasticsearch
┌─────────────────────────────────────────────────────────────┐
│              Elasticsearch 8+ (Full-Text Index)             │
│  - documents index (full-text search)                       │
│  - BM25 relevance scoring                                   │
│  - Aggregations (faceted search)                            │
│  - Highlighting                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Frontend Components

**SearchView.vue** (Main component)
- Search input with autocomplete
- Advanced query builder (toggle simple/advanced mode)
- Faceted filters sidebar
- Search results list
- Pagination controls
- Saved searches panel

**QueryBuilder.vue**
- Visual query builder (drag-and-drop)
- Boolean operators (AND, OR, NOT)
- Field selectors (author, document_type, date)
- Query validation and syntax highlighting

**SearchResult.vue**
- Document title and metadata
- Context snippets with keyword highlighting
- Relevance score display
- "Explain Score" button
- "View Document" link

**FacetedFilters.vue**
- Document type facets
- Author facets
- Department facets
- Date range slider
- Clear filters button

#### Backend Services

**SearchService** (`app/services/search_service.py`)
```python
class SearchService:
    """Full-text search service using Elasticsearch"""

    async def search_documents(
        self,
        query: str,
        filters: SearchFilters,
        user: User,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResults:
        """Execute full-text search with filters"""
        # 1. Parse query (keyword, phrase, boolean, field-specific)
        # 2. Build Elasticsearch DSL query
        # 3. Apply filters (document_type, author, date_range)
        # 4. Apply relevance boosting (title, recency)
        # 5. Execute search with highlighting
        # 6. Audit log search
        # 7. Return SearchResults

    async def get_search_suggestions(
        self,
        partial_query: str
    ) -> List[str]:
        """Get autocomplete suggestions"""
        # 1. Query Elasticsearch suggester
        # 2. Return top 10 suggestions

    async def explain_score(
        self,
        document_id: str,
        query: str
    ) -> ScoreExplanation:
        """Explain relevance score for document"""
        # 1. Execute Elasticsearch explain API
        # 2. Parse score breakdown
        # 3. Return human-readable explanation

    async def save_search(
        self,
        name: str,
        query: str,
        filters: SearchFilters,
        user: User
    ) -> SavedSearch:
        """Save search for reuse"""
        # 1. Validate query
        # 2. Store in PostgreSQL
        # 3. Return SavedSearch model

    async def export_search_results(
        self,
        query: str,
        filters: SearchFilters,
        format: str,  # "csv", "json", "fhir"
        user: User
    ) -> bytes:
        """Export search results"""
        # 1. Execute search (all results, no pagination)
        # 2. Format as CSV/JSON/FHIR
        # 3. Audit log export
        # 4. Return file bytes
```

**ElasticsearchQueryBuilder** (`app/search/query_builder.py`)
```python
class ElasticsearchQueryBuilder:
    """Build Elasticsearch DSL queries from user input"""

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse user query into Elasticsearch DSL"""
        # 1. Detect query type (keyword, phrase, boolean, field-specific)
        # 2. Build bool query with must/should/must_not clauses
        # 3. Apply field boosting (title^10, content^1)
        # 4. Return Elasticsearch query dict

    def apply_filters(
        self,
        query: Dict[str, Any],
        filters: SearchFilters
    ) -> Dict[str, Any]:
        """Apply filters to query"""
        # 1. Add filter clauses (document_type, author, date_range)
        # 2. Return modified query

    def apply_relevance_boosting(
        self,
        query: Dict[str, Any],
        boost_config: BoostConfig
    ) -> Dict[str, Any]:
        """Apply relevance boosting"""
        # 1. Add function_score for recency boost
        # 2. Add field boosts (title, author)
        # 3. Return modified query

    def build_aggregations(
        self,
        fields: List[str]
    ) -> Dict[str, Any]:
        """Build aggregations for faceted search"""
        # 1. Create terms aggregations (document_type, author, department)
        # 2. Create date histogram aggregation (date)
        # 3. Return aggregations dict
```

#### Database Models

**SearchResults** (Pydantic response model)
```python
class SearchResults(BaseModel):
    query: str
    total_results: int
    page: int
    page_size: int
    documents: List[SearchResultDocument]
    facets: Facets
    execution_time_ms: int

class SearchResultDocument(BaseModel):
    document_id: str
    title: str
    document_type: str
    author: Optional[str]
    date: datetime
    department: Optional[str]
    relevance_score: float  # 0.0 to 100.0
    highlights: List[Highlight]

class Highlight(BaseModel):
    field: str  # "title", "content"
    snippets: List[str]  # Context snippets with <em>keyword</em>

class Facets(BaseModel):
    document_types: List[FacetValue]
    authors: List[FacetValue]
    departments: List[FacetValue]
    date_range: DateRangeFacet

class FacetValue(BaseModel):
    value: str
    count: int
```

### API Endpoints

#### POST `/api/v1/search`
Execute full-text search.

**Request**:
```json
{
  "query": "(diabetes OR hypertension) AND medication",
  "filters": {
    "document_types": ["clinical_note", "discharge_summary"],
    "authors": ["Dr. Smith"],
    "departments": ["cardiology"],
    "date_range": {
      "start": "2023-01-01T00:00:00Z",
      "end": "2023-12-31T23:59:59Z"
    }
  },
  "page": 1,
  "page_size": 20,
  "sort": "relevance"  // "relevance", "date", "title"
}
```

**Response**:
```json
{
  "query": "(diabetes OR hypertension) AND medication",
  "total_results": 142,
  "page": 1,
  "page_size": 20,
  "documents": [
    {
      "document_id": "doc-123",
      "title": "Diabetes Clinic Note",
      "document_type": "clinical_note",
      "author": "Dr. Smith",
      "date": "2023-06-15T10:30:00Z",
      "department": "endocrinology",
      "relevance_score": 95.3,
      "highlights": [
        {
          "field": "content",
          "snippets": [
            "Patient with <em>diabetes</em> and <em>hypertension</em>. Started on <em>medication</em>: metformin 500mg BD."
          ]
        }
      ]
    }
  ],
  "facets": {
    "document_types": [
      {"value": "clinical_note", "count": 85},
      {"value": "discharge_summary", "count": 57}
    ],
    "authors": [
      {"value": "Dr. Smith", "count": 42},
      {"value": "Dr. Jones", "count": 38}
    ],
    "departments": [
      {"value": "endocrinology", "count": 67},
      {"value": "cardiology", "count": 45}
    ],
    "date_range": {
      "min": "2023-01-01T00:00:00Z",
      "max": "2023-12-31T23:59:59Z"
    }
  },
  "execution_time_ms": 450
}
```

#### GET `/api/v1/search/suggestions`
Get autocomplete suggestions.

**Request**: `?q=diabet`

**Response**:
```json
{
  "query": "diabet",
  "suggestions": [
    "diabetes",
    "diabetes mellitus",
    "diabetes type 2",
    "diabetic",
    "diabetic retinopathy"
  ]
}
```

#### GET `/api/v1/search/{document_id}/explain`
Explain relevance score.

**Response**:
```json
{
  "document_id": "doc-123",
  "relevance_score": 95.3,
  "explanation": {
    "bm25_score": 82.1,
    "field_boosts": {
      "title": 10.0,
      "content": 1.0
    },
    "recency_boost": 3.2,
    "matching_terms": [
      {"term": "diabetes", "field": "content", "weight": 45.2},
      {"term": "medication", "field": "content", "weight": 36.9}
    ]
  }
}
```

---

## Database Schema

### New Tables

#### `saved_searches` (Save Complex Queries)
```sql
CREATE TABLE saved_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    query TEXT NOT NULL,
    filters JSONB,
    is_shared BOOLEAN DEFAULT FALSE,  -- Share with project team
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)
);

CREATE INDEX idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_project ON saved_searches(project_id);
```

#### `search_analytics` (Track Search Patterns)
```sql
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    query TEXT NOT NULL,
    filters JSONB,
    results_count INTEGER NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    clicked_documents UUID[],  -- Array of document IDs clicked
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    session_id VARCHAR(100)
);

CREATE INDEX idx_search_analytics_user ON search_analytics(user_id);
CREATE INDEX idx_search_analytics_created ON search_analytics(created_at);
CREATE INDEX idx_search_analytics_query ON search_analytics USING gin(to_tsvector('english', query));
```

### Elasticsearch Index Mapping

```json
PUT /documents
{
  "settings": {
    "index": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "analysis": {
        "analyzer": {
          "clinical_text": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "stop", "snowball"]
          }
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "document_id": {"type": "keyword"},
      "patient_id": {"type": "keyword"},
      "title": {
        "type": "text",
        "analyzer": "clinical_text",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "content": {
        "type": "text",
        "analyzer": "clinical_text"
      },
      "document_type": {"type": "keyword"},
      "author": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "department": {"type": "keyword"},
      "date": {"type": "date"},
      "created_at": {"type": "date"},
      "updated_at": {"type": "date"}
    }
  }
}
```

---

## Search Query Language

### Supported Query Syntax

#### Basic Keyword Search
```
diabetes
```
Matches documents containing "diabetes"

#### Phrase Search
```
"chest pain"
```
Matches documents containing exact phrase "chest pain"

#### Boolean Operators
```
diabetes AND hypertension
diabetes OR hypertension
diabetes NOT "type 1"
```

#### Nested Queries
```
(diabetes OR hypertension) AND medication
```

#### Wildcard Search
```
diabet*  # Matches diabetes, diabetic, diabetics
```

#### Proximity Search
```
diabetes NEAR/5 insulin  # "diabetes" within 5 words of "insulin"
```

#### Field-Specific Search
```
author:"Dr. Smith"
document_type:"discharge_summary"
department:cardiology
date:[2023-01-01 TO 2023-12-31]
```

#### Combined Query
```
(diabetes OR hypertension)
  AND medication
  AND author:"Dr. Smith"
  AND date:[2023-01-01 TO 2023-12-31]
```

---

## Relevance Ranking Algorithm

### BM25 Scoring

**Formula**: BM25 (Best Matching 25) is the industry-standard relevance algorithm.

```
score(D,Q) = ∑ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl))

Where:
- D = document
- Q = query
- qi = query term i
- f(qi,D) = frequency of qi in D
- |D| = length of document D
- avgdl = average document length
- k1 = 1.2 (term frequency saturation)
- b = 0.75 (length normalization)
- IDF(qi) = inverse document frequency of qi
```

### Field Boosting

```python
field_boosts = {
    "title": 10.0,      # Title matches highly relevant
    "content": 1.0,     # Content matches baseline
    "author": 2.0,      # Author matches moderately relevant
    "department": 1.5   # Department matches slightly relevant
}
```

### Recency Boost

```python
def recency_boost(document_date: datetime) -> float:
    """Boost recent documents"""
    days_old = (datetime.now() - document_date).days

    if days_old <= 30:  # Last month
        return 1.5
    elif days_old <= 365:  # Last year
        return 1.2
    else:  # Older than 1 year
        return 1.0
```

### Custom Scoring

```python
final_score = (
    bm25_score
    * field_boost
    * recency_boost
    * custom_weight  # Admin-configurable (default: 1.0)
)
```

---

## Integration Points

### Elasticsearch Integration
- **Purpose**: Full-text search and relevance ranking
- **Index**: `documents` (clinical documents full-text indexed)
- **Queries**: Bool queries, aggregations, highlighting
- **Indexing**: Batch indexing every 5 minutes (configurable)

### PostgreSQL Integration
- **Purpose**: Saved searches, search analytics, audit logs
- **Tables**: `saved_searches`, `search_analytics`, `audit_logs`

### CogStack-ModelServe Integration
- **Purpose**: Concept extraction for search suggestions
- **Endpoint**: `POST http://cogstack-modelserve:8000/api/process`
- **Use Case**: Suggest SNOMED-CT concepts when user types keywords

---

## Performance Requirements

### Load Time Targets
- **Simple queries** (<3 terms): <1 second
- **Complex queries** (>3 terms, filters): <2 seconds
- **Autocomplete suggestions**: <200ms
- **Faceted search updates**: <500ms
- **Export search results** (CSV): <5 seconds for <1000 documents

### Scalability Targets
- **Total documents**: 10 million
- **Concurrent searches**: 20 users
- **Searches per day**: 100,000
- **Indexing throughput**: 10,000 documents per minute

### Optimization Strategies
- **Elasticsearch caching**: Cache aggregations (5-minute TTL)
- **Query result caching**: Cache frequent queries (Redis, 10-minute TTL)
- **Index optimization**: Shard balancing, replica placement
- **Pagination**: Limit max results to 10,000 (Elasticsearch default)

---

## Constraints

### Technical Constraints
1. **Single workstation deployment** - No distributed Elasticsearch cluster
2. **Elasticsearch 8+** - Must use latest version for security features
3. **English only** - No multi-language support in this sprint
4. **BM25 only** - No ML-based ranking yet
5. **Batch indexing** - Real-time indexing deferred to future sprint

### Regulatory Constraints
1. **HIPAA compliance** - All searches audited
2. **GDPR compliance** - Users can search only assigned patients (row-level security)
3. **21 CFR Part 11** - Audit trails for compliance reporting

### Resource Constraints
1. **RAM**: Elasticsearch must run in <4GB RAM
2. **Disk**: Elasticsearch index size <2x source document size
3. **CPU**: Indexing must not block search queries

---

## Acceptance Criteria

### Functional Acceptance

- [ ] **Full-Text Search**:
  - [ ] Keyword search returns matching documents
  - [ ] Phrase search matches exact phrases
  - [ ] Boolean operators (AND, OR, NOT) work correctly
  - [ ] Nested queries with parentheses supported
  - [ ] Wildcard and proximity search functional

- [ ] **Structured Field Search**:
  - [ ] Filter by document type, author, department, date range
  - [ ] Faceted search shows counts for each filter value
  - [ ] Multi-select filters combine correctly
  - [ ] Clear all filters button resets search

- [ ] **Advanced Query Builder**:
  - [ ] Visual query builder (drag-and-drop)
  - [ ] Query validation highlights syntax errors
  - [ ] Query suggestions (autocomplete)
  - [ ] Toggle simple/advanced mode

- [ ] **Relevance Ranking**:
  - [ ] Results sorted by relevance (highest first)
  - [ ] Field boosting applied (title > content)
  - [ ] Recency boost applied (recent documents ranked higher)
  - [ ] Explain score shows breakdown

- [ ] **Search Result Highlighting**:
  - [ ] Matching keywords highlighted
  - [ ] Context snippets show surrounding text
  - [ ] Multiple highlights per document

- [ ] **Saved Searches**:
  - [ ] Save complex queries with name/description
  - [ ] Execute saved search with one click
  - [ ] Edit/delete saved searches
  - [ ] Share saved searches with team (project-level)

- [ ] **Export**:
  - [ ] Export to CSV (document list with metadata)
  - [ ] Export to JSON (machine-readable)
  - [ ] Export to FHIR R4 (DocumentReference bundle)
  - [ ] Audit log entry created for exports

- [ ] **Search Analytics**:
  - [ ] Track top queries, zero-result queries, slow queries
  - [ ] Analytics dashboard with filters
  - [ ] Export analytics to CSV

- [ ] **Audit Logging**:
  - [ ] All searches logged (query, user, timestamp, results count)
  - [ ] Clicked results logged
  - [ ] Admin can query audit logs

### Performance Acceptance

- [ ] Simple queries in <1 second
- [ ] Complex queries in <2 seconds
- [ ] Autocomplete in <200ms
- [ ] Faceted search updates in <500ms
- [ ] Supports 20 concurrent users

### Security Acceptance

- [ ] Authentication required for all searches
- [ ] Row-level security (users see assigned patients only)
- [ ] Audit logging for all searches
- [ ] Query injection prevention
- [ ] Rate limiting (60 searches per minute per user)

### Usability Acceptance

- [ ] Intuitive search interface (Google-like)
- [ ] Keyboard shortcuts functional
- [ ] WCAG 2.1 AA compliance
- [ ] Responsive design (1920x1080 and 1366x768)

### Testing Acceptance

- [ ] Unit test coverage ≥80%
- [ ] Integration test coverage ≥70%
- [ ] E2E test for search workflow
- [ ] Performance tests verify targets

---

## Alignment with Constitution

### Principle 1: Patient Safety First
- **Search accuracy**: Meta-annotation filtering ensures relevant results
- **Audit trails**: Track all searches for clinical governance
- **Error handling**: Graceful degradation if Elasticsearch unavailable

### Principle 2: Privacy by Design
- **Row-level security**: Users search only assigned patients
- **Audit logging**: All searches logged (WHO, WHAT, WHEN, WHERE)
- **Rate limiting**: Prevent data scraping

### Principle 3: Evidence-Based Development
- **BM25 scoring**: Industry-standard relevance algorithm
- **Elasticsearch**: Production-tested search engine
- **FHIR R4 export**: Open standard for interoperability

### Principle 5: Open Standards and Interoperability
- **FHIR R4 export**: DocumentReference bundle
- **SNOMED-CT**: Standard medical terminology
- **JSON export**: Machine-readable format

### Principle 6: Transparency and Explainability
- **Relevance score**: Show why document ranked highly
- **Explain score**: Breakdown of relevance calculation
- **Context snippets**: Show why document matched query

### Principle 9: Clinical Workflow Integration
- **Fast search**: <1 second for simple queries
- **Saved searches**: Reuse complex queries easily
- **Keyboard shortcuts**: Efficient workflow

---

## Testing Strategy

### Unit Tests (60%)

**Frontend**:
```typescript
describe('SearchView', () => {
  it('should execute search and display results', async () => {
    const wrapper = mount(SearchView)
    await wrapper.find('input[name="search"]').setValue('diabetes')
    await wrapper.find('button[type="submit"]').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.search-result')).toHaveLength(20)
  })

  it('should apply faceted filters', async () => {
    const wrapper = mount(SearchView)
    await wrapper.find('input[value="clinical_note"]').trigger('change')
    expect(wrapper.vm.filters.document_types).toContain('clinical_note')
  })
})
```

**Backend**:
```python
@pytest.mark.asyncio
async def test_search_documents(search_service, mock_elasticsearch):
    # Arrange
    query = "diabetes AND hypertension"
    filters = SearchFilters(document_types=["clinical_note"])

    # Act
    results = await search_service.search_documents(
        query, filters, user=mock_user
    )

    # Assert
    assert results.total_results > 0
    assert all(doc.document_type == "clinical_note" for doc in results.documents)

@pytest.mark.asyncio
async def test_explain_score(search_service):
    # Act
    explanation = await search_service.explain_score("doc-123", "diabetes")

    # Assert
    assert explanation.bm25_score > 0
    assert "diabetes" in [term.term for term in explanation.matching_terms]
```

### Integration Tests (30%)

```python
@pytest.mark.asyncio
async def test_search_endpoint(async_client, auth_headers):
    # Act
    response = await async_client.post(
        "/api/v1/search",
        json={
            "query": "diabetes",
            "filters": {"document_types": ["clinical_note"]},
            "page": 1,
            "page_size": 20
        },
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    assert len(data["documents"]) <= 20
```

### E2E Tests (10%)

```typescript
test('full search workflow', async ({ page }) => {
  await page.goto('http://localhost:8080/search')

  // Execute search
  await page.fill('input[name="search"]', 'diabetes')
  await page.click('button[type="submit"]')
  await page.waitForSelector('.search-result')

  // Apply filter
  await page.click('input[value="clinical_note"]')
  await page.waitForSelector('.search-result')

  // Save search
  await page.click('button:has-text("Save Search")')
  await page.fill('input[name="name"]', 'Diabetes Notes')
  await page.click('button:has-text("Save")')

  // Execute saved search
  await page.click('text=Diabetes Notes')
  await page.waitForSelector('.search-result')
})
```

---

## Deployment Considerations

### Docker Compose Updates

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

volumes:
  es_data:
    driver: local
```

### Environment Variables

```bash
# Search Configuration
SEARCH_ENABLED=true
ELASTICSEARCH_URL=http://elasticsearch:9200
SEARCH_INDEX_NAME=documents
SEARCH_BATCH_INTERVAL_MINUTES=5
SEARCH_MAX_RESULTS=10000
SEARCH_CACHE_TTL_SECONDS=600  # 10 minutes
```

### Database Migrations

```bash
alembic revision --autogenerate -m "Add saved_searches and search_analytics tables"
alembic upgrade head
```

### Elasticsearch Index Creation

```bash
curl -X PUT "http://localhost:9200/documents" -H 'Content-Type: application/json' -d @elasticsearch-mapping.json
```

---

## Open Questions

1. **Search Ranking Weights**:
   - Q: What are optimal field boost values (title, content, author)?
   - A: [To be tuned based on user feedback] - Propose title:10, content:1, author:2

2. **Indexing Frequency**:
   - Q: How often to index new documents?
   - A: [To be decided] - Propose every 5 minutes (balance freshness vs load)

3. **Zero-Result Handling**:
   - Q: What to show when search returns no results?
   - A: [To be decided] - Propose: "Did you mean?" suggestions, related searches

4. **Export Limits**:
   - Q: Max documents to export (prevent large file downloads)?
   - A: [To be decided] - Propose 10,000 documents (CSV), unlimited (JSON/FHIR with pagination)

5. **Saved Search Sharing**:
   - Q: Should saved searches be private or shareable?
   - A: [To be decided] - Propose: both (private by default, option to share with project team)

---

**Status**: Ready for review and approval
**Next Steps**: Create Technical Plan for Sprint 3 (Full-Text Search Enhancement) after specification approval
**Dependencies**: Base Application (MVP), Patient Search (Sprint 1)
**Estimated Effort**: 120 hours over 4 weeks
