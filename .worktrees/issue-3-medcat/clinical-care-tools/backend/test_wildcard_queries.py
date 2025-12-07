#!/usr/bin/env python3
"""
Direct test runner for wildcard query parsing tests.
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


def test_single_wildcard_asterisk():
    """Test single asterisk wildcard query."""
    query = SearchQueryBuilder.build_wildcard_query("diabet*")

    assert "query" in query
    assert "wildcard" in query["query"]
    assert query["query"]["wildcard"]["_all"]["value"] == "diabet*"
    print("[PASS] Single asterisk wildcard test passed")


def test_single_wildcard_question():
    """Test single question mark wildcard query."""
    query = SearchQueryBuilder.build_wildcard_query("diabet?s")

    assert "query" in query
    assert "wildcard" in query["query"]
    assert query["query"]["wildcard"]["_all"]["value"] == "diabet?s"
    print("[PASS] Single question mark wildcard test passed")


def test_multiple_wildcards():
    """Test query with multiple wildcards."""
    query = SearchQueryBuilder.build_wildcard_query("*cardia* OR hyper*")

    assert "query" in query
    assert "bool" in query["query"]
    should_clauses = query["query"]["bool"]["should"]
    assert len(should_clauses) == 2
    assert should_clauses[0]["wildcard"]["_all"]["value"] == "*cardia*"
    assert should_clauses[1]["wildcard"]["_all"]["value"] == "hyper*"
    print("[PASS] Multiple wildcards test passed")


def test_wildcard_with_boolean_operators():
    """Test wildcard queries with Boolean operators."""
    query = SearchQueryBuilder.build_wildcard_query("diabet* AND complicat*")

    assert "query" in query
    assert "bool" in query["query"]
    must_clauses = query["query"]["bool"]["must"]
    assert len(must_clauses) == 2
    assert must_clauses[0]["wildcard"]["_all"]["value"] == "diabet*"
    assert must_clauses[1]["wildcard"]["_all"]["value"] == "complicat*"
    print("[PASS] Wildcard with Boolean operators test passed")


def test_field_specific_wildcard():
    """Test field-specific wildcard query."""
    query = SearchQueryBuilder.build_wildcard_query("title:cardio* AND content:*tension")

    assert "query" in query
    must_clauses = query["query"]["bool"]["must"]
    assert must_clauses[0]["wildcard"]["title"]["value"] == "cardio*"
    assert must_clauses[1]["wildcard"]["content"]["value"] == "*tension"
    print("[PASS] Field-specific wildcard test passed")


def test_wildcard_phrase_protection():
    """Test that wildcards inside quotes are treated as literals."""
    query = SearchQueryBuilder.build_wildcard_query('"heart * disease"')

    assert "query" in query
    # Should be a phrase match, not wildcard
    assert "match_phrase" in query["query"]
    assert query["query"]["match_phrase"]["_all"] == "heart * disease"
    print("[PASS] Wildcard phrase protection test passed")


def test_escape_special_characters():
    """Test escaping special characters in wildcard queries."""
    query = SearchQueryBuilder.build_wildcard_query(r"test\*literal")

    assert "query" in query
    # Escaped asterisk should be treated as literal
    assert "match" in query["query"]
    assert query["query"]["match"]["_all"] == "test*literal"
    print("[PASS] Escape special characters test passed")


def test_empty_wildcard_query():
    """Test handling of empty wildcard query."""
    query = SearchQueryBuilder.build_wildcard_query("")

    assert "query" in query
    assert query["query"]["match_all"] == {}
    print("[PASS] Empty wildcard query test passed")


def test_wildcard_performance_warning():
    """Test that leading wildcards generate performance warnings."""
    query, warnings = SearchQueryBuilder.build_wildcard_query("*diabetes", return_warnings=True)

    assert "query" in query
    assert warnings is not None
    assert len(warnings) > 0
    assert "leading wildcard" in warnings[0].lower()
    print("[PASS] Wildcard performance warning test passed")


def test_wildcard_with_filters():
    """Test wildcard query with additional filters."""
    query = SearchQueryBuilder.build_wildcard_query(
        "diabet*",
        filters={
            "document_type": "progress_note",
            "department": "Endocrinology"
        }
    )

    assert "query" in query
    bool_query = query["query"]["bool"]
    assert "must" in bool_query
    assert "filter" in bool_query
    assert len(bool_query["filter"]) == 2
    print("[PASS] Wildcard with filters test passed")


if __name__ == "__main__":
    print("Running Wildcard Query Tests")
    print("=" * 50)

    try:
        test_single_wildcard_asterisk()
        test_single_wildcard_question()
        test_multiple_wildcards()
        test_wildcard_with_boolean_operators()
        test_field_specific_wildcard()
        test_wildcard_phrase_protection()
        test_escape_special_characters()
        test_empty_wildcard_query()
        test_wildcard_performance_warning()
        test_wildcard_with_filters()

        print("=" * 50)
        print("[SUCCESS] All wildcard query tests passed!")
        print("\nWildcard query implementation is working correctly.")

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)