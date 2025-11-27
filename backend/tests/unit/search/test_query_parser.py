"""
Unit tests for QueryParser (Lark-based advanced query parsing).

Tests cover:
- Simple term queries
- AND/OR/NOT boolean operators
- Parenthesized grouping
- Field-specific queries
- Phrase queries
- Operator precedence
"""

import pytest
from lark.exceptions import LarkError

from app.search.query_parser import QueryParser


class TestQueryParserBasics:
    """Test basic query parsing functionality."""

    def test_parse_simple_term(self):
        """Test parsing single term query."""
        parser = QueryParser()
        result = parser.parse("diabetes")

        # Should return a multi_match query
        assert "multi_match" in result
        assert result["multi_match"]["query"] == "diabetes"
        assert "title^10" in result["multi_match"]["fields"]

    def test_parse_phrase(self):
        """Test parsing quoted phrase."""
        parser = QueryParser()
        result = parser.parse('"chest pain"')

        # Should return a phrase query
        assert "multi_match" in result
        assert result["multi_match"]["query"] == "chest pain"
        assert result["multi_match"]["type"] == "phrase"


class TestBooleanOperators:
    """Test boolean operator parsing."""

    def test_parse_and_query(self):
        """Test AND operator creates must clauses."""
        parser = QueryParser()
        result = parser.parse("diabetes AND hypertension")

        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 2

    def test_parse_or_query(self):
        """Test OR operator creates should clauses."""
        parser = QueryParser()
        result = parser.parse("diabetes OR hypertension")

        assert "bool" in result
        assert "should" in result["bool"]
        assert len(result["bool"]["should"]) == 2
        assert result["bool"]["minimum_should_match"] == 1

    def test_parse_not_query(self):
        """Test NOT operator creates must_not clauses."""
        parser = QueryParser()
        result = parser.parse("diabetes NOT type1")

        assert "bool" in result
        assert "must" in result["bool"]
        assert "must_not" in result["bool"]


class TestNestedQueries:
    """Test nested queries with parentheses."""

    def test_parse_nested_query(self):
        """Test parenthesized grouping with boolean operators."""
        parser = QueryParser()
        result = parser.parse("(diabetes OR hypertension) AND medication")

        # Should have AND at top level
        assert "bool" in result
        assert "must" in result["bool"]
        # First must clause should be OR of diabetes/hypertension
        # Second must clause should be medication

    def test_parse_complex_nested_query(self):
        """Test complex nested query with multiple levels."""
        parser = QueryParser()
        result = parser.parse("((diabetes AND hypertension) OR medication) NOT insulin")

        assert "bool" in result
        # Should have must and must_not at top level


class TestFieldQueries:
    """Test field-specific query parsing."""

    def test_parse_field_query_text_field(self):
        """Test field:value syntax for text fields."""
        parser = QueryParser()
        result = parser.parse('author:"Dr. Smith"')

        assert "match" in result
        assert "author" in result["match"]
        assert result["match"]["author"]["query"] == "Dr. Smith"

    def test_parse_field_query_keyword_field(self):
        """Test field:value syntax for keyword fields."""
        parser = QueryParser()
        result = parser.parse('document_type:clinical_note')

        assert "term" in result
        assert "document_type" in result["term"]

    def test_parse_field_query_with_boolean(self):
        """Test field queries combined with boolean operators."""
        parser = QueryParser()
        result = parser.parse('author:"Dr. Smith" AND document_type:clinical_note')

        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 2


class TestOperatorPrecedence:
    """Test operator precedence (NOT > AND > OR)."""

    def test_precedence_not_before_and(self):
        """Test NOT has higher precedence than AND."""
        parser = QueryParser()
        result = parser.parse("diabetes AND NOT type1 AND hypertension")

        # Should parse as: diabetes AND (NOT type1) AND hypertension
        assert "bool" in result
        assert "must" in result["bool"]
        assert "must_not" in result["bool"]

    def test_precedence_and_before_or(self):
        """Test AND has higher precedence than OR."""
        parser = QueryParser()
        result = parser.parse("diabetes AND hypertension OR medication")

        # Should parse as: (diabetes AND hypertension) OR medication
        assert "bool" in result
        assert "should" in result["bool"]


class TestErrorHandling:
    """Test error handling for invalid queries."""

    def test_parse_invalid_query(self):
        """Test invalid syntax raises LarkError."""
        parser = QueryParser()

        # Unmatched parenthesis
        with pytest.raises(LarkError):
            parser.parse("(diabetes AND hypertension")

    def test_parse_empty_query(self):
        """Test empty query returns None or match_all."""
        parser = QueryParser()
        result = parser.parse("")

        # Should return match_all or None
        assert result is None or result == {"match_all": {}}
