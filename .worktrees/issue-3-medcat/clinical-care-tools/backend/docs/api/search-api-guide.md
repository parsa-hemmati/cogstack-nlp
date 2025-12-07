# Search API Documentation

## Overview

The Clinical Care Tools search API provides advanced full-text search capabilities with support for multiple query types, faceted filtering, and performance optimization through caching.

## Base URL

```
/api/v1/search
```

## Authentication

All search endpoints require authentication via Bearer token:

```http
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. Search Documents

**Endpoint:** `GET /api/v1/search`

**Description:** Search documents with advanced query support.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| q | string | Yes | - | Search query string |
| query_type | string | No | standard | Query type (see Query Types section) |
| document_type | string | No | - | Filter by document type |
| date_from | string | No | - | Start date (ISO format) |
| date_to | string | No | - | End date (ISO format) |
| department | string | No | - | Filter by department |
| author | string | No | - | Filter by author |
| page | integer | No | 1 | Page number (1-indexed) |
| page_size | integer | No | 20 | Results per page (max 100) |

#### Query Types

- **standard**: Basic multi-field search with automatic fuzziness
- **boolean**: AND/OR/NOT operators for precise searches
- **wildcard**: Pattern matching with * and ?
- **fuzzy**: Typo-tolerant search with ~
- **proximity**: Find terms within specified distance (NEAR/W/ADJ)
- **range**: Numeric and date range queries
- **regex**: Regular expression pattern matching

#### Example Request

```http
GET /api/v1/search?q=diabetes+AND+hypertension&query_type=boolean&page=1&page_size=20
```

#### Example Response

```json
{
  "query": "diabetes AND hypertension",
  "total_results": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "results": [
    {
      "document_id": "doc-123",
      "title": "Patient Summary - Diabetes Management",
      "content_snippet": "Patient presents with type 2 diabetes and hypertension...",
      "document_type": "clinical_note",
      "author": "Dr. Smith",
      "department": "Endocrinology",
      "date": "2023-12-01",
      "relevance_score": 8.5,
      "highlights": [
        "Patient presents with type 2 <em>diabetes</em> and <em>hypertension</em>"
      ]
    }
  ],
  "facets": {
    "document_type": {
      "clinical_note": 89,
      "discharge_summary": 45,
      "lab_report": 22
    },
    "department": {
      "Endocrinology": 67,
      "Cardiology": 89
    }
  },
  "execution_time_ms": 145
}
```

---

### 2. Get Query Help

**Endpoint:** `GET /api/v1/search/query-help`

**Description:** Get syntax help and examples for query types.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query_type | string | No | Specific query type to get help for |

#### Example Request

```http
GET /api/v1/search/query-help?query_type=boolean
```

#### Example Response

```json
{
  "query_type": "boolean",
  "description": "Advanced search with AND, OR, NOT operators",
  "syntax": "term1 AND term2, term1 OR term2, term1 NOT term2",
  "examples": [
    {
      "query": "diabetes AND hypertension",
      "description": "Both conditions must be present"
    },
    {
      "query": "diabetes NOT family",
      "description": "Diabetes but exclude family history"
    }
  ],
  "use_case": "Precise searches requiring specific term combinations"
}
```

---

### 3. Validate Query

**Endpoint:** `POST /api/v1/search/validate`

**Description:** Validate a search query without executing it.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Query to validate |
| query_type | string | No | Query type (default: standard) |

#### Example Request

```http
POST /api/v1/search/validate?q=diabetes+AND+hypertension&query_type=boolean
```

#### Example Response (Valid)

```json
{
  "valid": true,
  "query": "diabetes AND hypertension",
  "query_type": "boolean",
  "elasticsearch_query": {
    "query": {
      "bool": {
        "must": [
          {"match": {"_all": "diabetes"}},
          {"match": {"_all": "hypertension"}}
        ]
      }
    }
  },
  "message": "Query syntax is valid"
}
```

#### Example Response (Invalid)

```json
{
  "valid": false,
  "query": "diabetes AND",
  "query_type": "boolean",
  "error": "Incomplete AND expression",
  "message": "Query syntax is invalid",
  "suggestion": "Check the query syntax using /search/query-help endpoint"
}
```

---

### 4. Get Search Suggestions

**Endpoint:** `GET /api/v1/search/suggest`

**Description:** Get autocomplete suggestions for search query.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Partial query (min 2 chars) |
| size | integer | No | Max suggestions (1-10, default: 5) |

#### Example Request

```http
GET /api/v1/search/suggest?q=diab&size=5
```

#### Example Response

```json
{
  "query": "diab",
  "suggestions": [
    "diabetes",
    "diabetic ketoacidosis",
    "diabetic neuropathy",
    "diabetes mellitus",
    "diabetic retinopathy"
  ]
}
```

---

### 5. Cache Statistics (Admin Only)

**Endpoint:** `GET /api/v1/search/cache/stats`

**Description:** Get search cache statistics and performance metrics.

**Required Role:** Admin

#### Example Response

```json
{
  "cache_stats": {
    "standard": {
      "hits": 1250,
      "misses": 450,
      "sets": 450,
      "total_requests": 1700,
      "hit_rate": 73.53,
      "ttl_seconds": 3600
    },
    "boolean": {
      "hits": 340,
      "misses": 160,
      "sets": 160,
      "total_requests": 500,
      "hit_rate": 68.00,
      "ttl_seconds": 3600
    },
    "total_cached_queries": 387
  },
  "message": "Cache statistics retrieved successfully"
}
```

---

### 6. Invalidate Cache (Admin Only)

**Endpoint:** `POST /api/v1/search/cache/invalidate`

**Description:** Clear search cache entries.

**Required Role:** Admin

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| pattern | string | No | Pattern to match (e.g., 'boolean:*') |

#### Example Request

```http
POST /api/v1/search/cache/invalidate?pattern=wildcard:*
```

#### Example Response

```json
{
  "invalidated": 45,
  "pattern": "wildcard:*",
  "message": "Invalidated 45 cache entries matching pattern"
}
```

---

## Query Syntax Guide

### Standard Query

Basic keyword search with automatic typo tolerance.

```
diabetes mellitus
"heart failure"
cardio
```

### Boolean Query

Combine terms with AND, OR, NOT operators.

```
diabetes AND hypertension
diabetes OR hypertension NOT family
"heart failure" AND (diabetes OR obesity)
title:diabetes AND content:treatment
```

### Wildcard Query

Use * for any characters, ? for single character.

```
diabet*                 # Matches diabetes, diabetic, diabetology
wom?n                   # Matches woman, women
*cardia*                # Matches cardiac, myocardial, tachycardia
diagnosis:hyper*        # Field-specific wildcard
```

### Fuzzy Query

Use ~ for typo tolerance.

```
diabets~                # Finds diabetes (AUTO fuzziness)
diabets~1               # Allow 1 character difference
diabets~2               # Allow 2 character differences
"heart failure"~2       # Phrase with up to 2 words between
diagnosis:cardiak~      # Field-specific fuzzy search
```

### Proximity Query

Find terms within specified distance.

```
diabetes NEAR complications      # Within 5 words (default)
heart NEAR/3 failure            # Within 3 words
blood W/2 pressure              # Within 2 words (alternative syntax)
myocardial ADJ infarction       # Adjacent terms (next to each other)
diabetes WITHIN/10 treatment    # Within 10 words
```

### Range Query

Search numeric or date ranges.

```
age:[18 TO 65]                          # Age between 18 and 65 (inclusive)
age:{18 TO 65}                          # Age between 18 and 65 (exclusive)
age:[18 TO 65}                          # Mixed (inclusive min, exclusive max)
bp_systolic:>140                        # Greater than 140
bp_diastolic:<=90                       # Less than or equal to 90
date:[2023-01-01 TO 2023-12-31]        # Date range
date:[2023-01-01 TO *]                  # From date to now
glucose:[* TO 7.0]                       # From beginning to 7.0
```

### Regular Expression Query

Use /pattern/ for regex matching.

```
/diabet.*/                              # Basic regex
/diabet.*/i                             # Case-insensitive
/heart.+(failure|disease)/              # Complex pattern with groups
/[Cc]ardio.*/                          # Character classes
diagnosis:/^[A-Z]\d{2}\.\d/             # ICD-10 code pattern
name:/^Smith.*/                         # Names starting with Smith
```

---

## Performance Optimization

### Caching

Results are automatically cached with the following TTL:

| Query Type | TTL | Reason |
|------------|-----|--------|
| standard | 1 hour | Stable results |
| boolean | 1 hour | Stable results |
| wildcard | 30 minutes | More dynamic |
| fuzzy | 1 hour | Stable results |
| proximity | 1 hour | Stable results |
| range | 10 minutes | Time-sensitive |
| regex | Not cached | Safety/complexity |
| suggestions | 2 hours | Rarely changes |

### Query Optimization

The API automatically optimizes queries:

1. **Wildcard Optimization**
   - Trailing wildcards converted to prefix queries
   - Leading wildcards flagged with warnings

2. **Boolean Optimization**
   - Term/range queries moved to filter context for caching
   - Empty clauses removed

3. **Fuzzy Optimization**
   - Automatic prefix_length and max_expansions limits

4. **Regex Optimization**
   - Simple patterns converted to prefix queries
   - max_determinized_states limits added

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid query syntax) |
| 401 | Unauthorized |
| 403 | Forbidden (insufficient permissions) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message describing the issue",
  "status_code": 400,
  "type": "validation_error"
}
```

---

## Best Practices

1. **Choose the Right Query Type**
   - Use `standard` for general searches
   - Use `boolean` for precise requirements
   - Use `fuzzy` when dealing with potential typos
   - Use `proximity` for related concepts
   - Use `range` for filtering by values

2. **Performance Tips**
   - Avoid leading wildcards (*term)
   - Use filters to narrow results
   - Leverage caching by consistent queries
   - Validate complex queries before execution

3. **Query Complexity**
   - Keep regex patterns simple
   - Limit fuzzy distance to 2
   - Use specific fields when possible
   - Combine query types with filters

---

## Examples

### Find Patients with Multiple Conditions

```http
GET /api/v1/search?q=diabetes+AND+hypertension+AND+obesity&query_type=boolean
```

### Search with Typo Tolerance

```http
GET /api/v1/search?q=diabets~+OR+hypertenion~&query_type=fuzzy
```

### Find Recent Documents

```http
GET /api/v1/search?q=covid&date_from=2023-01-01&date_to=2023-12-31
```

### Complex Medical Search

```http
GET /api/v1/search?q=diagnosis:/diabet.*/+AND+age:[50+TO+70]&query_type=regex
```

### Proximity Search for Related Terms

```http
GET /api/v1/search?q=heart+NEAR/3+failure+AND+ejection+NEAR/2+fraction&query_type=proximity
```

---

## Rate Limiting

- **Standard users**: 100 requests per minute
- **Premium users**: 500 requests per minute
- **Admin users**: No limit

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

---

## Support

For API support or to report issues:
- GitHub Issues: https://github.com/cogstack/clinical-care-tools/issues
- Documentation: https://docs.cogstack.org/search-api