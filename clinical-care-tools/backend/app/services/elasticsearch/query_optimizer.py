"""Query optimization service for performance improvements.

Provides:
- Query rewriting for better performance
- Index hint suggestions
- Query complexity analysis
- Performance recommendations
"""

import re
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Optimize search queries for better Elasticsearch performance."""

    # Complexity weights for different query types
    COMPLEXITY_WEIGHTS = {
        "match": 1,
        "match_phrase": 2,
        "wildcard": 5,
        "fuzzy": 3,
        "regexp": 10,
        "range": 2,
        "span_near": 4,
        "bool": 1  # Multiplier for nested queries
    }

    # Maximum complexity threshold
    MAX_COMPLEXITY = 100

    @staticmethod
    def optimize_query(
        query_dict: Dict[str, Any],
        query_type: str,
        index_stats: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Optimize Elasticsearch query for performance.

        Args:
            query_dict: Original Elasticsearch query
            query_type: Type of query (standard, boolean, etc.)
            index_stats: Optional index statistics for optimization

        Returns:
            Tuple of (optimized query, list of optimization notes)
        """
        optimizations = []
        optimized = query_dict.copy()

        # Optimize based on query type
        if query_type == "wildcard":
            optimized, notes = QueryOptimizer._optimize_wildcard(optimized)
            optimizations.extend(notes)

        elif query_type == "regex":
            optimized, notes = QueryOptimizer._optimize_regex(optimized)
            optimizations.extend(notes)

        elif query_type == "fuzzy":
            optimized, notes = QueryOptimizer._optimize_fuzzy(optimized)
            optimizations.extend(notes)

        elif query_type == "boolean":
            optimized, notes = QueryOptimizer._optimize_boolean(optimized)
            optimizations.extend(notes)

        # General optimizations
        optimized, notes = QueryOptimizer._apply_general_optimizations(optimized)
        optimizations.extend(notes)

        # Add execution hints if index stats available
        if index_stats:
            hints = QueryOptimizer._add_execution_hints(optimized, index_stats)
            optimizations.extend(hints)

        return optimized, optimizations

    @staticmethod
    def _optimize_wildcard(query: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Optimize wildcard queries.

        Args:
            query: Wildcard query dictionary

        Returns:
            Tuple of (optimized query, optimization notes)
        """
        notes = []
        optimized = query.copy()

        def optimize_wildcard_clause(clause):
            if isinstance(clause, dict):
                if "wildcard" in clause:
                    for field, params in clause["wildcard"].items():
                        value = params.get("value", "") if isinstance(params, dict) else params

                        # Convert leading wildcard to prefix if possible
                        if value.startswith("*") and not value.startswith("**"):
                            # Leading wildcard is expensive
                            notes.append(f"WARNING: Leading wildcard '*{value[1:]}' is expensive")

                            # Suggest using ngram tokenizer instead
                            if len(value) > 3:
                                notes.append("TIP: Consider using ngram tokenizer for substring matching")

                        # Convert trailing wildcard to prefix query if no other wildcards
                        if value.endswith("*") and "*" not in value[:-1] and "?" not in value:
                            # Can use more efficient prefix query
                            prefix_value = value[:-1]
                            return {"prefix": {field: prefix_value}}

                # Recursively optimize nested structures
                for key in ["must", "should", "must_not", "filter"]:
                    if key in clause.get("bool", {}):
                        clauses = clause["bool"][key]
                        if isinstance(clauses, list):
                            clause["bool"][key] = [optimize_wildcard_clause(c) for c in clauses]

            return clause

        if "query" in optimized:
            optimized["query"] = optimize_wildcard_clause(optimized["query"])

        return optimized, notes

    @staticmethod
    def _optimize_regex(query: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Optimize regex queries.

        Args:
            query: Regex query dictionary

        Returns:
            Tuple of (optimized query, optimization notes)
        """
        notes = []
        optimized = query.copy()

        def optimize_regex_clause(clause):
            if isinstance(clause, dict) and "regexp" in clause:
                for field, params in clause["regexp"].items():
                    pattern = params.get("value", "") if isinstance(params, dict) else params

                    # Check for patterns that could be simplified
                    if pattern == ".*":
                        notes.append("WARNING: Pattern '.*' matches everything - consider removing")
                        return {"match_all": {}}

                    # Check for simple prefix patterns
                    if re.match(r'^\^[a-zA-Z0-9]+', pattern):
                        # Can convert to prefix query
                        prefix_value = pattern[1:].rstrip(".*")
                        notes.append(f"Optimized regex '^{prefix_value}.*' to prefix query")
                        return {"prefix": {field: prefix_value}}

                    # Check for expensive patterns
                    if pattern.startswith(".*"):
                        notes.append("WARNING: Leading .* in regex is very expensive")

                    # Suggest max_determinized_states if not set
                    if isinstance(params, dict) and "max_determinized_states" not in params:
                        params["max_determinized_states"] = 10000
                        notes.append("Added max_determinized_states limit for safety")

            return clause

        if "query" in optimized:
            optimized["query"] = optimize_regex_clause(optimized["query"])

        return optimized, notes

    @staticmethod
    def _optimize_fuzzy(query: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Optimize fuzzy queries.

        Args:
            query: Fuzzy query dictionary

        Returns:
            Tuple of (optimized query, optimization notes)
        """
        notes = []
        optimized = query.copy()

        def optimize_fuzzy_clause(clause):
            if isinstance(clause, dict) and "fuzzy" in clause:
                for field, params in clause["fuzzy"].items():
                    if isinstance(params, dict):
                        # Ensure prefix_length is set for performance
                        if "prefix_length" not in params:
                            params["prefix_length"] = 2
                            notes.append("Added prefix_length=2 for better fuzzy performance")

                        # Limit max_expansions if not set
                        if "max_expansions" not in params:
                            params["max_expansions"] = 50
                            notes.append("Added max_expansions=50 to limit fuzzy expansions")

            return clause

        if "query" in optimized:
            optimized["query"] = optimize_fuzzy_clause(optimized["query"])

        return optimized, notes

    @staticmethod
    def _optimize_boolean(query: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Optimize boolean queries.

        Args:
            query: Boolean query dictionary

        Returns:
            Tuple of (optimized query, optimization notes)
        """
        notes = []
        optimized = query.copy()

        def optimize_bool_structure(clause):
            if isinstance(clause, dict) and "bool" in clause:
                bool_clause = clause["bool"]

                # Move filters from must to filter context for caching
                if "must" in bool_clause:
                    must_clauses = bool_clause["must"]
                    filter_candidates = []
                    remaining_must = []

                    for subclause in must_clauses:
                        # Term and range queries can be moved to filter context
                        if any(k in subclause for k in ["term", "terms", "range", "exists"]):
                            filter_candidates.append(subclause)
                        else:
                            remaining_must.append(subclause)

                    if filter_candidates:
                        bool_clause["must"] = remaining_must
                        bool_clause["filter"] = bool_clause.get("filter", []) + filter_candidates
                        notes.append(f"Moved {len(filter_candidates)} clauses to filter context for caching")

                # Remove empty arrays
                for key in list(bool_clause.keys()):
                    if isinstance(bool_clause[key], list) and not bool_clause[key]:
                        del bool_clause[key]

            return clause

        if "query" in optimized:
            optimized["query"] = optimize_bool_structure(optimized["query"])

        return optimized, notes

    @staticmethod
    def _apply_general_optimizations(query: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Apply general query optimizations.

        Args:
            query: Query dictionary

        Returns:
            Tuple of (optimized query, optimization notes)
        """
        notes = []
        optimized = query.copy()

        # Add preference for local shards if not set
        if "_source" not in optimized:
            optimized["_source"] = True

        # Limit highlighting fields if many are requested
        if "highlight" in optimized:
            highlight = optimized["highlight"]
            if "fields" in highlight and len(highlight["fields"]) > 5:
                # Limit to most important fields
                important_fields = ["title", "content", "diagnosis", "summary", "notes"]
                limited_fields = {k: v for k, v in highlight["fields"].items()
                                 if k in important_fields}
                optimized["highlight"]["fields"] = limited_fields
                notes.append("Limited highlighting to 5 most important fields")

        # Add track_total_hits optimization for large result sets
        if "track_total_hits" not in optimized:
            optimized["track_total_hits"] = 10000
            notes.append("Added track_total_hits limit for performance")

        return optimized, notes

    @staticmethod
    def _add_execution_hints(query: Dict[str, Any], index_stats: Dict[str, Any]) -> List[str]:
        """
        Add execution hints based on index statistics.

        Args:
            query: Query dictionary
            index_stats: Index statistics

        Returns:
            List of execution hints
        """
        hints = []

        # Check index size
        doc_count = index_stats.get("doc_count", 0)
        if doc_count > 1000000:
            hints.append("TIP: Large index detected - consider using filters to narrow results")

        # Check if warming would help
        if doc_count > 100000:
            hints.append("TIP: Consider index warming for frequently used queries")

        return hints

    @staticmethod
    def analyze_complexity(query_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze query complexity.

        Args:
            query_dict: Elasticsearch query dictionary

        Returns:
            Complexity analysis with score and breakdown
        """
        complexity_score = 0
        breakdown = {}

        def calculate_complexity(clause, depth=1):
            nonlocal complexity_score, breakdown

            if isinstance(clause, dict):
                for query_type, params in clause.items():
                    if query_type in QueryOptimizer.COMPLEXITY_WEIGHTS:
                        weight = QueryOptimizer.COMPLEXITY_WEIGHTS[query_type]
                        score = weight * depth
                        complexity_score += score
                        breakdown[query_type] = breakdown.get(query_type, 0) + score

                    # Recurse for nested structures
                    if query_type == "bool":
                        for key in ["must", "should", "must_not", "filter"]:
                            if key in params:
                                clauses = params[key]
                                if isinstance(clauses, list):
                                    for subclause in clauses:
                                        calculate_complexity(subclause, depth + 1)

        if "query" in query_dict:
            calculate_complexity(query_dict["query"])

        return {
            "total_score": complexity_score,
            "max_score": QueryOptimizer.MAX_COMPLEXITY,
            "is_complex": complexity_score > QueryOptimizer.MAX_COMPLEXITY,
            "breakdown": breakdown,
            "recommendations": QueryOptimizer._get_complexity_recommendations(
                complexity_score, breakdown
            )
        }

    @staticmethod
    def _get_complexity_recommendations(score: int, breakdown: Dict[str, str]) -> List[str]:
        """
        Get recommendations based on complexity analysis.

        Args:
            score: Total complexity score
            breakdown: Complexity breakdown by query type

        Returns:
            List of recommendations
        """
        recommendations = []

        if score > QueryOptimizer.MAX_COMPLEXITY:
            recommendations.append("Query is very complex - consider simplifying or splitting")

        if breakdown.get("regexp", 0) > 20:
            recommendations.append("Regex queries are expensive - consider alternatives")

        if breakdown.get("wildcard", 0) > 15:
            recommendations.append("Many wildcards detected - consider using ngram tokenizer")

        if breakdown.get("fuzzy", 0) > 10:
            recommendations.append("Multiple fuzzy queries - ensure prefix_length is set")

        return recommendations