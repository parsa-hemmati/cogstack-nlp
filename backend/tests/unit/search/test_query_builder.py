"""
Unit tests for QueryBuilder class.

Tests query type detection and basic query building functionality.
"""
import pytest
from app.search.query_builder import QueryBuilder


class TestQueryTypeDetection:
    """Test query type detection methods."""

    def test_is_phrase_query_detects_quoted_strings(self):
        """Test that _is_phrase_query() detects quoted strings."""
        builder = QueryBuilder()

        # Single quoted phrase
        assert builder._is_phrase_query('"chest pain"') is True

        # Multiple quoted phrases
        assert builder._is_phrase_query('"diabetes" AND "hypertension"') is True

        # No quotes
        assert builder._is_phrase_query('diabetes hypertension') is False

        # Empty quotes
        assert builder._is_phrase_query('""') is False

    def test_is_boolean_query_detects_operators(self):
        """Test that _is_boolean_query() detects AND/OR/NOT keywords."""
        builder = QueryBuilder()

        # AND operator
        assert builder._is_boolean_query('diabetes AND hypertension') is True

        # OR operator
        assert builder._is_boolean_query('diabetes OR hypertension') is True

        # NOT operator
        assert builder._is_boolean_query('diabetes NOT insulin') is True

        # Multiple operators
        assert builder._is_boolean_query('diabetes AND (hypertension OR heart)') is True

        # No operators
        assert builder._is_boolean_query('diabetes hypertension') is False

        # Case-insensitive
        assert builder._is_boolean_query('diabetes and hypertension') is True

    def test_is_field_query_detects_field_syntax(self):
        """Test that _is_field_query() detects field:value syntax."""
        builder = QueryBuilder()

        # Single field query
        assert builder._is_field_query('title:diabetes') is True

        # Multiple field queries
        assert builder._is_field_query('title:diabetes author:smith') is True

        # Field with quoted value
        assert builder._is_field_query('title:"chest pain"') is True

        # No field syntax
        assert builder._is_field_query('diabetes') is False

        # Colon not followed by value
        assert builder._is_field_query('diabetes:') is False


class TestQueryBuilding:
    """Test query building functionality."""

    def test_build_query_returns_dict(self):
        """Test that build_query() returns a dictionary."""
        builder = QueryBuilder()
        query = builder.build_query("diabetes", filters=None, page=1, page_size=20, sort="relevance")

        assert isinstance(query, dict)
        assert "query" in query
        assert "from" in query
        assert "size" in query

    def test_build_query_handles_simple_keyword(self):
        """Test that build_query() handles simple keyword queries."""
        builder = QueryBuilder()
        query = builder.build_query("diabetes", filters=None, page=1, page_size=20, sort="relevance")

        # Should contain multi_match query for simple keyword
        assert "query" in query
        assert "bool" in query["query"] or "multi_match" in query["query"]

    def test_build_query_handles_pagination(self):
        """Test that build_query() handles pagination correctly."""
        builder = QueryBuilder()

        # Page 1
        query = builder.build_query("diabetes", filters=None, page=1, page_size=20, sort="relevance")
        assert query["from"] == 0
        assert query["size"] == 20

        # Page 2
        query = builder.build_query("diabetes", filters=None, page=2, page_size=20, sort="relevance")
        assert query["from"] == 20
        assert query["size"] == 20

        # Custom page size
        query = builder.build_query("diabetes", filters=None, page=1, page_size=50, sort="relevance")
        assert query["from"] == 0
        assert query["size"] == 50

    def test_build_query_handles_sorting(self):
        """Test that build_query() handles sorting options."""
        builder = QueryBuilder()

        # Relevance sort (default - no sort key, uses _score)
        query = builder.build_query("diabetes", filters=None, page=1, page_size=20, sort="relevance")
        # Relevance sort should not add explicit sort (uses _score by default)
        # OR it may add {"_score": {"order": "desc"}}

        # Date sort
        query = builder.build_query("diabetes", filters=None, page=1, page_size=20, sort="date")
        assert "sort" in query

        # Title sort
        query = builder.build_query("diabetes", filters=None, page=1, page_size=20, sort="title")
        assert "sort" in query

    def test_build_query_handles_empty_query(self):
        """Test that build_query() handles empty query string."""
        builder = QueryBuilder()

        # Empty query should match all documents
        query = builder.build_query("", filters=None, page=1, page_size=20, sort="relevance")
        assert "query" in query
        # Should use match_all query
        assert "match_all" in query["query"] or "bool" in query["query"]

    def test_build_query_includes_filters(self):
        """Test that build_query() includes filters when provided."""
        builder = QueryBuilder()

        filters = {
            "document_types": ["clinical_note"],
            "authors": ["Dr. Smith"]
        }

        query = builder.build_query("diabetes", filters=filters, page=1, page_size=20, sort="relevance")

        # Should include filter clauses
        assert "query" in query
        assert "bool" in query["query"]
        # Filter clauses should be in must or filter array
        bool_query = query["query"]["bool"]
        assert "filter" in bool_query or "must" in bool_query


class TestQueryBuilderEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_special_characters(self):
        """Test that QueryBuilder handles special characters in queries."""
        builder = QueryBuilder()

        # Special characters that might break Elasticsearch
        query = builder.build_query('diabetes & hypertension', filters=None, page=1, page_size=20, sort="relevance")
        assert isinstance(query, dict)

        query = builder.build_query('diabetes / hypertension', filters=None, page=1, page_size=20, sort="relevance")
        assert isinstance(query, dict)

    def test_handles_very_long_query(self):
        """Test that QueryBuilder handles very long query strings."""
        builder = QueryBuilder()

        long_query = "diabetes " * 100  # 100 words
        query = builder.build_query(long_query, filters=None, page=1, page_size=20, sort="relevance")
        assert isinstance(query, dict)

    def test_handles_unicode_characters(self):
        """Test that QueryBuilder handles Unicode characters."""
        builder = QueryBuilder()

        query = builder.build_query('diabète, hipertensión, 糖尿病', filters=None, page=1, page_size=20, sort="relevance")
        assert isinstance(query, dict)


class TestSimpleQueryBuilding:
    """Test simple keyword query building (Task 2.2)."""

    def test_build_simple_query_returns_bool_query(self):
        """Test that _build_simple_query() returns bool query with should clauses."""
        builder = QueryBuilder()
        result = builder._build_simple_query("diabetes")

        # Should return bool query structure
        assert "bool" in result
        assert "should" in result["bool"]
        assert isinstance(result["bool"]["should"], list)
        assert len(result["bool"]["should"]) >= 3  # title, content, author

    def test_build_simple_query_applies_field_boosting(self):
        """Test that _build_simple_query() applies correct field boosting."""
        builder = QueryBuilder()
        result = builder._build_simple_query("diabetes")

        should_clauses = result["bool"]["should"]

        # Find title, content, and author match clauses
        title_clause = next((c for c in should_clauses if "match" in c and "title" in c["match"]), None)
        content_clause = next((c for c in should_clauses if "match" in c and "content" in c["match"]), None)
        author_clause = next((c for c in should_clauses if "match" in c and "author" in c["match"]), None)

        # Verify all clauses exist
        assert title_clause is not None, "Title match clause not found"
        assert content_clause is not None, "Content match clause not found"
        assert author_clause is not None, "Author match clause not found"

        # Verify field boosting (title^10, content^1, author^2)
        assert title_clause["match"]["title"]["boost"] == 10
        assert content_clause["match"]["content"]["boost"] == 1
        assert author_clause["match"]["author"]["boost"] == 2

    def test_build_simple_query_sets_minimum_should_match(self):
        """Test that _build_simple_query() sets minimum_should_match=1."""
        builder = QueryBuilder()
        result = builder._build_simple_query("diabetes")

        # Should have minimum_should_match=1
        assert "bool" in result
        assert "minimum_should_match" in result["bool"]
        assert result["bool"]["minimum_should_match"] == 1

    def test_build_simple_query_with_multi_word_query(self):
        """Test that _build_simple_query() handles multi-word queries."""
        builder = QueryBuilder()
        result = builder._build_simple_query("diabetes mellitus type 2")

        # Should return bool query
        assert "bool" in result
        assert "should" in result["bool"]

        # Should contain the full query text
        should_clauses = result["bool"]["should"]
        for clause in should_clauses:
            if "match" in clause:
                for field, value in clause["match"].items():
                    assert value["query"] == "diabetes mellitus type 2"


class TestPhraseQueryBuilding:
    """Test phrase query building (Task 2.3)."""

    def test_build_phrase_query_extracts_single_phrase(self):
        """Test that _build_phrase_query() extracts single phrase from quotes."""
        builder = QueryBuilder()
        result = builder._build_phrase_query('"chest pain"')

        # Should return bool query with must clauses
        assert "bool" in result
        assert "must" in result["bool"]
        assert isinstance(result["bool"]["must"], list)
        assert len(result["bool"]["must"]) >= 1

        # Should contain multi_match with type=phrase
        must_clause = result["bool"]["must"][0]
        assert "multi_match" in must_clause
        assert must_clause["multi_match"]["type"] == "phrase"
        assert must_clause["multi_match"]["query"] == "chest pain"

    def test_build_phrase_query_extracts_multiple_phrases(self):
        """Test that _build_phrase_query() extracts multiple phrases (AND logic)."""
        builder = QueryBuilder()
        result = builder._build_phrase_query('"diabetes mellitus" AND "chest pain"')

        # Should return bool query with must clauses (AND logic)
        assert "bool" in result
        assert "must" in result["bool"]
        must_clauses = result["bool"]["must"]
        assert len(must_clauses) == 2

        # First phrase
        assert "multi_match" in must_clauses[0]
        assert must_clauses[0]["multi_match"]["query"] == "diabetes mellitus"
        assert must_clauses[0]["multi_match"]["type"] == "phrase"

        # Second phrase
        assert "multi_match" in must_clauses[1]
        assert must_clauses[1]["multi_match"]["query"] == "chest pain"
        assert must_clauses[1]["multi_match"]["type"] == "phrase"

    def test_build_phrase_query_searches_multiple_fields(self):
        """Test that _build_phrase_query() searches title and content fields."""
        builder = QueryBuilder()
        result = builder._build_phrase_query('"atrial flutter"')

        must_clause = result["bool"]["must"][0]
        # Should search both title and content fields
        assert "fields" in must_clause["multi_match"]
        fields = must_clause["multi_match"]["fields"]
        assert "title" in fields or "title^10" in fields
        assert "content" in fields or "content^1" in fields

    def test_build_phrase_query_with_empty_quotes(self):
        """Test that _build_phrase_query() handles empty quotes."""
        builder = QueryBuilder()
        result = builder._build_phrase_query('""')

        # Empty quotes should return empty must clauses
        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 0

    def test_build_phrase_query_mixed_with_text(self):
        """Test that _build_phrase_query() extracts only quoted phrases."""
        builder = QueryBuilder()
        result = builder._build_phrase_query('patient with "chest pain" and symptoms')

        # Should extract only "chest pain" phrase
        assert "bool" in result
        assert "must" in result["bool"]
        must_clauses = result["bool"]["must"]
        assert len(must_clauses) == 1
        assert must_clauses[0]["multi_match"]["query"] == "chest pain"


class TestBooleanQueryBuilding:
    """Test boolean query parsing (AND/OR/NOT operators)."""

    def test_build_boolean_query_with_and_operator(self):
        """Test AND operator creates must clauses."""
        builder = QueryBuilder()
        result = builder._build_boolean_query("diabetes AND hypertension")

        # Should create bool query with must clauses
        assert "bool" in result
        assert "must" in result["bool"]
        must_clauses = result["bool"]["must"]

        # Should have 2 must clauses (one for each term)
        assert len(must_clauses) == 2

        # Each clause should be a match query
        assert "match" in must_clauses[0] or "multi_match" in must_clauses[0]
        assert "match" in must_clauses[1] or "multi_match" in must_clauses[1]

        # Terms should be extracted correctly
        terms = [
            list(must_clauses[0].values())[0]["query"],
            list(must_clauses[1].values())[0]["query"]
        ]
        assert "diabetes" in terms
        assert "hypertension" in terms

    def test_build_boolean_query_with_or_operator(self):
        """Test OR operator creates should clauses."""
        builder = QueryBuilder()
        result = builder._build_boolean_query("diabetes OR hypertension")

        # Should create bool query with should clauses
        assert "bool" in result
        assert "should" in result["bool"]
        should_clauses = result["bool"]["should"]

        # Should have 2 should clauses (one for each term)
        assert len(should_clauses) == 2

        # Each clause should be a match query
        assert "match" in should_clauses[0] or "multi_match" in should_clauses[0]
        assert "match" in should_clauses[1] or "multi_match" in should_clauses[1]

        # Terms should be extracted correctly
        terms = [
            list(should_clauses[0].values())[0]["query"],
            list(should_clauses[1].values())[0]["query"]
        ]
        assert "diabetes" in terms
        assert "hypertension" in terms

    def test_build_boolean_query_with_not_operator(self):
        """Test NOT operator creates must + must_not clauses."""
        builder = QueryBuilder()
        result = builder._build_boolean_query("diabetes NOT type1")

        # Should create bool query with must and must_not clauses
        assert "bool" in result
        assert "must" in result["bool"]
        assert "must_not" in result["bool"]

        must_clauses = result["bool"]["must"]
        must_not_clauses = result["bool"]["must_not"]

        # Should have 1 must clause (positive term)
        assert len(must_clauses) == 1
        assert list(must_clauses[0].values())[0]["query"] == "diabetes"

        # Should have 1 must_not clause (negated term)
        assert len(must_not_clauses) == 1
        assert list(must_not_clauses[0].values())[0]["query"] == "type1"

    def test_build_boolean_query_with_multiple_operators(self):
        """Test multiple operators in single query."""
        builder = QueryBuilder()
        result = builder._build_boolean_query("diabetes AND hypertension OR medication")

        # Should create bool query
        assert "bool" in result

        # Should have both must and should clauses (AND has higher precedence)
        # Expected: (diabetes AND hypertension) OR medication
        # Result: bool with should clauses containing:
        #   1. bool with must [diabetes, hypertension]
        #   2. match medication
        assert "should" in result["bool"]
        should_clauses = result["bool"]["should"]
        assert len(should_clauses) >= 2

    def test_build_boolean_query_case_insensitive(self):
        """Test operators are case-insensitive."""
        builder = QueryBuilder()

        result_upper = builder._build_boolean_query("diabetes AND hypertension")
        result_lower = builder._build_boolean_query("diabetes and hypertension")
        result_mixed = builder._build_boolean_query("diabetes AnD hypertension")

        # All should produce bool queries with must clauses
        assert "bool" in result_upper and "must" in result_upper["bool"]
        assert "bool" in result_lower and "must" in result_lower["bool"]
        assert "bool" in result_mixed and "must" in result_mixed["bool"]

    def test_build_boolean_query_with_quoted_phrases(self):
        """Test boolean operators with quoted phrases."""
        builder = QueryBuilder()
        result = builder._build_boolean_query('"chest pain" AND diabetes')

        # Should create bool query with must clauses
        assert "bool" in result
        assert "must" in result["bool"]
        must_clauses = result["bool"]["must"]

        # Should have 2 must clauses
        assert len(must_clauses) == 2

        # One should be a phrase query for "chest pain"
        phrase_queries = [
            clause for clause in must_clauses
            if "multi_match" in clause and clause["multi_match"].get("type") == "phrase"
        ]
        assert len(phrase_queries) == 1
        assert phrase_queries[0]["multi_match"]["query"] == "chest pain"

    def test_build_boolean_query_preserves_field_boosting(self):
        """Test boolean queries preserve field boosting."""
        builder = QueryBuilder()
        result = builder._build_boolean_query("diabetes AND hypertension")

        # Should create bool query with must clauses
        assert "bool" in result
        assert "must" in result["bool"]
        must_clauses = result["bool"]["must"]

        # Each clause should search multiple fields with boosting
        for clause in must_clauses:
            if "multi_match" in clause:
                assert "fields" in clause["multi_match"]
                fields = clause["multi_match"]["fields"]
                # Should have title^10, content^1, etc.
                assert any("^" in field for field in fields)


class TestFieldQueryBuilding:
    """Test field-specific query parsing (field:value syntax)."""

    def test_build_field_query_single_text_field(self):
        """Test field:value syntax for text fields."""
        builder = QueryBuilder()
        result = builder._build_field_query('author:"Dr. Smith"')

        # Should create match query for author field
        assert "match" in result
        assert "author" in result["match"]
        assert result["match"]["author"]["query"] == "Dr. Smith"

    def test_build_field_query_keyword_field(self):
        """Test field:value syntax for keyword fields."""
        builder = QueryBuilder()
        result = builder._build_field_query('document_type:"clinical_note"')

        # Should create term query for keyword fields
        assert "term" in result
        assert "document_type" in result["term"]
        assert result["term"]["document_type"] == "clinical_note"

    def test_build_field_query_multiple_fields(self):
        """Test multiple field:value pairs with AND."""
        builder = QueryBuilder()
        result = builder._build_field_query('author:"Dr. Smith" AND document_type:"clinical_note"')

        # Should create bool query with must clauses
        assert "bool" in result
        assert "must" in result["bool"]
        must_clauses = result["bool"]["must"]
        assert len(must_clauses) == 2

        # Check for author match query
        author_queries = [c for c in must_clauses if "match" in c and "author" in c.get("match", {})]
        assert len(author_queries) == 1
        assert author_queries[0]["match"]["author"]["query"] == "Dr. Smith"

        # Check for document_type term query
        type_queries = [c for c in must_clauses if "term" in c and "document_type" in c.get("term", {})]
        assert len(type_queries) == 1
        assert type_queries[0]["term"]["document_type"] == "clinical_note"

    def test_build_field_query_unquoted_value(self):
        """Test field:value syntax without quotes."""
        builder = QueryBuilder()
        result = builder._build_field_query('author:Smith')

        # Should create match query for single-word value
        assert "match" in result
        assert "author" in result["match"]
        assert result["match"]["author"]["query"] == "Smith"

    def test_build_field_query_mixed_with_boolean(self):
        """Test field queries mixed with boolean operators."""
        builder = QueryBuilder()
        result = builder._build_field_query('author:"Dr. Smith" OR author:"Dr. Jones"')

        # Should create bool query with should clauses
        assert "bool" in result
        assert "should" in result["bool"]
        should_clauses = result["bool"]["should"]
        assert len(should_clauses) == 2

        # Check both author queries
        authors = [c["match"]["author"]["query"] for c in should_clauses if "match" in c and "author" in c.get("match", {})]
        assert "Dr. Smith" in authors
        assert "Dr. Jones" in authors

    def test_build_field_query_department_field(self):
        """Test department field (keyword field)."""
        builder = QueryBuilder()
        result = builder._build_field_query('department:Cardiology')

        # Should create term query for keyword field
        assert "term" in result
        assert "department" in result["term"]
        assert result["term"]["department"] == "Cardiology"


class TestQueryParserIntegration:
    """Test QueryParser integration with QueryBuilder."""

    def test_build_boolean_query_with_parentheses(self):
        """Test complex nested query with parentheses uses QueryParser."""
        builder = QueryBuilder()
        result = builder._build_boolean_query('(diabetes OR hypertension) AND medication')

        # Should create nested bool query
        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 2

        # First must clause should be OR of diabetes/hypertension
        first_must = result["bool"]["must"][0]
        assert "bool" in first_must
        assert "should" in first_must["bool"]
        assert len(first_must["bool"]["should"]) == 2

        # Second must clause should be medication
        second_must = result["bool"]["must"][1]
        assert "multi_match" in second_must
        assert second_must["multi_match"]["query"] == "medication"

    def test_build_boolean_query_complex_nested(self):
        """Test highly complex nested query."""
        builder = QueryBuilder()
        result = builder._build_boolean_query('((diabetes AND hypertension) OR medication) NOT insulin')

        # Should create nested bool query with must_not
        assert "bool" in result
        # Complex structure with nested boolean logic

    def test_build_boolean_query_fallback_on_parse_error(self):
        """Test fallback to simple query on parse error."""
        builder = QueryBuilder()

        # Query with unmatched parenthesis (should fail to parse)
        result = builder._build_boolean_query('(diabetes AND hypertension')

        # Should fall back to simple multi_match query
        assert "multi_match" in result
        assert result["multi_match"]["query"] == '(diabetes AND hypertension'

    def test_build_boolean_query_field_queries(self):
        """Test QueryParser handles field queries in boolean context."""
        builder = QueryBuilder()
        result = builder._build_boolean_query('author:"Dr. Smith" AND document_type:clinical_note')

        # Should create bool query with must clauses
        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 2

        # Check for match query (text field) and term query (keyword field)
        has_match = any("match" in clause for clause in result["bool"]["must"])
        has_term = any("term" in clause for clause in result["bool"]["must"])
        assert has_match and has_term

    def test_existing_boolean_tests_still_pass(self):
        """Verify existing boolean query tests still work with QueryParser."""
        builder = QueryBuilder()

        # Test simple AND
        and_result = builder._build_boolean_query('diabetes AND hypertension')
        assert "bool" in and_result
        assert "must" in and_result["bool"]
        assert len(and_result["bool"]["must"]) == 2

        # Test simple OR
        or_result = builder._build_boolean_query('diabetes OR hypertension')
        assert "bool" in or_result
        assert "should" in or_result["bool"]
        assert len(or_result["bool"]["should"]) == 2

        # Test simple NOT
        not_result = builder._build_boolean_query('diabetes NOT type1')
        assert "bool" in not_result
