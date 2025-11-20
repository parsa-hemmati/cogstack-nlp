"""
Advanced query parser using Lark for complex search syntax.

Converts natural search queries with boolean operators, parentheses, field queries,
and phrases into Elasticsearch DSL queries.

Examples:
    - "diabetes" → multi_match query
    - "diabetes AND hypertension" → bool must query
    - "(diabetes OR hypertension) AND medication" → nested bool query
    - 'author:"Dr. Smith"' → match query on author field
"""

from typing import Dict, Optional

from lark import Transformer, v_args
from lark.exceptions import LarkError

from app.search.query_grammar import get_query_parser


class QueryTransformer(Transformer):
    """
    Transforms Lark parse tree into Elasticsearch DSL query.

    Each method corresponds to a grammar rule and returns an ES query dict.
    """

    # Define keyword fields (exact match)
    KEYWORD_FIELDS = {"document_type", "department"}

    @v_args(inline=True)
    def term(self, word):
        """
        Transform single term into multi_match query.

        Args:
            word: Term to search for

        Returns:
            Multi-match query dict
        """
        return {
            "multi_match": {
                "query": str(word),
                "fields": ["title^10", "content^1", "author^2"]
            }
        }

    @v_args(inline=True)
    def phrase(self, escaped_string):
        """
        Transform quoted phrase into phrase query.

        Args:
            escaped_string: Quoted phrase (Lark removes quotes automatically)

        Returns:
            Multi-match phrase query dict
        """
        # Lark's ESCAPED_STRING includes quotes, strip them
        phrase_text = str(escaped_string).strip('"')
        return {
            "multi_match": {
                "query": phrase_text,
                "fields": ["title^10", "content^1"],
                "type": "phrase"
            }
        }

    def field_query(self, args):
        """
        Transform field:value or field:"phrase" into appropriate query.

        Args:
            args: [field_name, value_token]

        Returns:
            Match query for text fields, term query for keyword fields
        """
        field_name = str(args[0])
        value_token = args[1]

        # Extract value (strip quotes if present)
        value = str(value_token).strip('"')

        # Choose query type based on field
        if field_name in self.KEYWORD_FIELDS:
            return {"term": {field_name: value}}
        else:
            return {"match": {field_name: {"query": value}}}

    @v_args(inline=True)
    def and_op(self, left, right):
        """
        Transform AND operation into bool must query.

        Args:
            left: Left operand query
            right: Right operand query

        Returns:
            Bool query with must clauses
        """
        # Flatten nested AND operations
        must_clauses = []

        # Extract must clauses from left operand
        if isinstance(left, dict) and "bool" in left and "must" in left["bool"]:
            must_clauses.extend(left["bool"]["must"])
        else:
            must_clauses.append(left)

        # Extract must clauses from right operand
        if isinstance(right, dict) and "bool" in right and "must" in right["bool"]:
            must_clauses.extend(right["bool"]["must"])
        else:
            must_clauses.append(right)

        return {"bool": {"must": must_clauses}}

    @v_args(inline=True)
    def or_op(self, left, right):
        """
        Transform OR operation into bool should query.

        Args:
            left: Left operand query
            right: Right operand query

        Returns:
            Bool query with should clauses
        """
        # Flatten nested OR operations
        should_clauses = []

        # Extract should clauses from left operand
        if isinstance(left, dict) and "bool" in left and "should" in left["bool"]:
            should_clauses.extend(left["bool"]["should"])
        else:
            should_clauses.append(left)

        # Extract should clauses from right operand
        if isinstance(right, dict) and "bool" in right and "should" in right["bool"]:
            should_clauses.extend(right["bool"]["should"])
        else:
            should_clauses.append(right)

        return {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }

    @v_args(inline=True)
    def not_op(self, operand):
        """
        Transform NOT operation into bool must_not query.

        For "A NOT B", this creates: {bool: {must: [A], must_not: [B]}}
        However, since Lark parses "NOT B" as a single expression,
        we need to handle context differently.

        Args:
            operand: Operand to negate

        Returns:
            Bool query with must_not clause
        """
        # NOT is unary, but in "A NOT B", the parser sees "A" and "NOT B" separately
        # The AND operation will combine them
        return {"bool": {"must_not": [operand]}}

    @v_args(inline=True)
    def group(self, expr):
        """
        Transform parenthesized group.

        Args:
            expr: Inner expression

        Returns:
            Inner expression unchanged (parentheses just group)
        """
        return expr


class QueryParser:
    """
    Advanced query parser using Lark grammar.

    Parses complex search queries with boolean operators, field queries,
    phrases, and parentheses into Elasticsearch DSL queries.

    Example:
        parser = QueryParser()
        query = parser.parse("(diabetes OR hypertension) AND medication")
        # Returns: Elasticsearch DSL query dict
    """

    def __init__(self):
        """Initialize parser with query grammar."""
        self.lark_parser = get_query_parser()
        self.transformer = QueryTransformer()

    def parse(self, query_string: str) -> Optional[Dict]:
        """
        Parse query string into Elasticsearch DSL query.

        Args:
            query_string: Natural language search query

        Returns:
            Elasticsearch DSL query dict, or None if empty

        Raises:
            LarkError: If query syntax is invalid
        """
        # Handle empty query
        if not query_string or not query_string.strip():
            return None

        try:
            # Parse with Lark
            tree = self.lark_parser.parse(query_string)

            # Transform to Elasticsearch DSL
            es_query = self.transformer.transform(tree)

            return es_query

        except LarkError as e:
            # Re-raise parse errors for caller to handle
            raise e
