# Technical Plan: Full-Text Search Enhancement (Sprint 3)

**Version**: 1.0.0
**Date**: 2025-11-18
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Sprint Duration**: 3 weeks (~90 hours)
**Dependencies**: Sprint 1 (Patient Search), Sprint 2 (Timeline View)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [API Design](#api-design)
5. [Database Schema](#database-schema)
6. [Component Design](#component-design)
7. [Testing Strategy](#testing-strategy)
8. [Performance Requirements](#performance-requirements)
9. [Risks & Mitigations](#risks--mitigations)
10. [Implementation Phases](#implementation-phases)

---

## Overview

### Goals

Sprint 3 delivers **advanced full-text search** with:
- **Multi-field search**: Search across multiple document fields simultaneously
- **Faceted search**: Filter by document type, date range, author, department
- **Search result highlighting**: Highlight matching text in search results
- **Relevance ranking**: BM25 scoring with custom boosting
- **Search suggestions**: Autocomplete and "did you mean?" corrections
- **Search analytics**: Track popular searches, zero-result queries

### Success Criteria

- [ ] Multi-field search with faceting operational
- [ ] Search result highlighting with context snippets
- [ ] Autocomplete suggestions with <200ms response time
- [ ] Search analytics dashboard showing top queries
- [ ] 80% test coverage (unit + integration)
- [ ] Performance: <500ms for typical queries on 100K documents

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  SearchView.vue                                       │  │
│  │  - Search input with autocomplete                     │  │
│  │  - Facet filters (type, date, author, dept)          │  │
│  │  - Result list with highlighting                     │  │
│  │  - Pagination                                         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    REST API (FastAPI)
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Search Service                                       │  │
│  │  - Multi-field query builder                         │  │
│  │  - Facet aggregations                                │  │
│  │  - Result highlighting                               │  │
│  │  - Search analytics tracking                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Elasticsearch Client                                 │  │
│  │  - Query DSL builder                                 │  │
│  │  - Aggregations                                       │  │
│  │  - Highlighting                                       │  │
│  │  - Suggestions API                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│              Elasticsearch (Full-Text Search Engine)        │
│  - documents index (title, content, metadata)               │
│  - BM25 relevance scoring                                   │
│  - Facet aggregations (terms, date histogram)              │
│  - Highlighting with fragments                              │
│  - Suggest API (completion, phrase)                         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Search Flow**:
1. User types query in search input → autocomplete suggestions shown
2. User submits search → Frontend sends GET `/api/v1/search` with query params
3. Backend builds Elasticsearch multi_match query across title, content, author fields
4. Elasticsearch returns results with BM25 relevance scores
5. Backend adds highlighting (matching text snippets)
6. Backend tracks search query in `search_analytics` table
7. Frontend displays results with highlighted snippets + facet filters

**Faceting Flow**:
1. User selects facet filter (e.g., "Discharge Summary") → Frontend sends updated query
2. Backend adds filter to Elasticsearch query (`term` filter on `document_type`)
3. Backend requests aggregations (facet counts for each document type)
4. Frontend updates facet counts (e.g., "Progress Notes (342)")

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Search Engine | Elasticsearch | 8.11 | Full-text search, aggregations, highlighting |
| ES Client | elasticsearch-py | 8.11 | Python client for Elasticsearch |
| Web Framework | FastAPI | 0.104 | REST API endpoints |
| Validation | Pydantic | 2.5 | Request/response schemas |
| Async | asyncio | stdlib | Async Elasticsearch queries |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Vue 3 | 3.3 | Reactive UI |
| UI Library | Vuetify | 3.4 | Material Design components |
| HTTP Client | Axios | 1.6 | API requests |
| State | Pinia | 2.1 | Search state management |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Cache | Redis | 7.2 | Autocomplete suggestions cache |
| Database | PostgreSQL | 15 | Search analytics storage |

---

## API Design

### Endpoints

#### GET `/api/v1/search`

Search documents with full-text query.

**Query Parameters**:
```
q: str              # Search query (required)
fields: List[str]   # Fields to search (default: ["title", "content", "author"])
document_type: str  # Filter by document type (optional)
date_from: str      # Filter by date range (ISO format, optional)
date_to: str        # Filter by date range (ISO format, optional)
department: str     # Filter by department (optional)
author: str         # Filter by author (optional)
page: int           # Page number (default: 1)
page_size: int      # Results per page (default: 20)
```

**Request Example**:
```http
GET /api/v1/search?q=diabetes+mellitus&document_type=discharge_summary&date_from=2023-01-01&page=1&page_size=20
```

**Response Schema**:
```json
{
  "query": "diabetes mellitus",
  "total_results": 342,
  "page": 1,
  "page_size": 20,
  "total_pages": 18,
  "results": [
    {
      "document_id": "doc-123",
      "title": "Discharge Summary - Patient John Doe",
      "content_snippet": "Patient has <em>Type 2 Diabetes Mellitus</em> managed with metformin...",
      "document_type": "discharge_summary",
      "author": "Dr. Jane Smith",
      "department": "Endocrinology",
      "date": "2023-11-15T00:00:00Z",
      "relevance_score": 15.432,
      "highlights": [
        "Patient has <em>Type 2 Diabetes Mellitus</em> managed with metformin",
        "HbA1c 7.2% indicates fair glycemic control in <em>diabetes</em> patient"
      ]
    }
  ],
  "facets": {
    "document_type": {
      "discharge_summary": 152,
      "progress_note": 98,
      "consultation": 62,
      "lab_report": 30
    },
    "department": {
      "Endocrinology": 123,
      "Internal Medicine": 87,
      "Primary Care": 65
    },
    "date_histogram": {
      "2023-11": 142,
      "2023-10": 98,
      "2023-09": 102
    }
  },
  "execution_time_ms": 234
}
```

**Error Responses**:
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Elasticsearch unavailable

---

#### GET `/api/v1/search/suggest`

Get autocomplete suggestions as user types.

**Query Parameters**:
```
q: str              # Partial query (minimum 2 characters)
size: int           # Max suggestions (default: 5)
```

**Request Example**:
```http
GET /api/v1/search/suggest?q=diab&size=5
```

**Response Schema**:
```json
{
  "query": "diab",
  "suggestions": [
    "diabetes mellitus",
    "diabetes type 2",
    "diabetic ketoacidosis",
    "diabetic retinopathy",
    "diabetic neuropathy"
  ]
}
```

**Response Time**: <200ms (cached in Redis)

---

#### GET `/api/v1/search/analytics`

Get search analytics (admin only).

**Query Parameters**:
```
date_from: str      # Start date (ISO format)
date_to: str        # End date (ISO format)
limit: int          # Max results (default: 50)
```

**Response Schema**:
```json
{
  "date_range": {
    "from": "2023-11-01",
    "to": "2023-11-30"
  },
  "total_searches": 12543,
  "unique_users": 234,
  "top_queries": [
    {"query": "diabetes", "count": 542},
    {"query": "hypertension", "count": 421},
    {"query": "chest pain", "count": 387}
  ],
  "zero_result_queries": [
    {"query": "rare disease xyz", "count": 12},
    {"query": "obsolete drug name", "count": 8}
  ],
  "avg_results_per_query": 23.4,
  "avg_response_time_ms": 287
}
```

---

## Database Schema

### Existing Tables (No Changes)

- `documents`: Document storage (from Sprint 1)
- `audit_logs`: Audit trail (from MVP)

### New Tables

#### `search_analytics` (Search Query Tracking)

```sql
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    query TEXT NOT NULL,
    filters JSONB,  -- Applied facet filters (document_type, date range, etc.)
    total_results INTEGER NOT NULL,
    page INTEGER DEFAULT 1,
    execution_time_ms INTEGER,
    clicked_result_id UUID REFERENCES documents(id),  -- NULL if no click
    clicked_result_rank INTEGER,  -- Position in results (1, 2, 3...)
    session_id UUID,  -- Group queries in same session
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_search_analytics_user ON search_analytics(user_id);
CREATE INDEX idx_search_analytics_created_at ON search_analytics(created_at);
CREATE INDEX idx_search_analytics_query ON search_analytics USING gin(to_tsvector('english', query));
```

**Purpose**:
- Track search usage patterns
- Identify popular queries (optimize indexing)
- Identify zero-result queries (add synonyms, fix spelling)
- Measure click-through rate (result relevance)

---

## Component Design

### Backend Services

#### `SearchService` (`app/services/search_service.py`)

```python
from typing import List, Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel
import redis.asyncio as redis

class SearchQuery(BaseModel):
    """Search query parameters"""
    q: str
    fields: List[str] = ["title", "content", "author"]
    document_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    department: Optional[str] = None
    author: Optional[str] = None
    page: int = 1
    page_size: int = 20

class SearchResult(BaseModel):
    """Search result item"""
    document_id: str
    title: str
    content_snippet: str
    document_type: str
    author: str
    department: str
    date: str
    relevance_score: float
    highlights: List[str]

class SearchResponse(BaseModel):
    """Search response"""
    query: str
    total_results: int
    page: int
    page_size: int
    total_pages: int
    results: List[SearchResult]
    facets: Dict[str, Dict[str, int]]
    execution_time_ms: int

class SearchService:
    """Full-text search service using Elasticsearch"""

    def __init__(self, es_client: AsyncElasticsearch, redis_client: redis.Redis):
        self.es = es_client
        self.redis = redis_client

    async def search(
        self,
        query: SearchQuery,
        user_id: str
    ) -> SearchResponse:
        """
        Execute full-text search with faceting and highlighting.

        Args:
            query: Search parameters
            user_id: User executing search (for analytics)

        Returns:
            Search results with facets and highlights
        """
        import time
        start_time = time.time()

        # Build Elasticsearch query
        es_query = self._build_query(query)

        # Execute search
        response = await self.es.search(
            index="documents",
            body=es_query,
            from_=(query.page - 1) * query.page_size,
            size=query.page_size
        )

        # Parse results
        results = self._parse_results(response)
        facets = self._parse_facets(response)

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Track search analytics (async, don't block response)
        await self._track_search(
            user_id=user_id,
            query=query,
            total_results=response['hits']['total']['value'],
            execution_time_ms=execution_time_ms
        )

        return SearchResponse(
            query=query.q,
            total_results=response['hits']['total']['value'],
            page=query.page,
            page_size=query.page_size,
            total_pages=(response['hits']['total']['value'] + query.page_size - 1) // query.page_size,
            results=results,
            facets=facets,
            execution_time_ms=execution_time_ms
        )

    def _build_query(self, query: SearchQuery) -> Dict[str, Any]:
        """Build Elasticsearch query DSL"""
        # Multi-field search with boosting
        multi_match = {
            "multi_match": {
                "query": query.q,
                "fields": [
                    "title^3",      # Boost title matches 3x
                    "content^1",    # Content at normal weight
                    "author^2"      # Boost author matches 2x
                ],
                "type": "best_fields",
                "fuzziness": "AUTO"  # Handle typos
            }
        }

        # Build filters
        filters = []
        if query.document_type:
            filters.append({"term": {"document_type": query.document_type}})
        if query.date_from or query.date_to:
            date_filter = {"range": {"date": {}}}
            if query.date_from:
                date_filter["range"]["date"]["gte"] = query.date_from
            if query.date_to:
                date_filter["range"]["date"]["lte"] = query.date_to
            filters.append(date_filter)
        if query.department:
            filters.append({"term": {"department": query.department}})
        if query.author:
            filters.append({"match": {"author": query.author}})

        # Combine query and filters
        bool_query = {
            "must": [multi_match]
        }
        if filters:
            bool_query["filter"] = filters

        # Build full query with aggregations and highlighting
        es_query = {
            "query": {"bool": bool_query},
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 0},
                    "content": {
                        "fragment_size": 150,
                        "number_of_fragments": 3,
                        "pre_tags": ["<em>"],
                        "post_tags": ["</em>"]
                    }
                }
            },
            "aggs": {
                "document_type": {
                    "terms": {"field": "document_type.keyword", "size": 20}
                },
                "department": {
                    "terms": {"field": "department.keyword", "size": 20}
                },
                "date_histogram": {
                    "date_histogram": {
                        "field": "date",
                        "calendar_interval": "month"
                    }
                }
            }
        }

        return es_query

    def _parse_results(self, response: Dict) -> List[SearchResult]:
        """Parse Elasticsearch response into SearchResult objects"""
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            highlights = []

            # Extract highlights
            if 'highlight' in hit:
                if 'title' in hit['highlight']:
                    highlights.extend(hit['highlight']['title'])
                if 'content' in hit['highlight']:
                    highlights.extend(hit['highlight']['content'])

            # Content snippet (use first highlight or truncate content)
            if highlights:
                content_snippet = highlights[0]
            else:
                content_snippet = source.get('content', '')[:200] + '...'

            results.append(SearchResult(
                document_id=hit['_id'],
                title=source.get('title', 'Untitled'),
                content_snippet=content_snippet,
                document_type=source.get('document_type', 'unknown'),
                author=source.get('author', 'Unknown'),
                department=source.get('department', 'Unknown'),
                date=source.get('date'),
                relevance_score=hit['_score'],
                highlights=highlights
            ))

        return results

    def _parse_facets(self, response: Dict) -> Dict[str, Dict[str, int]]:
        """Parse Elasticsearch aggregations into facet counts"""
        facets = {}

        # Document type facet
        if 'document_type' in response['aggregations']:
            facets['document_type'] = {
                bucket['key']: bucket['doc_count']
                for bucket in response['aggregations']['document_type']['buckets']
            }

        # Department facet
        if 'department' in response['aggregations']:
            facets['department'] = {
                bucket['key']: bucket['doc_count']
                for bucket in response['aggregations']['department']['buckets']
            }

        # Date histogram facet
        if 'date_histogram' in response['aggregations']:
            facets['date_histogram'] = {
                bucket['key_as_string']: bucket['doc_count']
                for bucket in response['aggregations']['date_histogram']['buckets']
            }

        return facets

    async def _track_search(
        self,
        user_id: str,
        query: SearchQuery,
        total_results: int,
        execution_time_ms: int
    ):
        """Track search analytics in database"""
        # Insert into search_analytics table
        # (Implementation uses SQLAlchemy async session)
        pass

    async def get_suggestions(self, partial_query: str, size: int = 5) -> List[str]:
        """
        Get autocomplete suggestions.

        Uses Redis cache for fast response (<200ms).
        Falls back to Elasticsearch completion suggester if not cached.
        """
        # Check Redis cache
        cache_key = f"suggest:{partial_query.lower()}"
        cached = await self.redis.get(cache_key)
        if cached:
            return cached.split(',')[:size]

        # Query Elasticsearch suggest API
        response = await self.es.search(
            index="documents",
            body={
                "suggest": {
                    "text": partial_query,
                    "simple_phrase": {
                        "phrase": {
                            "field": "content",
                            "size": size,
                            "gram_size": 3,
                            "direct_generator": [{
                                "field": "content",
                                "suggest_mode": "always"
                            }]
                        }
                    }
                }
            }
        )

        # Parse suggestions
        suggestions = [
            option['text']
            for option in response['suggest']['simple_phrase'][0]['options']
        ]

        # Cache for 1 hour
        await self.redis.setex(cache_key, 3600, ','.join(suggestions))

        return suggestions[:size]

    async def get_analytics(
        self,
        date_from: str,
        date_to: str,
        limit: int = 50
    ) -> Dict:
        """Get search analytics (top queries, zero-result queries, etc.)"""
        # Query search_analytics table
        # (Implementation uses SQLAlchemy aggregations)
        pass
```

---

### Frontend Components

#### `SearchView.vue` (`webapp/src/views/SearchView.vue`)

```vue
<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <h1>Document Search</h1>
      </v-col>
    </v-row>

    <!-- Search Input -->
    <v-row>
      <v-col cols="12" md="8">
        <v-autocomplete
          v-model="searchQuery"
          :items="suggestions"
          :loading="loadingSuggestions"
          :search-input.sync="searchInput"
          label="Search documents"
          placeholder="Enter search terms..."
          prepend-inner-icon="mdi-magnify"
          hide-no-data
          hide-details
          clearable
          @keyup.enter="executeSearch"
        >
          <template v-slot:append>
            <v-btn
              color="primary"
              @click="executeSearch"
            >
              Search
            </v-btn>
          </template>
        </v-autocomplete>
      </v-col>
    </v-row>

    <v-row v-if="searchResults">
      <!-- Facet Filters (Sidebar) -->
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title>Filters</v-card-title>
          <v-card-text>
            <!-- Document Type Facet -->
            <v-list>
              <v-list-subheader>Document Type</v-list-subheader>
              <v-list-item
                v-for="(count, docType) in facets.document_type"
                :key="docType"
                @click="filterDocumentType(docType)"
                :class="{ 'v-list-item--active': selectedDocType === docType }"
              >
                <v-list-item-title>
                  {{ formatDocType(docType) }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ count }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <!-- Department Facet -->
            <v-list>
              <v-list-subheader>Department</v-list-subheader>
              <v-list-item
                v-for="(count, dept) in facets.department"
                :key="dept"
                @click="filterDepartment(dept)"
                :class="{ 'v-list-item--active': selectedDepartment === dept }"
              >
                <v-list-item-title>{{ dept }}</v-list-item-title>
                <v-list-item-subtitle>{{ count }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <!-- Date Range Filter -->
            <v-list>
              <v-list-subheader>Date Range</v-list-subheader>
              <v-list-item>
                <v-text-field
                  v-model="dateFrom"
                  label="From"
                  type="date"
                  dense
                  hide-details
                  @change="executeSearch"
                />
              </v-list-item>
              <v-list-item>
                <v-text-field
                  v-model="dateTo"
                  label="To"
                  type="date"
                  dense
                  hide-details
                  @change="executeSearch"
                />
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Search Results -->
      <v-col cols="12" md="9">
        <v-card>
          <v-card-title>
            {{ totalResults }} results for "{{ searchQuery }}"
            <v-spacer />
            <v-chip small>{{ executionTime }}ms</v-chip>
          </v-card-title>

          <v-card-text>
            <v-list>
              <v-list-item
                v-for="result in results"
                :key="result.document_id"
                @click="openDocument(result.document_id)"
                three-line
              >
                <v-list-item-content>
                  <v-list-item-title>
                    {{ result.title }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <span v-html="result.content_snippet"></span>
                  </v-list-item-subtitle>
                  <v-list-item-subtitle class="mt-2">
                    <v-chip x-small>{{ result.document_type }}</v-chip>
                    <v-chip x-small class="ml-2">{{ result.department }}</v-chip>
                    <v-chip x-small class="ml-2">{{ formatDate(result.date) }}</v-chip>
                    <span class="ml-2 text-caption">Relevance: {{ result.relevance_score.toFixed(2) }}</span>
                  </v-list-item-subtitle>

                  <!-- Highlights -->
                  <div v-if="result.highlights.length > 0" class="mt-2">
                    <div
                      v-for="(highlight, idx) in result.highlights.slice(0, 2)"
                      :key="idx"
                      class="text-caption grey--text text--darken-1 mt-1"
                    >
                      ... <span v-html="highlight"></span> ...
                    </div>
                  </div>
                </v-list-item-content>
              </v-list-item>
            </v-list>

            <!-- Pagination -->
            <v-pagination
              v-model="currentPage"
              :length="totalPages"
              @input="executeSearch"
              class="mt-4"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSearchStore } from '@/stores/search'
import { useRouter } from 'vue-router'

const searchStore = useSearchStore()
const router = useRouter()

const searchQuery = ref('')
const searchInput = ref('')
const suggestions = ref<string[]>([])
const loadingSuggestions = ref(false)

const searchResults = ref(null)
const results = ref([])
const facets = ref({})
const totalResults = ref(0)
const totalPages = ref(0)
const currentPage = ref(1)
const executionTime = ref(0)

const selectedDocType = ref(null)
const selectedDepartment = ref(null)
const dateFrom = ref(null)
const dateTo = ref(null)

// Watch search input for autocomplete
watch(searchInput, async (newValue) => {
  if (newValue && newValue.length >= 2) {
    loadingSuggestions.value = true
    suggestions.value = await searchStore.getSuggestions(newValue)
    loadingSuggestions.value = false
  }
})

async function executeSearch() {
  const response = await searchStore.search({
    q: searchQuery.value,
    document_type: selectedDocType.value,
    department: selectedDepartment.value,
    date_from: dateFrom.value,
    date_to: dateTo.value,
    page: currentPage.value
  })

  searchResults.value = response
  results.value = response.results
  facets.value = response.facets
  totalResults.value = response.total_results
  totalPages.value = response.total_pages
  executionTime.value = response.execution_time_ms
}

function filterDocumentType(docType: string) {
  selectedDocType.value = selectedDocType.value === docType ? null : docType
  currentPage.value = 1
  executeSearch()
}

function filterDepartment(dept: string) {
  selectedDepartment.value = selectedDepartment.value === dept ? null : dept
  currentPage.value = 1
  executeSearch()
}

function openDocument(documentId: string) {
  // Track click for analytics
  searchStore.trackClick(documentId)

  // Navigate to document view
  router.push({ name: 'document', params: { id: documentId } })
}

function formatDocType(docType: string): string {
  return docType.split('_').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}
</script>
```

---

## Testing Strategy

### Unit Tests (60% of effort)

#### Backend: `SearchService` Tests

```python
import pytest
from app.services.search_service import SearchService, SearchQuery

@pytest.fixture
async def search_service(es_client, redis_client):
    return SearchService(es_client, redis_client)

@pytest.mark.asyncio
async def test_search_simple_query(search_service):
    """Test basic search query"""
    query = SearchQuery(q="diabetes", page=1, page_size=20)
    response = await search_service.search(query, user_id="user-123")

    assert response.total_results > 0
    assert len(response.results) <= 20
    assert "diabetes" in response.query.lower()

@pytest.mark.asyncio
async def test_search_with_facets(search_service):
    """Test search with document type facet"""
    query = SearchQuery(
        q="hypertension",
        document_type="discharge_summary"
    )
    response = await search_service.search(query, user_id="user-123")

    assert all(r.document_type == "discharge_summary" for r in response.results)
    assert "document_type" in response.facets

@pytest.mark.asyncio
async def test_search_highlighting(search_service):
    """Test search result highlighting"""
    query = SearchQuery(q="chest pain")
    response = await search_service.search(query, user_id="user-123")

    if response.results:
        first_result = response.results[0]
        assert len(first_result.highlights) > 0
        assert "<em>" in first_result.highlights[0]

@pytest.mark.asyncio
async def test_autocomplete_suggestions(search_service):
    """Test autocomplete suggestions"""
    suggestions = await search_service.get_suggestions("diab", size=5)

    assert len(suggestions) <= 5
    assert all("diab" in s.lower() for s in suggestions)

@pytest.mark.asyncio
async def test_search_analytics_tracking(search_service, db_session):
    """Test search query is tracked in analytics"""
    query = SearchQuery(q="test query")
    await search_service.search(query, user_id="user-123")

    # Verify analytics record created
    from app.models import SearchAnalytic
    analytics = await db_session.execute(
        "SELECT * FROM search_analytics WHERE query = 'test query' ORDER BY created_at DESC LIMIT 1"
    )
    record = analytics.fetchone()

    assert record is not None
    assert record.user_id == "user-123"
```

#### Frontend: Component Tests

```typescript
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import SearchView from '@/views/SearchView.vue'

describe('SearchView', () => {
  it('renders search input', () => {
    const wrapper = mount(SearchView, {
      global: {
        plugins: [createTestingPinia()]
      }
    })

    expect(wrapper.find('input[type="search"]').exists()).toBe(true)
  })

  it('displays autocomplete suggestions', async () => {
    const wrapper = mount(SearchView, {
      global: {
        plugins: [createTestingPinia({
          initialState: {
            search: {
              suggestions: ['diabetes', 'diabetic ketoacidosis']
            }
          }
        })]
      }
    })

    await wrapper.find('input').setValue('diab')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('diabetes')
  })

  it('displays search results with highlighting', async () => {
    const wrapper = mount(SearchView, {
      global: {
        plugins: [createTestingPinia({
          initialState: {
            search: {
              results: [{
                document_id: 'doc-1',
                title: 'Test Document',
                content_snippet: 'Patient has <em>diabetes</em>',
                highlights: ['<em>diabetes</em> mellitus']
              }]
            }
          }
        })]
      }
    })

    expect(wrapper.html()).toContain('<em>diabetes</em>')
  })
})
```

### Integration Tests (30% of effort)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_endpoint(async_client, auth_headers, seed_documents):
    """Test GET /api/v1/search endpoint"""
    response = await async_client.get(
        "/api/v1/search",
        params={"q": "diabetes", "page": 1, "page_size": 20},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    assert len(data["results"]) <= 20
    assert "facets" in data
    assert data["execution_time_ms"] < 1000

@pytest.mark.integration
@pytest.mark.asyncio
async def test_suggest_endpoint(async_client, auth_headers):
    """Test GET /api/v1/search/suggest endpoint"""
    response = await async_client.get(
        "/api/v1/search/suggest",
        params={"q": "diab", "size": 5},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) <= 5
```

### E2E Tests (10% of effort)

```typescript
import { test, expect } from '@playwright/test'

test('full-text search workflow', async ({ page }) => {
  await page.goto('http://localhost:8080/search')

  // Type search query
  await page.fill('input[type="search"]', 'diabetes')

  // Wait for autocomplete suggestions
  await page.waitForSelector('.v-autocomplete__content')
  await expect(page.locator('.v-autocomplete__content')).toContainText('diabetes')

  // Submit search
  await page.click('button:has-text("Search")')

  // Verify results displayed
  await page.waitForSelector('.v-list-item')
  await expect(page.locator('.v-card-title')).toContainText('results for "diabetes"')

  // Verify highlighting
  const firstResult = page.locator('.v-list-item').first()
  await expect(firstResult).toContainText('diabetes')

  // Apply facet filter
  await page.click('text=Discharge Summary')
  await page.waitForSelector('.v-list-item')

  // Verify filtered results
  const docTypeChips = page.locator('.v-chip:has-text("discharge_summary")')
  await expect(docTypeChips).toHaveCount(await docTypeChips.count())
})
```

---

## Performance Requirements

### Response Time Targets

| Operation | Target | Max Acceptable |
|-----------|--------|----------------|
| Simple search (1-3 words) | <300ms | <500ms |
| Complex search (filters, facets) | <500ms | <1000ms |
| Autocomplete suggestions | <100ms | <200ms |
| Search analytics query | <1000ms | <3000ms |

### Throughput Targets

- **Concurrent searches**: Support 50 concurrent users
- **Documents indexed**: 100,000 documents (initial target)
- **Indexing throughput**: 1,000 documents/minute

### Elasticsearch Optimization

1. **Index Settings**:
```json
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "refresh_interval": "5s",
    "analysis": {
      "analyzer": {
        "medical_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "medical_analyzer",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "content": {
        "type": "text",
        "analyzer": "medical_analyzer"
      },
      "document_type": {
        "type": "keyword"
      },
      "department": {
        "type": "keyword"
      },
      "date": {
        "type": "date"
      }
    }
  }
}
```

2. **Query Optimization**:
   - Use `best_fields` for multi_match (better relevance than `cross_fields`)
   - Limit highlight fragments to 3 (reduce processing time)
   - Use `from` + `size` pagination (not `search_after` for initial MVP)

3. **Caching**:
   - Cache autocomplete suggestions in Redis (1 hour TTL)
   - Cache facet aggregations (5 minute TTL)

---

## Risks & Mitigations

### Risk 1: Elasticsearch Scalability

**Risk**: Elasticsearch performance degrades with >100K documents or complex queries

**Likelihood**: Medium | **Impact**: High

**Mitigation**:
- Monitor Elasticsearch cluster metrics (CPU, memory, disk I/O)
- Add Elasticsearch nodes if needed (vertical or horizontal scaling)
- Optimize index mapping (disable unnecessary fields)
- Use index lifecycle management (ILM) to move old documents to cold storage

**Contingency**: If Elasticsearch unavailable, fallback to PostgreSQL full-text search (slower but functional)

---

### Risk 2: Search Relevance Tuning

**Risk**: Search results not relevant (users can't find documents)

**Likelihood**: Medium | **Impact**: Medium

**Mitigation**:
- Collect search analytics (zero-result queries, click-through rates)
- Tune field boosting (title^3, author^2, content^1)
- Add synonyms (e.g., "MI" → "myocardial infarction")
- Implement "did you mean?" spelling corrections

**Contingency**: Provide manual "Advanced Search" with field-specific queries

---

### Risk 3: Autocomplete Response Time

**Risk**: Autocomplete suggestions slow (>200ms), poor user experience

**Likelihood**: Low | **Impact**: Medium

**Mitigation**:
- Cache suggestions in Redis (1 hour TTL)
- Use Elasticsearch completion suggester (optimized for speed)
- Limit suggestion size to 5 results

**Contingency**: Disable autocomplete if response time exceeds 300ms

---

## Implementation Phases

### Phase 3.1: Elasticsearch Integration (1 week, 30 hours)

**Tasks**:
1. Set up Elasticsearch index for documents (index mapping, analyzers) - 10h
2. Implement document indexing service (sync PostgreSQL → Elasticsearch) - 8h
3. Build multi-field query builder with BM25 scoring - 6h
4. Add facet aggregations (document type, department, date histogram) - 4h
5. Unit tests for SearchService - 2h

**Deliverable**: SearchService can execute multi-field queries with facets

**Test Coverage**: 80% (unit tests)

---

### Phase 3.2: Search Result Highlighting (0.5 week, 15 hours)

**Tasks**:
1. Configure Elasticsearch highlighting (fragment size, pre/post tags) - 5h
2. Parse highlights in SearchService - 3h
3. Display highlights in SearchView component (<em> tags, styling) - 5h
4. Unit tests for highlighting - 2h

**Deliverable**: Search results show highlighted matching text

**Test Coverage**: 80% (unit tests)

---

### Phase 3.3: Autocomplete Suggestions (0.5 week, 15 hours)

**Tasks**:
1. Implement Elasticsearch phrase suggester - 5h
2. Add Redis caching for suggestions (1 hour TTL) - 3h
3. Build autocomplete UI in SearchView (v-autocomplete) - 5h
4. Unit tests for suggestions - 2h

**Deliverable**: Autocomplete suggestions appear as user types (<200ms response)

**Test Coverage**: 80% (unit tests)

---

### Phase 3.4: Search Analytics (0.5 week, 15 hours)

**Tasks**:
1. Create search_analytics table and migration - 3h
2. Implement search tracking in SearchService - 4h
3. Build analytics dashboard (top queries, zero-result queries) - 6h
4. Unit tests for analytics - 2h

**Deliverable**: Search analytics dashboard showing query patterns

**Test Coverage**: 80% (unit tests)

---

### Phase 3.5: Testing & Performance Tuning (0.5 week, 15 hours)

**Tasks**:
1. Integration tests (API endpoints) - 5h
2. E2E tests (search workflow) - 5h
3. Performance testing (load test with 50 concurrent users) - 3h
4. Elasticsearch optimization (tune mappings, analyzers) - 2h

**Deliverable**: 80% test coverage, performance targets met

---

## Deployment Checklist

### Infrastructure

- [ ] Elasticsearch 8.11 cluster running (2 nodes minimum for production)
- [ ] Redis cache running (for autocomplete suggestions)
- [ ] PostgreSQL database updated (search_analytics table migration)

### Configuration

- [ ] Environment variables configured:
  ```bash
  ELASTICSEARCH_URL=http://elasticsearch:9200
  ELASTICSEARCH_INDEX=documents
  REDIS_URL=redis://redis:6379
  SEARCH_ANALYTICS_ENABLED=true
  ```

### Data Migration

- [ ] Index existing documents to Elasticsearch:
  ```bash
  python scripts/index_documents.py
  ```

### Monitoring

- [ ] Elasticsearch monitoring enabled (CPU, memory, disk usage)
- [ ] Search analytics dashboard accessible to admins
- [ ] Alert if search response time exceeds 1 second

---

## Success Metrics

- [ ] **Multi-field search**: Operational with title, content, author fields
- [ ] **Faceted search**: Filters by document type, department, date range
- [ ] **Highlighting**: Matching text highlighted in search results
- [ ] **Autocomplete**: Suggestions displayed in <200ms
- [ ] **Search analytics**: Dashboard showing top queries, zero-result queries
- [ ] **Performance**: <500ms response for typical queries on 100K documents
- [ ] **Test coverage**: 80% (unit + integration tests)
- [ ] **User acceptance**: 5 pilot users sign off on search experience

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-18
**Status**: Ready for implementation
**Dependencies**: Sprint 1 (Patient Search), Sprint 2 (Timeline View), Elasticsearch 8.11, Redis 7.2
**Estimated Effort**: 90 hours over 3 weeks
