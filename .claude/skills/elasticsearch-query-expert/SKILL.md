---
name: elasticsearch-query-expert
description: Elasticsearch DSL query building patterns, analyzers, relevance scoring, filters, and performance optimization. Use when implementing full-text search, building Elasticsearch queries, configuring analyzers, debugging relevance issues, or optimizing search performance. Covers query types (match, multi_match, bool, phrase), boosting, filter context, aggregations, and highlighting.
---

# Elasticsearch Query Expert

Expert guidance for building Elasticsearch queries, configuring analyzers, and optimizing search relevance for Sprint 3 Full-Text Search Enhancement.

## When to Use This Skill

- Building Elasticsearch DSL queries (match, multi_match, bool, phrase, term)
- Implementing query builders (QueryBuilder class)
- Configuring custom analyzers and tokenizers
- Debugging relevance scoring issues
- Implementing filter context vs query context
- Optimizing search performance
- Adding highlighting and aggregations
- Working with nested queries and boolean logic

## Core Concepts

### Query Context vs Filter Context

**Query Context** (affects relevance score):
```python
# Use for: Full-text search, relevance ranking
{
    "query": {
        "match": {
            "content": {
                "query": "diabetes medication",
                "boost": 2.0  # Affects _score
            }
        }
    }
}
```

**Filter Context** (no scoring, faster, cached):
```python
# Use for: Exact matches, metadata filtering
{
    "query": {
        "bool": {
            "must": [  # Query context (scores)
                {"match": {"content": "diabetes"}}
            ],
            "filter": [  # Filter context (no scoring, cached)
                {"term": {"document_type": "clinical_note"}},
                {"range": {"date": {"gte": "2024-01-01"}}}
            ]
        }
    }
}
```

**Rule**: Use filters for **exact** matches (types, dates, IDs), use queries for **relevance** (full-text search).

---

## Query Types

### 1. Simple Match Query

**When**: Single-field full-text search

```python
{
    "query": {
        "match": {
            "content": {
                "query": "diabetes",
                "operator": "and",  # Default: "or"
                "minimum_should_match": 1
            }
        }
    }
}
```

### 2. Multi-Match Query (Cross-field Search)

**When**: Search across multiple fields with boosting

```python
{
    "query": {
        "multi_match": {
            "query": "chest pain",
            "fields": [
                "title^10",    # Boost title 10x
                "content^1",   # Baseline
                "author^2"     # Boost author 2x
            ],
            "type": "best_fields",  # Options: best_fields, most_fields, cross_fields
            "minimum_should_match": "75%"
        }
    }
}
```

**Field boosting priorities** (Sprint 3):
- `title^10` - Most important (document title)
- `author^2` - Moderately important (author name)
- `content^1` - Baseline (document body)

### 3. Phrase Query (Exact Match)

**When**: Quoted strings, exact phrase matching

```python
{
    "query": {
        "match_phrase": {
            "content": {
                "query": "chest pain",
                "slop": 0  # Exact order, no words between
            }
        }
    }
}
```

**With slop** (allow words in between):
```python
{
    "match_phrase": {
        "content": {
            "query": "diabetes medication",
            "slop": 2  # Allow up to 2 words between: "diabetes with medication"
        }
    }
}
```

### 4. Term Query (Exact Match, No Analysis)

**When**: Keyword fields, exact IDs, metadata

```python
{
    "query": {
        "term": {
            "document_type.keyword": "clinical_note"  # Note: .keyword field
        }
    }
}
```

**Terms query** (multiple exact matches):
```python
{
    "query": {
        "terms": {
            "author.keyword": ["Dr. Smith", "Dr. Jones", "Dr. Brown"]
        }
    }
}
```

### 5. Bool Query (Combine Multiple Queries)

**Structure**:
- `must`: AND (affects score, required)
- `should`: OR (affects score, optional)
- `must_not`: NOT (excludes, no score)
- `filter`: AND (no score, cached)

```python
{
    "query": {
        "bool": {
            "must": [  # Required, affects score
                {"match": {"content": "diabetes"}}
            ],
            "should": [  # Optional, boosts score
                {"match": {"title": "medication"}},
                {"match": {"author": "Dr. Smith"}}
            ],
            "must_not": [  # Excluded, no score
                {"term": {"document_type": "draft"}}
            ],
            "filter": [  # Required, no score (faster)
                {"range": {"date": {"gte": "2024-01-01"}}},
                {"term": {"department": "cardiology"}}
            ],
            "minimum_should_match": 1  # At least 1 should clause must match
        }
    }
}
```

**Optimization**: Use `filter` for **exact** matches (faster, cached), `must` for **relevance** (scoring).

### 6. Nested Query (For Nested Objects)

**When**: Querying concepts array (nested field)

```python
{
    "query": {
        "nested": {
            "path": "concepts",
            "query": {
                "bool": {
                    "must": [
                        {"term": {"concepts.cui": "C0011849"}},  # CUI for diabetes
                        {"term": {"concepts.negation": "Affirmed"}}
                    ]
                }
            },
            "score_mode": "max"  # Options: avg, sum, min, max, none
        }
    }
}
```

---

## Analyzers and Tokenization

### Custom Clinical Analyzer (Sprint 3)

```json
{
    "settings": {
        "analysis": {
            "filter": {
                "clinical_synonyms": {
                    "type": "synonym",
                    "synonyms": [
                        "MI, myocardial infarction",
                        "CAD, coronary artery disease",
                        "CHF, congestive heart failure",
                        "DM, diabetes mellitus",
                        "HTN, hypertension"
                    ]
                },
                "english_stop": {
                    "type": "stop",
                    "stopwords": "_english_"
                },
                "english_stemmer": {
                    "type": "stemmer",
                    "language": "english"
                }
            },
            "analyzer": {
                "clinical_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "clinical_synonyms",
                        "english_stop",
                        "english_stemmer"
                    ]
                }
            }
        }
    }
}
```

**Why this matters**:
- "MI" and "myocardial infarction" match
- "diabetes" and "diabetic" match (stemming)
- Common stop words removed ("the", "a", "an")

---

## Relevance Scoring and Boosting

### Function Score Query (Advanced Scoring)

**When**: Custom relevance formulas (recency boost, popularity)

```python
{
    "query": {
        "function_score": {
            "query": {
                "match": {"content": "diabetes"}
            },
            "functions": [
                {
                    "gauss": {  # Recency boost
                        "date": {
                            "origin": "now",
                            "scale": "30d",
                            "decay": 0.5
                        }
                    },
                    "weight": 2
                },
                {
                    "field_value_factor": {  # Popularity boost
                        "field": "view_count",
                        "modifier": "log1p",
                        "factor": 0.1
                    }
                }
            ],
            "score_mode": "sum",  # Options: sum, multiply, avg, max, min
            "boost_mode": "multiply"  # Options: multiply, sum, replace
        }
    }
}
```

**Sprint 3 boosting strategy**:
1. Field boosting (title^10, author^2, content^1)
2. Recency (prefer recent documents)
3. No popularity (not tracking views yet)

---

## Query Builder Patterns (Sprint 3)

### QueryBuilder Class Structure

```python
from typing import Dict, List, Optional
from enum import Enum


class QueryType(Enum):
    SIMPLE = "simple"
    PHRASE = "phrase"
    BOOLEAN = "boolean"
    FIELD = "field"
    COMPLEX = "complex"


class QueryBuilder:
    """Builds Elasticsearch DSL queries from user input."""

    def __init__(self):
        self.default_fields = ["title^10", "content^1", "author^2"]
        self.default_operator = "and"

    def build_query(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
        sort: Optional[str] = None
    ) -> Dict:
        """
        Build complete Elasticsearch query.

        Args:
            query: User search query
            filters: Metadata filters (document_type, author, date_range)
            page: Page number (1-indexed)
            page_size: Results per page
            sort: Sort field (relevance, date, title)

        Returns:
            Elasticsearch DSL query dict
        """
        # 1. Detect query type
        query_type = self._detect_query_type(query)

        # 2. Build base query
        if query_type == QueryType.SIMPLE:
            base_query = self._build_simple_query(query)
        elif query_type == QueryType.PHRASE:
            base_query = self._build_phrase_query(query)
        elif query_type == QueryType.BOOLEAN:
            base_query = self._build_boolean_query(query)
        elif query_type == QueryType.FIELD:
            base_query = self._build_field_query(query)
        else:  # COMPLEX
            base_query = self._build_complex_query(query)

        # 3. Apply filters (filter context, no scoring)
        if filters:
            base_query = self._apply_filters(base_query, filters)

        # 4. Add pagination
        from_offset = (page - 1) * page_size

        # 5. Add sorting
        sort_clause = self._build_sort(sort)

        # 6. Construct final query
        es_query = {
            "query": base_query,
            "from": from_offset,
            "size": page_size,
            "track_total_hits": True,
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {"fragment_size": 150, "number_of_fragments": 3}
                }
            }
        }

        if sort_clause:
            es_query["sort"] = sort_clause

        return es_query

    def _detect_query_type(self, query: str) -> QueryType:
        """Detect query type from user input."""
        if self._is_phrase_query(query):
            return QueryType.PHRASE
        elif self._is_boolean_query(query):
            return QueryType.BOOLEAN
        elif self._is_field_query(query):
            return QueryType.FIELD
        elif self._is_complex_query(query):
            return QueryType.COMPLEX
        else:
            return QueryType.SIMPLE

    def _is_phrase_query(self, query: str) -> bool:
        """Check if query contains quoted phrases."""
        return '"' in query

    def _is_boolean_query(self, query: str) -> bool:
        """Check if query contains boolean operators."""
        return any(op in query.upper() for op in [" AND ", " OR ", " NOT "])

    def _is_field_query(self, query: str) -> bool:
        """Check if query contains field:value syntax."""
        import re
        return bool(re.search(r'\w+:"[^"]+"', query) or re.search(r'\w+:\w+', query))

    def _is_complex_query(self, query: str) -> bool:
        """Check if query contains parentheses (complex nested queries)."""
        return "(" in query and ")" in query

    def _build_simple_query(self, query: str) -> Dict:
        """Build multi_match query for simple keyword search."""
        return {
            "multi_match": {
                "query": query,
                "fields": self.default_fields,
                "type": "best_fields",
                "operator": self.default_operator,
                "minimum_should_match": 1
            }
        }

    def _build_phrase_query(self, query: str) -> Dict:
        """Build match_phrase queries for quoted phrases."""
        import re

        # Extract phrases
        phrases = re.findall(r'"([^"]*)"', query)

        if not phrases:
            return self._build_simple_query(query)

        # Build bool query with phrase queries
        must_clauses = []
        for phrase in phrases:
            must_clauses.append({
                "multi_match": {
                    "query": phrase,
                    "fields": self.default_fields,
                    "type": "phrase"
                }
            })

        # Extract non-phrase terms
        remaining = re.sub(r'"[^"]*"', '', query).strip()
        if remaining:
            must_clauses.append(self._build_simple_query(remaining))

        if len(must_clauses) == 1:
            return must_clauses[0]

        return {
            "bool": {
                "must": must_clauses
            }
        }

    def _build_boolean_query(self, query: str) -> Dict:
        """Build bool query for AND/OR/NOT operators."""
        # This is simplified - use Lark parser for complex queries
        import re

        # Split by OR (lowest precedence)
        or_parts = re.split(r'\s+OR\s+', query, flags=re.IGNORECASE)

        if len(or_parts) > 1:
            should_clauses = [self._build_and_query(part) for part in or_parts]
            return {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            }

        return self._build_and_query(query)

    def _build_and_query(self, query: str) -> Dict:
        """Build AND query with NOT handling."""
        import re

        # Split by AND
        and_parts = re.split(r'\s+AND\s+', query, flags=re.IGNORECASE)

        must_clauses = []
        must_not_clauses = []

        for part in and_parts:
            part = part.strip()

            # Handle NOT
            if part.upper().startswith('NOT '):
                term = part[4:].strip()
                must_not_clauses.append(self._build_term_clause(term))
            else:
                must_clauses.append(self._build_term_clause(part))

        query_dict = {"bool": {}}

        if must_clauses:
            query_dict["bool"]["must"] = must_clauses
        if must_not_clauses:
            query_dict["bool"]["must_not"] = must_not_clauses

        return query_dict

    def _build_term_clause(self, term: str) -> Dict:
        """Build clause for single term."""
        term = term.strip()

        if '"' in term:
            return self._build_phrase_query(term)
        else:
            return self._build_simple_query(term)

    def _build_field_query(self, query: str) -> Dict:
        """Build field-specific queries (author:\"Dr. Smith\")."""
        import re

        # Parse field:value pairs
        field_queries = []
        remaining_query = query

        # Match field:"value" or field:value
        pattern = r'(\w+):("([^"]*)"|(\S+))'
        matches = re.finditer(pattern, query)

        for match in matches:
            field = match.group(1)
            value = match.group(3) or match.group(4)

            field_queries.append({
                "match": {
                    field: {
                        "query": value,
                        "operator": "and"
                    }
                }
            })

            # Remove matched portion
            remaining_query = remaining_query.replace(match.group(0), '').strip()

        # Handle remaining non-field query
        if remaining_query:
            field_queries.append(self._build_simple_query(remaining_query))

        if len(field_queries) == 1:
            return field_queries[0]

        return {
            "bool": {
                "must": field_queries
            }
        }

    def _apply_filters(self, base_query: Dict, filters: Dict) -> Dict:
        """Apply metadata filters (filter context, no scoring)."""
        filter_clauses = []

        # Document type filter
        if "document_types" in filters and filters["document_types"]:
            filter_clauses.append({
                "terms": {"document_type": filters["document_types"]}
            })

        # Author filter
        if "authors" in filters and filters["authors"]:
            filter_clauses.append({
                "terms": {"author.keyword": filters["authors"]}
            })

        # Department filter
        if "departments" in filters and filters["departments"]:
            filter_clauses.append({
                "terms": {"department": filters["departments"]}
            })

        # Date range filter
        if "date_range" in filters:
            range_filter = {"range": {"date": {}}}

            if "gte" in filters["date_range"]:
                range_filter["range"]["date"]["gte"] = filters["date_range"]["gte"]
            if "lte" in filters["date_range"]:
                range_filter["range"]["date"]["lte"] = filters["date_range"]["lte"]

            if range_filter["range"]["date"]:
                filter_clauses.append(range_filter)

        if not filter_clauses:
            return base_query

        # Wrap base query with filters
        return {
            "bool": {
                "must": [base_query],
                "filter": filter_clauses
            }
        }

    def _build_sort(self, sort: Optional[str]) -> Optional[List[Dict]]:
        """Build sort clause."""
        if not sort or sort == "relevance":
            return None  # Default: relevance (_score)

        if sort == "date":
            return [{"date": {"order": "desc"}}, "_score"]
        elif sort == "title":
            return [{"title.keyword": {"order": "asc"}}, "_score"]

        return None
```

---

## Performance Optimization

### 1. Use Filter Context for Exact Matches

**Slow** (query context, scores everything):
```python
{"query": {"match": {"document_type": "clinical_note"}}}
```

**Fast** (filter context, no scoring, cached):
```python
{
    "query": {
        "bool": {
            "filter": [
                {"term": {"document_type": "clinical_note"}}
            ]
        }
    }
}
```

### 2. Limit Fields in multi_match

**Slow** (searches all fields):
```python
{"multi_match": {"query": "diabetes", "fields": ["*"]}}
```

**Fast** (specific fields only):
```python
{"multi_match": {"query": "diabetes", "fields": ["title^10", "content"]}}
```

### 3. Use _source Filtering

**Slow** (returns entire document):
```python
{"query": {...}}
```

**Fast** (return only needed fields):
```python
{
    "query": {...},
    "_source": ["title", "author", "date", "document_id"]
}
```

### 4. Pagination with search_after (Large Datasets)

**Slow** (deep pagination, `from: 10000`):
```python
{"query": {...}, "from": 10000, "size": 20}
```

**Fast** (search_after with sort values):
```python
{
    "query": {...},
    "size": 20,
    "sort": [{"date": "desc"}, {"_id": "asc"}],
    "search_after": ["2024-01-15", "doc_123"]
}
```

---

## Common Patterns for Sprint 3

### Pattern 1: Simple Keyword Search with Filters

```python
query_builder = QueryBuilder()

result = query_builder.build_query(
    query="diabetes medication",
    filters={
        "document_types": ["clinical_note"],
        "date_range": {"gte": "2024-01-01", "lte": "2024-12-31"}
    },
    page=1,
    page_size=20,
    sort="relevance"
)
```

### Pattern 2: Phrase Search

```python
result = query_builder.build_query(
    query='"chest pain" AND "shortness of breath"',
    filters=None,
    page=1,
    page_size=20
)
```

### Pattern 3: Field-Specific Search

```python
result = query_builder.build_query(
    query='author:"Dr. Smith" diabetes',
    filters={"document_types": ["clinical_note"]},
    page=1,
    page_size=20
)
```

### Pattern 4: Complex Boolean Query

```python
result = query_builder.build_query(
    query='(diabetes OR "high blood sugar") AND medication NOT insulin',
    filters=None,
    page=1,
    page_size=20
)
```

---

## Testing Elasticsearch Queries

### Test Query Locally

```bash
# Test simple match
curl -X POST "http://localhost:9200/documents/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "diabetes"}
  }
}
'

# Test with explain (see scoring)
curl -X POST "http://localhost:9200/documents/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "diabetes"}
  },
  "explain": true
}
'

# Test analyzer
curl -X POST "http://localhost:9200/documents/_analyze?pretty" -H 'Content-Type: application/json' -d'
{
  "analyzer": "clinical_analyzer",
  "text": "Patient diagnosed with MI (myocardial infarction)"
}
'
```

### Unit Test Example

```python
import pytest
from app.search.query_builder import QueryBuilder


def test_build_simple_query():
    """Test simple keyword query building."""
    builder = QueryBuilder()

    result = builder.build_query(query="diabetes", page=1, page_size=20)

    # Verify structure
    assert "query" in result
    assert result["query"]["multi_match"]["query"] == "diabetes"
    assert result["query"]["multi_match"]["fields"] == ["title^10", "content^1", "author^2"]
    assert result["from"] == 0
    assert result["size"] == 20


def test_build_phrase_query():
    """Test phrase query building."""
    builder = QueryBuilder()

    result = builder.build_query(query='"chest pain"', page=1, page_size=20)

    # Verify phrase query
    assert "query" in result
    assert result["query"]["multi_match"]["type"] == "phrase"
    assert result["query"]["multi_match"]["query"] == "chest pain"


def test_apply_filters():
    """Test filter application."""
    builder = QueryBuilder()

    result = builder.build_query(
        query="diabetes",
        filters={
            "document_types": ["clinical_note"],
            "date_range": {"gte": "2024-01-01"}
        },
        page=1,
        page_size=20
    )

    # Verify filters in filter context
    assert "query" in result
    assert result["query"]["bool"]["filter"]
    filters = result["query"]["bool"]["filter"]
    assert any(f.get("terms", {}).get("document_type") == ["clinical_note"] for f in filters)
    assert any(f.get("range", {}).get("date", {}).get("gte") == "2024-01-01" for f in filters)
```

---

## Debugging Relevance Issues

### Use Explain API

```bash
curl -X POST "http://localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "diabetes"}
  },
  "explain": true
}
'
```

This shows:
- Why each document matched
- How _score was calculated
- Which query clauses contributed

### Use Validate API

```bash
curl -X POST "http://localhost:9200/documents/_validate/query?explain" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "diabetes"}
  }
}
'
```

This shows:
- If query is valid
- Rewritten query (how Elasticsearch actually runs it)

---

## References

- **Elasticsearch DSL**: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
- **Relevance Scoring**: https://www.elastic.co/guide/en/elasticsearch/guide/current/relevance-intro.html
- **Analyzers**: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html
- **Sprint 3 Tasks**: `.specify/tasks/sprint-3-full-text-search-tasks.md`
- **Sprint 3 Plan**: `.specify/plans/sprint-3-full-text-search-plan.md`

---

**Questions?** Refer to Elasticsearch documentation or Sprint 3 specifications.
