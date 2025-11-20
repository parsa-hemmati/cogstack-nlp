#!/usr/bin/env python3
"""
Direct test runner for Boolean query parsing tests.
This script runs the tests without requiring the full test infrastructure.
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


def test_simple_and_query():
    """Test parsing query with AND operator."""
    query = SearchQueryBuilder.build_boolean_query("diabetes AND hypertension")

    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]

    # Should have two must clauses
    must_clauses = query["query"]["bool"]["must"]
    assert len(must_clauses) == 2
    print("[PASS] Simple AND query test passed")


def test_simple_or_query():
    """Test parsing query with OR operator."""
    query = SearchQueryBuilder.build_boolean_query("diabetes OR hypertension")

    assert "query" in query
    assert "bool" in query["query"]
    assert "should" in query["query"]["bool"]
    assert query["query"]["bool"]["minimum_should_match"] == 1

    # Should have two should clauses
    should_clauses = query["query"]["bool"]["should"]
    assert len(should_clauses) == 2
    print("[PASS] Simple OR query test passed")


def test_simple_not_query():
    """Test parsing query with NOT operator."""
    query = SearchQueryBuilder.build_boolean_query("diabetes NOT family")

    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]
    assert "must_not" in query["query"]["bool"]

    # Should have one must and one must_not clause
    assert len(query["query"]["bool"]["must"]) == 1
    assert len(query["query"]["bool"]["must_not"]) == 1
    print("[PASS] Simple NOT query test passed")


def test_phrase_query():
    """Test parsing quoted phrase query."""
    query = SearchQueryBuilder.build_boolean_query('"heart failure" AND diabetes')

    assert "query" in query
    must_clauses = query["query"]["bool"]["must"]
    assert len(must_clauses) == 2

    # First clause should be a phrase match
    assert "match_phrase" in must_clauses[0]
    assert must_clauses[0]["match_phrase"]["_all"] == "heart failure"
    # Second clause should be a regular match
    assert must_clauses[1]["match"]["_all"] == "diabetes"
    print("[PASS] Phrase query test passed")


def test_case_insensitive_operators():
    """Test that Boolean operators are case-insensitive."""
    query1 = SearchQueryBuilder.build_boolean_query("diabetes AND hypertension")
    query2 = SearchQueryBuilder.build_boolean_query("diabetes and hypertension")
    query3 = SearchQueryBuilder.build_boolean_query("diabetes And hypertension")

    # All queries should produce the same structure
    assert query1 == query2
    assert query2 == query3
    print("[PASS] Case-insensitive operators test passed")


def test_handle_empty_query():
    """Test handling of empty query string."""
    query = SearchQueryBuilder.build_boolean_query("")

    assert "query" in query
    assert query["query"]["match_all"] == {}
    print("[PASS] Empty query handling test passed")


def test_handle_single_term():
    """Test handling of single term without operators."""
    query = SearchQueryBuilder.build_boolean_query("diabetes")

    assert "query" in query
    assert "match" in query["query"]
    assert query["query"]["match"]["_all"] == "diabetes"
    print("[PASS] Single term query test passed")


def test_multiple_not_operators():
    """Test handling multiple NOT operators."""
    query = SearchQueryBuilder.build_boolean_query("diabetes NOT family NOT history")

    assert "query" in query
    bool_query = query["query"]["bool"]

    assert len(bool_query["must"]) == 1
    assert bool_query["must"][0]["match"]["_all"] == "diabetes"

    assert len(bool_query["must_not"]) == 2
    assert bool_query["must_not"][0]["match"]["_all"] == "family"
    assert bool_query["must_not"][1]["match"]["_all"] == "history"
    print("[PASS] Multiple NOT operators test passed")


def test_field_specific_boolean_query():
    """Test Boolean operators with field-specific searches."""
    query = SearchQueryBuilder.build_boolean_query(
        "title:diabetes AND content:hypertension"
    )

    assert "query" in query
    must_clauses = query["query"]["bool"]["must"]

    assert len(must_clauses) == 2
    assert must_clauses[0]["match"]["title"] == "diabetes"
    assert must_clauses[1]["match"]["content"] == "hypertension"
    print("[PASS] Field-specific Boolean query test passed")


def test_integrate_with_filters():
    """Test Boolean query with additional filters."""
    query = SearchQueryBuilder.build_boolean_query(
        "diabetes AND hypertension",
        filters={
            "document_type": "discharge_summary",
            "department": "Cardiology"
        }
    )

    assert "query" in query
    bool_query = query["query"]["bool"]

    # Should have AND clauses
    assert len(bool_query["must"]) == 2

    # Should have filters
    assert "filter" in bool_query
    assert len(bool_query["filter"]) == 2
    print("[PASS] Boolean query with filters test passed")


def test_complex_boolean_combinations():
    """Test various complex Boolean combinations."""
    # Test multiple operators
    query1 = SearchQueryBuilder.build_boolean_query("diabetes AND hypertension OR copd")
    assert "query" in query1

    # Test with quoted phrases and operators
    query2 = SearchQueryBuilder.build_boolean_query('"type 2 diabetes" OR "type 1 diabetes"')
    assert "query" in query2

    # Test field-specific with NOT
    query3 = SearchQueryBuilder.build_boolean_query("title:diabetes NOT content:family")
    assert "query" in query3

    print("[PASS] Complex Boolean combinations test passed")


if __name__ == "__main__":
    print("Running Boolean Query Parsing Tests")
    print("=" * 50)

    try:
        test_simple_and_query()
        test_simple_or_query()
        test_simple_not_query()
        test_phrase_query()
        test_case_insensitive_operators()
        test_handle_empty_query()
        test_handle_single_term()
        test_multiple_not_operators()
        test_field_specific_boolean_query()
        test_integrate_with_filters()
        test_complex_boolean_combinations()

        print("=" * 50)
        print("[SUCCESS] All tests passed successfully!")
        print("\nBoolean query parsing implementation is working correctly.")

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)