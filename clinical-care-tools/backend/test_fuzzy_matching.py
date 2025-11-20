#!/usr/bin/env python3
"""
Direct test runner for fuzzy matching tests.
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


def test_simple_fuzzy_query():
    """Test basic fuzzy query with tilde operator."""
    query = SearchQueryBuilder.build_fuzzy_query("diabets~")

    assert "query" in query
    assert "fuzzy" in query["query"]
    assert query["query"]["fuzzy"]["_all"]["value"] == "diabets"
    assert query["query"]["fuzzy"]["_all"]["fuzziness"] == "AUTO"
    print("[PASS] Simple fuzzy query test passed")


def test_fuzzy_with_edit_distance():
    """Test fuzzy query with specific edit distance."""
    import sys
    sys.path.insert(0, module_path)

    # Let's trace through what's happening
    test_text = "diabets~2"

    # First, check what _extract_phrases_fuzzy returns
    phrases, modified_text = SearchQueryBuilder._extract_phrases_fuzzy(test_text)
    print(f"Debug: After extract_phrases: phrases={phrases}, modified_text='{modified_text}'")

    query = SearchQueryBuilder.build_fuzzy_query("diabets~2")

    import json
    print(f"Debug: Query structure: {json.dumps(query, indent=2)}")

    assert "query" in query
    assert "fuzzy" in query["query"]
    assert query["query"]["fuzzy"]["_all"]["value"] == "diabets"
    assert query["query"]["fuzzy"]["_all"]["fuzziness"] == 2
    print("[PASS] Fuzzy with edit distance test passed")


def test_fuzzy_with_boolean_operators():
    """Test fuzzy queries combined with Boolean operators."""
    query = SearchQueryBuilder.build_fuzzy_query("diabets~ AND hypertenshun~")

    assert "query" in query
    assert "bool" in query["query"]
    must_clauses = query["query"]["bool"]["must"]
    assert len(must_clauses) == 2
    assert must_clauses[0]["fuzzy"]["_all"]["value"] == "diabets"
    assert must_clauses[1]["fuzzy"]["_all"]["value"] == "hypertenshun"
    print("[PASS] Fuzzy with Boolean operators test passed")


def test_field_specific_fuzzy():
    """Test field-specific fuzzy matching."""
    query = SearchQueryBuilder.build_fuzzy_query("title:cardiak~ AND content:arythmia~2")

    assert "query" in query
    must_clauses = query["query"]["bool"]["must"]
    assert must_clauses[0]["fuzzy"]["title"]["value"] == "cardiak"
    assert must_clauses[0]["fuzzy"]["title"]["fuzziness"] == "AUTO"
    assert must_clauses[1]["fuzzy"]["content"]["value"] == "arythmia"
    assert must_clauses[1]["fuzzy"]["content"]["fuzziness"] == 2
    print("[PASS] Field-specific fuzzy test passed")


def test_fuzzy_phrase_query():
    """Test fuzzy matching on phrase queries."""
    query = SearchQueryBuilder.build_fuzzy_query('"heart failur"~2')

    assert "query" in query
    assert "match_phrase" in query["query"]
    assert query["query"]["match_phrase"]["_all"]["query"] == "heart failur"
    assert query["query"]["match_phrase"]["_all"]["slop"] == 2
    print("[PASS] Fuzzy phrase query test passed")


def test_mixed_fuzzy_and_exact():
    """Test mixing fuzzy and exact terms."""
    query = SearchQueryBuilder.build_fuzzy_query("diabets~ AND medication")

    assert "query" in query
    must_clauses = query["query"]["bool"]["must"]
    assert len(must_clauses) == 2
    assert "fuzzy" in must_clauses[0]
    assert "match" in must_clauses[1]
    print("[PASS] Mixed fuzzy and exact test passed")


def test_fuzzy_with_filters():
    """Test fuzzy query with additional filters."""
    query = SearchQueryBuilder.build_fuzzy_query(
        "diabets~",
        filters={
            "document_type": "clinical_note",
            "date_from": "2023-01-01"
        }
    )

    assert "query" in query
    bool_query = query["query"]["bool"]
    assert "must" in bool_query
    assert "filter" in bool_query
    assert len(bool_query["filter"]) == 2
    print("[PASS] Fuzzy with filters test passed")


def test_auto_fuzziness():
    """Test AUTO fuzziness based on term length."""
    query = SearchQueryBuilder.build_fuzzy_query("cat~")  # Short term
    assert query["query"]["fuzzy"]["_all"]["fuzziness"] == "AUTO"

    query = SearchQueryBuilder.build_fuzzy_query("medication~")  # Long term
    assert query["query"]["fuzzy"]["_all"]["fuzziness"] == "AUTO"
    print("[PASS] AUTO fuzziness test passed")


def test_fuzzy_with_transpositions():
    """Test fuzzy matching with transposition support."""
    query = SearchQueryBuilder.build_fuzzy_query("diabtes~", transpositions=True)

    assert "query" in query
    assert query["query"]["fuzzy"]["_all"]["transpositions"] is True
    print("[PASS] Fuzzy with transpositions test passed")


def test_fuzzy_prefix_length():
    """Test fuzzy matching with prefix length constraint."""
    query = SearchQueryBuilder.build_fuzzy_query("diabets~", prefix_length=3)

    assert "query" in query
    assert query["query"]["fuzzy"]["_all"]["prefix_length"] == 3
    print("[PASS] Fuzzy prefix length test passed")


def test_fuzzy_max_expansions():
    """Test limiting fuzzy expansions for performance."""
    query = SearchQueryBuilder.build_fuzzy_query("dia~", max_expansions=50)

    assert "query" in query
    assert query["query"]["fuzzy"]["_all"]["max_expansions"] == 50
    print("[PASS] Fuzzy max expansions test passed")


def test_invalid_fuzziness_handling():
    """Test handling of invalid fuzziness values."""
    query = SearchQueryBuilder.build_fuzzy_query("diabetes~5")  # Max is 2

    assert "query" in query
    # Should cap at maximum allowed value
    assert query["query"]["fuzzy"]["_all"]["fuzziness"] == 2
    print("[PASS] Invalid fuzziness handling test passed")


if __name__ == "__main__":
    print("Running Fuzzy Matching Tests")
    print("=" * 50)

    try:
        test_simple_fuzzy_query()
        test_fuzzy_with_edit_distance()
        test_fuzzy_with_boolean_operators()
        test_field_specific_fuzzy()
        test_fuzzy_phrase_query()
        test_mixed_fuzzy_and_exact()
        test_fuzzy_with_filters()
        test_auto_fuzziness()
        test_fuzzy_with_transpositions()
        test_fuzzy_prefix_length()
        test_fuzzy_max_expansions()
        test_invalid_fuzziness_handling()

        print("=" * 50)
        print("[SUCCESS] All fuzzy matching tests passed!")
        print("\nFuzzy matching implementation is working correctly.")

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