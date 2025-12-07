#!/usr/bin/env python3
"""
Direct test runner for proximity search tests.
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


def test_simple_near_operator():
    """Test basic NEAR operator with default proximity."""
    query = SearchQueryBuilder.build_proximity_query("diabetes NEAR complications")

    assert "query" in query
    assert "span_near" in query["query"]
    assert query["query"]["span_near"]["slop"] == 5  # Default proximity
    assert len(query["query"]["span_near"]["clauses"]) == 2
    print("[PASS] Simple NEAR operator test passed")


def test_near_with_specific_distance():
    """Test NEAR operator with specific distance."""
    query = SearchQueryBuilder.build_proximity_query("heart NEAR/3 failure")

    assert "query" in query
    assert "span_near" in query["query"]
    assert query["query"]["span_near"]["slop"] == 3
    assert query["query"]["span_near"]["clauses"][0]["span_term"]["_all"] == "heart"
    assert query["query"]["span_near"]["clauses"][1]["span_term"]["_all"] == "failure"
    print("[PASS] NEAR with specific distance test passed")


def test_within_operator():
    """Test W/n operator (alternative syntax)."""
    query = SearchQueryBuilder.build_proximity_query("blood W/2 pressure")

    assert "query" in query
    assert "span_near" in query["query"]
    assert query["query"]["span_near"]["slop"] == 2
    print("[PASS] W/n operator test passed")


def test_adjacent_operator():
    """Test ADJ operator for adjacent terms."""
    query = SearchQueryBuilder.build_proximity_query("myocardial ADJ infarction")

    assert "query" in query
    assert "span_near" in query["query"]
    assert query["query"]["span_near"]["slop"] == 1
    print("[PASS] ADJ operator test passed")


def test_multiple_proximity_operators():
    """Test multiple proximity operators in one query."""
    query = SearchQueryBuilder.build_proximity_query(
        "diabetes NEAR/3 mellitus heart NEAR/2 disease"
    )

    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]
    # Should have 2 proximity clauses
    proximity_count = sum(1 for clause in query["query"]["bool"]["must"]
                         if "span_near" in clause)
    assert proximity_count == 2
    print("[PASS] Multiple proximity operators test passed")


def test_phrase_slop_syntax():
    """Test phrase with slop syntax."""
    query = SearchQueryBuilder.build_proximity_query('"heart failure"~3')

    assert "query" in query
    assert "match_phrase" in query["query"]
    assert query["query"]["match_phrase"]["_all"]["slop"] == 3
    print("[PASS] Phrase slop syntax test passed")


def test_mixed_proximity_and_regular_terms():
    """Test proximity operators mixed with regular terms."""
    query = SearchQueryBuilder.build_proximity_query(
        "patient diabetes NEAR/2 complications severe"
    )

    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]
    # Should have proximity clause and regular match clause
    has_proximity = any("span_near" in clause for clause in query["query"]["bool"]["must"])
    has_match = any("match" in clause for clause in query["query"]["bool"]["must"])
    assert has_proximity and has_match
    print("[PASS] Mixed proximity and regular terms test passed")


def test_case_insensitive_operators():
    """Test that proximity operators are case-insensitive."""
    queries = [
        "diabetes near complications",
        "diabetes NEAR complications",
        "diabetes Near complications"
    ]

    for query_text in queries:
        query = SearchQueryBuilder.build_proximity_query(query_text)
        assert "span_near" in query["query"]
    print("[PASS] Case-insensitive operators test passed")


def test_within_alternative_syntax():
    """Test WITHIN/n operator."""
    query = SearchQueryBuilder.build_proximity_query("diabetes WITHIN/4 complications")

    assert "query" in query
    assert "span_near" in query["query"]
    assert query["query"]["span_near"]["slop"] == 4
    print("[PASS] WITHIN alternative syntax test passed")


def test_proximity_with_filters():
    """Test proximity search with additional filters."""
    query = SearchQueryBuilder.build_proximity_query(
        "diabetes NEAR/3 complications",
        filters={"document_type": "clinical_note", "department": "Endocrinology"}
    )

    assert "query" in query
    assert "bool" in query["query"]
    assert "filter" in query["query"]["bool"]
    assert len(query["query"]["bool"]["filter"]) == 2
    print("[PASS] Proximity with filters test passed")


def test_ordered_proximity():
    """Test that in_order is False by default (terms in any order)."""
    query = SearchQueryBuilder.build_proximity_query("diabetes NEAR/3 treatment")

    assert "query" in query
    assert "span_near" in query["query"]
    assert query["query"]["span_near"]["in_order"] is False
    print("[PASS] Ordered proximity test passed")


def test_empty_proximity_query():
    """Test handling of empty query."""
    query = SearchQueryBuilder.build_proximity_query("")

    assert "query" in query
    assert query["query"] == {"match_all": {}}
    print("[PASS] Empty proximity query test passed")


if __name__ == "__main__":
    print("Running Proximity Search Tests")
    print("=" * 50)

    try:
        test_simple_near_operator()
        test_near_with_specific_distance()
        test_within_operator()
        test_adjacent_operator()
        test_multiple_proximity_operators()
        test_phrase_slop_syntax()
        test_mixed_proximity_and_regular_terms()
        test_case_insensitive_operators()
        test_within_alternative_syntax()
        test_proximity_with_filters()
        test_ordered_proximity()
        test_empty_proximity_query()

        print("=" * 50)
        print("[SUCCESS] All proximity search tests passed!")
        print("\nProximity search implementation is working correctly.")

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