# Search Module API Documentation

## Overview

The search module exposes RESTful API endpoints for full-text document search with Elasticsearch backend. All endpoints require authentication via JWT token and include HIPAA audit logging.

## Base URL

```
POST /api/v1/search
```

## Authentication

All search endpoints require:

- **Header**: `Authorization: Bearer <JWT_TOKEN>`
- **Token source**: Obtained from `/api/v1/auth/login`
- **Expiration**: 24 hours (configurable)
- **RBAC**: Any authenticated user can search (searches audit logged)

### Example

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes",
    "page": 1,
    "page_size": 20
  }'
```

## Endpoints

### 1. POST /api/v1/search - Full-Text Search

Performs full-text search across documents with optional filtering, sorting, and pagination.

#### Request

**Method**: `POST`

**Content-Type**: `application/json`

**Body**:

```json
{
  "query": "diabetes",
  "filters": {
    "document_types": ["note", "lab"],
    "authors": ["user-123", "user-456"],
    "departments": ["Cardiology", "Neurology"],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
  },
  "page": 1,
  "page_size": 20,
  "sort": "relevance"
}
```

**Field Definitions**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | `string` | Yes | — | Search keywords (1-1000 characters). Can include: keywords, phrases, boolean operators. |
| `filters` | `object` | No | `null` | Optional search filters (see table below) |
| `filters.document_types` | `string[]` | No | `null` | Filter by document type: `['note', 'lab', 'imaging', 'discharge', 'letter']` |
| `filters.authors` | `string[]` | No | `null` | Filter by user IDs (authors) |
| `filters.departments` | `string[]` | No | `null` | Filter by clinical departments |
| `filters.date_from` | `date` | No | `null` | Filter from date (ISO 8601 format, inclusive) |
| `filters.date_to` | `date` | No | `null` | Filter to date (ISO 8601 format, inclusive) |
| `page` | `integer` | No | `1` | Page number for pagination (1-indexed) |
| `page_size` | `integer` | No | `20` | Results per page (min: 1, max: 100) |
| `sort` | `string` | No | `"relevance"` | Sort order: `"relevance"`, `"date"`, `"title"` |

#### Response

**Status**: `200 OK`

**Content-Type**: `application/json`

**Body**:

```json
{
  "results": [
    {
      "id": "doc-550e8400-e29b-41d4-a716-446655440000",
      "title": "Type 2 Diabetes Mellitus - Follow-up",
      "content": "Patient presents with well-controlled diabetes...",
      "document_type": "note",
      "author": "Dr. Jane Smith",
      "date": "2024-11-15T10:30:00Z",
      "score": 95.5,
      "highlights": {
        "title": ["Type 2 <mark>Diabetes</mark> Mellitus - Follow-up"],
        "content": ["Patient presents with well-controlled <mark>diabetes</mark>..."]
      }
    },
    {
      "id": "doc-550e8400-e29b-41d4-a716-446655440001",
      "title": "Lab Results - Glucose Levels",
      "content": "Fasting glucose 120 mg/dL",
      "document_type": "lab",
      "author": "Lab System",
      "date": "2024-11-10T08:00:00Z",
      "score": 87.2,
      "highlights": {
        "title": ["Lab Results - Glucose Levels"],
        "content": []
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8
  },
  "performance": {
    "search_time_ms": 245,
    "highlighting_time_ms": 12
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `results` | `object[]` | Array of search results (see SearchResult schema below) |
| `results[].id` | `string` | Unique document identifier (UUID) |
| `results[].title` | `string` | Document title |
| `results[].content` | `string` | Document excerpt (first 500 characters) |
| `results[].document_type` | `string` | Document type: `note`, `lab`, `imaging`, `discharge`, `letter` |
| `results[].author` | `string` | Document creator/author name |
| `results[].date` | `string` | Document date (ISO 8601 format) |
| `results[].score` | `number` | Relevance score (0-100, higher = more relevant) |
| `results[].highlights` | `object` | Elasticsearch highlights with `<mark>` tags |
| `results[].highlights.title` | `string[]` | Title excerpt with highlighted matches |
| `results[].highlights.content` | `string[]` | Content excerpt with highlighted matches |
| `pagination.page` | `number` | Current page number |
| `pagination.page_size` | `number` | Results per page |
| `pagination.total` | `number` | Total matching documents |
| `pagination.total_pages` | `number` | Total pages available |
| `performance.search_time_ms` | `number` | Elasticsearch query time (ms) |
| `performance.highlighting_time_ms` | `number` | Highlight generation time (ms) |

#### Examples

**Example 1: Simple Keyword Search**

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "heart failure"
  }'
```

**Response** (simplified):
```json
{
  "results": [
    {
      "id": "doc-123",
      "title": "Congestive <mark>Heart</mark> <mark>Failure</mark> Assessment",
      "score": 98.5
    }
  ],
  "pagination": {
    "total": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

**Example 2: Filtered Search**

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes",
    "filters": {
      "document_types": ["note", "lab"],
      "date_from": "2024-01-01",
      "date_to": "2024-12-31"
    },
    "page": 1,
    "page_size": 10
  }'
```

**Example 3: Paginated Search**

```bash
# Get page 2 of results
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hypertension",
    "page": 2,
    "page_size": 50
  }'
```

**Example 4: Sorted Search**

```bash
# Sort by date (newest first)
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cancer",
    "sort": "date",
    "page": 1,
    "page_size": 20
  }'
```

#### Error Responses

**400 Bad Request - Invalid Query**

```json
{
  "detail": "Search query must be between 1 and 1000 characters"
}
```

**400 Bad Request - Invalid Page Size**

```json
{
  "detail": "Page size must be between 1 and 100"
}
```

**401 Unauthorized - Missing Token**

```json
{
  "detail": "Not authenticated"
}
```

**401 Unauthorized - Invalid Token**

```json
{
  "detail": "Invalid authentication credentials"
}
```

**429 Too Many Requests - Rate Limit Exceeded**

```json
{
  "detail": "Rate limit exceeded: 100 requests per minute per user"
}
```

**500 Internal Server Error**

```json
{
  "detail": "An error occurred while processing your search. Please try again."
}
```

#### HTTP Status Codes

| Code | Meaning | When Occurs |
|------|---------|-------------|
| `200` | OK | Search successful, results returned |
| `400` | Bad Request | Invalid query, filters, or pagination parameters |
| `401` | Unauthorized | Missing or invalid authentication token |
| `429` | Too Many Requests | Rate limit exceeded (100 req/min per user) |
| `500` | Internal Server Error | Elasticsearch or database error |

#### Performance Characteristics

| Metric | Target | Notes |
|--------|--------|-------|
| Response time (p50) | <200ms | Typical query on indexed data |
| Response time (p95) | <500ms | Complex query with many filters |
| Response time (p99) | <1s | Large result sets or timeout edge cases |
| Highlights generation | <50ms | Per result, parallelized |
| Maximum results/page | 100 | Prevents excessive data transfer |
| Rate limit | 100 req/min | Per authenticated user |

#### Security & Compliance

- **Authentication**: JWT token required (RBAC enforced at user level)
- **Authorization**: Any authenticated user can search
- **Audit Logging**: All searches logged to `audit_logs` table with:
  - User ID
  - Timestamp
  - Query text
  - IP address
  - Results count
- **PHI Handling**: All results may contain PHI (Protected Health Information), subject to HIPAA rules
- **Encryption**: All data encrypted in transit (TLS 1.3) and at rest (AES-256)
- **XSS Prevention**: HTML in highlights is escaped (safe for rendering)

#### Rate Limiting

Requests are rate limited to **100 per minute per authenticated user**:

- **Header**: `X-RateLimit-Limit: 100`
- **Header**: `X-RateLimit-Remaining: 95` (after first request)
- **Header**: `X-RateLimit-Reset: 1637329200` (Unix timestamp)

If limit exceeded, returns `429 Too Many Requests`.

#### Caching

API responses are **not cached** (real-time search results) but frontend caches last 10 searches in browser storage.

#### Query Syntax

The `query` parameter supports:

- **Keywords**: `diabetes`, `heart failure`
- **Phrases**: `"type 2 diabetes"`, `"acute myocardial infarction"`
- **Boolean operators** (future): `diabetes AND hypertension`, `NOT type1`
- **Special characters**: Automatically escaped

### 2. POST /api/v1/search/highlights - Get Highlights for Documents

Returns Elasticsearch highlights for specific documents and search query (used internally by search results component).

#### Request

**Method**: `POST`

**Path**: `/api/v1/search/highlights`

**Body**:

```json
{
  "document_ids": ["doc-123", "doc-456"],
  "query": "diabetes"
}
```

#### Response

**Status**: `200 OK`

```json
{
  "highlights": {
    "doc-123": {
      "title": ["Patient with <mark>Diabetes</mark> Mellitus"],
      "content": ["Type 2 <mark>diabetes</mark> diagnosed in 2020"]
    },
    "doc-456": {
      "title": [],
      "content": ["<mark>Diabetes</mark> management and complications"]
    }
  }
}
```

## Client Library Examples

### JavaScript/TypeScript

```typescript
// frontend/src/api/search.ts
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/v1'

export interface SearchRequest {
  query: string
  filters?: DocumentSearchFilters
  page?: number
  page_size?: number
  sort?: 'relevance' | 'date' | 'title'
}

export interface SearchResponse {
  results: SearchResult[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
  performance: {
    search_time_ms: number
    highlighting_time_ms: number
  }
}

export async function search(request: SearchRequest): Promise<SearchResponse> {
  const response = await axios.post(`${API_BASE}/search`, request, {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  })
  return response.data
}

export async function getHighlights(
  documentIds: string[],
  query: string
): Promise<any> {
  const response = await axios.post(`${API_BASE}/search/highlights`, {
    document_ids: documentIds,
    query
  }, {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  })
  return response.data.highlights
}
```

### Python

```python
# backend/clients/search_client.py
import requests
from typing import Dict, List, Optional

class SearchClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'

    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = 'relevance',
        filters: Optional[Dict] = None
    ) -> Dict:
        """Perform full-text search"""
        payload = {
            'query': query,
            'page': page,
            'page_size': page_size,
            'sort': sort,
        }
        if filters:
            payload['filters'] = filters

        response = self.session.post(
            f'{self.base_url}/api/v1/search',
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_highlights(self, document_ids: List[str], query: str) -> Dict:
        """Get highlights for documents"""
        response = self.session.post(
            f'{self.base_url}/api/v1/search/highlights',
            json={
                'document_ids': document_ids,
                'query': query
            }
        )
        response.raise_for_status()
        return response.json()
```

### cURL

```bash
#!/bin/bash

# Set your token
TOKEN="your_jwt_token_here"
API="http://localhost:8000/api/v1"

# Basic search
curl -X POST "$API/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes",
    "page": 1,
    "page_size": 20
  }'

# Filtered search
curl -X POST "$API/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "heart failure",
    "filters": {
      "document_types": ["note", "lab"],
      "date_from": "2024-01-01",
      "date_to": "2024-12-31"
    },
    "page": 1,
    "page_size": 50,
    "sort": "date"
  }'

# Get highlights
curl -X POST "$API/search/highlights" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc-123", "doc-456"],
    "query": "diabetes"
  }'
```

## OpenAPI/Swagger Specification

```yaml
openapi: 3.0.0
info:
  title: CogStack Search API
  version: 1.0.0
  description: Full-text search for clinical documents

servers:
  - url: http://localhost:8000/api/v1

paths:
  /search:
    post:
      summary: Full-text search
      tags:
        - Search
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SearchRequest'
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SearchResponse'
        '400':
          description: Invalid request
        '401':
          description: Unauthorized
        '429':
          description: Rate limit exceeded
        '500':
          description: Internal server error

components:
  schemas:
    SearchRequest:
      type: object
      required:
        - query
      properties:
        query:
          type: string
          minLength: 1
          maxLength: 1000
          description: Search keywords
        filters:
          $ref: '#/components/schemas/DocumentSearchFilters'
        page:
          type: integer
          minimum: 1
          default: 1
        page_size:
          type: integer
          minimum: 1
          maximum: 100
          default: 20
        sort:
          type: string
          enum: [relevance, date, title]
          default: relevance

    SearchResponse:
      type: object
      properties:
        results:
          type: array
          items:
            $ref: '#/components/schemas/SearchResult'
        pagination:
          $ref: '#/components/schemas/Pagination'
        performance:
          $ref: '#/components/schemas/Performance'

    SearchResult:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        content:
          type: string
        document_type:
          type: string
          enum: [note, lab, imaging, discharge, letter]
        author:
          type: string
        date:
          type: string
          format: date-time
        score:
          type: number
          minimum: 0
          maximum: 100
        highlights:
          type: object
          properties:
            title:
              type: array
              items:
                type: string
            content:
              type: array
              items:
                type: string

    Pagination:
      type: object
      properties:
        page:
          type: integer
        page_size:
          type: integer
        total:
          type: integer
        total_pages:
          type: integer

    Performance:
      type: object
      properties:
        search_time_ms:
          type: number
        highlighting_time_ms:
          type: number

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: Missing or invalid JWT token

**Solution**:
1. Obtain token from `/api/v1/auth/login`
2. Include in Authorization header: `Authorization: Bearer <token>`
3. Token expires after 24 hours, login again

### Issue: 400 Bad Request

**Cause**: Invalid query or parameters

**Solution**:
1. Verify query is 1-1000 characters
2. Verify page_size is 1-100
3. Check date format (ISO 8601: YYYY-MM-DD)
4. Validate filters object structure

### Issue: 429 Too Many Requests

**Cause**: Rate limit exceeded (100 req/min per user)

**Solution**:
1. Wait before sending more requests
2. Implement exponential backoff
3. Cache results to reduce API calls
4. Use pagination to limit requests

### Issue: 500 Internal Server Error

**Cause**: Elasticsearch or database error

**Solution**:
1. Check Elasticsearch is running: `curl http://localhost:9200`
2. Check database is running: psql
3. Check server logs: `docker logs cogstack-api`
4. Retry request (may be temporary)

---

**Last Updated**: 2025-11-22
**API Version**: v1
**Specification Version**: 1.0.0
