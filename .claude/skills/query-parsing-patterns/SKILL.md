---
name: query-parsing-patterns
description: Lark parser patterns for complex query parsing, EBNF grammar design, parse tree transformation, boolean logic (AND/OR/NOT precedence), parenthesized grouping, and field queries. Use when implementing QueryParser, designing query grammars, debugging parse errors, transforming parse trees to Elasticsearch DSL, or handling complex nested queries.
---

# Query Parsing Patterns

Expert guidance for implementing query parsers using Lark, designing EBNF grammars, and transforming parse trees to Elasticsearch DSL for Sprint 3 Advanced Query Parsing.

## When to Use This Skill

- Implementing QueryParser class with Lark
- Designing EBNF grammars for search queries
- Handling boolean operators (AND/OR/NOT) with correct precedence
- Parsing parenthesized grouping: `(A OR B) AND C`
- Implementing field queries: `author:"Dr. Smith"`
- Transforming parse trees to Elasticsearch DSL
- Debugging parse errors and grammar ambiguity
- Integrating QueryParser with QueryBuilder

## Core Concepts

### Why Use a Parser (vs Regex)?

**Regex approach** (fragile, incorrect precedence):
```python
# ❌ WRONG: Can't handle nested parentheses or operator precedence
parts = re.split(r'\s+(AND|OR|NOT)\s+', query)
```

**Parser approach** (correct, robust):
```python
# ✅ CORRECT: Formal grammar, correct precedence, handles nesting
from lark import Lark
parser = Lark(grammar, start='query', parser='lalr')
tree = parser.parse("(diabetes OR hypertension) AND medication")
```

**Advantages of Lark**:
- Formal grammar specification (EBNF)
- Automatic parse tree generation
- Correct operator precedence
- Handles complex nesting
- Better error messages
- Easier to maintain and extend

---

## Lark Grammar for Search Queries (Sprint 3)

### Complete Grammar

```ebnf
// backend/app/search/query_grammar.py

from lark import Lark

QUERY_GRAMMAR = r"""
?query: or_expr

// Operator precedence (lowest to highest):
// 1. OR (lowest)
// 2. AND
// 3. NOT (highest)

?or_expr: and_expr
        | or_expr "OR" and_expr  -> or_op

?and_expr: not_expr
         | and_expr "AND" not_expr  -> and_op

?not_expr: "NOT" not_expr  -> not_op
         | atom

?atom: term
     | phrase
     | field_query
     | group

term: WORD+
phrase: ESCAPED_STRING
field_query: FIELD_NAME ":" (phrase | WORD)
group: "(" query ")"

FIELD_NAME: /[a-zA-Z_][a-zA-Z0-9_]*(?=:)/  // Lookahead to avoid ambiguity
WORD: /[^\s"()]+/
ESCAPED_STRING: /"(?:[^"\\]|\\.)*"/

%import common.WS
%ignore WS
"""

def get_query_parser():
    """Get Lark parser instance for query parsing."""
    return Lark(
        QUERY_GRAMMAR,
        start='query',
        parser='lalr',  // Faster than Earley, sufficient for our grammar
        transformer=None  // Apply transformer separately
    )
```

### Grammar Explanation

**Operator Precedence** (same as boolean algebra):
1. `NOT` (highest priority) - Unary, binds tightest
2. `AND` (medium priority) - Binary, left-associative
3. `OR` (lowest priority) - Binary, left-associative

**Example parsing**:
```
Query: "diabetes OR hypertension AND NOT medication"

Parse tree:
  or_op
  ├─ term("diabetes")
  └─ and_op
      ├─ term("hypertension")
      └─ not_op
          └─ term("medication")

Interpretation: "diabetes" OR ("hypertension" AND (NOT "medication"))
```

**Why this precedence?**:
- Matches boolean algebra conventions
- Intuitive for users: `A OR B AND C` means `A OR (B AND C)`, not `(A OR B) AND C`
- Parentheses override: `(A OR B) AND C` forces OR first

---

## Parse Tree Transformation

### Transformer Class

```python
# backend/app/search/query_parser.py

from lark import Transformer, Tree, Token
from typing import Dict, List, Union


class QueryTransformer(Transformer):
    """Transforms Lark parse tree to Elasticsearch DSL."""

    def __init__(self):
        super().__init__()
        self.default_fields = ["title^10", "content^1", "author^2"]

    def term(self, items: List[Token]) -> Dict:
        """
        Transform term nodes to multi_match query.

        Args:
            items: List of WORD tokens

        Returns:
            Elasticsearch multi_match query dict
        """
        # Join multiple words
        query_text = " ".join(str(item) for item in items)

        return {
            "multi_match": {
                "query": query_text,
                "fields": self.default_fields,
                "type": "best_fields",
                "operator": "and"
            }
        }

    def phrase(self, items: List[Token]) -> Dict:
        """
        Transform phrase nodes to match_phrase query.

        Args:
            items: List containing ESCAPED_STRING token

        Returns:
            Elasticsearch match_phrase query dict
        """
        # Extract phrase from quotes
        phrase_text = str(items[0])[1:-1]  # Remove surrounding quotes

        return {
            "multi_match": {
                "query": phrase_text,
                "fields": self.default_fields,
                "type": "phrase"
            }
        }

    def field_query(self, items: List[Token]) -> Dict:
        """
        Transform field_query nodes to field-specific match.

        Args:
            items: [FIELD_NAME, phrase|WORD]

        Returns:
            Elasticsearch match query dict

        Example:
            author:"Dr. Smith" → {"match": {"author": {"query": "Dr. Smith"}}}
        """
        field_name = str(items[0])

        # Extract value (might be phrase or word)
        if isinstance(items[1], str):
            value = items[1]
        elif isinstance(items[1], Token):
            value_str = str(items[1])
            # Remove quotes if present
            value = value_str[1:-1] if value_str.startswith('"') else value_str
        else:
            # Already transformed to dict (shouldn't happen with current grammar)
            return items[1]

        return {
            "match": {
                field_name: {
                    "query": value,
                    "operator": "and"
                }
            }
        }

    def and_op(self, items: List[Dict]) -> Dict:
        """
        Transform AND operations to bool must clauses.

        Args:
            items: [left_query, right_query]

        Returns:
            Elasticsearch bool must query dict
        """
        left, right = items

        # Flatten nested AND operations
        must_clauses = []

        if isinstance(left, dict) and "bool" in left and "must" in left["bool"]:
            must_clauses.extend(left["bool"]["must"])
        else:
            must_clauses.append(left)

        if isinstance(right, dict) and "bool" in right and "must" in right["bool"]:
            must_clauses.extend(right["bool"]["must"])
        else:
            must_clauses.append(right)

        return {
            "bool": {
                "must": must_clauses
            }
        }

    def or_op(self, items: List[Dict]) -> Dict:
        """
        Transform OR operations to bool should clauses.

        Args:
            items: [left_query, right_query]

        Returns:
            Elasticsearch bool should query dict
        """
        left, right = items

        # Flatten nested OR operations
        should_clauses = []

        if isinstance(left, dict) and "bool" in left and "should" in left["bool"]:
            should_clauses.extend(left["bool"]["should"])
        else:
            should_clauses.append(left)

        if isinstance(right, dict) and "bool" in right and "should" in right["bool"]:
            should_clauses.extend(right["bool"]["should"])
        else:
            should_clauses.append(right)

        return {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }

    def not_op(self, items: List[Dict]) -> Dict:
        """
        Transform NOT operations to bool must_not clauses.

        Args:
            items: [query_to_negate]

        Returns:
            Elasticsearch bool must_not query dict
        """
        query_to_negate = items[0]

        return {
            "bool": {
                "must_not": [query_to_negate]
            }
        }

    def group(self, items: List[Dict]) -> Dict:
        """
        Transform grouped expressions (parentheses).

        Args:
            items: [query_inside_parentheses]

        Returns:
            Query inside parentheses (no wrapping needed)
        """
        # Parentheses only affect parsing order, not final query
        return items[0]
```

### QueryParser Class

```python
# backend/app/search/query_parser.py

from lark import Lark, LarkError
from typing import Dict, Optional


class QueryParser:
    """Parses complex search queries using Lark grammar."""

    def __init__(self):
        self.parser = get_query_parser()
        self.transformer = QueryTransformer()

    def parse(self, query: str) -> Optional[Dict]:
        """
        Parse query string to Elasticsearch DSL.

        Args:
            query: User search query

        Returns:
            Elasticsearch query dict, or None if parse fails

        Raises:
            LarkError: If query syntax is invalid

        Examples:
            >>> parser = QueryParser()
            >>> parser.parse("diabetes")
            {'multi_match': {'query': 'diabetes', 'fields': [...]}}

            >>> parser.parse("(diabetes OR hypertension) AND medication")
            {'bool': {'must': [
                {'bool': {'should': [
                    {'multi_match': {'query': 'diabetes', ...}},
                    {'multi_match': {'query': 'hypertension', ...}}
                ], 'minimum_should_match': 1}},
                {'multi_match': {'query': 'medication', ...}}
            ]}}
        """
        if not query or not query.strip():
            return None

        try:
            # 1. Parse to tree
            tree = self.parser.parse(query)

            # 2. Transform tree to Elasticsearch DSL
            es_query = self.transformer.transform(tree)

            return es_query

        except LarkError as e:
            # Parse error - return None or raise
            # Caller can fallback to simple query
            raise LarkError(f"Query parse error: {e}")
```

---

## Integration with QueryBuilder

### Pattern: Fallback to Simple Query

```python
# backend/app/search/query_builder.py

from app.search.query_parser import QueryParser, LarkError


class QueryBuilder:
    def __init__(self):
        self.query_parser = QueryParser()
        self.default_fields = ["title^10", "content^1", "author^2"]

    def _build_boolean_query(self, query: str) -> Dict:
        """
        Build boolean query using QueryParser, with fallback.

        Args:
            query: User query with boolean operators

        Returns:
            Elasticsearch query dict
        """
        try:
            # Try to parse with QueryParser
            parsed_query = self.query_parser.parse(query)

            if parsed_query:
                return parsed_query

            # Empty query
            return self._build_simple_query(query)

        except LarkError:
            # Parse error - fall back to simple query
            # Log error for monitoring
            logger.warning(f"Query parse error, falling back to simple: {query}")
            return self._build_simple_query(query)
```

**Why fallback?**:
- Graceful degradation (always return results)
- User doesn't see parse errors
- Simple queries still work if grammar changes
- Monitoring can track parse error rate

---

## Common Patterns

### Pattern 1: Simple Term

**Query**: `diabetes`

**Parse tree**:
```
query
  └─ term
      └─ WORD("diabetes")
```

**Transformed DSL**:
```python
{
    "multi_match": {
        "query": "diabetes",
        "fields": ["title^10", "content^1", "author^2"],
        "type": "best_fields",
        "operator": "and"
    }
}
```

---

### Pattern 2: Phrase

**Query**: `"chest pain"`

**Parse tree**:
```
query
  └─ phrase
      └─ ESCAPED_STRING('"chest pain"')
```

**Transformed DSL**:
```python
{
    "multi_match": {
        "query": "chest pain",
        "fields": ["title^10", "content^1", "author^2"],
        "type": "phrase"
    }
}
```

---

### Pattern 3: AND Operation

**Query**: `diabetes AND medication`

**Parse tree**:
```
query
  └─ and_op
      ├─ term("diabetes")
      └─ term("medication")
```

**Transformed DSL**:
```python
{
    "bool": {
        "must": [
            {"multi_match": {"query": "diabetes", ...}},
            {"multi_match": {"query": "medication", ...}}
        ]
    }
}
```

---

### Pattern 4: OR Operation

**Query**: `diabetes OR hypertension`

**Parse tree**:
```
query
  └─ or_op
      ├─ term("diabetes")
      └─ term("hypertension")
```

**Transformed DSL**:
```python
{
    "bool": {
        "should": [
            {"multi_match": {"query": "diabetes", ...}},
            {"multi_match": {"query": "hypertension", ...}}
        ],
        "minimum_should_match": 1
    }
}
```

---

### Pattern 5: NOT Operation

**Query**: `diabetes NOT insulin`

**Parse tree**:
```
query
  └─ and_op
      ├─ term("diabetes")
      └─ not_op
          └─ term("insulin")
```

**Transformed DSL**:
```python
{
    "bool": {
        "must": [
            {"multi_match": {"query": "diabetes", ...}}
        ],
        "must_not": [
            {"multi_match": {"query": "insulin", ...}}
        ]
    }
}
```

---

### Pattern 6: Parenthesized Grouping

**Query**: `(diabetes OR hypertension) AND medication`

**Parse tree**:
```
query
  └─ and_op
      ├─ group
      │   └─ or_op
      │       ├─ term("diabetes")
      │       └─ term("hypertension")
      └─ term("medication")
```

**Transformed DSL**:
```python
{
    "bool": {
        "must": [
            {
                "bool": {
                    "should": [
                        {"multi_match": {"query": "diabetes", ...}},
                        {"multi_match": {"query": "hypertension", ...}}
                    ],
                    "minimum_should_match": 1
                }
            },
            {"multi_match": {"query": "medication", ...}}
        ]
    }
}
```

---

### Pattern 7: Field Query

**Query**: `author:"Dr. Smith" diabetes`

**Parse tree**:
```
query
  └─ and_op
      ├─ field_query
      │   ├─ FIELD_NAME("author")
      │   └─ ESCAPED_STRING('"Dr. Smith"')
      └─ term("diabetes")
```

**Transformed DSL**:
```python
{
    "bool": {
        "must": [
            {"match": {"author": {"query": "Dr. Smith", "operator": "and"}}},
            {"multi_match": {"query": "diabetes", ...}}
        ]
    }
}
```

---

### Pattern 8: Complex Nested Query

**Query**: `((diabetes OR "high blood sugar") AND medication) NOT insulin`

**Parse tree**:
```
query
  └─ and_op
      ├─ group
      │   └─ and_op
      │       ├─ group
      │       │   └─ or_op
      │       │       ├─ term("diabetes")
      │       │       └─ phrase("high blood sugar")
      │       └─ term("medication")
      └─ not_op
          └─ term("insulin")
```

**Transformed DSL**:
```python
{
    "bool": {
        "must": [
            {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": [
                                    {"multi_match": {"query": "diabetes", ...}},
                                    {"multi_match": {"query": "high blood sugar", "type": "phrase", ...}}
                                ],
                                "minimum_should_match": 1
                            }
                        },
                        {"multi_match": {"query": "medication", ...}}
                    ]
                }
            }
        ],
        "must_not": [
            {"multi_match": {"query": "insulin", ...}}
        ]
    }
}
```

---

## Testing Query Parser

### Unit Tests

```python
# backend/tests/unit/search/test_query_parser.py

import pytest
from app.search.query_parser import QueryParser, LarkError


class TestSimpleTerms:
    """Test simple term parsing."""

    def test_parse_single_term(self):
        """Test parsing single term."""
        parser = QueryParser()
        result = parser.parse("diabetes")

        assert result["multi_match"]["query"] == "diabetes"
        assert result["multi_match"]["fields"] == ["title^10", "content^1", "author^2"]

    def test_parse_multiple_terms(self):
        """Test parsing multiple terms (implicit AND)."""
        parser = QueryParser()
        result = parser.parse("diabetes medication")

        assert result["multi_match"]["query"] == "diabetes medication"


class TestPhrases:
    """Test phrase parsing."""

    def test_parse_phrase(self):
        """Test parsing quoted phrase."""
        parser = QueryParser()
        result = parser.parse('"chest pain"')

        assert result["multi_match"]["query"] == "chest pain"
        assert result["multi_match"]["type"] == "phrase"


class TestBooleanOperators:
    """Test boolean operator parsing."""

    def test_parse_and_operator(self):
        """Test AND operator."""
        parser = QueryParser()
        result = parser.parse("diabetes AND medication")

        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 2

    def test_parse_or_operator(self):
        """Test OR operator."""
        parser = QueryParser()
        result = parser.parse("diabetes OR hypertension")

        assert "bool" in result
        assert "should" in result["bool"]
        assert len(result["bool"]["should"]) == 2
        assert result["bool"]["minimum_should_match"] == 1

    def test_parse_not_operator(self):
        """Test NOT operator."""
        parser = QueryParser()
        result = parser.parse("diabetes NOT insulin")

        assert "bool" in result
        assert "must" in result["bool"]
        assert "must_not" in result["bool"]


class TestNestedQueries:
    """Test nested query parsing."""

    def test_parse_parentheses(self):
        """Test parenthesized grouping."""
        parser = QueryParser()
        result = parser.parse("(diabetes OR hypertension) AND medication")

        # Should have top-level must with 2 clauses
        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 2

        # First clause should be OR
        first_clause = result["bool"]["must"][0]
        assert "bool" in first_clause
        assert "should" in first_clause["bool"]

    def test_parse_complex_nested(self):
        """Test complex nested query."""
        parser = QueryParser()
        result = parser.parse("((diabetes OR \"high blood sugar\") AND medication) NOT insulin")

        assert "bool" in result
        assert "must" in result["bool"]
        assert "must_not" in result["bool"]


class TestFieldQueries:
    """Test field-specific query parsing."""

    def test_parse_field_query(self):
        """Test field:value syntax."""
        parser = QueryParser()
        result = parser.parse('author:"Dr. Smith"')

        assert "match" in result
        assert "author" in result["match"]
        assert result["match"]["author"]["query"] == "Dr. Smith"

    def test_parse_mixed_field_and_term(self):
        """Test combination of field query and term."""
        parser = QueryParser()
        result = parser.parse('author:"Dr. Smith" diabetes')

        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 2


class TestErrorHandling:
    """Test error handling."""

    def test_parse_empty_query(self):
        """Test empty query returns None."""
        parser = QueryParser()
        result = parser.parse("")

        assert result is None

    def test_parse_invalid_syntax(self):
        """Test invalid syntax raises LarkError."""
        parser = QueryParser()

        with pytest.raises(LarkError):
            parser.parse("diabetes AND")  # Missing right operand

    def test_parse_unmatched_parentheses(self):
        """Test unmatched parentheses raises LarkError."""
        parser = QueryParser()

        with pytest.raises(LarkError):
            parser.parse("(diabetes AND medication"))  # Missing closing paren
```

---

## Debugging Parse Errors

### Visualize Parse Tree

```python
from lark import Lark, tree

parser = Lark(QUERY_GRAMMAR, start='query', parser='lalr')

query = "(diabetes OR hypertension) AND medication"
tree = parser.parse(query)

# Print tree
print(tree.pretty())

# Output:
# query
#   and_op
#     group
#       or_op
#         term  diabetes
#         term  hypertension
#     term  medication
```

### Test Transformations Step-by-Step

```python
from lark import Lark

parser = Lark(QUERY_GRAMMAR, start='query', parser='lalr')
transformer = QueryTransformer()

query = "diabetes AND medication"

# 1. Parse
tree = parser.parse(query)
print("Parse tree:", tree.pretty())

# 2. Transform
result = transformer.transform(tree)
print("Transformed DSL:", json.dumps(result, indent=2))
```

---

## Common Pitfalls

### Pitfall 1: Grammar Ambiguity

**Problem**: Multiple valid parse trees for same input

**Example**:
```ebnf
// ❌ AMBIGUOUS GRAMMAR
term: WORD+
WORD: /\w+/
FIELD_NAME: /\w+/  // Conflict with WORD!
```

**Solution**: Use lookahead in FIELD_NAME
```ebnf
// ✅ UNAMBIGUOUS GRAMMAR
FIELD_NAME: /[a-zA-Z_][a-zA-Z0-9_]*(?=:)/  // Lookahead assertion
WORD: /[^\s"()]+/
```

---

### Pitfall 2: Incorrect Operator Precedence

**Problem**: `A OR B AND C` parses as `(A OR B) AND C` instead of `A OR (B AND C)`

**Solution**: Define precedence in grammar rules (order matters!)
```ebnf
// ✅ CORRECT PRECEDENCE
?query: or_expr           // OR (lowest)

?or_expr: and_expr
        | or_expr "OR" and_expr

?and_expr: not_expr       // AND (medium)
         | and_expr "AND" not_expr

?not_expr: "NOT" not_expr  // NOT (highest)
         | atom
```

---

### Pitfall 3: Not Flattening Nested Operators

**Problem**: Deeply nested bool queries instead of flat arrays

**Bad**:
```python
# ❌ Deeply nested (hard to read, slow)
{
    "bool": {
        "must": [
            {"bool": {"must": [A, B]}},
            C
        ]
    }
}
```

**Good**:
```python
# ✅ Flattened (readable, faster)
{
    "bool": {
        "must": [A, B, C]
    }
}
```

**Solution**: Flatten in transformer
```python
def and_op(self, items):
    left, right = items

    must_clauses = []

    # Flatten left
    if isinstance(left, dict) and "bool" in left and "must" in left["bool"]:
        must_clauses.extend(left["bool"]["must"])  # Flatten!
    else:
        must_clauses.append(left)

    # Flatten right
    if isinstance(right, dict) and "bool" in right and "must" in right["bool"]:
        must_clauses.extend(right["bool"]["must"])  # Flatten!
    else:
        must_clauses.append(right)

    return {"bool": {"must": must_clauses}}
```

---

## Performance Considerations

### 1. Parser Choice: LALR vs Earley

**LALR** (fast, deterministic):
```python
parser = Lark(grammar, parser='lalr')  # ✅ Use for Sprint 3
```

**Earley** (slower, handles ambiguous grammars):
```python
parser = Lark(grammar, parser='earley')  # Only if grammar is ambiguous
```

**Sprint 3**: Use LALR (our grammar is unambiguous, performance matters)

### 2. Cache Parser Instance

**Slow** (recreates parser every time):
```python
def parse(query):
    parser = Lark(grammar, parser='lalr')  # ❌ Slow!
    return parser.parse(query)
```

**Fast** (reuse parser):
```python
class QueryParser:
    def __init__(self):
        self.parser = Lark(grammar, parser='lalr')  # ✅ Create once

    def parse(self, query):
        return self.parser.parse(query)  # Reuse
```

### 3. Transform In-Place

**Slow** (deep copy):
```python
import copy
def transform(tree):
    return transformer.transform(copy.deepcopy(tree))  # ❌ Unnecessary copy
```

**Fast** (in-place):
```python
def transform(tree):
    return transformer.transform(tree)  # ✅ In-place
```

---

## References

- **Lark Documentation**: https://lark-parser.readthedocs.io/
- **EBNF Tutorial**: https://lark-parser.readthedocs.io/en/latest/grammar.html
- **Parse Tree Transformers**: https://lark-parser.readthedocs.io/en/latest/visitors.html
- **Sprint 3 Tasks**: `.specify/tasks/sprint-3-full-text-search-tasks.md` (Tasks 2.6-2.7)
- **Sprint 3 Plan**: `.specify/plans/sprint-3-full-text-search-plan.md`

---

**Questions?** Refer to Lark documentation or Sprint 3 specifications.
