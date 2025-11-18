"""Tests for SearchQueryBuilder.

Tests ensure:
- Multi-field query built correctly
- Field boosting applied
- Filters work (document_type, date range, department, author)
- Fuzziness enabled
- Aggregations included
- Highlighting configured
"""

import pytest
from app.services.elasticsearch.search_query_builder import SearchQueryBuilder


class TestQueryBuilding:
    """Test query construction."""

    def test_build_simple_query(self):
        """Test building simple search query."""
        query = SearchQueryBuilder.build_query(
            query_text="diabetes",
            include_aggregations=False,
            include_highlighting=False
        )

        assert "query" in query
        assert "bool" in query["query"]
        assert "must" in query["query"]["bool"]

        # Check multi_match query
        multi_match = query["query"]["bool"]["must"][0]["multi_match"]
        assert multi_match["query"] == "diabetes"
        assert multi_match["type"] == "best_fields"
        assert multi_match["fuzziness"] == "AUTO"

    def test_default_fields_with_boosting(self):
        """Test default fields include boosting."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=False,
            include_highlighting=False
        )

        fields = query["query"]["bool"]["must"][0]["multi_match"]["fields"]

        assert "title^3" in fields  # Title boosted 3x
        assert "content^1" in fields  # Content normal weight
        assert "author^2" in fields  # Author boosted 2x

    def test_custom_fields(self):
        """Test custom field list."""
        custom_fields = ["title^5", "content^1"]

        query = SearchQueryBuilder.build_query(
            query_text="test",
            fields=custom_fields,
            include_aggregations=False,
            include_highlighting=False
        )

        fields = query["query"]["bool"]["must"][0]["multi_match"]["fields"]

        assert fields == custom_fields


class TestFilters:
    """Test query filters."""

    def test_document_type_filter(self):
        """Test document type filter."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            document_type="discharge_summary",
            include_aggregations=False,
            include_highlighting=False
        )

        filters = query["query"]["bool"]["filter"]

        assert len(filters) == 1
        assert filters[0] == {"term": {"document_type": "discharge_summary"}}

    def test_date_range_filter(self):
        """Test date range filter."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            date_from="2023-01-01",
            date_to="2023-12-31",
            include_aggregations=False,
            include_highlighting=False
        )

        filters = query["query"]["bool"]["filter"]

        assert len(filters) == 1
        assert "range" in filters[0]
        assert filters[0]["range"]["date"]["gte"] == "2023-01-01"
        assert filters[0]["range"]["date"]["lte"] == "2023-12-31"

    def test_date_from_only(self):
        """Test date range with only start date."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            date_from="2023-01-01",
            include_aggregations=False,
            include_highlighting=False
        )

        filters = query["query"]["bool"]["filter"]

        assert len(filters) == 1
        assert "gte" in filters[0]["range"]["date"]
        assert "lte" not in filters[0]["range"]["date"]

    def test_department_filter(self):
        """Test department filter."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            department="Cardiology",
            include_aggregations=False,
            include_highlighting=False
        )

        filters = query["query"]["bool"]["filter"]

        assert len(filters) == 1
        assert filters[0] == {"term": {"department": "Cardiology"}}

    def test_author_filter(self):
        """Test author filter."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            author="Dr. Smith",
            include_aggregations=False,
            include_highlighting=False
        )

        filters = query["query"]["bool"]["filter"]

        assert len(filters) == 1
        assert filters[0] == {"match": {"author": "Dr. Smith"}}

    def test_multiple_filters(self):
        """Test combining multiple filters."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            document_type="discharge_summary",
            date_from="2023-01-01",
            department="Cardiology",
            include_aggregations=False,
            include_highlighting=False
        )

        filters = query["query"]["bool"]["filter"]

        assert len(filters) == 3

    def test_no_filters(self):
        """Test query without filters."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=False,
            include_highlighting=False
        )

        assert "filter" not in query["query"]["bool"]


class TestAggregations:
    """Test facet aggregations."""

    def test_aggregations_included(self):
        """Test aggregations included when requested."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=True,
            include_highlighting=False
        )

        assert "aggs" in query

        aggs = query["aggs"]
        assert "document_type" in aggs
        assert "department" in aggs
        assert "date_histogram" in aggs

    def test_document_type_aggregation(self):
        """Test document type aggregation structure."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=True,
            include_highlighting=False
        )

        doc_type_agg = query["aggs"]["document_type"]

        assert doc_type_agg["terms"]["field"] == "document_type"
        assert doc_type_agg["terms"]["size"] == 20

    def test_department_aggregation(self):
        """Test department aggregation structure."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=True,
            include_highlighting=False
        )

        dept_agg = query["aggs"]["department"]

        assert dept_agg["terms"]["field"] == "department"
        assert dept_agg["terms"]["size"] == 20

    def test_date_histogram_aggregation(self):
        """Test date histogram aggregation."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=True,
            include_highlighting=False
        )

        date_agg = query["aggs"]["date_histogram"]

        assert date_agg["date_histogram"]["field"] == "date"
        assert date_agg["date_histogram"]["calendar_interval"] == "month"
        assert date_agg["date_histogram"]["format"] == "yyyy-MM"

    def test_aggregations_excluded(self):
        """Test aggregations excluded when not requested."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=False,
            include_highlighting=False
        )

        assert "aggs" not in query


class TestHighlighting:
    """Test highlighting configuration."""

    def test_highlighting_included(self):
        """Test highlighting included when requested."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=False,
            include_highlighting=True
        )

        assert "highlight" in query
        assert "fields" in query["highlight"]

    def test_title_highlighting(self):
        """Test title field highlighting config."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=False,
            include_highlighting=True
        )

        title_config = query["highlight"]["fields"]["title"]

        # Title should return full text (no fragments)
        assert title_config["number_of_fragments"] == 0

    def test_content_highlighting(self):
        """Test content field highlighting config."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=False,
            include_highlighting=True
        )

        content_config = query["highlight"]["fields"]["content"]

        assert content_config["fragment_size"] == 150
        assert content_config["number_of_fragments"] == 3
        assert content_config["pre_tags"] == ["<em>"]
        assert content_config["post_tags"] == ["</em>"]

    def test_highlighting_excluded(self):
        """Test highlighting excluded when not requested."""
        query = SearchQueryBuilder.build_query(
            query_text="test",
            include_aggregations=False,
            include_highlighting=False
        )

        assert "highlight" not in query


class TestSuggestQuery:
    """Test autocomplete suggestion query."""

    def test_suggest_query_structure(self):
        """Test suggestion query structure."""
        query = SearchQueryBuilder.build_suggest_query("diab", size=5)

        assert "suggest" in query
        assert query["suggest"]["text"] == "diab"
        assert "simple_phrase" in query["suggest"]

    def test_suggest_query_parameters(self):
        """Test suggestion query parameters."""
        query = SearchQueryBuilder.build_suggest_query("test", size=10)

        phrase_config = query["suggest"]["simple_phrase"]["phrase"]

        assert phrase_config["field"] == "content"
        assert phrase_config["size"] == 10
        assert phrase_config["gram_size"] == 3

    def test_suggest_query_direct_generator(self):
        """Test suggestion direct generator config."""
        query = SearchQueryBuilder.build_suggest_query("test")

        direct_gen = query["suggest"]["simple_phrase"]["phrase"]["direct_generator"][0]

        assert direct_gen["field"] == "content"
        assert direct_gen["suggest_mode"] == "always"
        assert direct_gen["min_word_length"] == 2
