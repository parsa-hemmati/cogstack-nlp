"""Full-text search service using Elasticsearch.

Provides:
- Multi-field document search with relevance ranking
- Faceted search (document type, department, date histogram)
- Search result highlighting
- Autocomplete suggestions with Redis caching
- Search analytics tracking
"""

from typing import List, Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
import redis.asyncio as redis
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import time
import logging

from app.services.elasticsearch.search_query_builder import SearchQueryBuilder
from app.services.elasticsearch.index_config import INDEX_NAME

logger = logging.getLogger(__name__)


# Pydantic models for search
class SearchQuery(BaseModel):
    """Search query parameters."""
    q: str
    query_type: Optional[str] = "standard"  # standard, boolean, wildcard, fuzzy, proximity, range, regex
    fields: Optional[List[str]] = None
    document_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    department: Optional[str] = None
    author: Optional[str] = None
    page: int = 1
    page_size: int = 20


class SearchResult(BaseModel):
    """Single search result."""
    document_id: str
    title: str
    content_snippet: str
    document_type: str
    author: str
    department: str
    date: Optional[str]
    relevance_score: float
    highlights: List[str]


class SearchResponse(BaseModel):
    """Search response with results and metadata."""
    query: str
    total_results: int
    page: int
    page_size: int
    total_pages: int
    results: List[SearchResult]
    facets: Dict[str, Dict[str, int]]
    execution_time_ms: int


class SearchService:
    """Full-text search service using Elasticsearch."""

    def __init__(
        self,
        es_client: AsyncElasticsearch,
        redis_client: Optional[redis.Redis] = None,
        db: Optional[AsyncSession] = None
    ):
        """
        Initialize search service.

        Args:
            es_client: Async Elasticsearch client
            redis_client: Optional Redis client for caching
            db: Optional database session for analytics tracking
        """
        self.es = es_client
        self.redis = redis_client
        self.db = db

    async def search(
        self,
        query: SearchQuery,
        user_id: Optional[str] = None
    ) -> SearchResponse:
        """
        Execute full-text search with faceting and highlighting.

        Args:
            query: Search parameters
            user_id: User executing search (for analytics)

        Returns:
            Search results with facets and highlights

        Raises:
            elasticsearch.exceptions.ElasticsearchException: If search fails
        """
        start_time = time.time()

        try:
            # Build filters for advanced query types
            filters = {}
            if query.document_type:
                filters["document_type"] = query.document_type
            if query.department:
                filters["department"] = query.department
            if query.date_from or query.date_to:
                filters["date_from"] = query.date_from
                filters["date_to"] = query.date_to

            # Build Elasticsearch query based on query type
            if query.query_type == "boolean":
                # Boolean query with AND/OR/NOT
                es_query = SearchQueryBuilder.build_boolean_query(
                    query_text=query.q,
                    filters=filters,
                    fields=query.fields
                )
            elif query.query_type == "wildcard":
                # Wildcard query with * and ?
                es_query = SearchQueryBuilder.build_wildcard_query(
                    query_text=query.q,
                    filters=filters
                )
            elif query.query_type == "fuzzy":
                # Fuzzy query for typo tolerance
                es_query = SearchQueryBuilder.build_fuzzy_query(
                    query_text=query.q,
                    filters=filters
                )
            elif query.query_type == "proximity":
                # Proximity search with NEAR/W/ADJ operators
                es_query = SearchQueryBuilder.build_proximity_query(
                    query_text=query.q,
                    filters=filters
                )
            elif query.query_type == "range":
                # Range queries for numeric and date fields
                es_query = SearchQueryBuilder.build_range_query(
                    query_text=query.q,
                    filters=filters
                )
            elif query.query_type == "regex":
                # Regular expression queries
                es_query = SearchQueryBuilder.build_regex_query(
                    query_text=query.q,
                    filters=filters
                )
            else:
                # Default to standard multi-field query
                es_query = SearchQueryBuilder.build_query(
                    query_text=query.q,
                    fields=query.fields,
                    document_type=query.document_type,
                    date_from=query.date_from,
                    date_to=query.date_to,
                    department=query.department,
                    author=query.author,
                    page=query.page,
                    page_size=query.page_size,
                    include_aggregations=True,
                    include_highlighting=True
                )

            # Add aggregations for non-standard query types
            if query.query_type != "standard" and "aggs" not in es_query:
                es_query["aggs"] = SearchQueryBuilder._build_aggregations()

            # Add highlighting for non-standard query types
            if query.query_type != "standard" and "highlight" not in es_query:
                es_query["highlight"] = SearchQueryBuilder._build_highlighting()

            # Execute search
            from_offset = (query.page - 1) * query.page_size

            response = await self.es.search(
                index=INDEX_NAME,
                body=es_query,
                from_=from_offset,
                size=query.page_size
            )

            # Parse results
            results = self._parse_results(response)
            facets = self._parse_facets(response)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Calculate total pages
            total_results = response['hits']['total']['value']
            total_pages = (total_results + query.page_size - 1) // query.page_size

            # Track search analytics (async, don't block response)
            if user_id and self.db:
                try:
                    await self._track_search(
                        user_id=user_id,
                        query=query,
                        total_results=total_results,
                        execution_time_ms=execution_time_ms
                    )
                except Exception as e:
                    logger.warning(f"Failed to track search analytics: {e}")

            return SearchResponse(
                query=query.q,
                total_results=total_results,
                page=query.page,
                page_size=query.page_size,
                total_pages=total_pages,
                results=results,
                facets=facets,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _parse_results(self, response: Dict[str, Any]) -> List[SearchResult]:
        """
        Parse Elasticsearch response into SearchResult objects.

        Args:
            response: Elasticsearch search response

        Returns:
            List of SearchResult objects
        """
        results = []

        for hit in response['hits']['hits']:
            source = hit['_source']
            highlights = []

            # Extract highlights
            if 'highlight' in hit:
                if 'title' in hit['highlight']:
                    highlights.extend(hit['highlight']['title'])
                if 'content' in hit['highlight']:
                    highlights.extend(hit['highlight']['content'])

            # Content snippet (use first highlight or truncate content)
            if highlights:
                content_snippet = highlights[0]
            else:
                content = source.get('content', '')
                content_snippet = content[:200] + '...' if len(content) > 200 else content

            results.append(SearchResult(
                document_id=source.get('document_id', hit['_id']),
                title=source.get('title', 'Untitled'),
                content_snippet=content_snippet,
                document_type=source.get('document_type', 'unknown'),
                author=source.get('author', 'Unknown'),
                department=source.get('department', 'Unknown'),
                date=source.get('date'),
                relevance_score=hit['_score'],
                highlights=highlights
            ))

        return results

    def _parse_facets(self, response: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """
        Parse Elasticsearch aggregations into facet counts.

        Args:
            response: Elasticsearch search response

        Returns:
            Dictionary of facet counts
        """
        facets = {}

        if 'aggregations' not in response:
            return facets

        aggs = response['aggregations']

        # Document type facet
        if 'document_type' in aggs:
            facets['document_type'] = {
                bucket['key']: bucket['doc_count']
                for bucket in aggs['document_type']['buckets']
            }

        # Department facet
        if 'department' in aggs:
            facets['department'] = {
                bucket['key']: bucket['doc_count']
                for bucket in aggs['department']['buckets']
            }

        # Date histogram facet
        if 'date_histogram' in aggs:
            facets['date_histogram'] = {
                bucket['key_as_string']: bucket['doc_count']
                for bucket in aggs['date_histogram']['buckets']
            }

        return facets

    async def _track_search(
        self,
        user_id: str,
        query: SearchQuery,
        total_results: int,
        execution_time_ms: int
    ):
        """
        Track search analytics in database.

        Args:
            user_id: User executing search
            query: Search query
            total_results: Number of results found
            execution_time_ms: Query execution time in milliseconds
        """
        if not self.db:
            logger.warning("Database session not available for search tracking")
            return

        try:
            from app.services.search_analytics_service import SearchAnalyticsService
            from uuid import UUID

            analytics_service = SearchAnalyticsService(self.db)

            # Build filters dict
            filters = {}
            if query.document_type:
                filters['document_type'] = query.document_type
            if query.date_from:
                filters['date_from'] = query.date_from
            if query.date_to:
                filters['date_to'] = query.date_to
            if query.department:
                filters['department'] = query.department
            if query.author:
                filters['author'] = query.author

            # Track search
            await analytics_service.track_search(
                user_id=UUID(user_id),
                query=query.q,
                filters=filters if filters else None,
                total_results=total_results,
                page=query.page,
                execution_time_ms=execution_time_ms
            )

            logger.info(
                f"Search tracked: user={user_id}, query='{query.q}', "
                f"results={total_results}, time={execution_time_ms}ms"
            )

        except Exception as e:
            logger.error(f"Failed to track search: {e}")
            # Don't raise - tracking failure shouldn't break search

    async def get_suggestions(
        self,
        partial_query: str,
        size: int = 5
    ) -> List[str]:
        """
        Get autocomplete suggestions.

        Uses Redis cache for fast response (<200ms).
        Falls back to Elasticsearch completion suggester if not cached.

        Args:
            partial_query: Partial search query (minimum 2 chars)
            size: Maximum suggestions to return

        Returns:
            List of suggestion strings

        Raises:
            ValueError: If partial_query too short
        """
        if len(partial_query) < 2:
            raise ValueError("Query must be at least 2 characters")

        try:
            # Check Redis cache
            if self.redis:
                cache_key = f"suggest:{partial_query.lower()}"
                cached = await self.redis.get(cache_key)

                if cached:
                    # Decode and parse cached suggestions
                    suggestions_str = cached.decode('utf-8') if isinstance(cached, bytes) else cached
                    return suggestions_str.split(',')[:size]

            # Query Elasticsearch suggest API
            suggest_query = SearchQueryBuilder.build_suggest_query(partial_query, size)

            response = await self.es.search(
                index=INDEX_NAME,
                body=suggest_query
            )

            # Parse suggestions
            suggestions = []
            if 'suggest' in response:
                for suggestion in response['suggest']['simple_phrase']:
                    for option in suggestion['options']:
                        suggestions.append(option['text'])

            # Cache for 1 hour
            if self.redis and suggestions:
                cache_key = f"suggest:{partial_query.lower()}"
                await self.redis.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    ','.join(suggestions)
                )

            return suggestions[:size]

        except Exception as e:
            logger.error(f"Suggestions failed: {e}")
            # Return empty list on error (don't fail search UX)
            return []

    async def get_analytics(
        self,
        date_from: str,
        date_to: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get search analytics (top queries, zero-result queries, etc.).

        Args:
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            limit: Maximum results to return

        Returns:
            Analytics dictionary
        """
        if not self.db:
            logger.warning("Database session not available for analytics")
            return {
                "date_range": {"from": date_from, "to": date_to},
                "total_searches": 0,
                "unique_users": 0,
                "top_queries": [],
                "zero_result_queries": []
            }

        try:
            from app.services.search_analytics_service import SearchAnalyticsService
            from datetime import datetime

            analytics_service = SearchAnalyticsService(self.db)

            # Parse dates
            date_from_dt = datetime.fromisoformat(date_from)
            date_to_dt = datetime.fromisoformat(date_to)

            # Get analytics
            analytics = await analytics_service.get_full_analytics(
                date_from=date_from_dt,
                date_to=date_to_dt,
                limit=limit
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            raise
