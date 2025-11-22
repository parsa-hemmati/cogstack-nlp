"""
Lark grammar for advanced search query parsing.

Supports:
- Simple terms: diabetes
- Phrases: "chest pain"
- Boolean operators: AND, OR, NOT (both unary and binary)
- Parentheses: (diabetes OR hypertension) AND medication
- Field queries: author:"Dr. Smith", document_type:clinical_note
- Operator precedence: NOT > AND > OR (standard boolean logic)

Grammar based on Lark EBNF syntax:
https://lark-parser.readthedocs.io/en/latest/grammar.html
"""

from lark import Lark

# Query grammar definition
# Priority levels (higher number = higher precedence):
# 1. OR (lowest)
# 2. AND (medium)
# 3. NOT (highest - both unary and binary)
# 4. Parentheses, terms, phrases (atomic)

QUERY_GRAMMAR = r"""
    ?start: or_expr

    ?or_expr: and_expr
            | or_expr "OR"i and_expr      -> or_op

    ?and_expr: not_expr
             | and_expr "AND"i not_expr   -> and_op

    ?not_expr: atom
             | "NOT"i atom                -> unary_not_op
             | not_expr "NOT"i atom       -> binary_not_op

    ?atom: "(" or_expr ")"                            -> group
         | FIELD_NAME ":" (ESCAPED_STRING | TERM)     -> field_query
         | ESCAPED_STRING                             -> phrase
         | TERM                                       -> term

    FIELD_NAME: /[a-zA-Z_][a-zA-Z0-9_]*(?=:)/
    TERM: /[^\s()":]+/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""

def get_query_parser() -> Lark:
    """
    Get Lark parser instance for query grammar.

    Returns:
        Lark parser configured with query grammar
    """
    return Lark(
        QUERY_GRAMMAR,
        start='start',
        parser='lalr',  # LALR parser for efficiency
    )
