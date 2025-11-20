#!/usr/bin/env python3
"""
Direct test runner for regular expression query tests.
"""

import sys
import os

# Add the specific module directory to the path
module_path = os.path.join(os.path.dirname(__file__), 'app', 'services', 'elasticsearch')
sys.path.insert(0, module_path)

# Import directly from the module file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "search_query_builder",
    os.path.join(module_path, "search_query_builder.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SearchQueryBuilder = module.SearchQueryBuilder


def test_basic_regex_pattern():
    """Test basic regex pattern."""
    query = SearchQueryBuilder.build_regex_query("/diabet.*/")

    assert "query" in query
    assert "regexp" in query["query"]
    assert "_all" in query["query"]["regexp"]
    assert query["query"]["regexp"]["_all"]["value"] == "diabet.*"
    print("[PASS] Basic regex pattern test passed")


def test_field_specific_regex():
    """Test field-specific regex pattern."""
    query = SearchQueryBuilder.build_regex_query("diagnosis:/heart.+failure/")

    assert "query" in query
    assert "regexp" in query["query"]
    assert "diagnosis" in query["query"]["regexp"]
    assert query["query"]["regexp"]["diagnosis"]["value"] == "heart.+failure"
    print("[PASS] Field-specific regex test passed")


def test_regex_with_flags():
    """Test regex pattern with flags."""
    query = SearchQueryBuilder.build_regex_query("/diabet.*/i")

    assert "query" in query
    assert "regexp" in query["query"]
    assert "flags" in query["query"]["regexp"]["_all"]
    assert "CASE_INSENSITIVE" in query["query"]["regexp"]["_all"]["flags"]
    print("[PASS] Regex with flags test passed")


def test_complex_regex_pattern():
    """Test complex regex pattern with groups."""
    query = SearchQueryBuilder.build_regex_query("/heart.+(failure|disease|attack)/")

    assert "query" in query
    assert "regexp" in query["query"]
    assert query["query"]["regexp"]["_all"]["value"] == "heart.+(failure|disease|attack)"
    print("[PASS] Complex regex pattern test passed")


def test_regex_with_anchors():
    """Test regex with start and end anchors."""
    query = SearchQueryBuilder.build_regex_query("name:/^Smith.*/")

    assert "query" in query
    assert "regexp" in query["query"]
    assert query["query"]["regexp"]["name"]["value"] == "^Smith.*"
    print("[PASS] Regex with anchors test passed")


def test_character_class_regex():
    """Test regex with character classes."""
    query = SearchQueryBuilder.build_regex_query("/[Cc]ardio.*/")

    assert "query" in query
    assert "regexp" in query["query"]
    assert query["query"]["regexp"]["_all"]["value"] == "[Cc]ardio.*"
    print("[PASS] Character class regex test passed")


def test_multiple_regex_with_and():
    """Test multiple regex patterns with AND operator."""
    query = SearchQueryBuilder.build_regex_query("/diabet.*/ AND /complic.*/")

    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]
    assert len(query["query"]["bool"]["must"]) == 2
    print("[PASS] Multiple regex with AND test passed")


def test_multiple_regex_with_or():
    """Test multiple regex patterns with OR operator."""
    query = SearchQueryBuilder.build_regex_query("/diabet.*/ OR /hyperten.*/")

    assert "query" in query
    assert "bool" in query["query"]
    assert "should" in query["query"]["bool"]
    assert len(query["query"]["bool"]["should"]) == 2
    print("[PASS] Multiple regex with OR test passed")


def test_regex_with_regular_terms():
    """Test regex mixed with regular search terms."""
    query = SearchQueryBuilder.build_regex_query("/diabet.*/ AND patient")

    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]
    # Should have regex and match clauses
    has_regexp = any("regexp" in clause for clause in query["query"]["bool"]["must"])
    has_match = any("match" in clause for clause in query["query"]["bool"]["must"])
    assert has_regexp and has_match
    print("[PASS] Regex with regular terms test passed")


def test_regex_with_filters():
    """Test regex query with additional filters."""
    query = SearchQueryBuilder.build_regex_query(
        "/diabet.*/",
        filters={"document_type": "clinical_note", "department": "Endocrinology"}
    )

    assert "query" in query
    assert "bool" in query["query"]
    assert "filter" in query["query"]["bool"]
    assert len(query["query"]["bool"]["filter"]) == 2
    print("[PASS] Regex with filters test passed")


def test_multiple_flags():
    """Test regex with multiple flags."""
    query = SearchQueryBuilder.build_regex_query("/pattern/im")

    assert "query" in query
    assert "regexp" in query["query"]
    assert "flags" in query["query"]["regexp"]["_all"]
    flags = query["query"]["regexp"]["_all"]["flags"]
    assert "CASE_INSENSITIVE" in flags
    assert "MULTILINE" in flags
    print("[PASS] Multiple flags test passed")


def test_empty_regex_query():
    """Test handling of empty query."""
    query = SearchQueryBuilder.build_regex_query("")

    assert "query" in query
    assert query["query"] == {"match_all": {}}
    print("[PASS] Empty regex query test passed")


if __name__ == "__main__":
    print("Running Regular Expression Query Tests")
    print("=" * 50)

    try:
        test_basic_regex_pattern()
        test_field_specific_regex()
        test_regex_with_flags()
        test_complex_regex_pattern()
        test_regex_with_anchors()
        test_character_class_regex()
        test_multiple_regex_with_and()
        test_multiple_regex_with_or()
        test_regex_with_regular_terms()
        test_regex_with_filters()
        test_multiple_flags()
        test_empty_regex_query()

        print("=" * 50)
        print("[SUCCESS] All regex query tests passed!")
        print("\nRegular expression query implementation is working correctly.")
        print("\n[WARNING] Regex queries can be expensive on large datasets.")
        print("Use with caution in production environments.")

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)