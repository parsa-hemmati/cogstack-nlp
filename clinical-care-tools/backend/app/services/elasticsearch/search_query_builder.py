"""Elasticsearch query builder for multi-field search.

Builds complex Elasticsearch queries with:
- Multi-field matching (title, content, author)
- Field boosting for relevance ranking
- Filters (document type, date range, department, author)
- Fuzzy matching for typo tolerance
- Aggregations for faceting
- Highlighting configuration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class SearchQueryBuilder:
    """Builder for Elasticsearch search queries."""

    @staticmethod
    def build_query(
        query_text: str,
        fields: Optional[List[str]] = None,
        document_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        department: Optional[str] = None,
        author: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_aggregations: bool = True,
        include_highlighting: bool = True
    ) -> Dict[str, Any]:
        """
        Build Elasticsearch query DSL for multi-field search.

        Args:
            query_text: Search query string
            fields: Fields to search (default: ["title", "content", "author"])
            document_type: Filter by document type
            date_from: Filter by date range start (ISO format)
            date_to: Filter by date range end (ISO format)
            department: Filter by department
            author: Filter by author name
            page: Page number (1-indexed)
            page_size: Results per page
            include_aggregations: Include facet aggregations
            include_highlighting: Include result highlighting

        Returns:
            Elasticsearch query DSL dictionary
        """
        # Default fields with boosting
        if fields is None:
            fields = [
                "title^3",      # Boost title matches 3x
                "content^1",    # Content at normal weight
                "author^2"      # Boost author matches 2x
            ]

        # Build multi-match query
        multi_match = {
            "multi_match": {
                "query": query_text,
                "fields": fields,
                "type": "best_fields",
                "fuzziness": "AUTO",  # Handle typos
                "operator": "or"
            }
        }

        # Build filters
        filters = []

        if document_type:
            filters.append({"term": {"document_type": document_type}})

        if date_from or date_to:
            date_filter = {"range": {"date": {}}}
            if date_from:
                date_filter["range"]["date"]["gte"] = date_from
            if date_to:
                date_filter["range"]["date"]["lte"] = date_to
            filters.append(date_filter)

        if department:
            filters.append({"term": {"department": department}})

        if author:
            filters.append({"match": {"author": author}})

        # Build bool query
        bool_query = {
            "must": [multi_match]
        }

        if filters:
            bool_query["filter"] = filters

        # Build complete query
        es_query: Dict[str, Any] = {
            "query": {"bool": bool_query}
        }

        # Add aggregations for faceting
        if include_aggregations:
            es_query["aggs"] = SearchQueryBuilder._build_aggregations()

        # Add highlighting
        if include_highlighting:
            es_query["highlight"] = SearchQueryBuilder._build_highlighting()

        return es_query

    @staticmethod
    def _build_aggregations() -> Dict[str, Any]:
        """
        Build facet aggregations.

        Returns:
            Aggregations for document_type, department, date_histogram
        """
        return {
            "document_type": {
                "terms": {
                    "field": "document_type",
                    "size": 20
                }
            },
            "department": {
                "terms": {
                    "field": "department",
                    "size": 20
                }
            },
            "date_histogram": {
                "date_histogram": {
                    "field": "date",
                    "calendar_interval": "month",
                    "format": "yyyy-MM"
                }
            }
        }

    @staticmethod
    def _build_highlighting() -> Dict[str, Any]:
        """
        Build highlighting configuration.

        Returns:
            Highlighting config for title and content fields
        """
        return {
            "fields": {
                "title": {
                    "number_of_fragments": 0  # Return full title
                },
                "content": {
                    "fragment_size": 150,
                    "number_of_fragments": 3,
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"]
                }
            }
        }

    @staticmethod
    def build_suggest_query(
        partial_query: str,
        size: int = 5
    ) -> Dict[str, Any]:
        """
        Build query for autocomplete suggestions.

        Args:
            partial_query: Partial search query
            size: Maximum suggestions to return

        Returns:
            Elasticsearch suggest query
        """
        return {
            "suggest": {
                "text": partial_query,
                "simple_phrase": {
                    "phrase": {
                        "field": "content",
                        "size": size,
                        "gram_size": 3,
                        "direct_generator": [{
                            "field": "content",
                            "suggest_mode": "always",
                            "min_word_length": 2
                        }]
                    }
                }
            }
        }
