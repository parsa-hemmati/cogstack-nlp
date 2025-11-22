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

        Flattens nested bool queries and combines must/must_not clauses.

        Args:
            left: Left operand query
            right: Right operand query

        Returns:
            Bool query with must clauses (and must_not if present)
        """
        # Flatten nested AND operations
        must_clauses = []
        must_not_clauses = []

        # Extract clauses from left operand
        if isinstance(left, dict) and "bool" in left:
            if "must" in left["bool"]:
                must_clauses.extend(left["bool"]["must"])
            elif "must_not" in left["bool"]:
                # Unary NOT on left side
                must_not_clauses.extend(left["bool"]["must_not"])
            else:
                must_clauses.append(left)

            # Also carry forward any existing must_not
            if "must_not" in left["bool"] and "must" in left["bool"]:
                must_not_clauses.extend(left["bool"]["must_not"])
        else:
            must_clauses.append(left)

        # Extract clauses from right operand
        if isinstance(right, dict) and "bool" in right:
            if "must" in right["bool"]:
                must_clauses.extend(right["bool"]["must"])
            elif "must_not" in right["bool"]:
                # Unary NOT on right side
                must_not_clauses.extend(right["bool"]["must_not"])
            else:
                must_clauses.append(right)

            # Also carry forward any existing must_not
            if "must_not" in right["bool"] and "must" in right["bool"]:
                must_not_clauses.extend(right["bool"]["must_not"])
        else:
            must_clauses.append(right)

        result = {"bool": {"must": must_clauses}}
        if must_not_clauses:
            result["bool"]["must_not"] = must_not_clauses

        return result

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
    def unary_not_op(self, operand):
        """
        Transform unary NOT operation (NOT term) into bool must_not query.

        For "NOT B", this creates: {bool: {must_not: [B]}}

        Args:
            operand: Operand to negate

        Returns:
            Bool query with must_not clause
        """
        return {"bool": {"must_not": [operand]}}

    @v_args(inline=True)
    def binary_not_op(self, left, right):
        """
        Transform binary NOT operation (A NOT B) into bool with must and must_not.

        For "A NOT B", this creates: {bool: {must: [A], must_not: [B]}}
        This is equivalent to "A AND NOT B".

        Args:
            left: Left operand (what to include)
            right: Right operand (what to exclude)

        Returns:
            Bool query with must and must_not clauses
        """
        must_clauses = []
        must_not_clauses = [right]

        # Extract must clauses from left operand
        if isinstance(left, dict) and "bool" in left:
            if "must" in left["bool"]:
                must_clauses.extend(left["bool"]["must"])
            else:
                must_clauses.append(left)

            # Carry forward any existing must_not clauses
            if "must_not" in left["bool"]:
                must_not_clauses.extend(left["bool"]["must_not"])
        else:
            must_clauses.append(left)

        return {
            "bool": {
                "must": must_clauses,
                "must_not": must_not_clauses
            }
        }

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
