# Elasticsearch Query Expert

Expert knowledge of Elasticsearch query DSL and optimization patterns for clinical document search. Use when building search features, optimizing query performance, or debugging search issues. Based on Sprint 3 implementation experience with 7 query types.

## When This Skill Activates

**Activates automatically when**:
- Building Elasticsearch queries
- Implementing search features
- Optimizing query performance
- Debugging search relevance issues
- Adding new query types
- Working with aggregations and facets

**Keywords**: elasticsearch, query DSL, search, facets, aggregations, relevance, scoring

## Knowledge Base

### 7 Implemented Query Types

Based on Sprint 3 Phase 2 implementation:

#### 1. Standard Multi-Match Query
```python
{
    "query": {
        "multi_match": {
            "query": "diabetes",
            "fields": ["title^2", "content", "diagnosis^1.5"],
            "type": "best_fields",
            "fuzziness": "AUTO",
            "prefix_length": 2
        }
    }
}
```
- Use field boosting (^2) for relevance
- Apply AUTO fuzziness for typo tolerance
- Set prefix_length to avoid false matches

#### 2. Boolean Query with Filters
```python
{
    "query": {
        "bool": {
            "must": [  # Scoring queries
                {"match": {"content": "diabetes"}}
            ],
            "filter": [  # Non-scoring, cached
                {"term": {"document_type": "clinical_note"}},
                {"range": {"date": {"gte": "2023-01-01"}}}
            ],
            "should": [  # Optional boost
                {"match": {"diagnosis": "diabetes"}}
            ],
            "must_not": [  # Exclusions
                {"term": {"status": "draft"}}
            ]
        }
    }
}
```
**Optimization**: Move term/range queries to filter context for caching

#### 3. Wildcard Patterns
```python
# Convert trailing wildcards to prefix queries (faster)
"diab*" → {"prefix": {"content": "diab"}}

# Keep wildcard for complex patterns
"*itis" → {"wildcard": {"content": "*itis"}}  # Warning: slow

# Add case_insensitive flag
{"wildcard": {"content": {"value": "diab*", "case_insensitive": true}}}
```

#### 4. Fuzzy Matching
```python
{
    "fuzzy": {
        "content": {
            "value": "diabets",
            "fuzziness": 2,
            "prefix_length": 2,  # Required for performance
            "max_expansions": 50,  # Limit expansions
            "transpositions": true
        }
    }
}
```

#### 5. Proximity/Span Queries
```python
# Span near query for proximity
{
    "span_near": {
        "clauses": [
            {"span_term": {"content": "heart"}},
            {"span_term": {"content": "failure"}}
        ],
        "slop": 3,  # Words between
        "in_order": false
    }
}

# Alternative: match_phrase with slop
{
    "match_phrase": {
        "content": {
            "query": "heart failure",
            "slop": 3
        }
    }
}
```

#### 6. Range Queries
```python
# Numeric range
{"range": {"age": {"gte": 18, "lte": 65}}}

# Date range
{"range": {"date": {"gte": "2023-01-01", "lte": "2023-12-31"}}}

# Use gt/lt for exclusive, gte/lte for inclusive
```

#### 7. Regular Expressions
```python
{
    "regexp": {
        "content": {
            "value": "diabet.*",
            "flags": "INTERSECTION|COMPLEMENT",
            "max_determinized_states": 10000,  # Safety limit
            "rewrite": "constant_score"
        }
    }
}
```
**Warning**: Very expensive, use sparingly

### Aggregations for Faceted Search

```python
{
    "aggs": {
        "document_type": {
            "terms": {
                "field": "document_type.keyword",
                "size": 10
            }
        },
        "date_histogram": {
            "date_histogram": {
                "field": "date",
                "calendar_interval": "month",
                "min_doc_count": 1
            }
        },
        "department_filter": {
            "filter": {"term": {"department": "Cardiology"}},
            "aggs": {
                "avg_score": {"avg": {"field": "_score"}}
            }
        }
    }
}
```

### Performance Optimization Patterns

#### 1. Filter Context for Non-Scoring
```python
# Bad: Everything in must (scores everything)
"must": [
    {"match": {"content": "diabetes"}},
    {"term": {"type": "note"}},  # Doesn't need scoring
    {"range": {"date": {...}}}    # Doesn't need scoring
]

# Good: Non-scoring in filter
"must": [{"match": {"content": "diabetes"}}],
"filter": [
    {"term": {"type": "note"}},
    {"range": {"date": {...}}}
]
```

#### 2. Source Filtering
```python
{
    "_source": ["title", "date", "author"],  # Only needed fields
    "size": 20,
    "track_total_hits": 10000  # Limit counting
}
```

#### 3. Pagination Strategies
```python
# For small results (<10k): from + size
{"from": 0, "size": 20}

# For large results: search_after
{
    "size": 20,
    "sort": [{"date": "desc"}, {"_id": "asc"}],
    "search_after": ["2023-01-15", "doc-123"]
}

# For scrolling: PIT (Point In Time)
```

#### 4. Highlighting Optimization
```python
{
    "highlight": {
        "fields": {
            "content": {
                "fragment_size": 150,
                "number_of_fragments": 3,
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            }
        },
        "require_field_match": false,
        "boundary_scanner": "sentence"
    }
}
```

### Index Mapping Best Practices

```python
{
    "mappings": {
        "properties": {
            "content": {
                "type": "text",
                "analyzer": "english",
                "fields": {
                    "keyword": {"type": "keyword"},  # For aggregations
                    "ngram": {
                        "type": "text",
                        "analyzer": "ngram_analyzer"  # For substring
                    }
                }
            },
            "document_type": {
                "type": "keyword"  # For exact match and facets
            },
            "date": {
                "type": "date",
                "format": "yyyy-MM-dd"
            },
            "entities": {
                "type": "nested",  # For complex queries
                "properties": {
                    "cui": {"type": "keyword"},
                    "name": {"type": "text"}
                }
            }
        }
    }
}
```

### Query Complexity Analysis

From QueryOptimizer implementation:

```python
COMPLEXITY_WEIGHTS = {
    "match": 1,
    "match_phrase": 2,
    "wildcard": 5,
    "fuzzy": 3,
    "regexp": 10,
    "range": 2,
    "span_near": 4,
    "bool": 1  # Multiplier for nested
}

# Keep total complexity < 100
```

### Caching Strategy

From QueryCache implementation:

```python
TTL_CONFIG = {
    "standard": 3600,      # 1 hour - stable
    "boolean": 3600,       # 1 hour - stable
    "wildcard": 1800,      # 30 min - dynamic
    "fuzzy": 3600,         # 1 hour - stable
    "proximity": 3600,     # 1 hour - stable
    "range": 600,          # 10 min - time-sensitive
    "regex": 0,            # Don't cache - safety
}
```

### Common Pitfalls and Solutions

1. **Leading Wildcards**: Use ngram tokenizer instead
2. **Large Result Sets**: Use search_after, not from+size
3. **Slow Aggregations**: Use doc_values, not fielddata
4. **Memory Issues**: Limit bucket size in terms aggregations
5. **Relevance Issues**: Tune field boosting and analyzers

### Medical Search Specifics

1. **Synonym Expansion**: Use synonym token filter for medical terms
2. **Abbreviations**: Map common medical abbreviations
3. **SNOMED Codes**: Store as keyword for exact matching
4. **Date Parsing**: Handle various medical date formats
5. **Negation Detection**: Consider meta-annotations in queries

## Example Usage

### Building a Medical Document Search
```python
def build_medical_search(query_text: str, filters: Dict) -> Dict:
    """Build optimized medical document search."""

    es_query = {
        "query": {
            "bool": {
                "must": [{
                    "multi_match": {
                        "query": query_text,
                        "fields": [
                            "content",
                            "diagnosis^2",  # Boost diagnosis
                            "chief_complaint^1.5",
                            "medications"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                }],
                "filter": []
            }
        },
        "aggs": {
            "document_type": {
                "terms": {"field": "document_type.keyword"}
            },
            "department": {
                "terms": {"field": "department.keyword"}
            }
        },
        "highlight": {
            "fields": {
                "content": {"fragment_size": 200}
            }
        },
        "_source": ["title", "date", "author", "department"],
        "size": 20,
        "track_total_hits": 10000
    }

    # Add filters to filter context
    if filters.get("document_type"):
        es_query["query"]["bool"]["filter"].append({
            "term": {"document_type.keyword": filters["document_type"]}
        })

    if filters.get("date_from") or filters.get("date_to"):
        date_range = {"range": {"date": {}}}
        if filters.get("date_from"):
            date_range["range"]["date"]["gte"] = filters["date_from"]
        if filters.get("date_to"):
            date_range["range"]["date"]["lte"] = filters["date_to"]
        es_query["query"]["bool"]["filter"].append(date_range)

    # Add meta-annotation filters (negation, temporality)
    if filters.get("exclude_negated"):
        es_query["query"]["bool"]["must_not"] = [{
            "term": {"entities.meta_anns.Negation": "Negated"}
        }]

    return es_query
```

### Optimizing Slow Queries
```python
def optimize_query(query: Dict) -> Tuple[Dict, List[str]]:
    """Optimize Elasticsearch query for performance."""

    optimizations = []

    # Convert trailing wildcards to prefix
    if "wildcard" in str(query):
        # Check for patterns like "term*"
        # Convert to prefix query
        optimizations.append("Converted wildcard to prefix")

    # Move non-scoring to filter context
    if "bool" in query.get("query", {}):
        bool_query = query["query"]["bool"]
        if "must" in bool_query:
            # Move term/range queries to filter
            optimizations.append("Moved filters to filter context")

    # Add safety limits
    if "fuzzy" in str(query):
        # Add prefix_length and max_expansions
        optimizations.append("Added fuzzy safety limits")

    return query, optimizations
```

## Related Skills

- **medcat-meta-annotations**: For filtering by negation/temporality
- **redis-caching-patterns**: For result caching
- **search-performance-optimizer**: For query tuning
- **healthcare-compliance-checker**: For audit logging searches

## References

- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Sprint 3 Implementation](clinical-care-tools/backend/app/services/elasticsearch/)
- [Query Optimization Guide](clinical-care-tools/backend/docs/development/query-builders-guide.md)