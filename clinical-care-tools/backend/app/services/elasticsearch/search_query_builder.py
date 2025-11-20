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
        - \\* or \\? escapes wildcards to treat as literals

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
    def build_fuzzy_query(
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        transpositions: bool = True,
        prefix_length: int = 0,
        max_expansions: int = 50
    ) -> Dict[str, Any]:
        """
        Build Elasticsearch query with fuzzy matching for typo tolerance.

        Fuzzy syntax:
        - term~ : AUTO fuzziness based on term length
        - term~1 : Specific edit distance (max 2)
        - "phrase"~2 : Phrase with slop (word proximity)

        Args:
            query_text: Query string with fuzzy operators (~)
            filters: Additional filters to apply
            transpositions: Allow character transpositions (ab->ba)
            prefix_length: Number of initial characters that must match
            max_expansions: Maximum number of terms the fuzzy query will expand to

        Returns:
            Elasticsearch query DSL dictionary

        Note:
            - AUTO fuzziness: 0 for 1-2 chars, 1 for 3-5 chars, 2 for >5 chars
            - Edit distance is capped at 2 for performance
        """
        # Check for empty query
        if not query_text or not query_text.strip():
            return {"query": {"match_all": {}}}

        # Normalize operators
        query_text = SearchQueryBuilder._normalize_operators(query_text)

        # Extract and protect quoted phrases
        phrases, query_text = SearchQueryBuilder._extract_phrases_fuzzy(query_text)

        # Parse the fuzzy query
        parsed_query = SearchQueryBuilder._parse_fuzzy_expression(
            query_text, phrases, transpositions, prefix_length, max_expansions
        )

        # Build the final query
        es_query = {"query": parsed_query}

        # Add filters if provided
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if key == "document_type":
                    filter_clauses.append({"term": {"document_type": value}})
                elif key == "date_from":
                    filter_clauses.append({"range": {"date": {"gte": value}}})
                elif key == "date_to":
                    filter_clauses.append({"range": {"date": {"lte": value}}})

            if filter_clauses:
                # Wrap existing query in a bool query with filters
                if "bool" not in es_query["query"]:
                    es_query["query"] = {"bool": {"must": [es_query["query"]]}}
                es_query["query"]["bool"]["filter"] = filter_clauses

        return es_query

    @staticmethod
    def _extract_phrases_fuzzy(query_text: str) -> Tuple[Dict[str, Tuple[str, int]], str]:
        """
        Extract quoted phrases with fuzzy slop and replace with placeholders.

        Args:
            query_text: Query text with possible phrases

        Returns:
            Tuple of (phrases dict with slop values, modified query text)
        """
        import re
        phrases = {}
        phrase_counter = 0
        modified_text = query_text

        # Find all quoted phrases with optional fuzzy slop
        pattern = r'"([^"]+)"(~\d+)?'

        for match in re.finditer(pattern, query_text):
            phrase_text = match.group(1)
            fuzzy_part = match.group(2)

            # Extract slop value if present
            slop = 0
            if fuzzy_part:
                slop = int(fuzzy_part[1:])  # Skip the ~ character

            # Create placeholder
            phrase_id = f"__PHRASE_{phrase_counter}__"
            phrases[phrase_id] = (phrase_text, slop)
            phrase_counter += 1

            # Replace the entire match (phrase + optional fuzzy) with placeholder
            modified_text = modified_text.replace(match.group(0), phrase_id)

        return phrases, modified_text

    @staticmethod
    def _parse_fuzzy_expression(
        query_text: str,
        phrases: Dict[str, Tuple[str, int]],
        transpositions: bool,
        prefix_length: int,
        max_expansions: int
    ) -> Dict[str, Any]:
        """
        Parse fuzzy expression into Elasticsearch query.

        Args:
            query_text: Query string with fuzzy operators
            phrases: Dictionary of phrase placeholders with slop values
            transpositions: Allow character transpositions
            prefix_length: Prefix length requirement
            max_expansions: Maximum fuzzy expansions

        Returns:
            Elasticsearch query clause
        """
        # Remove extra whitespace
        query_text = ' '.join(query_text.split())

        # Handle single term
        if ' AND ' not in query_text and ' OR ' not in query_text and ' NOT ' not in query_text:
            return SearchQueryBuilder._create_fuzzy_clause(
                query_text, phrases, transpositions, prefix_length, max_expansions
            )

        # Handle Boolean operators with fuzzy
        bool_query = {"bool": {}}

        # Handle NOT operators
        if ' NOT ' in query_text:
            parts = query_text.split(' NOT ')
            left_part = parts[0].strip()

            # Parse the left part
            if ' OR ' in left_part:
                bool_query["bool"]["must"] = [SearchQueryBuilder._handle_fuzzy_or(
                    left_part, phrases, transpositions, prefix_length, max_expansions
                )]
            elif ' AND ' in left_part:
                bool_query["bool"]["must"] = SearchQueryBuilder._handle_fuzzy_and(
                    left_part, phrases, transpositions, prefix_length, max_expansions
                )
            else:
                bool_query["bool"]["must"] = [SearchQueryBuilder._create_fuzzy_clause(
                    left_part, phrases, transpositions, prefix_length, max_expansions
                )]

            # Add must_not clauses
            bool_query["bool"]["must_not"] = []
            for part in parts[1:]:
                term = part.strip().split()[0]
                bool_query["bool"]["must_not"].append(
                    SearchQueryBuilder._create_fuzzy_clause(
                        term, phrases, transpositions, prefix_length, max_expansions
                    )
                )

        # Handle AND operators
        elif ' AND ' in query_text:
            bool_query["bool"]["must"] = SearchQueryBuilder._handle_fuzzy_and(
                query_text, phrases, transpositions, prefix_length, max_expansions
            )

        # Handle OR operators
        elif ' OR ' in query_text:
            return SearchQueryBuilder._handle_fuzzy_or(
                query_text, phrases, transpositions, prefix_length, max_expansions
            )

        return bool_query

    @staticmethod
    def _handle_fuzzy_and(
        query_text: str,
        phrases: Dict[str, Tuple[str, int]],
        transpositions: bool,
        prefix_length: int,
        max_expansions: int
    ) -> List[Dict[str, Any]]:
        """Handle AND expressions with fuzzy."""
        parts = query_text.split(' AND ')
        must_clauses = []

        for part in parts:
            part = part.strip()
            must_clauses.append(SearchQueryBuilder._create_fuzzy_clause(
                part, phrases, transpositions, prefix_length, max_expansions
            ))

        return must_clauses

    @staticmethod
    def _handle_fuzzy_or(
        query_text: str,
        phrases: Dict[str, Tuple[str, int]],
        transpositions: bool,
        prefix_length: int,
        max_expansions: int
    ) -> Dict[str, Any]:
        """Handle OR expressions with fuzzy."""
        parts = query_text.split(' OR ')
        should_clauses = []

        for part in parts:
            part = part.strip()
            should_clauses.append(SearchQueryBuilder._create_fuzzy_clause(
                part, phrases, transpositions, prefix_length, max_expansions
            ))

        return {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }

    @staticmethod
    def _create_fuzzy_clause(
        term: str,
        phrases: Dict[str, Tuple[str, int]],
        transpositions: bool,
        prefix_length: int,
        max_expansions: int
    ) -> Dict[str, Any]:
        """
        Create a fuzzy or match clause based on term content.

        Args:
            term: Search term that may contain fuzzy operator
            phrases: Dictionary of phrase placeholders with slop
            transpositions: Allow transpositions
            prefix_length: Prefix length requirement
            max_expansions: Maximum expansions

        Returns:
            Elasticsearch query clause
        """
        term = term.strip()

        # Check if it's a phrase placeholder
        if term.startswith('__PHRASE_') and term.endswith('__'):
            phrase_text, slop = phrases.get(term, (term, 0))
            clause = {"match_phrase": {"_all": {"query": phrase_text}}}
            if slop > 0:
                clause["match_phrase"]["_all"]["slop"] = slop
            return clause

        # Check for field-specific search
        if ':' in term:
            field, value = term.split(':', 1)
            field = field.strip()
            value = value.strip()

            # Check if value has fuzzy operator
            if '~' in value:
                return SearchQueryBuilder._parse_fuzzy_term(
                    field, value, transpositions, prefix_length, max_expansions
                )
            else:
                return {"match": {field: value}}

        # Check if term has fuzzy operator
        if '~' in term:
            return SearchQueryBuilder._parse_fuzzy_term(
                "_all", term, transpositions, prefix_length, max_expansions
            )

        # Default to match query
        return {"match": {"_all": term}}

    @staticmethod
    def _parse_fuzzy_term(
        field: str,
        term: str,
        transpositions: bool,
        prefix_length: int,
        max_expansions: int
    ) -> Dict[str, Any]:
        """
        Parse a single fuzzy term.

        Args:
            field: Field to search
            term: Term with fuzzy operator
            transpositions: Allow transpositions
            prefix_length: Prefix length requirement
            max_expansions: Maximum expansions

        Returns:
            Fuzzy query clause
        """
        import re

        # Parse term~fuzziness pattern
        match = re.match(r'^(.+?)~(\d*)$', term)
        if match:
            base_term = match.group(1)
            fuzziness_str = match.group(2)

            # Determine fuzziness
            if fuzziness_str:
                fuzziness = min(int(fuzziness_str), 2)  # Cap at 2
            else:
                fuzziness = "AUTO"

            # Build fuzzy query
            fuzzy_query = {
                "fuzzy": {
                    field: {
                        "value": base_term,
                        "fuzziness": fuzziness,
                        "transpositions": transpositions,
                        "prefix_length": prefix_length,
                        "max_expansions": max_expansions
                    }
                }
            }

            return fuzzy_query

        # No fuzzy operator found
        return {"match": {field: term}}

    @staticmethod
    def build_proximity_query(
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        default_proximity: int = 5
    ) -> Dict[str, Any]:
        """
        Build Elasticsearch query with proximity search support.

        Proximity operators:
        - term1 NEAR term2 : Terms within default proximity (5 words)
        - term1 NEAR/n term2 : Terms within n words
        - term1 W/n term2 : Terms within n words (alternative syntax)
        - "term1 term2"~n : Phrase with slop (alternative for phrases)

        Args:
            query_text: Query string with proximity operators
            filters: Additional filters to apply
            default_proximity: Default word distance for NEAR operator

        Returns:
            Elasticsearch query DSL dictionary

        Examples:
            - "diabetes NEAR complications" : Within 5 words
            - "heart NEAR/3 failure" : Within 3 words
            - "blood W/2 pressure" : Within 2 words
        """
        # Check for empty query
        if not query_text or not query_text.strip():
            return {"query": {"match_all": {}}}

        # Normalize operators
        query_text = SearchQueryBuilder._normalize_proximity_operators(query_text)

        # Parse the proximity query
        parsed_query = SearchQueryBuilder._parse_proximity_expression(
            query_text, default_proximity
        )

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

        return es_query

    @staticmethod
    def _normalize_proximity_operators(query_text: str) -> str:
        """Normalize proximity operators to consistent format."""
        import re

        # Normalize NEAR/n to standard format
        query_text = re.sub(r'\bNEAR/(\d+)\b', r'NEAR/\1', query_text, flags=re.IGNORECASE)
        query_text = re.sub(r'\bNEAR\b(?!/\d)', f'NEAR/{5}', query_text, flags=re.IGNORECASE)

        # Normalize W/n (within) operator to NEAR/n
        query_text = re.sub(r'\bW/(\d+)\b', r'NEAR/\1', query_text, flags=re.IGNORECASE)
        query_text = re.sub(r'\bWITHIN/(\d+)\b', r'NEAR/\1', query_text, flags=re.IGNORECASE)

        # Normalize ADJ (adjacent) operator to NEAR/1
        query_text = re.sub(r'\bADJ\b', 'NEAR/1', query_text, flags=re.IGNORECASE)

        return query_text

    @staticmethod
    def _parse_proximity_expression(
        query_text: str,
        default_proximity: int
    ) -> Dict[str, Any]:
        """
        Parse proximity expression into Elasticsearch query.

        Args:
            query_text: Query string with proximity operators
            default_proximity: Default proximity distance

        Returns:
            Elasticsearch query clause
        """
        import re

        # Extract quoted phrases with slop (already handled by fuzzy)
        phrases = {}
        phrase_pattern = r'"([^"]+)"~(\d+)'

        for match in re.finditer(phrase_pattern, query_text):
            phrase_text = match.group(1)
            slop = int(match.group(2))
            placeholder = f"__PHRASE_{len(phrases)}__"
            phrases[placeholder] = (phrase_text, slop)
            query_text = query_text.replace(match.group(0), placeholder)

        # Parse NEAR/n operators
        near_pattern = r'(\S+)\s+NEAR/(\d+)\s+(\S+)'
        matches = list(re.finditer(near_pattern, query_text, re.IGNORECASE))

        if not matches and 'NEAR' not in query_text.upper():
            # No proximity operators, check for phrase placeholders
            if phrases:
                # Build query with phrase placeholders
                must_clauses = []
                for placeholder, (phrase_text, slop) in phrases.items():
                    must_clauses.append({
                        "match_phrase": {
                            "_all": {
                                "query": phrase_text,
                                "slop": slop
                            }
                        }
                    })

                if len(must_clauses) == 1:
                    return must_clauses[0]
                else:
                    return {"bool": {"must": must_clauses}}

            # No proximity operators, return simple match
            return {"match": {"_all": query_text}}

        # Build proximity queries
        proximity_clauses = []

        for match in matches:
            term1 = match.group(1).strip()
            proximity = int(match.group(2))
            term2 = match.group(3).strip()

            # Handle phrase placeholders in terms
            if term1 in phrases:
                phrase_text, _ = phrases[term1]
                term1 = phrase_text
            if term2 in phrases:
                phrase_text, _ = phrases[term2]
                term2 = phrase_text

            # Create span_near query for proximity search
            proximity_clauses.append(
                SearchQueryBuilder._create_proximity_clause(term1, term2, proximity)
            )

        # Handle any remaining text not part of proximity expressions
        remaining_text = query_text
        for match in matches:
            remaining_text = remaining_text.replace(match.group(0), '')

        remaining_text = remaining_text.strip()

        if remaining_text:
            # Add remaining terms as regular matches
            if proximity_clauses:
                # Combine with proximity clauses
                return {
                    "bool": {
                        "must": proximity_clauses + [{"match": {"_all": remaining_text}}]
                    }
                }
            else:
                return {"match": {"_all": remaining_text}}

        # Return proximity clauses
        if len(proximity_clauses) == 1:
            return proximity_clauses[0]
        else:
            return {"bool": {"must": proximity_clauses}}

    @staticmethod
    def _create_proximity_clause(
        term1: str,
        term2: str,
        proximity: int
    ) -> Dict[str, Any]:
        """
        Create proximity search clause using span queries.

        Args:
            term1: First term
            term2: Second term
            proximity: Maximum distance between terms

        Returns:
            Elasticsearch span query
        """
        # Use span_near query for proximity search
        return {
            "span_near": {
                "clauses": [
                    {"span_term": {"_all": term1.lower()}},
                    {"span_term": {"_all": term2.lower()}}
                ],
                "slop": proximity,
                "in_order": False  # Terms can appear in any order
            }
        }

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
