"""
QueryBuilder for constructing Elasticsearch queries.

Handles query parsing, type detection, and DSL generation.
"""
import re
from typing import Dict, List, Optional

from lark.exceptions import LarkError

from app.search.query_parser import QueryParser


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
        self.query_parser = QueryParser()

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

    def _build_phrase_query(self, query: str) -> Dict:
        """
        Build bool query with must clauses for phrase search.

        Extracts phrases from double quotes and creates multi_match queries
        with type=phrase for exact phrase matching. Multiple phrases use
        AND logic (all must match).

        Args:
            query: Search query string with quoted phrases

        Returns:
            Elasticsearch bool query with must clauses

        Examples:
            >>> _build_phrase_query('"chest pain"')
            {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": "chest pain",
                                "fields": ["title^10", "content^1"],
                                "type": "phrase"
                            }
                        }
                    ]
                }
            }

            >>> _build_phrase_query('"diabetes mellitus" AND "chest pain"')
            {
                "bool": {
                    "must": [
                        {"multi_match": {"query": "diabetes mellitus", "type": "phrase", ...}},
                        {"multi_match": {"query": "chest pain", "type": "phrase", ...}}
                    ]
                }
            }
        """
        # Extract phrases from double quotes
        phrase_pattern = r'"([^"]*)"'
        phrases = re.findall(phrase_pattern, query)

        # Filter out empty phrases
        phrases = [p.strip() for p in phrases if p.strip()]

        # Build must clauses for each phrase
        must_clauses = []
        for phrase in phrases:
            must_clauses.append({
                "multi_match": {
                    "query": phrase,
                    "fields": ["title^10", "content^1"],
                    "type": "phrase"
                }
            })

        return {
            "bool": {
                "must": must_clauses
            }
        }

    def _build_boolean_query(self, query: str) -> Dict:
        """
        Build bool query for boolean search with AND/OR/NOT operators.

        Now uses QueryParser (Lark-based) for parsing complex queries with
        proper operator precedence and parentheses support.

        Falls back to simple multi_match query if parsing fails.

        Operator precedence: NOT > AND > OR (standard boolean logic)

        Args:
            query: Search query with boolean operators

        Returns:
            Elasticsearch bool query with must/should/must_not clauses

        Examples:
            >>> _build_boolean_query("diabetes AND hypertension")
            {
                "bool": {
                    "must": [
                        {"multi_match": {"query": "diabetes", "fields": [...]}},
                        {"multi_match": {"query": "hypertension", "fields": [...]}}
                    ]
                }
            }

            >>> _build_boolean_query("(diabetes OR hypertension) AND medication")
            {
                "bool": {
                    "must": [
                        {"bool": {"should": [...]}},
                        {"multi_match": {"query": "medication", ...}}
                    ]
                }
            }
        """
        try:
            # Try using QueryParser for better handling of complex queries
            parsed_query = self.query_parser.parse(query)

            # If parser returns None (empty query), fall back to simple query
            if parsed_query is None:
                return self._build_term_clause(query)

            return parsed_query

        except LarkError as e:
            # Parse error - fall back to simple multi_match query
            # This handles cases where query syntax is invalid or too complex
            return self._build_term_clause(query)

    def _build_field_query(self, query: str) -> Dict:
        """
        Build query for field-specific search (field:value syntax).

        Supports field:value and field:"value with spaces" syntax.
        Uses match queries for text fields (author, title, content).
        Uses term queries for keyword fields (document_type, department).

        Args:
            query: Search query with field:value syntax

        Returns:
            Elasticsearch query clause (match, term, or bool query)

        Examples:
            >>> _build_field_query('author:"Dr. Smith"')
            {"match": {"author": {"query": "Dr. Smith"}}}

            >>> _build_field_query('document_type:"clinical_note"')
            {"term": {"document_type": "clinical_note"}}

            >>> _build_field_query('author:"Dr. Smith" AND document_type:"clinical_note"')
            {
                "bool": {
                    "must": [
                        {"match": {"author": {"query": "Dr. Smith"}}},
                        {"term": {"document_type": "clinical_note"}}
                    ]
                }
            }
        """
        # Define keyword fields (use term query)
        keyword_fields = {"document_type", "department"}

        # Check if query contains boolean operators
        if re.search(r'\b(AND|OR|NOT)\b', query, re.IGNORECASE):
            # Parse field queries and combine with boolean logic
            return self._build_field_boolean_query(query, keyword_fields)

        # Extract field:value pattern
        # Pattern: field:"quoted value" or field:unquoted_value
        field_pattern = r'(\w+):(\"[^\"]+\"|[^\s]+)'
        match = re.search(field_pattern, query)

        if not match:
            # No field syntax found, return simple query
            return self._build_term_clause(query)

        field_name = match.group(1)
        field_value = match.group(2)

        # Remove quotes if present
        if field_value.startswith('"') and field_value.endswith('"'):
            field_value = field_value[1:-1]

        # Use term query for keyword fields, match query for text fields
        if field_name in keyword_fields:
            return {
                "term": {
                    field_name: field_value
                }
            }
        else:
            return {
                "match": {
                    field_name: {
                        "query": field_value
                    }
                }
            }

    def _build_field_boolean_query(self, query: str, keyword_fields: set) -> Dict:
        """
        Build boolean query with field-specific clauses.

        Args:
            query: Query with field:value syntax and boolean operators
            keyword_fields: Set of field names that use term queries

        Returns:
            Elasticsearch bool query
        """
        # Handle OR operator
        if re.search(r'\bOR\b', query, re.IGNORECASE):
            or_parts = re.split(r'\s+OR\s+', query, flags=re.IGNORECASE)
            should_clauses = []

            for part in or_parts:
                part = part.strip()
                if not part:
                    continue

                # Parse field query for this part
                clause = self._build_field_query(part)
                should_clauses.append(clause)

            return {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            }

        # Handle NOT operator
        if re.search(r'\bNOT\b', query, re.IGNORECASE):
            parts = re.split(r'\s+NOT\s+', query, maxsplit=1, flags=re.IGNORECASE)
            positive_part = parts[0].strip()
            negative_part = parts[1].strip() if len(parts) > 1 else ""

            must_clauses = []
            must_not_clauses = []

            if positive_part:
                clause = self._build_field_query(positive_part)
                must_clauses.append(clause)

            if negative_part:
                clause = self._build_field_query(negative_part)
                must_not_clauses.append(clause)

            result = {"bool": {}}
            if must_clauses:
                result["bool"]["must"] = must_clauses
            if must_not_clauses:
                result["bool"]["must_not"] = must_not_clauses

            return result

        # Handle AND operator
        if re.search(r'\bAND\b', query, re.IGNORECASE):
            and_parts = re.split(r'\s+AND\s+', query, flags=re.IGNORECASE)
            must_clauses = []

            for part in and_parts:
                part = part.strip()
                if not part:
                    continue

                # Parse field query for this part
                clause = self._build_field_query(part)
                must_clauses.append(clause)

            return {
                "bool": {
                    "must": must_clauses
                }
            }

        # No boolean operators, single field query
        return self._build_field_query(query)

    def _build_term_clause(self, term: str) -> Dict:
        """
        Build query clause for a single term or phrase.

        Detects if term is a quoted phrase and builds appropriate query type.
        Applies field boosting (title^10, content^1, author^2).

        Args:
            term: Single search term or quoted phrase

        Returns:
            Multi_match query clause

        Examples:
            >>> _build_term_clause("diabetes")
            {"multi_match": {"query": "diabetes", "fields": ["title^10", "content^1", "author^2"]}}

            >>> _build_term_clause('"chest pain"')
            {"multi_match": {"query": "chest pain", "fields": ["title^10", "content^1"], "type": "phrase"}}
        """
        term = term.strip()

        # Check if quoted phrase
        if term.startswith('"') and term.endswith('"'):
            # Remove quotes
            phrase = term.strip('"')
            return {
                "multi_match": {
                    "query": phrase,
                    "fields": ["title^10", "content^1"],
                    "type": "phrase"
                }
            }

        # Regular term
        return {
            "multi_match": {
                "query": term,
                "fields": ["title^10", "content^1", "author^2"]
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

    def _apply_filters(self, query: Dict, filters: Optional[Dict] = None) -> Dict:
        """
        Apply filters to Elasticsearch query.

        Wraps base query in bool query with filter clauses (AND logic).
        Filters do not affect scoring, only narrow results.

        Supported filters:
        - document_types: List of document types (terms query)
        - authors: List of authors (terms query)
        - departments: List of departments (terms query)
        - date_range: Date range with start/end (range query)

        Args:
            query: Base Elasticsearch query
            filters: Dict of filter criteria (optional)

        Returns:
            Query with filters applied, or base query if no filters

        Examples:
            >>> _apply_filters({"match_all": {}}, {"document_types": ["clinical_note"]})
            {
                "bool": {
                    "must": [{"match_all": {}}],
                    "filter": [
                        {"terms": {"document_type": ["clinical_note"]}}
                    ]
                }
            }
        """
        # Return base query if no filters provided
        if not filters:
            return query

        filter_clauses = []

        # Document types filter (terms query for exact match on keyword field)
        if "document_types" in filters and filters["document_types"]:
            filter_clauses.append({
                "terms": {"document_type": filters["document_types"]}
            })

        # Authors filter (terms query)
        if "authors" in filters and filters["authors"]:
            filter_clauses.append({
                "terms": {"author": filters["authors"]}
            })

        # Departments filter (terms query)
        if "departments" in filters and filters["departments"]:
            filter_clauses.append({
                "terms": {"department": filters["departments"]}
            })

        # Date range filter (range query with gte/lte)
        if "date_range" in filters and filters["date_range"]:
            date_range = filters["date_range"]
            range_query = {"range": {"date": {}}}

            if "start" in date_range and date_range["start"]:
                range_query["range"]["date"]["gte"] = date_range["start"]

            if "end" in date_range and date_range["end"]:
                range_query["range"]["date"]["lte"] = date_range["end"]

            # Only add if at least one bound is set
            if range_query["range"]["date"]:
                filter_clauses.append(range_query)

        # Return base query if no filter clauses were added
        if not filter_clauses:
            return query

        # Wrap query in bool with filter clauses
        # Filter clauses use AND logic (all must match)
        return {
            "bool": {
                "must": [query],
                "filter": filter_clauses
            }
        }
