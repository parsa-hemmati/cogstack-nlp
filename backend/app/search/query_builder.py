"""
QueryBuilder for constructing Elasticsearch queries.

Handles query parsing, type detection, and DSL generation.
"""
import re
from typing import Dict, List, Optional


class QueryBuilder:
    """
    Constructs Elasticsearch queries from user search input.

    Supports multiple query types:
    - Simple keyword search (multi_match)
    - Phrase search ("exact phrase")
    - Boolean queries (AND, OR, NOT)
    - Field-specific search (title:diabetes)
    """

    def __init__(self):
        """Initialize QueryBuilder."""
        pass

    def _is_phrase_query(self, query: str) -> bool:
        """
        Detect if query contains quoted phrases.

        Args:
            query: Search query string

        Returns:
            True if query contains non-empty quoted phrases

        Examples:
            >>> _is_phrase_query('"chest pain"')
            True
            >>> _is_phrase_query('diabetes')
            False
        """
        # Match double-quoted phrases with content
        pattern = r'"[^"]+"'
        matches = re.findall(pattern, query)

        # Check if matches have non-empty content
        return any(len(match.strip('"').strip()) > 0 for match in matches)

    def _is_boolean_query(self, query: str) -> bool:
        """
        Detect if query contains boolean operators (AND, OR, NOT).

        Case-insensitive detection.

        Args:
            query: Search query string

        Returns:
            True if query contains AND, OR, or NOT operators

        Examples:
            >>> _is_boolean_query('diabetes AND hypertension')
            True
            >>> _is_boolean_query('diabetes or hypertension')
            True
            >>> _is_boolean_query('diabetes NOT insulin')
            True
            >>> _is_boolean_query('diabetes hypertension')
            False
        """
        # Case-insensitive regex for AND, OR, NOT as whole words
        pattern = r'\b(AND|OR|NOT)\b'
        return bool(re.search(pattern, query, re.IGNORECASE))

    def _is_field_query(self, query: str) -> bool:
        """
        Detect if query contains field-specific search syntax.

        Field syntax: field:value or field:"value with spaces"

        Args:
            query: Search query string

        Returns:
            True if query contains field:value syntax

        Examples:
            >>> _is_field_query('title:diabetes')
            True
            >>> _is_field_query('title:"chest pain"')
            True
            >>> _is_field_query('diabetes')
            False
        """
        # Match field:value pattern (field must be non-empty, value must follow)
        pattern = r'\w+:\S+'
        return bool(re.search(pattern, query))

    def build_query(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "relevance"
    ) -> Dict:
        """
        Build Elasticsearch query DSL from user input.

        Args:
            query: User search query string
            filters: Optional filters (document_types, authors, etc.)
            page: Page number (1-indexed)
            page_size: Results per page
            sort: Sort order (relevance, date, title)

        Returns:
            Elasticsearch query DSL dictionary

        Examples:
            >>> build_query("diabetes", page=1, page_size=20)
            {
                "query": {"multi_match": {...}},
                "from": 0,
                "size": 20
            }
        """
        # Initialize query structure
        es_query = {
            "from": (page - 1) * page_size,
            "size": page_size
        }

        # Handle empty query (match all documents)
        if not query or not query.strip():
            es_query["query"] = {"match_all": {}}
        else:
            # Build query clause (simple keyword for now, will be enhanced in later tasks)
            es_query["query"] = self._build_simple_query(query)

        # Add filters if provided
        if filters:
            es_query["query"] = self._apply_filters(es_query["query"], filters)

        # Add sorting
        if sort != "relevance":
            es_query["sort"] = self._build_sort(sort)

        return es_query

    def _build_simple_query(self, query: str) -> Dict:
        """
        Build bool query with should clauses for simple keyword search.

        Uses individual match queries for each field with specific boosting.
        At least one field must match (minimum_should_match=1).

        Args:
            query: Search query string

        Returns:
            Elasticsearch bool query with should clauses

        Examples:
            >>> _build_simple_query("diabetes")
            {
                "bool": {
                    "should": [
                        {"match": {"title": {"query": "diabetes", "boost": 10}}},
                        {"match": {"content": {"query": "diabetes", "boost": 1}}},
                        {"match": {"author": {"query": "diabetes", "boost": 2}}}
                    ],
                    "minimum_should_match": 1
                }
            }
        """
        return {
            "bool": {
                "should": [
                    {
                        "match": {
                            "title": {
                                "query": query,
                                "boost": 10
                            }
                        }
                    },
                    {
                        "match": {
                            "content": {
                                "query": query,
                                "boost": 1
                            }
                        }
                    },
                    {
                        "match": {
                            "author": {
                                "query": query,
                                "boost": 2
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }

    def _apply_filters(self, query_clause: Dict, filters: Dict) -> Dict:
        """
        Apply filters to query using bool query.

        Args:
            query_clause: Existing query clause
            filters: Filter dict (document_types, authors, etc.)

        Returns:
            Bool query with filters applied
        """
        filter_clauses = []

        # Document type filter
        if filters.get("document_types"):
            filter_clauses.append({
                "terms": {"document_type": filters["document_types"]}
            })

        # Author filter
        if filters.get("authors"):
            filter_clauses.append({
                "terms": {"author": filters["authors"]}
            })

        # Department filter
        if filters.get("departments"):
            filter_clauses.append({
                "terms": {"department": filters["departments"]}
            })

        # Date range filter
        if filters.get("date_from") or filters.get("date_to"):
            range_filter = {"date": {}}
            if filters.get("date_from"):
                range_filter["date"]["gte"] = filters["date_from"]
            if filters.get("date_to"):
                range_filter["date"]["lte"] = filters["date_to"]
            filter_clauses.append({"range": range_filter})

        # Wrap in bool query
        if filter_clauses:
            return {
                "bool": {
                    "must": [query_clause],
                    "filter": filter_clauses
                }
            }

        return query_clause

    def _build_sort(self, sort: str) -> List[Dict]:
        """
        Build sort clause for Elasticsearch query.

        Args:
            sort: Sort option (date, title)

        Returns:
            Sort clause list

        Examples:
            >>> _build_sort("date")
            [{"date": {"order": "desc"}}]
        """
        if sort == "date":
            return [{"date": {"order": "desc"}}]
        elif sort == "title":
            return [{"title.raw": {"order": "asc"}}]
        else:
            # Default to relevance (no explicit sort, uses _score)
            return []
