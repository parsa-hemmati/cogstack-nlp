"""Elasticsearch query builder for multi-field search.

Builds complex Elasticsearch queries with:
- Multi-field matching (title, content, author)
- Field boosting for relevance ranking
- Filters (document type, date range, department, author)
- Fuzzy matching for typo tolerance
- Aggregations for faceting
- Highlighting configuration
- Boolean operators (AND, OR, NOT) parsing
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re


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
    def build_boolean_query(
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build Elasticsearch query with Boolean operators (AND, OR, NOT).

        Supports:
        - AND operator: term1 AND term2
        - OR operator: term1 OR term2
        - NOT operator: term1 NOT term2
        - Parentheses for grouping: (term1 OR term2) AND term3
        - Quoted phrases: "exact phrase" AND term
        - Field-specific search: title:term1 AND content:term2

        Args:
            query_text: Query string with Boolean operators
            filters: Additional filters to apply
            fields: Default fields to search (if not field-specific)

        Returns:
            Elasticsearch query DSL dictionary
        """
        if not query_text or not query_text.strip():
            return {"query": {"match_all": {}}}

        # Default fields if not specified
        if fields is None:
            fields = ["title^3", "content^1", "author^2"]

        # Parse the query string
        parsed_query = SearchQueryBuilder._parse_boolean_expression(query_text)

        # Build the Elasticsearch query from parsed structure
        es_query = {"query": parsed_query}

        # Add filters if provided
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if key == "document_type":
                    filter_clauses.append({"term": {"document_type": value}})
                elif key == "department":
                    filter_clauses.append({"term": {"department": value}})
                # Add more filter types as needed

            if filter_clauses:
                # Wrap existing query in a bool query with filters
                if "bool" not in es_query["query"]:
                    es_query["query"] = {"bool": {"must": [es_query["query"]]}}
                es_query["query"]["bool"]["filter"] = filter_clauses

        return es_query

    @staticmethod
    def _parse_boolean_expression(query_text: str) -> Dict[str, Any]:
        """
        Parse Boolean expression into Elasticsearch query structure.

        Args:
            query_text: Query string with Boolean operators

        Returns:
            Elasticsearch query clause
        """
        # Handle empty query
        if not query_text.strip():
            return {"match_all": {}}

        # Normalize operators to uppercase for consistent parsing
        query_text = SearchQueryBuilder._normalize_operators(query_text)

        # Extract quoted phrases and replace with placeholders
        phrases, query_text = SearchQueryBuilder._extract_phrases(query_text)

        # Parse the expression
        clauses = SearchQueryBuilder._parse_boolean_logic(query_text, phrases)

        return clauses

    @staticmethod
    def _normalize_operators(query_text: str) -> str:
        """Normalize Boolean operators to uppercase."""
        # Replace word-boundary operators with uppercase versions
        query_text = re.sub(r'\b(and)\b', 'AND', query_text, flags=re.IGNORECASE)
        query_text = re.sub(r'\b(or)\b', 'OR', query_text, flags=re.IGNORECASE)
        query_text = re.sub(r'\b(not)\b', 'NOT', query_text, flags=re.IGNORECASE)
        return query_text

    @staticmethod
    def _extract_phrases(query_text: str) -> Tuple[Dict[str, str], str]:
        """Extract quoted phrases and replace with placeholders."""
        phrases = {}
        phrase_counter = 0

        def replace_phrase(match):
            nonlocal phrase_counter
            phrase_id = f"__PHRASE_{phrase_counter}__"
            phrases[phrase_id] = match.group(1)
            phrase_counter += 1
            return phrase_id

        # Replace quoted phrases with placeholders
        query_text = re.sub(r'"([^"]+)"', replace_phrase, query_text)

        return phrases, query_text

    @staticmethod
    def _parse_boolean_logic(query_text: str, phrases: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse Boolean logic into Elasticsearch query structure.

        This is a simplified parser that handles basic Boolean logic.
        For production use, consider using a proper expression parser.
        """
        # Remove extra whitespace
        query_text = ' '.join(query_text.split())

        # Handle single term without operators
        if ' AND ' not in query_text and ' OR ' not in query_text and ' NOT ' not in query_text:
            return SearchQueryBuilder._create_term_clause(query_text, phrases)

        # Initialize bool query structure
        bool_query = {"bool": {}}

        # Handle NOT operators first (highest precedence after parentheses)
        parts = query_text.split(' NOT ')
        if len(parts) > 1:
            # First part goes to must, rest go to must_not
            left_part = parts[0].strip()

            # Parse the left part (before NOT)
            if ' OR ' in left_part:
                bool_query["bool"]["must"] = [SearchQueryBuilder._handle_or_expression(left_part, phrases)]
            elif ' AND ' in left_part:
                bool_query["bool"]["must"] = SearchQueryBuilder._handle_and_expression(left_part, phrases)
            else:
                bool_query["bool"]["must"] = [SearchQueryBuilder._create_term_clause(left_part, phrases)]

            # Add must_not clauses
            bool_query["bool"]["must_not"] = []
            for part in parts[1:]:
                term = part.strip().split()[0]  # Take first word after NOT
                bool_query["bool"]["must_not"].append(SearchQueryBuilder._create_term_clause(term, phrases))

        # Handle AND operators
        elif ' AND ' in query_text:
            bool_query["bool"]["must"] = SearchQueryBuilder._handle_and_expression(query_text, phrases)

        # Handle OR operators
        elif ' OR ' in query_text:
            return SearchQueryBuilder._handle_or_expression(query_text, phrases)

        return bool_query

    @staticmethod
    def _handle_and_expression(query_text: str, phrases: Dict[str, str]) -> List[Dict[str, Any]]:
        """Handle AND expressions."""
        parts = query_text.split(' AND ')
        must_clauses = []

        for part in parts:
            part = part.strip()
            if ' OR ' in part:
                # Handle nested OR within AND
                must_clauses.append(SearchQueryBuilder._handle_or_expression(part, phrases))
            else:
                must_clauses.append(SearchQueryBuilder._create_term_clause(part, phrases))

        return must_clauses

    @staticmethod
    def _handle_or_expression(query_text: str, phrases: Dict[str, str]) -> Dict[str, Any]:
        """Handle OR expressions."""
        parts = query_text.split(' OR ')
        should_clauses = []

        for part in parts:
            part = part.strip()
            should_clauses.append(SearchQueryBuilder._create_term_clause(part, phrases))

        return {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }

    @staticmethod
    def _create_term_clause(term: str, phrases: Dict[str, str]) -> Dict[str, Any]:
        """Create a term clause (match or match_phrase)."""
        term = term.strip()

        # Handle parentheses by removing them
        term = term.strip('()')

        # Check if it's a phrase placeholder
        if term.startswith('__PHRASE_') and term.endswith('__'):
            phrase_text = phrases.get(term, term)
            return {"match_phrase": {"_all": phrase_text}}

        # Check for field-specific search (e.g., title:diabetes)
        if ':' in term:
            field, value = term.split(':', 1)
            field = field.strip()
            value = value.strip()

            # Check if value is a phrase
            if value.startswith('__PHRASE_') and value.endswith('__'):
                phrase_text = phrases.get(value, value)
                return {"match_phrase": {field: phrase_text}}
            else:
                return {"match": {field: value}}

        # Default to searching all fields
        return {"match": {"_all": term}}

    @staticmethod
    def build_wildcard_query(
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        return_warnings: bool = False
    ) -> Any:
        """
        Build Elasticsearch query with wildcard support (* and ?).

        Wildcards:
        - * matches any character sequence (including empty)
        - ? matches any single character
        - \* or \? escapes wildcards to treat as literals

        Args:
            query_text: Query string with wildcards
            filters: Additional filters to apply
            return_warnings: If True, return tuple (query, warnings)

        Returns:
            Elasticsearch query DSL dictionary or (query, warnings) tuple

        Note:
            Leading wildcards (*term) can cause performance issues
            as they prevent efficient index usage.
        """
        warnings = []

        # Check for empty query
        if not query_text or not query_text.strip():
            result = {"query": {"match_all": {}}}
            return (result, warnings) if return_warnings else result

        # Check for leading wildcards (performance warning)
        terms = query_text.split()
        for term in terms:
            if term.startswith('*') and not term.startswith(r'\*'):
                warnings.append(f"Leading wildcard in '{term}' may cause slow performance")

        # Normalize operators
        query_text = SearchQueryBuilder._normalize_operators(query_text)

        # Extract and protect quoted phrases
        phrases, query_text = SearchQueryBuilder._extract_phrases(query_text)

        # Parse the wildcard query
        parsed_query = SearchQueryBuilder._parse_wildcard_expression(query_text, phrases)

        # Build the final query
        es_query = {"query": parsed_query}

        # Add filters if provided
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if key == "document_type":
                    filter_clauses.append({"term": {"document_type": value}})
                elif key == "department":
                    filter_clauses.append({"term": {"department": value}})

            if filter_clauses:
                # Wrap existing query in a bool query with filters
                if "bool" not in es_query["query"]:
                    es_query["query"] = {"bool": {"must": [es_query["query"]]}}
                es_query["query"]["bool"]["filter"] = filter_clauses

        return (es_query, warnings) if return_warnings else es_query

    @staticmethod
    def _parse_wildcard_expression(query_text: str, phrases: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse wildcard expression into Elasticsearch query.

        Args:
            query_text: Query string with wildcards
            phrases: Dictionary of phrase placeholders

        Returns:
            Elasticsearch query clause
        """
        # Remove extra whitespace
        query_text = ' '.join(query_text.split())

        # Handle single term
        if ' AND ' not in query_text and ' OR ' not in query_text and ' NOT ' not in query_text:
            return SearchQueryBuilder._create_wildcard_clause(query_text, phrases)

        # Handle Boolean operators with wildcards
        bool_query = {"bool": {}}

        # Handle NOT operators
        if ' NOT ' in query_text:
            parts = query_text.split(' NOT ')
            left_part = parts[0].strip()

            # Parse the left part
            if ' OR ' in left_part:
                bool_query["bool"]["must"] = [SearchQueryBuilder._handle_wildcard_or(left_part, phrases)]
            elif ' AND ' in left_part:
                bool_query["bool"]["must"] = SearchQueryBuilder._handle_wildcard_and(left_part, phrases)
            else:
                bool_query["bool"]["must"] = [SearchQueryBuilder._create_wildcard_clause(left_part, phrases)]

            # Add must_not clauses
            bool_query["bool"]["must_not"] = []
            for part in parts[1:]:
                term = part.strip().split()[0]
                bool_query["bool"]["must_not"].append(
                    SearchQueryBuilder._create_wildcard_clause(term, phrases)
                )

        # Handle AND operators
        elif ' AND ' in query_text:
            bool_query["bool"]["must"] = SearchQueryBuilder._handle_wildcard_and(query_text, phrases)

        # Handle OR operators
        elif ' OR ' in query_text:
            return SearchQueryBuilder._handle_wildcard_or(query_text, phrases)

        return bool_query

    @staticmethod
    def _handle_wildcard_and(query_text: str, phrases: Dict[str, str]) -> List[Dict[str, Any]]:
        """Handle AND expressions with wildcards."""
        parts = query_text.split(' AND ')
        must_clauses = []

        for part in parts:
            part = part.strip()
            must_clauses.append(SearchQueryBuilder._create_wildcard_clause(part, phrases))

        return must_clauses

    @staticmethod
    def _handle_wildcard_or(query_text: str, phrases: Dict[str, str]) -> Dict[str, Any]:
        """Handle OR expressions with wildcards."""
        parts = query_text.split(' OR ')
        should_clauses = []

        for part in parts:
            part = part.strip()
            should_clauses.append(SearchQueryBuilder._create_wildcard_clause(part, phrases))

        return {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }

    @staticmethod
    def _create_wildcard_clause(term: str, phrases: Dict[str, str]) -> Dict[str, Any]:
        """
        Create a wildcard or match clause based on term content.

        Args:
            term: Search term that may contain wildcards
            phrases: Dictionary of phrase placeholders

        Returns:
            Elasticsearch query clause
        """
        term = term.strip()

        # Check if it's a phrase placeholder
        if term.startswith('__PHRASE_') and term.endswith('__'):
            phrase_text = phrases.get(term, term)
            # Phrases should not use wildcard queries
            return {"match_phrase": {"_all": phrase_text}}

        # Handle escaped wildcards (treat as literals)
        if r'\*' in term or r'\?' in term:
            # Remove escape characters for literal matching
            term = term.replace(r'\*', '*').replace(r'\?', '?')
            return {"match": {"_all": term}}

        # Check for field-specific search
        if ':' in term:
            field, value = term.split(':', 1)
            field = field.strip()
            value = value.strip()

            # Check if value contains wildcards
            if '*' in value or '?' in value:
                return {"wildcard": {field: {"value": value}}}
            else:
                return {"match": {field: value}}

        # Check if term contains wildcards
        if '*' in term or '?' in term:
            return {"wildcard": {"_all": {"value": term}}}

        # Default to match query
        return {"match": {"_all": term}}

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
