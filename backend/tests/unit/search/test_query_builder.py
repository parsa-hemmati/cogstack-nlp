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
