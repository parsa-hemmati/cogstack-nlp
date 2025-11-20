#!/usr/bin/env python3
"""
Direct test runner for range query tests.
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


def test_inclusive_range():
    """Test inclusive range with square brackets."""
    query = SearchQueryBuilder.build_range_query("age:[18 TO 65]")

    assert "query" in query
    assert "range" in query["query"]
    assert "age" in query["query"]["range"]
    assert query["query"]["range"]["age"]["gte"] == 18
    assert query["query"]["range"]["age"]["lte"] == 65
    print("[PASS] Inclusive range test passed")


def test_exclusive_range():
    """Test exclusive range with curly braces."""
    query = SearchQueryBuilder.build_range_query("lab_value:{0.5 TO 1.5}")

    assert "query" in query
    assert "range" in query["query"]
    assert "lab_value" in query["query"]["range"]
    assert query["query"]["range"]["lab_value"]["gt"] == 0.5
    assert query["query"]["range"]["lab_value"]["lt"] == 1.5
    print("[PASS] Exclusive range test passed")


def test_mixed_range():
    """Test mixed inclusive/exclusive range."""
    query = SearchQueryBuilder.build_range_query("score:[0 TO 100}")

    assert "query" in query
    assert "range" in query["query"]
    assert query["query"]["range"]["score"]["gte"] == 0
    assert query["query"]["range"]["score"]["lt"] == 100
    print("[PASS] Mixed range test passed")


def test_comparison_operators():
    """Test comparison operators (>, <, >=, <=)."""
    # Greater than
    query = SearchQueryBuilder.build_range_query("bp_systolic:>140")
    assert query["query"]["range"]["bp_systolic"]["gt"] == 140

    # Greater than or equal
    query = SearchQueryBuilder.build_range_query("age:>=18")
    assert query["query"]["range"]["age"]["gte"] == 18

    # Less than
    query = SearchQueryBuilder.build_range_query("temperature:<37")
    assert query["query"]["range"]["temperature"]["lt"] == 37

    # Less than or equal
    query = SearchQueryBuilder.build_range_query("heart_rate:<=100")
    assert query["query"]["range"]["heart_rate"]["lte"] == 100

    print("[PASS] Comparison operators test passed")


def test_date_range():
    """Test date range queries."""
    query = SearchQueryBuilder.build_range_query("date:[2023-01-01 TO 2023-12-31]")

    assert "query" in query
    assert "range" in query["query"]
    assert query["query"]["range"]["date"]["gte"] == "2023-01-01"
    assert query["query"]["range"]["date"]["lte"] == "2023-12-31"
    print("[PASS] Date range test passed")


def test_open_ended_range():
    """Test open-ended range with asterisk."""
    # From date to now
    query = SearchQueryBuilder.build_range_query("date:[2023-01-01 TO *]")
    assert "gte" in query["query"]["range"]["date"]
    assert "lte" not in query["query"]["range"]["date"]

    # From beginning to date
    query = SearchQueryBuilder.build_range_query("date:[* TO 2023-12-31]")
    assert "lte" in query["query"]["range"]["date"]
    assert "gte" not in query["query"]["range"]["date"]

    print("[PASS] Open-ended range test passed")


def test_multiple_ranges_with_boolean():
    """Test multiple range queries with Boolean operators."""
    query = SearchQueryBuilder.build_range_query(
        "bp_systolic:>140 OR bp_diastolic:>90"
    )

    assert "query" in query
    assert "bool" in query["query"]
    assert "should" in query["query"]["bool"]
    assert len(query["query"]["bool"]["should"]) == 2
    print("[PASS] Multiple ranges with Boolean test passed")


def test_range_with_regular_terms():
    """Test range queries mixed with regular terms."""
    # Test the parsing more directly
    test_query = "age:[18 TO 65] AND diagnosis:diabetes"
    print(f"Debug: Input query: {test_query}")

    query = SearchQueryBuilder.build_range_query(test_query)

    import json
    print(f"Debug: Query structure: {json.dumps(query, indent=2)}")

    assert "query" in query
    assert "bool" in query["query"]
    assert "must" in query["query"]["bool"]
    # Should have range query and match query
    has_range = any("range" in clause for clause in query["query"]["bool"]["must"])
    has_match = any("match" in clause for clause in query["query"]["bool"]["must"])
    assert has_range and has_match
    print("[PASS] Range with regular terms test passed")


def test_range_with_filters():
    """Test range query with additional filters."""
    query = SearchQueryBuilder.build_range_query(
        "age:[18 TO 65]",
        filters={"document_type": "patient_record", "department": "Cardiology"}
    )

    assert "query" in query
    assert "bool" in query["query"]
    assert "filter" in query["query"]["bool"]
    assert len(query["query"]["bool"]["filter"]) == 2
    print("[PASS] Range with filters test passed")


def test_float_values():
    """Test parsing of float values in ranges."""
    query = SearchQueryBuilder.build_range_query("glucose:[4.0 TO 7.0]")

    assert "query" in query
    assert query["query"]["range"]["glucose"]["gte"] == 4.0
    assert query["query"]["range"]["glucose"]["lte"] == 7.0
    assert isinstance(query["query"]["range"]["glucose"]["gte"], float)
    print("[PASS] Float values test passed")


def test_integer_values():
    """Test parsing of integer values in ranges."""
    query = SearchQueryBuilder.build_range_query("count:[10 TO 100]")

    assert "query" in query
    assert query["query"]["range"]["count"]["gte"] == 10
    assert query["query"]["range"]["count"]["lte"] == 100
    assert isinstance(query["query"]["range"]["count"]["gte"], int)
    print("[PASS] Integer values test passed")


def test_empty_range_query():
    """Test handling of empty query."""
    query = SearchQueryBuilder.build_range_query("")

    assert "query" in query
    assert query["query"] == {"match_all": {}}
    print("[PASS] Empty range query test passed")


if __name__ == "__main__":
    print("Running Range Query Tests")
    print("=" * 50)

    try:
        test_inclusive_range()
        test_exclusive_range()
        test_mixed_range()
        test_comparison_operators()
        test_date_range()
        test_open_ended_range()
        test_multiple_ranges_with_boolean()
        test_range_with_regular_terms()
        test_range_with_filters()
        test_float_values()
        test_integer_values()
        test_empty_range_query()

        print("=" * 50)
        print("[SUCCESS] All range query tests passed!")
        print("\nRange query implementation is working correctly.")

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